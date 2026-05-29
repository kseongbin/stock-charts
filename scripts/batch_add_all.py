"""
DART 전체 상장법인 배치 추가 스크립트

3단계 처리:
  Phase 1 register   - DART 전체 상장법인을 STOCKS 배열에 등록 (HTML 생성 없음)
  Phase 2 charts     - 차트 HTML 미생성 종목만 1개씩 순차 생성
  Phase 3 financials - 하루 300개씩 재무 HTML 생성

진행 상태는 scripts/batch_state.json에 저장 → 중단 후 재실행 시 이어서 처리

사용법:
  python3 scripts/batch_add_all.py --phase register
  python3 scripts/batch_add_all.py --phase charts
  python3 scripts/batch_add_all.py --phase financials
  python3 scripts/batch_add_all.py --phase financials --size 100
  python3 scripts/batch_add_all.py --status
  python3 scripts/batch_add_all.py --retry
"""

import sys, os, io, json, re, zipfile, time, subprocess, argparse
import datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE, 'scripts')
STATE_FILE  = os.path.join(SCRIPTS_DIR, 'batch_state.json')
LOG_FILE    = os.path.join(SCRIPTS_DIR, 'batch_log.txt')
CHART_SCRIPT     = os.path.join(SCRIPTS_DIR, 'update_chart.py')
FINANCIAL_SCRIPT = os.path.join(SCRIPTS_DIR, 'update_financial.py')

DART_KEY   = os.environ.get('DART_API_KEY', '')
PUSH_EVERY = 50   # N개마다 git push
API_SLEEP  = 1.5  # DART API 호출 간 대기 (초)


# ─── 상태 관리 ──────────────────────────────────────────────

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'all_companies':    [],  # [{name, code, corp_code}]
        'registered':       [],  # Phase1 완료 code 목록
        'charts_done':      [],  # Phase2 완료 code 목록
        'financials_done':  [],  # Phase3 완료 code 목록
        'failed_register':  {},  # {code: error}
        'failed_chart':     {},  # {code: error}
        'failed_financial': {},  # {code: error}
    }

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ─── 로그 ────────────────────────────────────────────────────

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


# ─── DART API ────────────────────────────────────────────────

def dart_get(path, params):
    params['crtfc_key'] = DART_KEY
    url = f'https://opendart.fss.or.kr/api/{path}?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def fetch_all_dart_companies():
    """DART corpCode.xml → 전체 상장법인 목록"""
    log("DART corpCode.xml 다운로드 중 (30~60초)...")
    url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}'
    with urllib.request.urlopen(url, timeout=90) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open('CORPCODE.xml') as f:
            tree = ET.parse(f)
    companies = []
    for corp in tree.getroot().findall('list'):
        stock_code = corp.findtext('stock_code', '').strip()
        if not stock_code:
            continue  # 비상장 제외
        companies.append({
            'code':      stock_code,
            'corp_code': corp.findtext('corp_code', '').strip(),
            'name':      corp.findtext('corp_name', '').strip(),
        })
    log(f"  → 상장법인 {len(companies):,}개")
    return companies


def get_market_suffix(corp_code):
    """DART company.json → .KS / .KQ 반환"""
    try:
        data = dart_get('company.json', {'corp_code': corp_code})
        if data.get('status') == '000':
            mkt  = data.get('stock_mkt', '')
            name = data.get('corp_name', '')
            if '코스닥' in mkt:
                return '.KQ', name
            if '유가' in mkt or 'KOSPI' in mkt.upper():
                return '.KS', name
    except Exception:
        pass
    return '.KQ', ''  # 기본값


# ─── 파일 수정 ────────────────────────────────────────────────

def get_registered_codes():
    """update_chart.py STOCKS에서 이미 등록된 종목코드 집합"""
    with open(CHART_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()
    return set(re.findall(r'"code":\s*"([^"]+)"', content))


def add_to_chart(name, code, ticker, filename):
    with open(CHART_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'\]\s*\nMA_DAYS', content)
    if not m:
        return False
    last_pos = content.rfind('},\n', 0, m.start())
    if last_pos == -1:
        return False
    ins = last_pos + len('},\n')
    entry = f'    {{"ticker": "{ticker}", "name": "{name}", "code": "{code}", "filename": "{filename}"}},\n'
    content = content[:ins] + entry + content[ins:]
    with open(CHART_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def add_to_financial(name, code, corp_code, ticker, filename_base):
    with open(FINANCIAL_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()
    stocks_start = content.find('STOCKS = [')
    if stocks_start == -1:
        return False
    stocks_end = content.find('\n]\n', stocks_start)
    if stocks_end == -1:
        return False
    last_pos = content.rfind('    },\n', stocks_start, stocks_end + 1)
    if last_pos == -1:
        return False
    ins = last_pos + len('    },\n')
    entry = (
        f"    {{\n"
        f"        'name': '{name}',\n"
        f"        'code': '{code}',\n"
        f"        'corp_code': '{corp_code}',\n"
        f"        'ticker': '{ticker}',\n"
        f"        'capital': 0,\n"
        f"        'annual_file': '{filename_base}_financial.html',\n"
        f"        'quarter_file': '{filename_base}_financial_q.html',\n"
        f"    }},\n"
    )
    content = content[:ins] + entry + content[ins:]
    with open(FINANCIAL_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def update_agent_mapping():
    with open(CHART_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = re.findall(
        r'\{"ticker": "(.+?)", "name": "(.+?)", "code": "(.+?)", "filename": "(.+?)"\}',
        content
    )
    lines = [
        "## 종목-파일명 매핑표 (반드시 이 표에서 {파일명} 조회)\n\n",
        "표에 없는 종목은 새로 추가된 것이므로 사용자에게 파일명 확인 요청.\n\n",
        "| 기업명 | 종목코드 | 파일명 |\n",
        "|--------|---------|--------|\n",
    ]
    for _, name, code, filename in entries:
        base = filename.replace('.html', '')
        lines.append(f"| {name} | {code} | {base} |\n")
    mapping_file = os.path.join(BASE, 'AGENT_MAPPING.md')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    log(f"AGENT_MAPPING.md 업데이트: {len(entries)}개 종목")


# ─── Git ─────────────────────────────────────────────────────

def git_commit_push(msg):
    subprocess.run(['git', 'add', '.'], cwd=BASE)
    r = subprocess.run(['git', 'commit', '-m', msg], cwd=BASE,
                       capture_output=True, text=True)
    if 'nothing to commit' in r.stdout + r.stderr:
        return
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE)
    if result.returncode == 0:
        _cleanup_local_html()
        try:
            urllib.request.urlopen(
                'https://purge.jsdelivr.net/gh/kseongbin/stock-charts@main/AGENT_MAPPING.md',
                timeout=10
            )
        except Exception:
            pass
        log("  ✅ push 완료")
    else:
        log("  ⚠️  push 실패 (나중에 수동 push 필요)")


def _cleanup_local_html():
    """push 완료 후 로컬 HTML 파일 삭제 (GitHub에는 유지, 디스크 공간 확보)"""
    r = subprocess.run(['git', 'ls-files', '*.html'], cwd=BASE,
                       capture_output=True, text=True)
    html_files = [f for f in r.stdout.splitlines() if f]
    if not html_files:
        return
    subprocess.run(['git', 'update-index', '--skip-worktree'] + html_files, cwd=BASE)
    removed = 0
    for f in html_files:
        path = os.path.join(BASE, f)
        if os.path.exists(path):
            os.remove(path)
            removed += 1
    if removed:
        log(f"  🗑️  로컬 HTML {removed}개 삭제 (GitHub에는 유지)")


# ─── Phase 1: Register ────────────────────────────────────────

def phase_register(state):
    log("=" * 60)
    log("Phase 1: 전체 상장법인 STOCKS 등록 시작")

    # 전체 목록 로드 (최초 1회만 DART 다운로드)
    if not state['all_companies']:
        state['all_companies'] = fetch_all_dart_companies()
        save_state(state)

    companies   = state['all_companies']
    in_script   = get_registered_codes()
    done_set    = set(state['registered'])
    failed_set  = set(state['failed_register'].keys())

    pending = [
        c for c in companies
        if c['code'] not in in_script
        and c['code'] not in done_set
        and c['code'] not in failed_set
    ]

    log(f"전체 {len(companies):,}개 | 스크립트 기등록 {len(in_script):,}개 | 신규 대상 {len(pending):,}개")

    if not pending:
        log("등록할 신규 종목이 없습니다.")
        return

    ok = fail = 0
    for i, corp in enumerate(pending, 1):
        code, corp_code, name = corp['code'], corp['corp_code'], corp['name']
        try:
            suffix, api_name = get_market_suffix(corp_code)
            if api_name:
                name = api_name

            ticker   = f'{code}{suffix}'
            filename = f'{code}.html'

            add_to_chart(name, code, ticker, filename)
            add_to_financial(name, code, corp_code, ticker, code)

            state['registered'].append(code)
            ok += 1

        except Exception as e:
            state['failed_register'][code] = str(e)
            fail += 1
            log(f"  ❌ [{code}] {name}: {e}")

        if i % 50 == 0:
            save_state(state)
            log(f"  진행 {i}/{len(pending)} (✅{ok} ❌{fail})")

        time.sleep(API_SLEEP)

    save_state(state)
    update_agent_mapping()
    git_commit_push(f'Batch register {ok} companies (Phase 1)')
    log(f"Phase 1 완료: 성공 {ok:,}개, 실패 {fail:,}개")
    if fail:
        log(f"  실패 목록은 batch_state.json 확인. --retry 로 재시도 가능.")


# ─── Phase 2: Charts ──────────────────────────────────────────

def phase_charts(state, batch_size=300):
    log("=" * 60)
    log(f"Phase 2: 차트 생성 시작 (배치 {batch_size}개/회)")

    charts_done_set = set(state['charts_done'])
    failed_set      = set(state['failed_chart'].keys())

    pending = [
        code for code in state['registered']
        if code not in charts_done_set and code not in failed_set
    ]

    # 이미 HTML이 있으면 done 처리
    truly_pending = []
    for code in pending:
        html_path = os.path.join(BASE, f'{code}.html')
        if os.path.exists(html_path):
            state['charts_done'].append(code)
        else:
            truly_pending.append(code)

    log(f"차트 미생성 {len(truly_pending):,}개 | 오늘 처리 {min(batch_size, len(truly_pending))}개")

    batch = truly_pending[:batch_size]
    ok = fail = 0

    for i, code in enumerate(batch, 1):
        try:
            r = subprocess.run(
                ['python3', CHART_SCRIPT, f'--only={code}'],
                cwd=BASE, timeout=60,
                env={**os.environ, 'DART_API_KEY': DART_KEY}
            )
            if r.returncode == 0:
                state['charts_done'].append(code)
                ok += 1
                log(f"  [{i}/{len(batch)}] ✅ {code}")
            else:
                state['failed_chart'][code] = 'returncode!=0'
                fail += 1
                log(f"  [{i}/{len(batch)}] ❌ {code}: 스크립트 오류")
        except subprocess.TimeoutExpired:
            state['failed_chart'][code] = 'timeout'
            fail += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: 타임아웃")
        except Exception as e:
            state['failed_chart'][code] = str(e)
            fail += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: {e}")

        if i % PUSH_EVERY == 0:
            save_state(state)
            git_commit_push(f'Batch charts {ok} done (Phase 2 progress)')

    save_state(state)
    git_commit_push(f'Batch charts batch complete: {ok} done, {fail} failed (Phase 2)')

    remaining = len(truly_pending) - len(batch)
    log(f"Phase 2 배치 완료: ✅{ok} ❌{fail} | 남은 {remaining:,}개")
    if remaining > 0:
        days = (remaining - 1) // batch_size + 1
        log(f"  내일 계속: python3 scripts/batch_add_all.py --phase charts --size {batch_size}")
        log(f"  예상 잔여 일수: {days}일")


# ─── Phase 3: Financials ─────────────────────────────────────

def phase_financials(state, batch_size=300):
    log("=" * 60)
    log(f"Phase 3: 재무 생성 시작 (배치 {batch_size}개/회)")

    done_set   = set(state['financials_done'])
    failed_set = set(state['failed_financial'].keys())

    pending = [
        code for code in state['registered']
        if code not in done_set and code not in failed_set
    ]

    # 이미 HTML이 있으면 done 처리
    truly_pending = []
    for code in pending:
        fin_path = os.path.join(BASE, f'{code}_financial.html')
        if os.path.exists(fin_path):
            state['financials_done'].append(code)
        else:
            truly_pending.append(code)

    log(f"재무 미생성 {len(truly_pending):,}개 | 오늘 처리 {min(batch_size, len(truly_pending))}개")

    batch = truly_pending[:batch_size]
    ok = fail = 0

    for i, code in enumerate(batch, 1):
        try:
            r = subprocess.run(
                ['python3', FINANCIAL_SCRIPT, f'--only={code}', '--force'],
                cwd=BASE, timeout=120,
                env={**os.environ, 'DART_API_KEY': DART_KEY}
            )
            if r.returncode == 0:
                state['financials_done'].append(code)
                ok += 1
                log(f"  [{i}/{len(batch)}] ✅ {code}")
            else:
                state['failed_financial'][code] = 'returncode!=0'
                fail += 1
                log(f"  [{i}/{len(batch)}] ❌ {code}: 스크립트 오류")
        except subprocess.TimeoutExpired:
            state['failed_financial'][code] = 'timeout'
            fail += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: 타임아웃")
        except Exception as e:
            state['failed_financial'][code] = str(e)
            fail += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: {e}")

        if i % PUSH_EVERY == 0:
            save_state(state)
            git_commit_push(f'Batch financials {ok} done (Phase 3 progress)')

        time.sleep(1)

    save_state(state)
    git_commit_push(f'Batch financials complete: {ok} done, {fail} failed (Phase 3)')

    remaining = len(truly_pending) - len(batch)
    log(f"Phase 3 배치 완료: ✅{ok} ❌{fail} | 남은 {remaining:,}개")
    if remaining > 0:
        days = (remaining - 1) // batch_size + 1
        log(f"  내일 계속: python3 scripts/batch_add_all.py --phase financials")
        log(f"  예상 잔여 일수: {days}일")


# ─── Status ──────────────────────────────────────────────────

def show_status(state):
    total    = len(state['all_companies'])
    reg      = len(state['registered'])
    ch_done  = len(state['charts_done'])
    fin_done = len(state['financials_done'])
    fail_r   = len(state['failed_register'])
    fail_c   = len(state['failed_chart'])
    fail_f   = len(state['failed_financial'])

    print(f"\n{'='*55}")
    print(f"  DART 배치 처리 현황")
    print(f"{'='*55}")
    print(f"  Phase 1 (등록)")
    print(f"    DART 전체       : {total:>6,}개")
    print(f"    등록 완료       : {reg:>6,}개")
    print(f"    등록 실패       : {fail_r:>6,}개")
    print(f"  Phase 2 (차트)")
    print(f"    차트 생성 완료  : {ch_done:>6,}개")
    print(f"    차트 실패       : {fail_c:>6,}개")
    if reg > 0:
        ch_remain = reg - ch_done - fail_c
        print(f"    차트 남은 종목  : {ch_remain:>6,}개 (약 {max(0,(ch_remain-1)//300+1)}일)")
    print(f"  Phase 3 (재무)")
    print(f"    재무 생성 완료  : {fin_done:>6,}개")
    print(f"    재무 실패       : {fail_f:>6,}개")
    if reg > 0:
        fin_remain = reg - fin_done - fail_f
        print(f"    재무 남은 종목  : {fin_remain:>6,}개 (약 {max(0,(fin_remain-1)//300+1)}일)")
    print(f"{'='*55}\n")


# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DART 전체 상장법인 배치 추가')
    parser.add_argument('--phase', choices=['register', 'charts', 'financials'],
                        help='실행 단계')
    parser.add_argument('--size', type=int, default=300,
                        help='배치 크기 (기본 300)')
    parser.add_argument('--status', action='store_true',
                        help='진행 상황 확인')
    parser.add_argument('--retry', action='store_true',
                        help='실패 종목을 실패 목록에서 제거해 재시도 대상으로 복원')
    args = parser.parse_args()

    if not DART_KEY:
        print("❌ DART_API_KEY 환경변수 필요\n   export DART_API_KEY='your_key'")
        sys.exit(1)

    state = load_state()

    if args.status:
        show_status(state)
        return

    if args.retry:
        fr = len(state['failed_register'])
        fc = len(state['failed_chart'])
        ff = len(state['failed_financial'])
        state['failed_register']  = {}
        state['failed_chart']     = {}
        state['failed_financial'] = {}
        save_state(state)
        log(f"실패 목록 초기화: 등록 {fr}개, 차트 {fc}개, 재무 {ff}개 → 재시도 대상으로 복원")
        return

    if args.phase == 'register':
        phase_register(state)
    elif args.phase == 'charts':
        phase_charts(state, batch_size=args.size)
    elif args.phase == 'financials':
        phase_financials(state, batch_size=args.size)
    else:
        show_status(state)
        print("사용법:")
        print("  python3 scripts/batch_add_all.py --phase register")
        print("  python3 scripts/batch_add_all.py --phase charts [--size 300]")
        print("  python3 scripts/batch_add_all.py --phase financials [--size 300]")
        print("  python3 scripts/batch_add_all.py --status")
        print("  python3 scripts/batch_add_all.py --retry")


if __name__ == '__main__':
    main()

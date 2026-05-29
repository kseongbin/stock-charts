"""
종목 자동 추가 스크립트
사용법:
  python3 scripts/add_stock.py --code 062970

기능:
  1. DART company.json API → 실패 시 corpcode.zip에서 corp_code 조회
  2. update_chart.py STOCKS에 자동 추가
  3. update_financial.py STOCKS에 자동 추가
  4. 차트 + 재무 HTML 자동 생성
  5. git add/commit/push 자동 실행
"""

import sys
import os
import re
import io
import json
import zipfile
import argparse
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DART_KEY = os.environ.get('DART_API_KEY', '')

SCRIPTS_DIR = os.path.join(BASE, 'scripts')
CHART_SCRIPT = os.path.join(SCRIPTS_DIR, 'update_chart.py')
FINANCIAL_SCRIPT = os.path.join(SCRIPTS_DIR, 'update_financial.py')


# ===== DART API 함수 =====

def dart_get(path, params):
    params['crtfc_key'] = DART_KEY
    url = f'https://opendart.fss.or.kr/api/{path}?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def find_corp_code_api(stock_code):
    """company.json API로 corp_code 조회"""
    try:
        data = dart_get('company.json', {'stock_code': stock_code})
        if data.get('status') == '000':
            return data.get('corp_code'), data.get('corp_name'), data.get('stock_mkt')
    except Exception as e:
        print(f"  company.json 실패: {e}")
    return None, None, None


def find_corp_code_zip(stock_code):
    """corpcode.zip에서 corp_code 조회"""
    print("  DART corpcode.zip 다운로드 중 (약 5-10초)...")
    url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}'
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open('CORPCODE.xml') as f:
            tree = ET.parse(f)
    for corp in tree.getroot().findall('list'):
        if corp.findtext('stock_code', '').strip() == stock_code:
            corp_code = corp.findtext('corp_code', '').strip()
            corp_name = corp.findtext('corp_name', '').strip()
            return corp_code, corp_name
    return None, None


def find_corp_code(stock_code):
    """company.json → corpcode.zip 순으로 corp_code 조회"""
    corp_code, corp_name, stock_mkt = find_corp_code_api(stock_code)
    if corp_code:
        return corp_code, corp_name, stock_mkt

    print("  API 조회 실패. corpcode.zip에서 재시도...")
    corp_code, corp_name = find_corp_code_zip(stock_code)
    if not corp_code:
        return None, None, None

    # zip에서 찾은 경우 corp_code로 company.json 재조회해서 시장 정보 획득
    try:
        data = dart_get('company.json', {'corp_code': corp_code})
        if data.get('status') == '000':
            return corp_code, data.get('corp_name', corp_name), data.get('stock_mkt')
    except Exception:
        pass
    return corp_code, corp_name, None


def detect_market_yfinance(code):
    """yfinance로 KS/KQ 시장 자동 감지 (회사명 있는 티커 우선)"""
    try:
        import yfinance as yf
        candidates = []
        for suffix in ('.KS', '.KQ'):
            try:
                t = yf.Ticker(f'{code}{suffix}')
                hist = t.history(period='5d')
                if hist.empty:
                    continue
                name = t.info.get('longName') or ''
                candidates.append((suffix, bool(name)))
            except Exception:
                continue
        # 회사명이 있는 티커 우선, 없으면 데이터 있는 첫 번째
        for suffix, has_name in candidates:
            if has_name:
                return suffix
        if candidates:
            return candidates[0][0]
    except ImportError:
        pass
    return None


def get_capital(corp_code):
    """최신 사업보고서에서 자본금 조회"""
    import datetime
    cur_year = datetime.datetime.now().year
    for year in range(cur_year - 1, cur_year - 4, -1):
        try:
            data = dart_get('fnlttSinglAcnt.json', {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011',
                'fs_div': 'CFS',
            })
            if data.get('status') == '000' and data.get('list'):
                for item in data['list']:
                    if '자본금' in item.get('account_nm', '') and item.get('sj_div') == 'BS':
                        val = item.get('thstrm_amount', '').replace(',', '').replace('-', '')
                        if val.isdigit():
                            return int(val)
        except Exception:
            pass
    return 0


# ===== 파일 수정 함수 =====

def already_in_file(filepath, pattern):
    with open(filepath, 'r', encoding='utf-8') as f:
        return pattern in f.read()


def add_to_chart(name, code, ticker, filename):
    """update_chart.py STOCKS 배열 끝에 종목 추가"""
    with open(CHART_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()

    # ]\n...\nMA_DAYS 패턴으로 STOCKS 배열 끝 위치 탐색
    m = re.search(r'\]\s*\nMA_DAYS', content)
    if not m:
        print("  ❌ update_chart.py STOCKS 배열 끝(MA_DAYS)을 찾을 수 없습니다.")
        return False

    stocks_end = m.start()  # ']' 위치
    # ']' 이전의 마지막 },\n 위치 탐색
    last_pos = content.rfind('},\n', 0, stocks_end)
    if last_pos == -1:
        print("  ❌ update_chart.py STOCKS 마지막 항목을 찾을 수 없습니다.")
        return False

    insert_pos = last_pos + len('},\n')
    new_entry = f'    {{"ticker": "{ticker}", "name": "{name}", "code": "{code}", "filename": "{filename}"}},\n'
    content = content[:insert_pos] + new_entry + content[insert_pos:]

    with open(CHART_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def add_to_financial(name, code, corp_code, ticker, capital, filename_base):
    """update_financial.py STOCKS 배열 끝에 종목 추가"""
    with open(FINANCIAL_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()

    stocks_start = content.find('STOCKS = [')
    if stocks_start == -1:
        print("  ❌ update_financial.py STOCKS 배열을 찾을 수 없습니다.")
        return False

    # STOCKS 배열 닫는 '\n]\n' 위치 탐색
    stocks_end = content.find('\n]\n', stocks_start)
    if stocks_end == -1:
        print("  ❌ update_financial.py STOCKS 배열 끝(])을 찾을 수 없습니다.")
        return False

    # stocks_end는 ']' 앞 '\n'의 위치. +1 포함해서 탐색해야 마지막 '    },\n' 검색 가능
    last_pos = content.rfind('    },\n', stocks_start, stocks_end + 1)
    if last_pos == -1:
        print("  ❌ update_financial.py STOCKS 마지막 항목을 찾을 수 없습니다.")
        return False

    insert_pos = last_pos + len('    },\n')
    new_entry = (
        f"    {{\n"
        f"        'name': '{name}',\n"
        f"        'code': '{code}',\n"
        f"        'corp_code': '{corp_code}',\n"
        f"        'ticker': '{ticker}',\n"
        f"        'capital': {capital},\n"
        f"        'annual_file': '{filename_base}_financial.html',\n"
        f"        'quarter_file': '{filename_base}_financial_q.html',\n"
        f"    }},\n"
    )
    content = content[:insert_pos] + new_entry + content[insert_pos:]

    with open(FINANCIAL_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


# ===== 스크립트 실행 함수 =====

def run_chart(code=None):
    print("\n📈 차트 생성 중...")
    cmd = ['python3', CHART_SCRIPT]
    if code:
        cmd.append(f'--only={code}')
    result = subprocess.run(
        cmd,
        cwd=BASE,
        env={**os.environ, 'DART_API_KEY': DART_KEY},
    )
    return result.returncode == 0


def run_financial(filename_key):
    print("\n💰 재무 데이터 생성 중...")
    result = subprocess.run(
        ['python3', FINANCIAL_SCRIPT, f'--only={filename_key}', '--force'],
        cwd=BASE,
        env={**os.environ, 'DART_API_KEY': DART_KEY},
    )
    return result.returncode == 0


def update_agent_mapping(new_name=None, new_code=None, new_filename=None):
    """에이전트 시스템 프롬프트용 종목-파일명 매핑표 재생성"""
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

    print(f"\n📋 에이전트 매핑표 업데이트 완료: AGENT_MAPPING.md ({len(entries)}개 종목)")

    if new_name and new_code and new_filename:
        base = new_filename.replace('.html', '')
        print(f"\n{'='*60}")
        print(f"⚠️  Claude.ai 기업분석 에이전트 지침 업데이트 필요!")
        print(f"   매핑표에 아래 줄을 추가하세요:")
        print(f"\n   | {new_name} | {new_code} | {base} |")
        print(f"{'='*60}")


def git_push(name, code):
    print("\n🚀 GitHub push 중...")
    subprocess.run(['git', 'add', '.'], cwd=BASE)
    subprocess.run(['git', 'commit', '-m', f'Add {name} ({code}) chart, financials'], cwd=BASE)
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE)
    return result.returncode == 0


# ===== 메인 =====

def main():
    parser = argparse.ArgumentParser(description='종목 자동 추가')
    parser.add_argument('--code', required=True, help='종목코드 (예: 062970)')
    parser.add_argument('--filename', default=None, help='파일명 키 (예: kacm). 미입력시 종목코드 사용')
    parser.add_argument('--market', default=None, help='KS 또는 KQ (미입력시 자동감지)')
    parser.add_argument('--corp-code', default=None, help='DART corp_code 직접 입력 (예: 00403766)')
    parser.add_argument('--name', default=None, help='회사명 직접 입력')
    parser.add_argument('--no-push', action='store_true', help='git push 생략')
    args = parser.parse_args()

    code = args.code.strip()

    if not DART_KEY:
        print("❌ DART_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   export DART_API_KEY='your_key'")
        sys.exit(1)

    # 1. corp_code / 기업명 / 시장 조회
    if args.corp_code:
        corp_code = args.corp_code
        corp_name = args.name or code
        stock_mkt = None
        print(f"\n🔍 [{code}] corp_code 직접 입력 사용: {corp_code}")
        if not args.name:
            try:
                data = dart_get('company.json', {'corp_code': corp_code})
                if data.get('status') == '000':
                    corp_name = data.get('corp_name', code)
                    stock_mkt = data.get('stock_mkt')
            except Exception:
                pass
    else:
        print(f"\n🔍 [{code}] DART에서 기업 정보 조회 중...")
        corp_code, corp_name, stock_mkt = find_corp_code(code)
        if not corp_code:
            print(f"❌ 종목코드 {code}를 DART에서 찾을 수 없습니다.")
            print(f"   --corp-code 옵션으로 직접 입력해보세요.")
            sys.exit(1)

    print(f"  기업명  : {corp_name}")
    print(f"  corp_code: {corp_code}")
    print(f"  시장    : {stock_mkt or '미확인'}")

    # 2. 티커 결정
    if args.market:
        suffix = f'.{args.market}'
    elif stock_mkt == 'KOSDAQ':
        suffix = '.KQ'
    elif stock_mkt == 'KOSPI':
        suffix = '.KS'
    else:
        print(f"\n🔎 시장 자동 감지 중 (yfinance)...")
        suffix = detect_market_yfinance(code)
        if suffix:
            print(f"  감지된 시장: {suffix}")
        else:
            print(f"  ⚠️  시장 감지 실패 → .KQ 기본값 사용")
            suffix = '.KQ'

    ticker = f'{code}{suffix}'
    filename_key = args.filename or code.lower()
    chart_filename = f'{filename_key}.html'

    print(f"  티커    : {ticker}")
    print(f"  파일명  : {filename_key}")

    # 3. 중복 여부 확인
    chart_exists = already_in_file(CHART_SCRIPT, f'"code": "{code}"')
    financial_exists = already_in_file(FINANCIAL_SCRIPT, f"'code': '{code}'")

    if chart_exists and financial_exists:
        print(f"\n⚠️  {code}가 이미 두 스크립트에 모두 등록되어 있습니다.")
    else:
        # 4. 자본금 조회 (추가 필요한 경우)
        print(f"\n💼 자본금 조회 중...")
        capital = get_capital(corp_code)
        if capital:
            print(f"  자본금: {capital:,}원")
        else:
            print(f"  ⚠️  자본금 조회 실패 (0으로 설정)")

        # 5. update_chart.py에 추가
        if chart_exists:
            print(f"\n⚠️  update_chart.py에 이미 {code}가 있습니다. 추가 생략.")
        else:
            print(f"\n📝 update_chart.py에 추가 중...")
            if add_to_chart(corp_name, code, ticker, chart_filename):
                print(f"  ✅ 추가 완료")
            else:
                sys.exit(1)

        # 6. update_financial.py에 추가
        if financial_exists:
            print(f"\n⚠️  update_financial.py에 이미 {code}가 있습니다. 추가 생략.")
        else:
            print(f"\n📝 update_financial.py에 추가 중...")
            if add_to_financial(corp_name, code, corp_code, ticker, capital, filename_key):
                print(f"  ✅ 추가 완료")
            else:
                sys.exit(1)

    # 7. 차트 + 재무 생성
    run_chart(code)
    run_financial(filename_key)

    # 8. 에이전트 매핑표 업데이트
    update_agent_mapping(corp_name, code, filename_key)

    # 9. git push
    if not args.no_push:
        git_push(corp_name, code)
        print(f"\n✅ 완료! 2~3분 후 확인:")
        print(f"   https://kseongbin.github.io/stock-charts/{chart_filename}")
    else:
        print(f"\n✅ 스크립트 추가 완료 (push 생략)")


if __name__ == '__main__':
    main()

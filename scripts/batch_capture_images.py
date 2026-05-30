"""
Phase 4: 전체 상장법인 홈페이지 이미지 배치 캡처

DART company.json에서 홈페이지 URL 조회 → Playwright로 5개 페이지 자동 선택 캡처 →
기본 크롭 → GitHub push (push 후 로컬 PNG 삭제, GitHub에는 유지)

사용법:
  python3 scripts/batch_capture_images.py              # 기본 100개
  python3 scripts/batch_capture_images.py --size 50   # 50개
  python3 scripts/batch_capture_images.py --status    # 현황 확인
  python3 scripts/batch_capture_images.py --retry     # 실패 목록 재시도 대상으로 복원

진행 상태는 batch_state.json에 images_done / failed_images 키로 저장됨
"""

import sys, os, json, time, subprocess, asyncio, argparse, datetime, shutil
import urllib.request, urllib.parse

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE, 'scripts')
STATE_FILE = os.path.join(SCRIPTS_DIR, 'batch_state.json')
LOG_FILE   = os.path.join(SCRIPTS_DIR, 'batch_log.txt')
IMAGES_DIR = os.path.join(BASE, 'images')
CROP_SCRIPT = os.path.join(SCRIPTS_DIR, 'crop_images.py')

DART_KEY   = os.environ.get('DART_API_KEY', '')
PUSH_EVERY = 20  # 20개 기업(~100장)마다 push


# ─── 상태 관리 ───────────────────────────────────────────────

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state: dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ─── 로그 ────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


# ─── DART / 홈페이지 ─────────────────────────────────────────

def get_homepage_url(corp_code: str) -> str:
    params = {'crtfc_key': DART_KEY, 'corp_code': corp_code}
    url = 'https://opendart.fss.or.kr/api/company.json?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
    if data.get('status') == '000':
        hm = data.get('hm_url', '').strip()
        if hm and not hm.startswith('http'):
            hm = 'https://' + hm
        return hm
    return ''


# ─── 이미지 캡처 (add_by_name.py auto_capture 동일 로직) ─────

NAV_KEYWORDS = [
    ['제품', '사업', '솔루션', 'product', 'solution', 'business', 'service'],
    ['기술', 'technology', 'tech', 'r&d', '연구개발', 'innovation'],
    ['소재', '부품', '배터리', 'material', 'component', 'battery', 'semiconductor'],
    ['회사소개', 'about', '기업소개', 'company', '소개', '개요'],
    ['뉴스', '공지', 'news', 'press', '미디어', 'media', '보도'],
]


async def auto_capture(code: str, homepage_url: str) -> list:
    """홈페이지 nav에서 5개 페이지 자동 선택 후 캡처 → images/temp_{code}/ 에 저장"""
    from playwright.async_api import async_playwright

    TEMP_DIR = os.path.join(IMAGES_DIR, f'temp_{code}')
    os.makedirs(TEMP_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        )
        page = await context.new_page()
        try:
            await page.goto(homepage_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception:
            await browser.close()
            return []

        links = await page.evaluate("""() => {
            const seen = new Set();
            const res = [];
            const sels = 'nav a, header a, .nav a, .gnb a, .menu a, .lnb a, .header a';
            document.querySelectorAll(sels).forEach(el => {
                const href = el.href;
                const text = (el.textContent || '').trim().toLowerCase();
                if (href && href.startsWith('http') && !seen.has(href) && text.length > 0) {
                    seen.add(href);
                    res.push({href, text});
                }
            });
            return res;
        }""")

        selected = []
        used = {homepage_url}

        for keywords in NAV_KEYWORDS:
            if len(selected) >= 5:
                break
            for link in links:
                if link['href'] in used:
                    continue
                if any(kw in link['text'] or kw in link['href'].lower() for kw in keywords):
                    selected.append(link['href'])
                    used.add(link['href'])
                    break

        for link in links:
            if len(selected) >= 5:
                break
            if link['href'] not in used:
                selected.append(link['href'])
                used.add(link['href'])

        if len(selected) < 5:
            selected.insert(0, homepage_url)

        await page.close()

        captured = []
        for i, url in enumerate(selected[:5], 1):
            pg = await context.new_page()
            try:
                await pg.goto(url, wait_until='networkidle', timeout=30000)
                await pg.wait_for_timeout(3000)
                await pg.evaluate("""
                    document.querySelectorAll('*').forEach(el => {
                        const st = getComputedStyle(el);
                        if ((st.position === 'fixed' || st.position === 'sticky') && parseInt(st.zIndex) > 10)
                            el.style.display = 'none';
                    });
                    document.body.style.overflow = 'auto';
                """)
                await pg.evaluate("window.scrollTo(0, 450)")
                await pg.wait_for_timeout(800)
                out = os.path.join(TEMP_DIR, f'{code}_{i}_full.png')
                await pg.screenshot(path=out, full_page=False)
                captured.append(out)
            except Exception:
                pass
            finally:
                await pg.close()

        await browser.close()

    return captured


def run_crop(code: str) -> bool:
    result = subprocess.run(
        ['python3', CROP_SCRIPT, '--company', code],
        cwd=BASE, capture_output=True
    )
    return result.returncode == 0


def cleanup_temp(code: str):
    temp_dir = os.path.join(IMAGES_DIR, f'temp_{code}')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def images_exist(code: str) -> bool:
    return all(
        os.path.exists(os.path.join(IMAGES_DIR, f'{code}_{i}.png'))
        for i in range(1, 6)
    )


# ─── URL 사전 수집 ────────────────────────────────────────────

def fetch_homepage_urls(state: dict, batch_size: int = 300):
    """DART company.json으로 전체 기업 홈페이지 URL 사전 수집 → homepage_urls 캐시에 저장.
    이 단계를 먼저 실행하면 이미지 캡처 단계에서 DART API 호출 불필요.
    """
    log("=" * 60)
    log(f"Phase 4 URL 수집: DART company.json 홈페이지 URL 사전 조회")

    url_cache: dict = state.setdefault('homepage_urls', {})
    companies = state.get('all_companies', [])

    pending = [c for c in companies if c['code'] not in url_cache]
    log(f"URL 미수집 {len(pending):,}개 | 오늘 처리 {min(batch_size, len(pending))}개")

    batch = pending[:batch_size]
    found = no_url = quota_hit = 0

    for i, company in enumerate(batch, 1):
        code      = company['code']
        corp_code = company.get('corp_code', '')

        if not corp_code:
            url_cache[code] = ''
            no_url += 1
            continue

        try:
            homepage = get_homepage_url(corp_code)
            url_cache[code] = homepage
            if homepage:
                found += 1
                log(f"  [{i}/{len(batch)}] ✅ {code}: {homepage}")
            else:
                no_url += 1
                log(f"  [{i}/{len(batch)}] ⚠️ {code}: URL 없음")
        except Exception as e:
            err = str(e)
            if '020' in err or 'quota' in err.lower() or '사용한도' in err:
                log(f"  ⚠️ DART API 한도 초과! URL 수집 중단 ({i}번째 {code})")
                quota_hit += 1
                break
            url_cache[code] = ''
            no_url += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: {e}")

        time.sleep(0.3)  # DART API 속도 제한 대응

    save_state(state)
    remaining = len(pending) - len(batch) + (1 if quota_hit else 0)
    log(f"URL 수집 완료: ✅{found} ⚠️{no_url} | 남은 {remaining:,}개")
    if quota_hit:
        log("  DART 한도 초과. 내일 자정 이후 재실행: python3 scripts/batch_capture_images.py --fetch-urls")
    elif remaining > 0:
        log(f"  계속: python3 scripts/batch_capture_images.py --fetch-urls --size {batch_size}")


# ─── Git ─────────────────────────────────────────────────────

def git_commit_push(msg: str):
    subprocess.run(['git', 'add', 'images/'], cwd=BASE)
    r = subprocess.run(['git', 'commit', '-m', msg], cwd=BASE,
                       capture_output=True, text=True)
    if 'nothing to commit' in r.stdout + r.stderr:
        return
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE)
    if result.returncode == 0:
        _cleanup_local_images()
        log("  ✅ push 완료 (로컬 PNG 삭제)")
    else:
        log("  ⚠️  push 실패 (나중에 수동 push 필요)")


def _cleanup_local_images():
    """push 후 로컬 PNG 삭제 (GitHub에는 유지, 디스크 공간 확보)"""
    r = subprocess.run(
        ['git', 'ls-files', 'images/'],
        cwd=BASE, capture_output=True, text=True
    )
    png_files = [f for f in r.stdout.splitlines() if f.endswith('.png')]
    if not png_files:
        return
    subprocess.run(['git', 'update-index', '--skip-worktree'] + png_files, cwd=BASE)
    removed = 0
    for f in png_files:
        path = os.path.join(BASE, f)
        if os.path.exists(path):
            os.remove(path)
            removed += 1
    if removed:
        log(f"  로컬 PNG {removed}개 삭제 (GitHub에는 유지)")


# ─── Phase 4 ─────────────────────────────────────────────────

def phase_images(state: dict, batch_size: int = 100):
    log("=" * 60)
    log(f"Phase 4: 이미지 캡처 시작 (배치 {batch_size}개/회)")

    code_to_corp = {c['code']: c['corp_code'] for c in state.get('all_companies', [])}
    if not code_to_corp:
        log("❌ all_companies가 비어있습니다. batch_add_all.py --phase register 먼저 실행하세요.")
        return

    done_set   = set(state.setdefault('images_done', []))
    failed_map = state.setdefault('failed_images', {})
    failed_set = set(failed_map.keys())

    pending = [
        code for code in state.get('registered', [])
        if code not in done_set and code not in failed_set
    ]

    # 이미 이미지가 있으면 done으로 이동
    truly_pending = []
    for code in pending:
        if images_exist(code):
            state['images_done'].append(code)
            done_set.add(code)
        else:
            truly_pending.append(code)

    log(f"이미지 미생성 {len(truly_pending):,}개 | 오늘 처리 {min(batch_size, len(truly_pending))}개")

    batch = truly_pending[:batch_size]
    ok = fail = 0

    for i, code in enumerate(batch, 1):
        # URL 캐시 우선 사용, 없으면 DART API 실시간 조회
        url_cache = state.get('homepage_urls', {})
        if code in url_cache:
            homepage = url_cache[code]
        else:
            corp_code = code_to_corp.get(code)
            if not corp_code:
                failed_map[code] = 'no_corp_code'
                fail += 1
                log(f"  [{i}/{len(batch)}] ⚠️ {code}: corp_code 없음")
                continue
            try:
                homepage = get_homepage_url(corp_code)
                url_cache[code] = homepage
            except Exception as e:
                failed_map[code] = f'dart_error:{str(e)[:80]}'
                fail += 1
                log(f"  [{i}/{len(batch)}] ❌ {code}: DART 조회 실패")
                continue

        if not homepage:
            failed_map[code] = 'no_homepage'
            fail += 1
            log(f"  [{i}/{len(batch)}] ⚠️ {code}: 홈페이지 URL 없음 (DART 미등록)")
            continue

        log(f"  [{i}/{len(batch)}] 🌐 {code}: {homepage}")

        try:
            captured = asyncio.run(auto_capture(code, homepage))

            if not captured:
                cleanup_temp(code)
                failed_map[code] = 'capture_failed'
                fail += 1
                log(f"  [{i}/{len(batch)}] ❌ {code}: 홈페이지 로드 실패")
                continue

            run_crop(code)
            cleanup_temp(code)

            if images_exist(code):
                state['images_done'].append(code)
                ok += 1
                log(f"  [{i}/{len(batch)}] ✅ {code}: {len(captured)}장 완료")
            else:
                failed_map[code] = 'crop_failed'
                fail += 1
                log(f"  [{i}/{len(batch)}] ❌ {code}: 크롭 후 파일 없음")

        except Exception as e:
            cleanup_temp(code)
            failed_map[code] = str(e)[:120]
            fail += 1
            log(f"  [{i}/{len(batch)}] ❌ {code}: {e}")

        if i % PUSH_EVERY == 0:
            save_state(state)
            git_commit_push(f'Batch images {ok} done (Phase 4 progress)')

        time.sleep(1.5)

    save_state(state)
    git_commit_push(f'Batch images complete: {ok} done, {fail} failed (Phase 4)')

    remaining = len(truly_pending) - len(batch)
    log(f"Phase 4 배치 완료: ✅{ok} ❌{fail} | 남은 {remaining:,}개")
    if remaining > 0:
        log(f"  계속: python3 scripts/batch_capture_images.py --size {batch_size}")


# ─── Status ──────────────────────────────────────────────────

def show_status(state: dict):
    reg       = len(state.get('registered', []))
    img_done  = len(state.get('images_done', []))
    failed    = state.get('failed_images', {})
    img_fail  = len(failed)
    img_remain = reg - img_done - img_fail

    print(f"\n{'='*55}")
    print(f"  Phase 4 (이미지) 현황")
    print(f"{'='*55}")
    print(f"    등록된 종목       : {reg:>6,}개")
    print(f"    이미지 완료       : {img_done:>6,}개")
    print(f"    이미지 실패       : {img_fail:>6,}개")
    if reg > 0:
        print(f"    남은 종목         : {img_remain:>6,}개")
    if failed:
        reasons: dict[str, int] = {}
        for v in failed.values():
            reasons[v] = reasons.get(v, 0) + 1
        print(f"\n  실패 원인:")
        for reason, cnt in sorted(reasons.items(), key=lambda x: -x[1])[:8]:
            print(f"    {reason:<35}: {cnt:,}개")
    print(f"{'='*55}\n")


# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Phase 4: 전체 기업 홈페이지 이미지 배치 캡처')
    parser.add_argument('--size',       type=int, default=100, help='배치 크기 (기본 100)')
    parser.add_argument('--status',     action='store_true',   help='현황 확인')
    parser.add_argument('--retry',      action='store_true',   help='실패 목록 재시도 대상으로 복원')
    parser.add_argument('--fetch-urls', action='store_true',
                        help='DART company.json으로 홈페이지 URL 사전 수집 (이미지 캡처 전 실행 권장)')
    args = parser.parse_args()

    if not DART_KEY:
        print("❌ DART_API_KEY 환경변수 필요\n   export DART_API_KEY='your_key'")
        sys.exit(1)

    state = load_state()
    if not state or not state.get('registered'):
        print("❌ batch_state.json 없음 또는 registered 비어있음.")
        print("   python3 scripts/batch_add_all.py --phase register 먼저 실행하세요.")
        sys.exit(1)

    if args.status:
        show_status(state)
        return

    if args.retry:
        n = len(state.get('failed_images', {}))
        state['failed_images'] = {}
        save_state(state)
        print(f"✅ 실패 목록 {n}개 초기화 완료 (재시도 대상으로 복원)")
        return

    if args.fetch_urls:
        fetch_homepage_urls(state, args.size)
        return

    phase_images(state, args.size)


if __name__ == '__main__':
    main()

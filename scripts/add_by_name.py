"""
기업명으로 종목 전체 자동 추가
- 기업명 → DART 종목코드 자동 조회
- 차트/재무 HTML 생성 + GitHub Pages 배포
- 기업 홈페이지 자동 탐색 → 5장 이미지 캡처/크롭
- AGENT_MAPPING.md 자동 업데이트

사용법:
  python3 scripts/add_by_name.py 삼성SDI
  python3 scripts/add_by_name.py 네이버 --no-images
  python3 scripts/add_by_name.py 삼성SDI --filename sdi
"""

import sys, os, io, zipfile, asyncio, argparse, subprocess
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE, 'scripts')
ADD_STOCK = os.path.join(SCRIPTS_DIR, 'add_stock.py')
CROP_SCRIPT = os.path.join(SCRIPTS_DIR, 'crop_images.py')
DART_KEY = os.environ.get('DART_API_KEY', '')


# ===== DART 검색 =====

def dart_get(path, params):
    import json, urllib.parse
    params['crtfc_key'] = DART_KEY
    url = f'https://opendart.fss.or.kr/api/{path}?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def search_by_name(query: str):
    """기업명으로 DART 전체 목록에서 검색 (상장사만)"""
    print(f"🔍 '{query}' DART 검색 중...")
    url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}'
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open('CORPCODE.xml') as f:
            tree = ET.parse(f)

    # 검색어 정규화
    q = query.replace(' ', '').replace('(주)', '').replace('주식회사', '').lower()

    exact, partial = [], []
    for corp in tree.getroot().findall('list'):
        name = corp.findtext('corp_name', '').strip()
        code = corp.findtext('stock_code', '').strip()
        corp_code = corp.findtext('corp_code', '').strip()

        if not code:  # 비상장 제외
            continue

        n = name.replace(' ', '').replace('(주)', '').replace('주식회사', '').lower()
        if q == n:
            exact.append((name, code, corp_code))
        elif q in n or n in q:
            partial.append((name, code, corp_code))

    return exact + partial


def get_homepage_url(corp_code: str) -> str:
    """DART company.json에서 홈페이지 URL 조회"""
    try:
        data = dart_get('company.json', {'corp_code': corp_code})
        if data.get('status') == '000':
            url = data.get('hm_url', '').strip()
            if url and not url.startswith('http'):
                url = 'https://' + url
            return url
    except Exception:
        pass
    return ''


# ===== 이미지 자동 캡처 =====

# 페이지 종류별 키워드 (우선순위 순) - 제품/기술 우선, 홈페이지 제외
NAV_KEYWORDS = [
    ['제품', '사업', '솔루션', 'product', 'solution', 'business', 'service'],
    ['기술', 'technology', 'tech', 'r&d', '연구개발', 'innovation'],
    ['소재', '부품', '배터리', 'material', 'component', 'battery', 'semiconductor'],
    ['회사소개', 'about', '기업소개', 'company', '소개', '개요'],
    ['뉴스', '공지', 'news', 'press', '미디어', 'media', '보도'],
]


async def auto_capture(company_key: str, homepage_url: str) -> list:
    """홈페이지 nav에서 5개 페이지 자동 선택 후 캡처"""
    from playwright.async_api import async_playwright

    TEMP_DIR = os.path.join(BASE, 'images', f'temp_{company_key}')
    os.makedirs(TEMP_DIR, exist_ok=True)

    print(f"\n🌐 홈페이지 탐색: {homepage_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        # 홈페이지 로드 → nav 링크 수집
        page = await context.new_page()
        try:
            await page.goto(homepage_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  ⚠️ 홈페이지 로드 실패: {e}")
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

        # 키워드 기반 5개 URL 선택 (홈페이지 제외, 서브페이지 우선)
        selected = []
        used = {homepage_url}  # 홈페이지는 fallback용으로만 예약

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

        # 부족하면 nav 링크로 채우기
        for link in links:
            if len(selected) >= 5:
                break
            if link['href'] not in used:
                selected.append(link['href'])
                used.add(link['href'])

        # 그래도 부족하면 홈페이지로 채우기
        if len(selected) < 5:
            selected.insert(0, homepage_url)

        print(f"  선택된 페이지 {len(selected)}개:")
        for i, u in enumerate(selected, 1):
            print(f"    {i}. {u}")
        await page.close()

        # 각 페이지 캡처 (히어로 배너 스킵 → 실제 콘텐츠 영역)
        captured = []
        for i, url in enumerate(selected[:5], 1):
            pg = await context.new_page()
            try:
                await pg.goto(url, wait_until='networkidle', timeout=30000)
                await pg.wait_for_timeout(3000)
                # 고정/스티키 요소 숨기기
                await pg.evaluate("""
                    document.querySelectorAll('*').forEach(el => {
                        const st = getComputedStyle(el);
                        if ((st.position === 'fixed' || st.position === 'sticky') && parseInt(st.zIndex) > 10)
                            el.style.display = 'none';
                    });
                    document.body.style.overflow = 'auto';
                """)
                # 히어로 배너 건너뛰기: 450px 아래로 스크롤
                await pg.evaluate("window.scrollTo(0, 450)")
                await pg.wait_for_timeout(800)
                out = os.path.join(TEMP_DIR, f'{company_key}_{i}_full.png')
                # 뷰포트 캡처 (스크롤 위치 기준)
                await pg.screenshot(path=out, full_page=False)
                sz = os.path.getsize(out)
                print(f"  [{i}/5] ✅ {sz:,} bytes")
                captured.append(out)
            except Exception as e:
                print(f"  [{i}/5] ❌ {e}")
            finally:
                await pg.close()

        await browser.close()

    return captured


def run_crop(company_key: str):
    """기본 크롭 설정으로 이미지 크롭"""
    result = subprocess.run(
        ['python3', CROP_SCRIPT, '--company', company_key],
        cwd=BASE
    )
    return result.returncode == 0


# ===== 메인 =====

def main():
    parser = argparse.ArgumentParser(description='기업명으로 종목 전체 자동 추가')
    parser.add_argument('company_name', help='기업명 (예: 삼성SDI, 네이버)')
    parser.add_argument('--filename', default=None, help='파일명 키 (미입력시 종목코드 사용)')
    parser.add_argument('--no-images', action='store_true', help='이미지 캡처 생략')
    parser.add_argument('--no-push', action='store_true', help='git push 생략')
    args = parser.parse_args()

    if not DART_KEY:
        print("❌ DART_API_KEY 환경변수 필요\n   export DART_API_KEY='your_key'")
        sys.exit(1)

    # 1. 기업 검색
    results = search_by_name(args.company_name)
    if not results:
        print(f"❌ '{args.company_name}'를 DART에서 찾을 수 없습니다.")
        sys.exit(1)

    if len(results) == 1:
        corp_name, code, corp_code = results[0]
        print(f"✅ {corp_name} ({code})")
    else:
        show = results[:10]
        print(f"\n검색 결과 {len(show)}개:")
        for i, (name, code, _) in enumerate(show, 1):
            print(f"  {i}. {name} ({code})")
        try:
            choice = int(input("\n번호 선택: ")) - 1
            corp_name, code, corp_code = show[choice]
        except (ValueError, IndexError, KeyboardInterrupt):
            print("❌ 취소")
            sys.exit(1)

    filename_key = args.filename or code.lower()
    print(f"  파일명: {filename_key}")

    # 2. 홈페이지 URL 조회
    homepage_url = ''
    if not args.no_images:
        print(f"\n🏠 DART에서 홈페이지 URL 조회 중...")
        homepage_url = get_homepage_url(corp_code)
        if homepage_url:
            print(f"  {homepage_url}")
        else:
            print(f"  ⚠️ URL 없음 → 이미지 캡처 생략")

    # 3. 차트/재무 파이프라인 (add_stock.py 호출)
    cmd = [
        'python3', ADD_STOCK,
        f'--code={code}',
        f'--corp-code={corp_code}',
        f'--name={corp_name}',
        f'--filename={filename_key}',
        '--no-push',
    ]
    result = subprocess.run(cmd, cwd=BASE, env={**os.environ, 'DART_API_KEY': DART_KEY})
    if result.returncode != 0:
        print("❌ 차트/재무 생성 실패")
        sys.exit(1)

    # 4. 이미지 자동 캡처 + 크롭
    if not args.no_images and homepage_url:
        print(f"\n📸 이미지 자동 캡처 시작...")
        captured = asyncio.run(auto_capture(filename_key, homepage_url))
        if captured:
            print(f"\n✂️  이미지 크롭 중...")
            run_crop(filename_key)
        else:
            print("⚠️  캡처 실패 — 이미지는 수동으로 추가하세요.")

    # 5. git push
    if not args.no_push:
        print(f"\n🚀 GitHub push 중...")
        subprocess.run(['git', 'add', '.'], cwd=BASE)
        subprocess.run(['git', 'commit', '-m', f'Add {corp_name} ({code}) - auto'], cwd=BASE)
        result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE)
        if result.returncode == 0:
            print(f"🔄 jsDelivr 캐시 초기화 중...")
            try:
                urllib.request.urlopen(
                    'https://purge.jsdelivr.net/gh/kseongbin/stock-charts@main/AGENT_MAPPING.md',
                    timeout=10
                )
                print(f"  ✅ 캐시 초기화 완료")
            except Exception:
                pass
            print(f"\n✅ 완료! 2~3분 후 확인:")
            print(f"   https://kseongbin.github.io/stock-charts/{filename_key}.html")
            print(f"\n이제 에이전트에 '{corp_name}' 입력하면 정상 HTML이 생성됩니다.")
        else:
            print("❌ push 실패")
    else:
        print(f"\n✅ 완료 (push 생략)")


if __name__ == '__main__':
    main()

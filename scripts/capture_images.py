"""
범용 기업 이미지 캡처 스크립트
사용법:
  python3 scripts/capture_images.py --company kec --urls "url1,url2,url3,url4,url5"

예시:
  python3 scripts/capture_images.py \
    --company kec \
    --urls "https://www.keccorp.com/product/discrete/mosfet,https://www.keccorp.com/product/discrete/transistor,https://www.keccorp.com/product/ic,https://www.keccorp.com/about,https://www.keccorp.com/ir"
"""

import sys
import os
import asyncio
import argparse

def get_base():
    # scripts/ 폴더 기준으로 상위 폴더(stock-charts)를 BASE로 설정
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def capture_pages(company: str, urls: list[str]):
    from playwright.async_api import async_playwright

    BASE = get_base()
    TEMP_DIR = os.path.join(BASE, 'images', f'temp_{company}')
    os.makedirs(TEMP_DIR, exist_ok=True)

    print(f"\n[{company}] 캡처 시작 - {len(urls)}개 페이지")
    print(f"저장 경로: {TEMP_DIR}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--host-resolver-rules=MAP sunic.co.kr 119.205.211.74, MAP sunic.15440835.com 119.205.211.74, MAP www.sunic.co.kr 119.205.211.74']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        for i, url in enumerate(urls, 1):
            fname = f'{company}_{i}'
            print(f"[{i}/{len(urls)}] {url}")

            page = await context.new_page()
            try:
                resp = await page.goto(url, wait_until='networkidle', timeout=30000)
                status = resp.status if resp else 'N/A'
                print(f"  HTTP: {status}")

                # 페이지 로딩 대기
                await page.wait_for_timeout(3000)

                # 고정(sticky/fixed) 요소 숨기기 (헤더/팝업 등)
                await page.evaluate("""
                    document.querySelectorAll('*').forEach(el => {
                        const st = getComputedStyle(el);
                        if ((st.position === 'fixed' || st.position === 'sticky') && parseInt(st.zIndex) > 10)
                            el.style.display = 'none';
                    });
                    document.body.style.overflow = 'auto';
                    document.documentElement.style.overflow = 'auto';
                """)
                await page.wait_for_timeout(500)

                # 풀페이지 스크린샷
                temp_path = os.path.join(TEMP_DIR, f'{fname}_full.png')
                await page.screenshot(path=temp_path, full_page=True)
                fsize = os.path.getsize(temp_path)
                print(f"  저장: {temp_path} ({fsize:,} bytes)")

                if fsize < 10000:
                    print(f"  ⚠️  파일이 너무 작습니다 (빈 페이지 가능성)")

            except Exception as e:
                print(f"  ❌ 오류: {e}")
            finally:
                await page.close()

        await browser.close()

    print(f"\n✅ 캡처 완료! temp 폴더 확인: {TEMP_DIR}")
    print(f"\n다음 단계: crop_images.py 실행")
    print(f"  python3 scripts/crop_images.py --company {company}")


def main():
    parser = argparse.ArgumentParser(description='기업 홈페이지 이미지 캡처')
    parser.add_argument('--company', required=True, help='회사명 (영문 소문자, 예: kec)')
    parser.add_argument('--urls', required=True, help='캡처할 URL 5개 (쉼표로 구분)')
    args = parser.parse_args()

    urls = [u.strip() for u in args.urls.split(',')]
    if len(urls) != 5:
        print(f"❌ URL은 정확히 5개여야 합니다. (현재 {len(urls)}개)")
        sys.exit(1)

    asyncio.run(capture_pages(args.company, urls))


if __name__ == '__main__':
    main()

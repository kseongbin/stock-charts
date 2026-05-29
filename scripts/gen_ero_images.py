import sys
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import os

BASE = r'C:\Users\riseo\Cluade Test\stock-charts'
IMG_DIR = os.path.join(BASE, 'images')
TEMP_DIR = os.path.join(BASE, 'images', 'temp_ero')
os.makedirs(TEMP_DIR, exist_ok=True)

# Pages to capture - mining operations pages on ero.com
PAGES = [
    {
        'url': 'https://www.ero.com/what-we-do/caraiba-operations/',
        'name': 'Caraiba Operations',
        'file': 'erocopper_1',
    },
    {
        'url': 'https://www.ero.com/what-we-do/tucuma-operation/',
        'name': 'Tucuma Operation',
        'file': 'erocopper_2',
    },
    {
        'url': 'https://www.ero.com/what-we-do/xavantina-operations/',
        'name': 'Xavantina Operations',
        'file': 'erocopper_3',
    },
    {
        'url': 'https://www.ero.com/what-we-do/furnas-project/',
        'name': 'Furnas Project',
        'file': 'erocopper_4',
    },
    {
        'url': 'https://www.ero.com/what-we-do-2/',
        'name': 'What We Do Overview',
        'file': 'erocopper_5',
    },
]

async def capture_pages():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            ignore_https_errors=True
        )

        for page_info in PAGES:
            url = page_info['url']
            name = page_info['name']
            fname = page_info['file']

            print(f"\n[{name}] Navigating to {url}...")
            page = await context.new_page()

            try:
                resp = await page.goto(url, wait_until='networkidle', timeout=30000)
                status = resp.status if resp else 'N/A'
                print(f"  HTTP status: {status}")

                # Wait for content to load
                await page.wait_for_timeout(3000)

                # Remove fixed/sticky elements
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

                # Full page screenshot
                temp_path = os.path.join(TEMP_DIR, f'{fname}_full.png')
                await page.screenshot(path=temp_path, full_page=True)
                fsize = os.path.getsize(temp_path)
                print(f"  Full page screenshot: {fsize:,} bytes -> {temp_path}")

                if fsize < 10000:
                    print(f"  WARNING: File too small, possible blank page!")

            except Exception as e:
                print(f"  ERROR: {e}")
            finally:
                await page.close()

        await browser.close()

    print("\n\nAll full-page screenshots saved to temp directory.")

asyncio.run(capture_pages())

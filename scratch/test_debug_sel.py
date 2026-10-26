import asyncio, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = Path("./profiles/acc_1").resolve()
    port = 9339
    url = "https://www.tiktok.com/@derrickappah4/photo/7697701219929885959"
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--start-maximized"
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(3)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(6)
            print("URL:", page.url)
            print("TITLE:", await page.title())

            # Check what selectors match on page
            sel_check = await page.evaluate('''() => {
                return {
                    like_icon: !!document.querySelector('[data-e2e*="like"]'),
                    all_e2e: Array.from(document.querySelectorAll('[data-e2e]')).map(e => e.getAttribute('data-e2e')),
                    all_buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText || b.getAttribute('aria-label'))
                };
            }''')
            print("SELECTORS CHECK:", sel_check)
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(inspect())

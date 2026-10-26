import asyncio, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = Path("./profiles/acc_1").resolve()
    port = 9337
    url = "https://www.tiktok.com/@tiktok/video/7201207604547996974"
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
            print("Current page URL:", page.url)
            print("Page title:", await page.title())
            body_text = await page.inner_text("body")
            print("Body text preview:", body_text[:300].replace("\n", " "))
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(inspect())

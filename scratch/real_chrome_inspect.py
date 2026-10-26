import asyncio, json, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile_dir = Path("./profiles/acc_1").resolve()
    port = 9334
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--start-maximized",
        "https://www.tiktok.com/@derrickappah4/photo/7697701219929885959"
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(4)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            # Wait for user video to load
            await asyncio.sleep(6)

            # Evaluate and inspect all action containers and counts
            data = await page.evaluate('''() => {
                const results = [];
                // Look for all buttons or spans or strongs or divs in action bar
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                    const e2e = (el.getAttribute('data-e2e') || '').toLowerCase();
                    const text = (el.innerText || '').toLowerCase();
                    return aria.includes('like') || aria.includes('comment') || aria.includes('favorite') || aria.includes('save') || aria.includes('share') ||
                           e2e.includes('like') || e2e.includes('comment') || e2e.includes('favorite') || e2e.includes('share') || e2e.includes('count');
                }).map(el => ({
                    tag: el.tagName,
                    e2e: el.getAttribute('data-e2e'),
                    aria: el.getAttribute('aria-label'),
                    text: (el.innerText || '').slice(0, 100),
                    className: (el.className || '').slice(0, 80),
                    html: el.outerHTML.slice(0, 200)
                }));

                return elements;
            }''')

            with open("scratch/chrome_dom.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Dumped {len(data)} matching action elements to scratch/chrome_dom.json")
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(inspect())

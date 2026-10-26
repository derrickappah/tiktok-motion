import asyncio, re
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.tiktok.com/@derrickappah4/photo/7697701219929885959"
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)
        content = await page.content()
        
        matches = re.findall(r'(\"diggCount\":\s*\d+|\"likeCount\":\s*\d+|\"stats\":\s*\{[^}]+\}|\"statsV2\":\s*\{[^}]+\})', content)
        print("Regex matches found:", len(matches))
        for m in matches[:10]:
            print("  MATCH:", m)

        # Also search for itemInfo or video info
        item_matches = re.findall(r'(\"itemInfo\":\s*\{[^}]+\})', content)
        print("itemInfo matches:", len(item_matches))
        for im in item_matches[:5]:
            print("  ITEM:", im)

        # Also find all scripts
        scripts = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('script')).map(s => ({
                id: s.id,
                type: s.type,
                src: s.src,
                len: s.textContent.length
            })).filter(s => s.len > 100);
        }''')
        print("Large script tags:")
        for s in scripts:
            print(" ", s)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())

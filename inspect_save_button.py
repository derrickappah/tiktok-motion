import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect_save():
    profile_dir = Path("./profiles/acc_1").resolve()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=True
        )
        page = await ctx.new_page()
        await page.goto("https://www.tiktok.com/@derrickappah4/photo/7697701219929885959", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        elements = await page.locator("button, span, div[role='button']").all()
        for el in elements:
            try:
                e2e = await el.get_attribute("data-e2e")
                aria = await el.get_attribute("aria-label")
                if e2e or (aria and any(w in aria.lower() for w in ["like", "comment", "share", "favorite", "save", "bookmark"])):
                    txt = await el.inner_text()
                    html = await el.evaluate("e => e.outerHTML")
                    print(f"E2E: {e2e} | ARIA: {aria} | TXT: {txt[:20]} | HTML: {html[:100]}")
            except Exception:
                pass
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(inspect_save())

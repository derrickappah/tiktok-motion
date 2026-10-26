import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def check_url():
    profile_dir = Path("./profiles/acc_1").resolve()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=True
        )
        page = await ctx.new_page()
        print("[*] Navigating...")
        await page.goto("https://vt.tiktok.com/ZSgjkcGkA/", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(6)
        print("[*] Final URL:", page.url)

        page_text = await page.inner_text("body")
        for phrase in ["Comments are turned off", "Log in to comment", "Add comment", "Be the first to comment", "Log in"]:
            if phrase.lower() in page_text.lower():
                print(f"[+] Found keyword: '{phrase}'")

        # Find all inputs / editables
        editables = await page.locator("div[contenteditable='true'], div[role='textbox'], input").all()
        print(f"[+] Number of editables/inputs found: {len(editables)}")
        for i, el in enumerate(editables):
            vis = await el.is_visible()
            html = await el.evaluate("e => e.outerHTML")
            print(f"  Input {i}: visible={vis}, html={html[:150]}")

        # Find comment icons
        icons = await page.locator("[data-e2e*='comment']").all()
        print(f"[+] Number of comment-related elements found: {len(icons)}")
        for i, el in enumerate(icons):
            vis = await el.is_visible()
            data_e2e = await el.get_attribute("data-e2e")
            print(f"  Element {i}: visible={vis}, data-e2e={data_e2e}")

        await page.screenshot(path="debug_post.png")
        print("[+] Saved screenshot to debug_post.png")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(check_url())

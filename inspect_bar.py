import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect_interaction_bar():
    profile_dir = Path("./profiles/acc_1").resolve()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=True
        )
        page = await ctx.new_page()
        await page.goto("https://www.tiktok.com/@derrickappah4/photo/7697701219929885959", wait_until="domcontentloaded")
        await asyncio.sleep(6)

        # Look for the action container / vertical column
        containers = await page.locator("[class*='ActionItem'], [class*='ActionBar'], [class*='FlexCenter']").all()
        print(f"Action containers found: {len(containers)}")

        # Find buttons around like icon
        like = page.locator('span[data-e2e="like-icon"], button[data-e2e="like-icon"]').first
        if await like.is_visible():
            parent_html = await like.evaluate("el => el.closest('div[class*=\"Action\"], div[class*=\"Item\"]').parentElement.innerHTML")
            print("--- PARENT HTML OF ACTION BAR ---")
            print(parent_html[:1500])
        else:
            print("Like icon not visible yet, taking screenshot...")
            await page.screenshot(path="save_debug.png")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(inspect_interaction_bar())

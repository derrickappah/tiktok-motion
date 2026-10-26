import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_acc1():
    profile_dir = Path("./profiles/acc_1").resolve()
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=True
        )
        page = await ctx.new_page()
        await page.goto("https://www.tiktok.com", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        print("URL:", page.url)
        login_btn = await page.locator("#header-login-button").count()
        avatar = await page.locator("[data-e2e='profile-icon']").count()
        print(f"Login buttons found: {login_btn} | User avatar found: {avatar}")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(test_acc1())

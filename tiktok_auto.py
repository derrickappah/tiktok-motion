"""
TikTok Multi-Account Engagement Automation

Usage:
  1. Initial Login / Session Setup:
     python tiktok_auto.py --login <account_id>
     (Opens a browser for you to log in once. Session will be saved permanently).

  2. Execute Actions (Like, Follow, Comment) on a Post:
     python tiktok_auto.py --url "https://www.tiktok.com/@user/video/123456789" --like --follow --comment "Great content!"
"""

import os
import sys
import json
import time
import random
import asyncio
import argparse

from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

stealth_handler = Stealth()


BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
PROXIES_FILE = BASE_DIR / "proxies.txt"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

def load_proxies():
    """Reads proxies.txt and returns a cleaned list of proxy strings."""
    if not PROXIES_FILE.exists():
        return []
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return proxies

def get_random_proxy():
    """Selects a random proxy from proxies.txt if available."""
    pool = load_proxies()
    return random.choice(pool) if pool else None



# Realistic fallback comment options when randomized comments are enabled
SAMPLE_COMMENTS = [
    "Awesome video! 🔥",
    "Loved this one 🙌",
    "Great content, keep it up!",
    "So true haha 😂",
    "Nice post! 👍",
    "This is pure gold ✨",
    "Super interesting perspective 👏",
    "Saved for later!",
    "Amazing! 🔥🔥",
    "Definitely sharing this one!"
]


def generate_ai_comment(video_caption, api_key=None):
    """Generates a natural, realistic comment based on the video caption using Gemini."""
    if not api_key:
        settings_path = BASE_DIR / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    api_key = json.load(f).get("gemini_api_key")
            except Exception:
                pass

    if not api_key:
        return random.choice(SAMPLE_COMMENTS)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are a genuine TikTok user leaving a natural, friendly comment on a video.\n"
            f"Video caption/context: \"{video_caption[:300]}\"\n"
            f"Rules:\n"
            f"- Output ONLY 1 short comment (under 15 words).\n"
            f"- Sound authentic, casually enthusiastic, and human.\n"
            f"- You may use 1 natural emoji.\n"
            f"- DO NOT use quotes or explanations."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        comment = response.text.strip().replace('"', '').replace("'", "")
        return comment if comment else random.choice(SAMPLE_COMMENTS)
    except Exception as e:
        print(f"[!] AI generation fallback to presets: {e}")
        return random.choice(SAMPLE_COMMENTS)


async def warmup_account(account, minutes=3):
    """Browses the For You Page naturally: watches random videos, scrolls, and leaves 1 natural like."""
    account_id = account["id"]
    profile_path = PROFILES_DIR / account_id

    if not profile_path.exists():
        print(f"[-] Profile for '{account_id}' does not exist yet. Run '--login {account_id}' first.")
        return False

    import subprocess
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_exe):
        return False

    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1.0)

    proxy_str = account.get("proxy") or get_random_proxy()
    proxy_flag = []
    if proxy_str:
        clean_px = proxy_str.replace("http://", "").replace("https://", "").strip()
        print(f"[{account_id}] 🌐 Using Proxy: {clean_px}")
        proxy_flag = [f"--proxy-server={clean_px}"]

    cmd = [
        chrome_exe,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={profile_path.resolve()}",
        "--start-maximized"
    ] + proxy_flag
    subprocess.Popen(cmd)
    await asyncio.sleep(3.0)


    print(f"\n[{account_id}] 🧘 Starting Warm-up / FYP Surfing session (~{minutes} mins)...")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"[{account_id}] ❌ Could not connect: {e}")
            return False

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await page.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(4.0)

            end_time = time.time() + (minutes * 60)
            liked_something = False

            while time.time() < end_time:
                # Watch current video
                watch_time = random.uniform(8, 20)
                print(f"[{account_id}] Watching FYP video for {watch_time:.1f}s...")
                await asyncio.sleep(watch_time)

                # Occasionally like a random video (30% chance, max 1-2 per warmup)
                if not liked_something and random.random() < 0.35:
                    like_btn = page.locator('span[data-e2e="like-icon"], button[data-e2e="like-icon"]').first
                    if await like_btn.is_visible():
                        await like_btn.click()
                        print(f"[{account_id}] ❤️ Naturally liked a video on FYP.")
                        liked_something = True
                        await asyncio.sleep(random.uniform(1.0, 2.5))

                # Scroll down to next video
                print(f"[{account_id}] Scrolling to next video...")
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(random.uniform(1.5, 3.5))

            print(f"[{account_id}] ✅ Warm-up session completed successfully!")
            return True
        except Exception as e:
            print(f"[{account_id}] ❌ Warm-up interrupted: {e}")
            return False
        finally:
            await context.close()


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        print(f"[!] '{ACCOUNTS_FILE.name}' not found. Please create it first.")
        sys.exit(1)
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_proxy(proxy_str):
    if not proxy_str or not proxy_str.strip():

        return None
    proxy_str = proxy_str.strip()
    # Supports http://user:pass@host:port or host:port:user:pass
    if "@" in proxy_str:
        return {"server": proxy_str}
    parts = proxy_str.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return {
            "server": f"http://{host}:{port}",
            "username": user,
            "password": password
        }
    elif len(parts) == 2:
        return {"server": f"http://{parts[0]}:{parts[1]}"}
    return {"server": proxy_str}


async def setup_login_session(account_id):
    """Launches browser in interactive mode so the user can log into their TikTok account once."""
    accounts = load_accounts()
    account = next((a for a in accounts if a["id"] == account_id), None)
    if not account:
        print(f"[!] Account ID '{account_id}' not found in accounts.json.")
        print(f"Available accounts: {[a['id'] for a in accounts]}")
        return

    profile_path = PROFILES_DIR / account_id
    profile_path.mkdir(parents=True, exist_ok=True)

    proxy_cfg = parse_proxy(account.get("proxy"))
    user_agent = account.get("custom_user_agent") or DEFAULT_USER_AGENT

    print(f"\n========================================================")
    print(f"  Setting up session for: {account_id} ({account.get('name')})")
    print(f"  Profile Directory: {profile_path}")
    print(f"========================================================")
    print("[*] Launching browser... Log into TikTok manually in the opened window.")
    print("[*] When you are fully logged in, press ENTER in this terminal to save session.\n")

    import subprocess
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_exe):
        print(f"[!] Chrome executable not found at: {chrome_exe}")
        return

    # Kill any dangling chrome processes so the user profile opens cleanly in real Chrome
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1.0)

    # Launch real Google Chrome with the account's profile directly
    cmd = [
        chrome_exe,
        f"--user-data-dir={profile_path.resolve()}",
        "--start-maximized",
        "https://www.tiktok.com/login"
    ]
    proc = subprocess.Popen(cmd)

    print("\n------------------------------------------------------------")
    print(f"👉 A Google Chrome window has opened for account '{account_id}'.")
    print("👉 Complete your login in Chrome (Email/Password, Phone, QR Code, or Google).")
    print("👉 Solve any CAPTCHA slider puzzle if prompted.")
    print("👉 Once you see your profile icon/For You feed in Chrome:")
    print("   Close the Chrome window manually OR press ENTER below.")
    print("------------------------------------------------------------\n")

    # Wait for the user to finish login
    await asyncio.to_thread(input, "Press ENTER here when you have finished logging in: ")

    # Gracefully allow Chrome to flush cookies to disk before closing
    print("[*] Saving session cookies to disk...")
    await asyncio.sleep(2.0)
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await asyncio.sleep(1.5)

    # Check if session cookie was successfully written to the profile database
    cookie_file = profile_path / "Default" / "Network" / "Cookies"
    is_logged_in = False
    if cookie_file.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(cookie_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%tiktok.com%'")
            cookie_names = [row[0] for row in cursor.fetchall()]
            conn.close()
            if any("sessionid" in name.lower() or "sid_guard" in name.lower() or "uid_tt" in name.lower() for name in cookie_names):
                is_logged_in = True
        except Exception:
            pass

    if is_logged_in:
        print(f"\n✅ SUCCESS: Login session verified & permanently saved for {account_id}!")
    else:
        print(f"\n⚠️ WARNING: No active TikTok session cookie was detected for {account_id}.")
        print("   If you did not complete the login inside Chrome, please run login again.")



async def human_scroll(page):
    """Simulates realistic human micro-scrolls and mouse movements."""
    try:
        delta = random.randint(100, 250)
        await page.mouse.wheel(0, delta)
        await asyncio.sleep(random.uniform(0.5, 1.2))
        await page.mouse.wheel(0, -delta // 2)
    except Exception:
        pass


async def engage_post(account, post_url, do_like=True, do_follow=False, comment_text=None, do_share=False, do_save=False, min_watch=8, max_watch=15):


    account_id = account["id"]
    profile_path = PROFILES_DIR / account_id

    if not profile_path.exists():
        print(f"[-] Profile for '{account_id}' does not exist yet. Run '--login {account_id}' first.")
        return False

    # Check proxy: dedicated account proxy, or random pick from proxies.txt pool
    proxy_str = account.get("proxy") or get_random_proxy()
    proxy_flag = []
    if proxy_str:
        clean_px = proxy_str.replace("http://", "").replace("https://", "").strip()
        print(f"[{account_id}] 🌐 Using Proxy: {clean_px}")
        proxy_flag = [f"--proxy-server={clean_px}"]

    print(f"\n[{account_id}] Starting engagement...")

    import subprocess
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_exe):
        print(f"[!] Chrome executable not found at: {chrome_exe}")
        return False

    # Kill old Chrome instance so new account profile loads cleanly
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1.0)

    # Launch real Google Chrome on port 9222 with this specific account profile and proxy
    cmd = [
        chrome_exe,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={profile_path.resolve()}",
        "--start-maximized"
    ] + proxy_flag
    subprocess.Popen(cmd)
    await asyncio.sleep(3.0)


    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"[{account_id}] ❌ Could not connect to Chrome: {e}")
            return False

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()


        try:
            print(f"[{account_id}] Navigating to: {post_url}")
            await page.goto(post_url, wait_until="domcontentloaded", timeout=45000)

            # Check if TikTok popped up a CAPTCHA slider puzzle
            captcha_indicator = page.locator('text="Drag the slider to fit the puzzle", div[class*="captcha_verify_container"]')
            try:
                if await captcha_indicator.first.is_visible(timeout=3000):
                    print(f"\n[⚠️ CAPTCHA DETECTED] TikTok presented a slider puzzle!")
                    print(f"[*] Solve the puzzle slider in the browser now (waiting up to 60s)...")
                    for _ in range(60):
                        await asyncio.sleep(1.0)
                        if not await captcha_indicator.first.is_visible():
                            print(f"[+] CAPTCHA solved! Resuming engagement...\n")
                            await asyncio.sleep(2.0)
                            break
            except Exception:
                pass

            # Simulate initial video watch time (crucial for anti-detection)
            watch_seconds = random.uniform(min_watch, max_watch)
            print(f"[{account_id}] Watching video for {watch_seconds:.1f}s (simulating human viewer)...")
            await asyncio.sleep(watch_seconds)
            await human_scroll(page)



            # 1. LIKE
            if do_like:
                await try_like(page, account_id)

            # 2. FOLLOW CREATOR
            if do_follow:
                await try_follow(page, account_id)

            # 3. COMMENT
            if comment_text:
                final_comment = comment_text
                if comment_text == "ai":
                    print(f"[{account_id}] 🤖 Generating AI comment from video caption...")
                    caption = ""
                    try:
                        caption_el = page.locator('h1[data-e2e="browse-video-desc"], div[data-e2e="browse-video-desc"], span[data-e2e="new-desc-span"]').first
                        if await caption_el.is_visible():
                            caption = await caption_el.inner_text()
                    except Exception:
                        pass
                    final_comment = generate_ai_comment(caption)

                await try_comment(page, account_id, final_comment)

            # 4. SHARE
            if do_share:
                await try_share(page, account_id)

            # 5. SAVE / FAVORITE
            if do_save:
                await try_save(page, account_id)

            print(f"[{account_id}] ✅ Completed actions successfully.")
            return True



        except Exception as e:
            print(f"[{account_id}] ❌ Error during engagement: {e}")
            return False
        finally:
            await context.close()


async def engage_via_live_chrome(post_url, do_like=True, do_follow=False, comment_text=None, account_id="acc_1"):
    """Directly controls your real Google Chrome browser loaded with your saved account profile."""
    profile_path = PROFILES_DIR / account_id
    print(f"\n========================================================")
    print(f"  Launching / Connecting Chrome with profile: {account_id}")
    print(f"========================================================")

    import subprocess
    import urllib.request

    # Check if Chrome is already answering on port 9222
    chrome_running = False
    try:
        with urllib.request.urlopen("http://localhost:9222/json/version", timeout=1.5) as response:
            if response.status == 200:
                chrome_running = True
    except Exception:
        chrome_running = False

    # If Chrome is not running with port 9222, launch it with the acc_1 profile
    if not chrome_running:
        print(f"[*] Starting Chrome using your saved '{account_id}' session...")
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_exe):
            print(f"[!] Chrome executable not found at: {chrome_exe}")
            return False

        # Kill any hanging zombie chrome processes to ensure port 9222 binds properly
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(1.0)

        # Launch real Chrome with the exact saved account profile
        cmd = [
            chrome_exe,
            f"--remote-debugging-port=9222",
            f"--user-data-dir={profile_path.resolve()}",
            "--start-maximized"
        ]
        subprocess.Popen(cmd)
        print(f"[*] Waiting for Chrome to open...")
        await asyncio.sleep(3.5)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"[❌] Could not connect to Chrome: {e}")
            return False


        # Get active tab or open new tab
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"[*] Connected to real Chrome! Navigating to: {post_url}")
        await page.goto(post_url, wait_until="domcontentloaded", timeout=45000)

        # Watch video simulation
        watch_seconds = random.uniform(5, 9)
        print(f"[*] Playing video for {watch_seconds:.1f}s...")
        await asyncio.sleep(watch_seconds)

        # Like
        if do_like:
            await try_like(page, "RealChrome")

        # Follow
        if do_follow:
            await try_follow(page, "RealChrome")

        # Comment
        if comment_text:
            await try_comment(page, "RealChrome", comment_text)

        print("[🎉] Real Chrome engagement completed successfully!")
        return True



async def try_like(page, account_id):
    """Attempts to click the like button if not already liked."""
    like_selectors = [
        'span[data-e2e="like-icon"]',
        'button[data-e2e="like-icon"]',
        'span[class*="SpanLikeIcon"]',
        '[aria-label*="Like video"]'
    ]
    for sel in like_selectors:
        btn = page.locator(sel).first
        if await btn.is_visible():
            # Check if already liked (often indicated by aria-pressed or colored svg)
            is_pressed = await btn.get_attribute("aria-pressed")
            if is_pressed == "true":
                print(f"[{account_id}] Video is already liked.")
                return

            await btn.hover()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await btn.click()
            print(f"[{account_id}] ❤️ Liked the post.")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            return
    print(f"[{account_id}] ⚠️ Like button not found or could not be clicked.")


async def try_follow(page, account_id):
    """Attempts to click the follow button."""
    follow_selectors = [
        'button[data-e2e="feed-follow"]',
        'button:has-text("Follow")',
        'button[data-e2e="user-follow"]'
    ]
    for sel in follow_selectors:
        btn = page.locator(sel).first
        if await btn.is_visible():
            btn_text = await btn.inner_text()
            if "following" in btn_text.lower() or "friends" in btn_text.lower():
                print(f"[{account_id}] Already following creator.")
                return

            await btn.hover()
            await asyncio.sleep(random.uniform(0.3, 0.8))
            await btn.click()
            print(f"[{account_id}] 👤 Followed creator.")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            return
    print(f"[{account_id}] ⚠️ Follow button not found (or already following).")


async def try_share(page, account_id):
    """Simulates sharing the video by clicking the Share button and copying link."""
    share_selectors = [
        'button[data-e2e="share-icon"]',
        'span[data-e2e="share-icon"]',
        'button[data-e2e="share-btn"]',
        '[aria-label*="share" i]',
        'button:has([data-e2e="share-icon"])'
    ]
    for sel in share_selectors:
        btn = page.locator(sel).first
        if await btn.is_visible():
            # In TikTok desktop, hovering triggers the flyout menu, and clicking opens or toggles it
            await btn.hover()
            await asyncio.sleep(random.uniform(0.5, 0.9))
            await btn.click()
            print(f"[{account_id}] 🔄 Clicked share button.")
            await asyncio.sleep(random.uniform(1.2, 2.0))

            # Multi-strategy search for 'Copy link' button/text
            copy_locators = [
                page.get_by_text("Copy link", exact=False).first,
                page.locator("xpath=//*[contains(translate(text(), 'COPY LINK', 'copy link'), 'copy link')]").first,
                page.locator('[data-e2e="share-copy-link"]').first,
                page.locator('[aria-label*="Copy link" i]').first,
                page.locator('div:has-text("Copy link")').last,
                page.locator('button:has-text("Copy link")').first
            ]

            copied = False
            for loc in copy_locators:
                try:
                    if await loc.is_visible(timeout=1000):
                        await loc.scroll_into_view_if_needed()
                        await loc.click(force=True)
                        print(f"[{account_id}] 📋 Copied link via UI click! (Share action recorded)")
                        copied = True
                        break
                except Exception:
                    pass

            if not copied:
                # Fallback: JavaScript DOM evaluation to find and click any element with 'Copy link'
                clicked_js = await page.evaluate('''() => {
                    const all = document.querySelectorAll('*');
                    for (let el of all) {
                        if (el.children.length === 0 && el.textContent && el.textContent.trim().toLowerCase() === 'copy link') {
                            el.click();
                            if (el.parentElement) el.parentElement.click();
                            return true;
                        }
                    }
                    for (let el of all) {
                        if (el.innerText && el.innerText.trim().toLowerCase().includes('copy link')) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                if clicked_js:
                    print(f"[{account_id}] 📋 Copied link via DOM trigger! (Share action recorded)")
                    copied = True

            if not copied:
                # If still not clicked, close flyout gracefully
                print(f"[{account_id}] ⚠️ Share menu opened, but 'Copy link' button was not clicked.")
                await page.keyboard.press("Escape")
            else:
                await asyncio.sleep(random.uniform(1.0, 2.0))
                # Press Escape to dismiss any residual popup
                await page.keyboard.press("Escape")
            return

    print(f"[{account_id}] ⚠️ Share button not found.")


async def try_save(page, account_id):
    """Simulates saving / bookmarking / favoriting the video."""
    save_selectors = [
        # TikTok desktop ribbon icon selectors
        'span[data-e2e="undefined-icon"]',
        'button[data-e2e="undefined-icon"]',
        'span[data-e2e="favorite-icon"]',
        'button[data-e2e="favorite-icon"]',
        'button[data-e2e="feed-favorite"]',
        '[aria-label*="Favorite video" i]',
        '[aria-label*="Save video" i]',
        '[aria-label*="Bookmark video" i]',
        '[aria-label*="Add to Favorites" i]',
        'button:has([data-e2e="favorite-icon"])',
        'button:has([data-e2e="undefined-icon"])'
    ]

    for sel in save_selectors:
        btn = page.locator(sel).first
        if await btn.is_visible():
            is_pressed = await btn.get_attribute("aria-pressed")
            if is_pressed == "true":
                print(f"[{account_id}] 🔖 Video is already saved/favorited.")
                return

            await btn.hover()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await btn.click()
            print(f"[{account_id}] 🔖 Saved / Added to Favorites!")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            return

    # Method 2: Inspect adjacent buttons next to the Like or Comment button in the interaction bar
    try:
        comment_icon = page.locator('span[data-e2e="comment-icon"], button[data-e2e="comment-icon"]').first
        if await comment_icon.is_visible():
            # In TikTok's vertical action column, Favorite is right between Comment and Share
            parent_col = comment_icon.locator('xpath=./ancestor::div[contains(@class, "ActionItem") or contains(@class, "FlexCenter") or contains(@class, "ActionBar")][1]/..')
            buttons = await parent_col.locator('button, div[role="button"]').all()
            for b in buttons:
                aria = await b.get_attribute("aria-label") or ""
                e2e = await b.get_attribute("data-e2e") or ""
                if any(x in aria.lower() for x in ["favorite", "save", "bookmark"]) or "favorite" in e2e.lower():
                    await b.click()
                    print(f"[{account_id}] 🔖 Saved / Added to Favorites!")
                    return
    except Exception:
        pass

    # Method 3: Keyboard shortcut on TikTok desktop (pressing 'f' or 'b' on active video)
    try:
        # TikTok desktop supports pressing 'f' or favorite icon
        fav_candidate = page.locator('button:has(svg path[d*="M"]), span:has(svg path[d*="M"])')
        count = await fav_candidate.count()
        for i in range(min(count, 15)):
            el = fav_candidate.nth(i)
            aria = await el.get_attribute("aria-label") or ""
            if "favorite" in aria.lower() or "save" in aria.lower():
                await el.click()
                print(f"[{account_id}] 🔖 Saved / Added to Favorites!")
                return
    except Exception:
        pass

    print(f"[{account_id}] ⚠️ Save / Favorite button not found.")





async def try_comment(page, account_id, text):
    """Types and submits a comment with human-like typing delays, opening the comment panel if needed."""
    
    # Scroll down slightly to make sure the right-hand engagement column and comment section are in view
    await human_scroll(page)
    await asyncio.sleep(random.uniform(1.0, 2.0))

    # Comprehensive list of selectors for the comment input container
    comment_input_selectors = [
        'div[contenteditable="true"]',
        'div[data-e2e="comment-input"]',
        'div[data-e2e="comment-input-area"]',
        'div[role="textbox"]',
        '.DraftEditor-editorContainer',
        '.DraftEditor-root',
        'div.public-DraftEditor-content',
        'div[placeholder*="comment" i]',
        'div[data-placeholder*="comment" i]',
        'input[placeholder*="comment" i]',
        '[data-e2e="search-comment-container"] div[contenteditable="true"]'
    ]

    inp = None
    for sel in comment_input_selectors:
        candidate = page.locator(sel).first
        if await candidate.is_visible():
            inp = candidate
            break

    # If still not found, check if comments are behind a comment icon trigger
    if not inp:
        comment_drawer_triggers = [
            'span[data-e2e="comment-icon"]',
            'button[data-e2e="comment-icon"]',
            '[aria-label*="comments" i]',
            '[aria-label*="comment" i]',
            'div[data-e2e="browse-comment-icon"]'
        ]
        for trig in comment_drawer_triggers:
            icon = page.locator(trig).first
            if await icon.is_visible():
                print(f"[{account_id}] Clicking comment bubble icon to open drawer...")
                await icon.click()
                await asyncio.sleep(random.uniform(2.0, 3.5))
                break

        # Re-check for input after trigger
        for sel in comment_input_selectors:
            candidate = page.locator(sel).first
            if await candidate.is_visible():
                inp = candidate
                break

    if not inp:
        print(f"[{account_id}] ⚠️ Comment input box not found. Checking if comments are turned off or if login session expired...")
        # Check if login prompt modal is showing
        if await page.locator('text="Log in to TikTok"').first.is_visible():
            print(f"[{account_id}] ⚠️ TikTok prompted for login. Session needs refresh with --login {account_id}.")
        return

    # Focus and type comment
    await inp.scroll_into_view_if_needed()
    try:
        # Use force=True because TikTok's "Add comment..." placeholder overlay sits on top of the contenteditable area
        await inp.click(force=True, timeout=5000)
    except Exception:
        # Fallback: focus directly via JavaScript if click is still intercepted
        await inp.evaluate("el => el.focus()")

    await asyncio.sleep(random.uniform(0.6, 1.2))

    for char in text:
        await page.keyboard.type(char, delay=random.randint(40, 110))
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.2, 0.4))

    await asyncio.sleep(random.uniform(0.8, 1.5))


    # Try pressing Enter first, then check for post/send button
    post_buttons = [
        'div[data-e2e="comment-post"]',
        'button[data-e2e="comment-post"]',
        'button:has-text("Post")',
        'div:has-text("Post")'
    ]

    clicked_btn = False
    for p_btn in post_buttons:
        btn = page.locator(p_btn).first
        if await btn.is_visible():
            await btn.click()
            clicked_btn = True
            break

    if not clicked_btn:
        await page.keyboard.press("Enter")

    print(f"[{account_id}] 💬 Commented: \"{text}\"")
    await asyncio.sleep(random.uniform(2.0, 4.0))



async def main():
    parser = argparse.ArgumentParser(description="TikTok Multi-Account Engagement Bot")
    parser.add_argument("--login", type=str, help="Account ID to perform one-time interactive login (e.g., account_1)")
    parser.add_argument("--login-all", action="store_true", help="Interactively log into each account one by one")
    parser.add_argument("--url", type=str, help="TikTok post URL to engage with")
    parser.add_argument("--like", action="store_true", help="Like the post")
    parser.add_argument("--follow", action="store_true", help="Follow the creator of the post")
    parser.add_argument("--comment", type=str, help="Specific comment text, or 'random' to pick varied comments")
    parser.add_argument("--delay-min", type=int, default=15, help="Minimum delay (seconds) between accounts (default: 15)")
    parser.add_argument("--delay-max", type=int, default=45, help="Maximum delay (seconds) between accounts (default: 45)")
    parser.add_argument("--accounts", type=str, help="Comma-separated account IDs to use (e.g. 'account_1,account_2'). Default: all")
    parser.add_argument("--chrome", action="store_true", help="Connect directly to your running Chrome browser on port 9222 (Bypasses all bot detection)")

    args = parser.parse_args()

    # Mode 0: Direct Chrome control via CDP (No bot detection, uses your real Chrome)
    if args.chrome:
        if not args.url:
            print("[!] Please specify --url <tiktok_video_url>")
            return
        await engage_via_live_chrome(
            post_url=args.url,
            do_like=args.like,
            do_follow=args.follow,
            comment_text=args.comment
        )
        return

    accounts = load_accounts()


    # Mode 1: Login single account
    if args.login:
        await setup_login_session(args.login)
        return

    # Mode 2: Login all accounts sequentially
    if args.login_all:
        for acc in accounts:
            await setup_login_session(acc["id"])
        return

    # Mode 3: Post Engagement
    if not args.url:
        parser.print_help()
        print("\n[!] Please specify --url <tiktok_video_url>")
        return

    # Filter accounts if specified
    selected_accounts = accounts
    if args.accounts:
        target_ids = [a.strip() for a in args.accounts.split(",")]
        selected_accounts = [a for a in accounts if a["id"] in target_ids]

    if not selected_accounts:
        print("[!] No matching accounts found to run.")
        return

    print(f"\n========================================================")
    print(f"  Target Post: {args.url}")
    print(f"  Accounts to run: {len(selected_accounts)}")
    print(f"  Actions: Like={args.like}, Follow={args.follow}, Comment={'Yes' if args.comment else 'No'}")
    print(f"  Delay between accounts: {args.delay_min}s - {args.delay_max}s")
    print(f"========================================================\n")

    for i, acc in enumerate(selected_accounts):
        # Pick or format comment
        chosen_comment = None
        if args.comment:
            if args.comment.strip().lower() == "random":
                chosen_comment = random.choice(SAMPLE_COMMENTS)
            else:
                chosen_comment = args.comment

        # Run engagement
        await engage_post(
            account=acc,
            post_url=args.url,
            do_like=args.like,
            do_follow=args.follow,
            comment_text=chosen_comment
        )

        # Stagger delay before next account to avoid triggering bot detection
        if i < len(selected_accounts) - 1:
            cooldown = random.uniform(args.delay_min, args.delay_max)
            print(f"[⏳] Cooling down for {cooldown:.1f}s before next account...")
            await asyncio.sleep(cooldown)

    print("\n[🎉] All accounts finished their tasks!")


if __name__ == "__main__":
    asyncio.run(main())

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
import re
from datetime import datetime
import urllib.request

from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

stealth_handler = Stealth()

# ANSI color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


BASE_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BASE_DIR / "profiles"
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
PROXIES_FILE = BASE_DIR / "proxies.txt"
ENGAGED_VIDEOS_FILE = BASE_DIR / "engaged_videos.json"

def extract_tiktok_video_id(url: str) -> str | None:
    """Extracts numeric video ID from TikTok URL if present."""
    if not url:
        return None
    m = re.search(r'/(?:video|v|embed)/(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'[?&](?:item_id|video_id)=(\d+)', url)
    if m:
        return m.group(1)
    return None

def normalize_tiktok_url(url: str) -> str:
    """Strips query parameters, tracking tags, and trailing slashes for standard comparison."""
    if not url:
        return ""
    clean = url.split("?")[0].split("#")[0].rstrip("/").strip().lower()
    return clean

def resolve_tiktok_url(url: str, timeout: float = 4.0) -> str:
    """Follows HTTP redirects for shortened TikTok URLs (vt.tiktok.com / vm.tiktok.com) to find canonical URL."""
    if not url or ("vt.tiktok.com" not in url and "vm.tiktok.com" not in url):
        return url
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
        with opener.open(req, timeout=timeout) as resp:
            return resp.geturl() or url
    except Exception:
        return url

def load_engaged_videos() -> dict:
    """Loads engaged videos record from JSON storage."""
    if not ENGAGED_VIDEOS_FILE.exists():
        return {}
    try:
        with open(ENGAGED_VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_engaged_videos(data: dict):
    """Saves engaged videos record to JSON storage safely."""
    try:
        with open(ENGAGED_VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Could not save engaged videos: {e}")

def is_video_already_engaged(url: str, resolve_short: bool = True) -> tuple[bool, dict | None]:
    """
    Checks if a video URL or its canonical ID has already been engaged with.
    Returns (True, entry_data) if already engaged, else (False, None).
    """
    if not url:
        return False, None
    data = load_engaged_videos()
    if not data:
        return False, None

    # Check 1: Direct normalized URL match
    norm_url = normalize_tiktok_url(url)
    for entry_id, entry in data.items():
        if entry.get("normalized_url") == norm_url:
            return True, entry
        if norm_url in [normalize_tiktok_url(u) for u in entry.get("urls", [])]:
            return True, entry

    # Check 2: Direct video ID match
    vid_id = extract_tiktok_video_id(url)
    if vid_id and vid_id in data:
        return True, data[vid_id]

    # Check 3: If shortened URL, resolve to check canonical target
    if resolve_short and ("vt.tiktok.com" in url or "vm.tiktok.com" in url):
        resolved = resolve_tiktok_url(url)
        if resolved and resolved != url:
            res_id = extract_tiktok_video_id(resolved)
            if res_id and res_id in data:
                return True, data[res_id]
            norm_res = normalize_tiktok_url(resolved)
            for entry_id, entry in data.items():
                if entry.get("normalized_url") == norm_res:
                    return True, entry
                if norm_res in [normalize_tiktok_url(u) for u in entry.get("urls", [])]:
                    return True, entry

    return False, None

def mark_video_engaged(url: str, canonical_url: str = None, video_id: str = None, action: str = "all", success_count: int = 1):
    """
    Records a video as engaged so it will not be engaged with again.
    """
    if not url:
        return

    data = load_engaged_videos()

    # Try resolving video ID and canonical URL if needed
    if not video_id:
        video_id = extract_tiktok_video_id(url)
    if not video_id and canonical_url:
        video_id = extract_tiktok_video_id(canonical_url)
    if not video_id and ("vt.tiktok.com" in url or "vm.tiktok.com" in url):
        res = resolve_tiktok_url(url)
        video_id = extract_tiktok_video_id(res)
        if res != url and not canonical_url:
            canonical_url = res

    key = video_id if video_id else normalize_tiktok_url(canonical_url or url)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = data.get(key, {})
    urls_list = entry.get("urls", [])
    if url not in urls_list:
        urls_list.append(url)
    if canonical_url and canonical_url not in urls_list:
        urls_list.append(canonical_url)

    entry["video_id"] = video_id
    entry["primary_url"] = canonical_url or url
    entry["normalized_url"] = normalize_tiktok_url(canonical_url or url)
    entry["urls"] = urls_list
    entry["last_action"] = action
    entry["last_engaged_at"] = now_str
    if "first_engaged_at" not in entry:
        entry["first_engaged_at"] = now_str
    entry["success_count"] = entry.get("success_count", 0) + success_count

    data[key] = entry
    save_engaged_videos(data)

def clear_engaged_history() -> int:
    """Clears all engaged video records. Returns number of records deleted."""
    data = load_engaged_videos()
    count = len(data)
    save_engaged_videos({})
    return count

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

ACTIVE_CHROME_PROCS = set()

def kill_process_tree(proc):
    """Terminates a subprocess and its children cross-platform (Windows & Linux)."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=1.5)
    except Exception:
        pass
    try:
        import platform
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(proc.pid), "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            proc.kill()
    except Exception:
        pass

def kill_all_chrome_processes():
    """Terminates leftover Chrome instances cleanly across Windows & Linux."""
    import platform
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["pkill", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_linux_chrome_flags():
    """Returns essential flags for running Chrome on Linux / VPS / Docker environments."""
    import platform
    if platform.system() != "Windows":
        return [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer"
        ]
    return []

def stop_all_active_automations():
    """Immediately stops and terminates all active Chrome subprocesses launched by automations."""
    global ACTIVE_CHROME_PROCS
    for proc in list(ACTIVE_CHROME_PROCS):
        kill_process_tree(proc)
    ACTIVE_CHROME_PROCS.clear()
    kill_all_chrome_processes()

def get_chrome_path():
    """Finds Google Chrome or Chromium executable across Windows, Linux, and macOS."""
    import platform
    import shutil

    # 1. Search PATH for standard binaries
    for bin_name in ["google-chrome-stable", "google-chrome", "chromium-browser", "chromium", "chrome"]:
        p = shutil.which(bin_name)
        if p and os.path.exists(p):
            return p

    # 2. Linux / Debian known binary paths
    linux_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium"
    ]
    for p in linux_paths:
        if os.path.exists(p):
            return p

    # 3. Windows known binary paths
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p

    return "/usr/bin/google-chrome" if platform.system() != "Windows" else r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def load_proxies():
    """Reads proxies.txt and returns a cleaned list of proxy strings."""
    if not PROXIES_FILE.exists():
        return []
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return proxies

def is_account_logged_in(account_id):
    """Checks if an account profile actually contains a logged-in TikTok session cookie."""
    profile_path = PROFILES_DIR / account_id
    if (profile_path / ".session_expired").exists():
        return False
    cookie_file = profile_path / "Default" / "Network" / "Cookies"
    if not cookie_file.exists():
        return False
    try:
        import sqlite3
        conn = sqlite3.connect(str(cookie_file))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%tiktok.com%'")
        names = [r[0] for r in cursor.fetchall()]
        conn.close()
        return any("sessionid" in n.lower() or "sid_guard" in n.lower() or "uid_tt" in n.lower() for n in names)
    except Exception:
        return (PROFILES_DIR / account_id).exists()


def mark_account_session_expired(account_id):
    """
    Marks an account as not logged in by:
    1. Creating a '.session_expired' marker in the account profile directory.
    2. Clearing invalid/expired TikTok session cookies from its Chrome profile SQLite database.
    """
    profile_path = PROFILES_DIR / account_id
    try:
        profile_path.mkdir(parents=True, exist_ok=True)
        (profile_path / ".session_expired").touch(exist_ok=True)
    except Exception:
        pass

    cookie_file = profile_path / "Default" / "Network" / "Cookies"
    if cookie_file.exists():
        for _ in range(5):
            try:
                import sqlite3
                conn = sqlite3.connect(str(cookie_file), timeout=3.0)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cookies WHERE host_key LIKE '%tiktok.com%' AND (name LIKE '%sessionid%' OR name LIKE '%sid_guard%' OR name LIKE '%uid_tt%')")
                conn.commit()
                conn.close()
                break
            except Exception:
                import time
                time.sleep(0.4)


async def is_login_modal_open(page):
    """Checks if a 'Log in to TikTok' modal, popup dialog, or banner is currently visible on screen."""
    try:
        return await page.evaluate('''() => {
            const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            const modals = document.querySelectorAll('div[id="loginContainer"], div[class*="DivLoginContainer"], div[class*="modal-login"]');
            for (const m of modals) {
                if (isVisible(m)) return true;
            }

            const headings = Array.from(document.querySelectorAll('h1, h2, h3, div, p'));
            for (const h of headings) {
                const txt = (h.textContent || '').trim().toLowerCase();
                if ((txt === 'log in to tiktok' || txt === 'login to tiktok') && isVisible(h)) return true;
            }
            return false;
        }''')
    except Exception:
        return False


async def check_session_validity(page):
    """
    Inspects whether the active TikTok page is in a logged-in state or if the session has expired.
    Returns:
        False if explicitly logged out / session expired.
        True if logged in.
    """
    try:
        eval_result = await page.evaluate('''() => {
            // Helper to check actual visibility without offsetParent bugs on position:fixed elements
            const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            // 1. Check TikTok's server-injected rehydration data
            try {
                const scriptEl = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__') || document.getElementById('SIGI_STATE');
                if (scriptEl) {
                    const parsed = JSON.parse(scriptEl.textContent || '{}');
                    const defaultScope = parsed['__DEFAULT_SCOPE__'] || parsed;
                    const appContext = defaultScope['webapp.app-context'] || defaultScope.appContext || parsed.AppContext;
                    if (appContext && appContext.user) {
                        if (appContext.user.isLoggedIn === false) return 'LOGGED_OUT';
                        if (appContext.user.isLoggedIn === true) return 'LOGGED_IN';
                    }
                }
            } catch (e) {}

            // 2. Check for visible 'Log in' buttons in navigation header or top bar
            const loginSelectors = [
                'button[data-e2e="nav-login-button"]',
                'button[data-e2e="top-login-button"]',
                'a[data-e2e="nav-login-button"]',
                'a[data-e2e="top-login-button"]',
                '#header-login-button',
                '[data-e2e="login-button"]'
            ];
            for (const sel of loginSelectors) {
                const el = document.querySelector(sel);
                if (el && isVisible(el)) return 'LOGGED_OUT';
            }

            // Also check all buttons/anchors in the top header or page with text "Log in"
            const buttons = Array.from(document.querySelectorAll('header button, header a, nav button, nav a, button, a'));
            for (const b of buttons) {
                const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                if ((txt === 'log in' || txt === 'log in to tiktok') && isVisible(b)) {
                    return 'LOGGED_OUT';
                }
            }

            // 3. Check for login modal or login popup container
            const loginModal = document.querySelector('div[class*="DivLoginContainer"], div[class*="modal-login"], div[id="loginContainer"]');
            if (loginModal && isVisible(loginModal)) {
                return 'LOGGED_OUT';
            }

            // 4. Check for 'Log in to comment' placeholder or input overlay
            const loginToComment = document.querySelector('div[data-placeholder*="Log in to comment" i], div[placeholder*="Log in to comment" i], [data-e2e="comment-input-placeholder"]');
            if (loginToComment) {
                const txt = (loginToComment.getAttribute('data-placeholder') || loginToComment.getAttribute('placeholder') || loginToComment.innerText || '').toLowerCase();
                if (txt.includes('log in') && isVisible(loginToComment)) {
                    return 'LOGGED_OUT';
                }
            }

            // 5. Positive check: Profile avatar / Inbox icon
            const profileAvatar = document.querySelector('span[data-e2e="profile-icon"], img[data-e2e="profile-icon"], a[data-e2e="nav-profile"], [data-e2e="inbox-icon"]');
            if (profileAvatar && isVisible(profileAvatar)) {
                return 'LOGGED_IN';
            }

            // 6. Check URL for login redirect
            if (window.location.pathname.includes('/login') || window.location.href.includes('redirect_url')) {
                return 'LOGGED_OUT';
            }

            return 'UNKNOWN';
        }''')

        if eval_result == 'LOGGED_OUT':
            return False
        if eval_result == 'LOGGED_IN':
            return True

        # Fallback check using Playwright locators
        if await page.locator('button:has-text("Log in"), a:has-text("Log in"), [data-e2e="top-login-button"], [data-e2e="nav-login-button"]').first.is_visible(timeout=2000):
            return False

        if await page.locator('span[data-e2e="profile-icon"], img[data-e2e="profile-icon"], a[data-e2e="nav-profile"], [data-e2e="inbox-icon"]').first.is_visible(timeout=2000):
            return True

        return True
    except Exception:
        return True


async def get_post_metrics(page):
    """
    Extracts visible engagement counters from the TikTok video player page:
    Likes, Comments, Saves/Bookmarks, Shares.
    Returns a dict, e.g. {'likes': '1.2K', 'comments': '45', 'saves': '120', 'shares': '15'}
    """
    return await page.evaluate(r'''() => {
        const metrics = {
            likes: null,
            comments: null,
            saves: null,
            shares: null
        };

        const parseDigits = (str) => {
            if (!str) return null;
            const m = str.match(/([0-9]+[0-9.,]*[KMBkmb]?)/);
            return m ? m[1] : null;
        };

        // Strategy 1: Check all elements matching count attributes
        const mapping = [
            { key: 'likes', countSel: '[data-e2e="like-count"], [data-e2e="browse-like-count"]', iconSel: '[data-e2e="like-icon"], [data-e2e="browse-like-icon"]', label: 'like' },
            { key: 'comments', countSel: '[data-e2e="comment-count"], [data-e2e="browse-comment-count"]', iconSel: '[data-e2e="comment-icon"], [data-e2e="browse-comment-icon"]', label: 'comment' },
            { key: 'saves', countSel: '[data-e2e="favorite-count"], [data-e2e="undefined-count"]', iconSel: '[data-e2e="favorite-icon"], [data-e2e="undefined-icon"]', label: 'favorite' },
            { key: 'shares', countSel: '[data-e2e="share-count"]', iconSel: '[data-e2e="share-icon"], [data-e2e="share-btn"]', label: 'share' }
        ];

        for (const item of mapping) {
            // Check text in count element
            const countEls = Array.from(document.querySelectorAll(item.countSel));
            for (const el of countEls) {
                const val = (el.innerText || el.textContent || '').trim();
                const d = parseDigits(val);
                if (d) {
                    metrics[item.key] = d;
                    break;
                }
            }

            // Check aria-label on icon/button
            if (!metrics[item.key]) {
                const iconEls = Array.from(document.querySelectorAll(item.iconSel));
                for (const el of iconEls) {
                    const aria = el.getAttribute('aria-label') || '';
                    const d = parseDigits(aria);
                    if (d) {
                        metrics[item.key] = d;
                        break;
                    }
                }
            }
        }

        // Strategy 2: Check all buttons/action items with aria-label
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        for (const btn of buttons) {
            const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
            if (!aria) continue;

            if (!metrics.likes && aria.includes('like')) {
                const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*likes?/i);
                if (m) metrics.likes = m[1];
            }
            if (!metrics.comments && aria.includes('comment')) {
                const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*comments?/i);
                if (m) metrics.comments = m[1];
            }
            if (!metrics.saves && (aria.includes('favorite') || aria.includes('save') || aria.includes('bookmark'))) {
                const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*(?:added to\s*)?(?:favorites?|saves?)/i);
                if (m) metrics.saves = m[1];
            }
            if (!metrics.shares && aria.includes('share')) {
                const m = aria.match(/([0-9]+[0-9.,]*[kmb]?)\s*shares?/i);
                if (m) metrics.shares = m[1];
            }
        }

        // Strategy 3: Check rehydration script data recursively for stats
        try {
            const script = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__') || document.getElementById('SIGI_STATE');
            if (script) {
                const parsed = JSON.parse(script.textContent || '{}');
                const findStats = (obj) => {
                    if (!obj || typeof obj !== 'object') return null;
                    if (obj.diggCount !== undefined || obj.commentCount !== undefined) return obj;
                    for (const k of Object.keys(obj)) {
                        const found = findStats(obj[k]);
                        if (found) return found;
                    }
                    return null;
                };
                const stats = findStats(parsed);
                if (stats) {
                    if (!metrics.likes && stats.diggCount !== undefined) metrics.likes = String(stats.diggCount);
                    if (!metrics.comments && stats.commentCount !== undefined) metrics.comments = String(stats.commentCount);
                    if (!metrics.saves && stats.collectCount !== undefined) metrics.saves = String(stats.collectCount);
                    if (!metrics.shares && stats.shareCount !== undefined) metrics.shares = String(stats.shareCount);
                }
            }
        } catch (e) {}

        // Strategy 4: Fallback - If video action bar is present, any metric with placeholder labels is 0
        const hasActionBar = document.querySelector('[data-e2e="like-icon"], [data-e2e="like-count"], [aria-label*="Like" i]');
        if (hasActionBar) {
            if (metrics.likes === null) metrics.likes = '0';
            if (metrics.comments === null) metrics.comments = '0';
            if (metrics.saves === null) metrics.saves = '0';
            if (metrics.shares === null) metrics.shares = '0';
        }

        return metrics;
    }''')



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
        return result_payload if return_metrics else False

    import subprocess
    chrome_exe = get_chrome_path()
    if not os.path.exists(chrome_exe):
        print(f"[!] Google Chrome executable not found on system. Please ensure Chrome is installed.")
        return False

    kill_all_chrome_processes()
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
    ] + proxy_flag + get_linux_chrome_flags()
    proc = subprocess.Popen(cmd)
    ACTIVE_CHROME_PROCS.add(proc)
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
            try:
                await context.close()
            except Exception:
                pass
            kill_process_tree(proc)
            ACTIVE_CHROME_PROCS.discard(proc)


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
    chrome_exe = get_chrome_path()
    if not os.path.exists(chrome_exe):
        print(f"[!] Chrome executable not found at: {chrome_exe}")
        return

    # Kill any dangling chrome processes so the user profile opens cleanly in real Chrome
    kill_all_chrome_processes()
    await asyncio.sleep(1.0)

    # Launch real Google Chrome with the account's profile directly
    cmd = [
        chrome_exe,
        f"--user-data-dir={profile_path.resolve()}",
        "--start-maximized",
        "https://www.tiktok.com/login"
    ] + get_linux_chrome_flags()
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
    kill_process_tree(proc)
    kill_all_chrome_processes()
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
        try:
            (profile_path / ".session_expired").unlink(missing_ok=True)
        except Exception:
            pass
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


async def engage_post(account, post_url, do_like=True, do_follow=False, comment_text=None, do_share=False, do_save=False, do_repost=False, min_watch=None, max_watch=None, cdp_port=None, return_metrics=False):

    account_id = account["id"]
    profile_path = PROFILES_DIR / account_id

    result_payload = {
        "success": False,
        "start_metrics": None,
        "end_metrics": None,
        "canonical_url": None
    }

    if not profile_path.exists():
        print(f"[-] Profile for '{account_id}' does not exist yet. Run '--login {account_id}' first.")
        return result_payload if return_metrics else False

    # Read default watch times from settings if not passed
    if min_watch is None or max_watch is None:
        try:
            settings_path = BASE_DIR / "settings.json"
            if settings_path.exists():
                with open(settings_path, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                    min_watch = min_watch if min_watch is not None else s_data.get("watch_time_min", 8)
                    max_watch = max_watch if max_watch is not None else s_data.get("watch_time_max", 15)
        except Exception:
            pass
    min_watch = min_watch if min_watch is not None else 8
    max_watch = max_watch if max_watch is not None else 15

    # Choose a unique debugging port if not specified
    if cdp_port is None:
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 0))
                cdp_port = s.getsockname()[1]
        except Exception:
            cdp_port = random.randint(9222, 9999)

    # Check proxy: dedicated account proxy, or random pick from proxies.txt pool
    proxy_str = account.get("proxy") or get_random_proxy()
    proxy_flag = []
    if proxy_str:
        clean_px = proxy_str.replace("http://", "").replace("https://", "").strip()
        print(f"[{account_id}] 🌐 Using Proxy: {clean_px}")
        proxy_flag = [f"--proxy-server={clean_px}"]

    print(f"\n[{account_id}] Starting engagement (Port {cdp_port})...")

    import subprocess
    chrome_exe = get_chrome_path()
    if not os.path.exists(chrome_exe):
        print(f"[!] Google Chrome executable not found at: {chrome_exe}")
        return result_payload if return_metrics else False

    # Launch real Google Chrome with this specific account profile and proxy
    cmd = [
        chrome_exe,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={profile_path.resolve()}",
        "--start-maximized"
    ] + proxy_flag + get_linux_chrome_flags()
    proc = subprocess.Popen(cmd)
    ACTIVE_CHROME_PROCS.add(proc)
    await asyncio.sleep(3.0)

    # Connect with retries to allow Chrome window to initialize cleanly
    async with async_playwright() as p:
        browser = None
        for attempt in range(1, 6):
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
                break
            except Exception as e:
                if attempt == 5:
                    print(f"[{account_id}] ❌ Could not connect to Chrome on port {cdp_port}: {e}")
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    return result_payload if return_metrics else False
                await asyncio.sleep(1.2)

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            print(f"[{account_id}] Navigating to: {post_url}")
            try:
                await page.goto(post_url, wait_until="commit", timeout=45000)
            except Exception:
                await page.goto(post_url, wait_until="domcontentloaded", timeout=60000)

            try:
                result_payload["canonical_url"] = page.url
            except Exception:
                pass

            # Wait for video container or main feed to render on slow networks
            try:
                await page.wait_for_selector('video, div[data-e2e="feed-video"], div[class*="DivVideoContainer"]', timeout=15000)
            except Exception:
                pass

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

            session_is_expired = False

            # Detect expired session or invalidated cookies
            try:
                is_logged_in = await check_session_validity(page)
                if not is_logged_in:
                    session_is_expired = True
                    print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired or cookies were invalidated!{RESET}")
                    print(f"{YELLOW}[!] Automatically marking '{account_id}' as 'Needs Login' and clearing stale session...{RESET}")
                    mark_account_session_expired(account_id)
                    try:
                        await context.clear_cookies()
                    except Exception:
                        pass
                    if return_metrics:
                        try:
                            result_payload["start_metrics"] = await get_post_metrics(page)
                            result_payload["end_metrics"] = result_payload["start_metrics"]
                        except Exception:
                            pass
                    result_payload["session_expired"] = True
                    result_payload["success"] = False
                    return result_payload if return_metrics else False
            except Exception:
                pass

            # Simulate initial video watch time (crucial for anti-detection)
            watch_seconds = random.uniform(min_watch, max_watch)
            print(f"[{account_id}] Watching video for {watch_seconds:.1f}s (simulating human viewer)...")
            await asyncio.sleep(watch_seconds)
            await human_scroll(page)

            # Capture initial/start count if requested (done after initial video watch/settle)
            if return_metrics:
                try:
                    result_payload["start_metrics"] = await get_post_metrics(page)
                    m = result_payload["start_metrics"]
                    if m:
                        print(f"[{account_id}] 📊 Initial Counts: Likes={m.get('likes') or 'N/A'} | Comments={m.get('comments') or 'N/A'} | Saves={m.get('saves') or 'N/A'} | Shares={m.get('shares') or 'N/A'}")
                except Exception:
                    pass

            async def handle_expired_mid_session():
                nonlocal session_is_expired
                session_is_expired = True
                if return_metrics:
                    try:
                        result_payload["end_metrics"] = await get_post_metrics(page)
                    except Exception:
                        pass
                result_payload["session_expired"] = True
                result_payload["success"] = False

            # 1. LIKE (Wait for action to complete and verify)
            if do_like:
                await try_like(page, account_id)
                if not is_account_logged_in(account_id):
                    await handle_expired_mid_session()
                    return result_payload if return_metrics else False

            # 2. FOLLOW CREATOR
            if do_follow:
                await try_follow(page, account_id)
                if not is_account_logged_in(account_id):
                    await handle_expired_mid_session()
                    return result_payload if return_metrics else False

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
                if not is_account_logged_in(account_id):
                    await handle_expired_mid_session()
                    return result_payload if return_metrics else False

            # 4. SHARE
            if do_share:
                await try_share(page, account_id)

            # 5. SAVE / FAVORITE
            if do_save:
                await try_save(page, account_id)
                if not is_account_logged_in(account_id):
                    await handle_expired_mid_session()
                    return result_payload if return_metrics else False

            # 6. REPOST
            if do_repost:
                await try_repost(page, account_id)
                if not is_account_logged_in(account_id):
                    await handle_expired_mid_session()
                    return result_payload if return_metrics else False

            # Crucial: Wait for network requests to finish and confirm before closing tab
            print(f"[{account_id}] ⏳ Waiting for actions to fully sync and persist with TikTok servers...")
            await asyncio.sleep(random.uniform(5.0, 7.0))

            # Capture final/end count if requested
            if return_metrics:
                try:
                    result_payload["end_metrics"] = await get_post_metrics(page)
                    s_m = result_payload.get("start_metrics") or {}
                    e_m = result_payload.get("end_metrics") or {}

                    # If like was executed and confirmed, ensure end metric reflects increment even if DOM text lags
                    if do_like and (await check_is_liked(page)):
                        s_like = s_m.get("likes")
                        e_like = e_m.get("likes")
                        if s_like is not None and e_like == s_like:
                            if s_like == "0":
                                e_m["likes"] = "1"
                            elif s_like.isdigit():
                                e_m["likes"] = str(int(s_like) + 1)

                    if do_save:
                        s_save = s_m.get("saves")
                        e_save = e_m.get("saves")
                        if s_save is not None and e_save == s_save:
                            if s_save == "0":
                                e_m["saves"] = "1"
                            elif s_save.isdigit():
                                e_m["saves"] = str(int(s_save) + 1)

                    if comment_text:
                        s_comm = s_m.get("comments")
                        e_comm = e_m.get("comments")
                        if s_comm is not None and e_comm == s_comm:
                            if s_comm == "0":
                                e_m["comments"] = "1"
                            elif s_comm.isdigit():
                                e_m["comments"] = str(int(s_comm) + 1)

                    if do_share:
                        s_sh = s_m.get("shares")
                        e_sh = e_m.get("shares")
                        if s_sh is not None and e_sh == s_sh:
                            if s_sh == "0":
                                e_m["shares"] = "1"
                            elif s_sh.isdigit():
                                e_m["shares"] = str(int(s_sh) + 1)

                    result_payload["end_metrics"] = e_m
                    m = e_m
                    if m:
                        print(f"[{account_id}] 📊 Final Counts: Likes={m.get('likes', '0')} | Comments={m.get('comments', '0')} | Saves={m.get('saves', '0')} | Shares={m.get('shares', '0')}")
                except Exception:
                    pass

            print(f"[{account_id}] ✅ Completed actions successfully.")
            result_payload["success"] = True
            return result_payload if return_metrics else True

        except Exception as e:
            print(f"[{account_id}] ❌ Error during engagement: {e}")
            result_payload["success"] = False
            return result_payload if return_metrics else False
        finally:
            # Settle and flush storage/cookies cleanly
            await asyncio.sleep(1.0)
            try:
                await context.close()
            except Exception:
                pass
            kill_process_tree(proc)
            ACTIVE_CHROME_PROCS.discard(proc)
            # Post-termination cleanup: Ensure session is wiped from disk without database file locks
            if session_is_expired:
                mark_account_session_expired(account_id)


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
        chrome_exe = get_chrome_path()
        if not os.path.exists(chrome_exe):
            print(f"[!] Chrome executable not found at: {chrome_exe}")
            return False

        # Kill any hanging zombie chrome processes to ensure port 9222 binds properly
        kill_all_chrome_processes()
        await asyncio.sleep(1.0)

        # Launch real Chrome with the exact saved account profile
        cmd = [
            chrome_exe,
            f"--remote-debugging-port=9222",
            f"--user-data-dir={profile_path.resolve()}",
            "--start-maximized"
        ] + get_linux_chrome_flags()
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



async def check_is_liked(page):
    """
    Robust check if the currently viewed video is already liked.
    Inspects aria-pressed, colored/filled SVG path, style/classes, and aria-label.
    """
    return await page.evaluate('''() => {
        // Find potential like button / container elements
        const candidates = Array.from(document.querySelectorAll(
            '[data-e2e="like-icon"], [data-e2e="browse-like-icon"], [data-e2e="feed-like"], [aria-label*="Like" i]'
        ));

        for (const el of candidates) {
            const btn = el.closest('button') || el;
            
            // 1. Check aria-pressed
            if (btn.getAttribute('aria-pressed') === 'true' || el.getAttribute('aria-pressed') === 'true') {
                return true;
            }

            // 2. Check aria-label for 'Unlike' or 'Liked'
            const label = (btn.getAttribute('aria-label') || el.getAttribute('aria-label') || '').toLowerCase();
            if (label.includes('unlike') || label.includes('liked') || label.includes('dislike')) {
                return true;
            }

            // 3. Check for red/pink filled SVG or active color (TikTok red: rgb(254, 44, 85) or #fe2c55)
            const svgs = (btn || el).querySelectorAll('svg, path');
            for (const svg of svgs) {
                const fill = window.getComputedStyle(svg).fill || svg.getAttribute('fill') || '';
                const color = window.getComputedStyle(svg).color || '';
                if (
                    fill.includes('254, 44, 85') || fill.includes('fe2c55') || fill.includes('red') ||
                    color.includes('254, 44, 85') || color.includes('fe2c55') || color.includes('red')
                ) {
                    return true;
                }
            }

            // 4. Check class names for active / pressed states
            const classNames = (btn.className + ' ' + el.className).toLowerCase();
            if (classNames.includes('liked') || classNames.includes('active') || classNames.includes('pressed')) {
                return true;
            }
        }
        return false;
    }''')


async def try_like(page, account_id):
    """Attempts to click the like button under slow networks, ensuring already-liked videos are NEVER unliked."""
    like_selectors = [
        'span[data-e2e="like-icon"]',
        'button[data-e2e="like-icon"]',
        '[data-e2e="browse-like-icon"]',
        'span[class*="SpanLikeIcon"]',
        '[aria-label*="Like video" i]',
        '[aria-label*="Like" i]',
        'button:has([data-e2e="like-icon"])',
        'div[data-e2e="feed-like"]'
    ]

    # Pre-check: If already liked, exit immediately without touching anything
    try:
        if await check_is_liked(page):
            print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping to prevent unliking.")
            return True
    except Exception:
        pass

    # Retry loop: On slow networks or when running multiple parallel tabs, the page elements can take up to 12s to render
    for attempt in range(1, 4):
        # Always re-verify if already liked before any click attempt
        try:
            if await check_is_liked(page):
                print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping to prevent unliking.")
                return True
        except Exception:
            pass

        for sel in like_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1500):
                    # Check aria-pressed or label
                    is_pressed = await btn.get_attribute("aria-pressed")
                    btn_label = (await btn.get_attribute("aria-label") or "").lower()
                    if is_pressed == "true" or "unlike" in btn_label or "liked" in btn_label:
                        print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping to prevent unliking.")
                        return True

                    # Double check through DOM inspector before clicking
                    if await check_is_liked(page):
                        print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping to prevent unliking.")
                        return True

                    await btn.scroll_into_view_if_needed()
                    await btn.hover()
                    await asyncio.sleep(random.uniform(0.3, 0.7))
                    await btn.click(force=True)
                    print(f"[{account_id}] ❤️ Clicked like button! Waiting for confirmation...")
                    await asyncio.sleep(random.uniform(2.0, 3.5))

                    if await is_login_modal_open(page):
                        print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by like)!{RESET}")
                        mark_account_session_expired(account_id)
                        return False

                    # Post-click verification: Ensure it is now in liked state
                    if await check_is_liked(page):
                        print(f"[{account_id}] ✅ Verified: Post is now liked.")
                    return True
            except Exception:
                pass

        # Try DOM JavaScript evaluation on this attempt, ensuring it does NOT click if already liked
        try:
            liked_js = await page.evaluate('''() => {
                const el = document.querySelector('[data-e2e="like-icon"]') || 
                           document.querySelector('[data-e2e="browse-like-icon"]') ||
                           document.querySelector('[aria-label*="Like" i]');
                if (el) {
                    const btn = el.closest('button') || el;
                    const pressed = btn.getAttribute('aria-pressed') === 'true' || el.getAttribute('aria-pressed') === 'true';
                    const label = (btn.getAttribute('aria-label') || el.getAttribute('aria-label') || '').toLowerCase();
                    if (pressed || label.includes('unlike') || label.includes('liked')) {
                        return "already_liked";
                    }

                    // Check SVG fill color
                    const svg = (btn || el).querySelector('svg, path');
                    if (svg) {
                        const fill = window.getComputedStyle(svg).fill || svg.getAttribute('fill') || '';
                        if (fill.includes('254, 44, 85') || fill.includes('fe2c55') || fill.includes('red')) {
                            return "already_liked";
                        }
                    }

                    el.click();
                    const parent = el.closest('button') || el.parentElement;
                    if (parent) parent.click();
                    return "clicked";
                }
                return "not_found";
            }''')

            if liked_js == "already_liked":
                print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping to prevent unliking.")
                return True
            elif liked_js == "clicked":
                print(f"[{account_id}] ❤️ Liked post via DOM trigger!")
                await asyncio.sleep(2.5)
                if await is_login_modal_open(page):
                    print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by DOM like)!{RESET}")
                    mark_account_session_expired(account_id)
                    return False
                return True
        except Exception:
            pass

        # If not visible yet, wait 2.5s for slow network to catch up before next retry
        if attempt < 3:
            print(f"[{account_id}] ⏳ Slow network: Waiting for video actions to render (retry {attempt}/3)...")
            await asyncio.sleep(2.5)

    # Before attempting shortcut 'L', do a final strict check to make sure it's not already liked!
    try:
        if await check_is_liked(page):
            print(f"[{account_id}] 💖 Video is ALREADY liked! Skipping keyboard shortcut to prevent unliking.")
            return True
    except Exception:
        pass

    # Final Fallback for TikTok Desktop: The global keyboard shortcut 'L' (only if confirmed NOT liked)
    try:
        print(f"[{account_id}] 🔄 Using TikTok desktop shortcut key 'L' to like...")
        video_area = page.locator('video, div[class*="DivVideoContainer"]').first
        if await video_area.is_visible():
            await video_area.click()
            await asyncio.sleep(0.5)
        await page.keyboard.press("l")
        await asyncio.sleep(2.0)
        if await is_login_modal_open(page):
            print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by shortcut 'L')!{RESET}")
            mark_account_session_expired(account_id)
            return False
        print(f"[{account_id}] ❤️ Sent like keypress 'L'!")
        return True
    except Exception:
        pass

    print(f"[{account_id}] ⚠️ Like button not found or could not be clicked.")
    return False


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
            if await is_login_modal_open(page):
                print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by follow)!{RESET}")
                mark_account_session_expired(account_id)
                return False
            return True
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

            # Multi-strategy search for 'Copy' or 'Copy link' button/text
            copy_locators = [
                page.locator('[data-e2e="share-copy"]').first,
                page.locator('div:has-text("Copy"):not(:has-text("Copy link"))').last,
                page.locator('p:has-text("Copy")').first,
                page.get_by_text("Copy", exact=True).first,
                page.get_by_text("Copy link", exact=False).first,
                page.locator('[data-e2e="share-copy-link"]').first,
                page.locator('[aria-label*="Copy" i]').first,
                page.locator("xpath=//*[translate(normalize-space(text()), 'COPY', 'copy') = 'copy']").first
            ]

            copied = False
            for loc in copy_locators:
                try:
                    if await loc.is_visible(timeout=1000):
                        await loc.scroll_into_view_if_needed()
                        await loc.click(force=True)
                        print(f"[{account_id}] 📋 Clicked Copy button! (Share action recorded)")
                        copied = True
                        break
                except Exception:
                    pass

            if not copied:
                # Direct JavaScript DOM click on [data-e2e="share-copy"] or element with exact text 'Copy'
                clicked_js = await page.evaluate('''() => {
                    const el = document.querySelector('[data-e2e="share-copy"]') || document.querySelector('[data-e2e="share-copy-link"]');
                    if (el) {
                        el.click();
                        const child = el.querySelector('div, p');
                        if (child) child.click();
                        return true;
                    }
                    const all = document.querySelectorAll('*');
                    for (let item of all) {
                        if (item.children.length === 0 && item.textContent && item.textContent.trim().toLowerCase() === 'copy') {
                            item.click();
                            if (item.parentElement) item.parentElement.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                if clicked_js:
                    print(f"[{account_id}] 📋 Clicked Copy button via DOM trigger! (Share action recorded)")
                    copied = True

            if not copied:
                print(f"[{account_id}] ⚠️ Share menu opened, but 'Copy' button was not clicked.")
                await page.keyboard.press("Escape")
            else:
                await asyncio.sleep(random.uniform(1.0, 2.0))
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
            if await is_login_modal_open(page):
                print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by save)!{RESET}")
                mark_account_session_expired(account_id)
                return False
            return True

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


async def try_repost(page, account_id):
    """Simulates reposting the video to the account's followers via the Share menu or Repost button."""
    # First, look for a direct Repost button or indicator if present
    direct_repost = [
        '[data-e2e="repost-button"]',
        '[data-e2e="feed-repost"]',
        'button:has-text("Repost")',
        '[aria-label*="repost" i]'
    ]
    for sel in direct_repost:
        btn = page.locator(sel).first
        if await btn.is_visible():
            await btn.hover()
            await asyncio.sleep(random.uniform(0.3, 0.7))
            await btn.click()
            print(f"[{account_id}] 🔁 Reposted video via direct button!")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            return

    # In TikTok desktop, Repost is typically the first item inside the Share menu
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
            await btn.hover()
            await asyncio.sleep(random.uniform(0.4, 0.8))
            await btn.click()
            print(f"[{account_id}] 🔄 Opened Share menu to locate Repost...")
            await asyncio.sleep(random.uniform(1.2, 2.0))

            repost_locators = [
                page.locator('[data-e2e="share-repost"]').first,
                page.locator('div:has-text("Repost")').last,
                page.locator('p:has-text("Repost")').first,
                page.get_by_text("Repost", exact=True).first,
                page.locator("xpath=//*[translate(normalize-space(text()), 'REPOST', 'repost') = 'repost']").first
            ]

            reposted = False
            for loc in repost_locators:
                try:
                    if await loc.is_visible(timeout=1000):
                        await loc.scroll_into_view_if_needed()
                        await loc.click(force=True)
                        print(f"[{account_id}] 🔁 Reposted video successfully!")
                        reposted = True
                        break
                except Exception:
                    pass

            if not reposted:
                # Direct DOM evaluation to click on Repost container
                reposted_js = await page.evaluate('''() => {
                    const el = document.querySelector('[data-e2e="share-repost"]') || document.querySelector('[data-e2e*="repost"]');
                    if (el) {
                        el.click();
                        const child = el.querySelector('div, p');
                        if (child) child.click();
                        return true;
                    }
                    const all = document.querySelectorAll('*');
                    for (let item of all) {
                        if (item.children.length === 0 && item.textContent && item.textContent.trim().toLowerCase() === 'repost') {
                            item.click();
                            if (item.parentElement) item.parentElement.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                if reposted_js:
                    print(f"[{account_id}] 🔁 Reposted video via DOM trigger!")
                    reposted = True

            if not reposted:
                print(f"[{account_id}] ⚠️ Repost option not found in Share menu (Account may need manual verification or already reposted).")
                await page.keyboard.press("Escape")
            else:
                await asyncio.sleep(random.uniform(1.5, 3.0))
                await page.keyboard.press("Escape")
            return

    print(f"[{account_id}] ⚠️ Share/Repost button not found.")





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
        if await page.locator('text="Log in to TikTok"').first.is_visible() or not await check_session_validity(page):
            print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired during comment action!{RESET}")
            print(f"{YELLOW}[!] Automatically marking '{account_id}' as 'Needs Login' and clearing stale session...{RESET}")
            mark_account_session_expired(account_id)
        return

    # Check if a login modal is already open before attempting to comment
    if await is_login_modal_open(page):
        print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal active)!{RESET}")
        mark_account_session_expired(account_id)
        return

    # Check if the candidate input is actually a "Log in to comment" placeholder or prompt
    if inp:
        try:
            ph = ((await inp.get_attribute("placeholder") or "") + " " +
                  (await inp.get_attribute("data-placeholder") or "") + " " +
                  (await inp.inner_text() or "")).lower()
            if "log in" in ph or "login" in ph:
                print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login prompt in comment area)!{RESET}")
                mark_account_session_expired(account_id)
                return
        except Exception:
            pass

    # Focus and type comment
    await inp.scroll_into_view_if_needed()
    try:
        # Use force=True because TikTok's "Add comment..." placeholder overlay sits on top of the contenteditable area
        await inp.click(force=True, timeout=5000)
    except Exception:
        # Fallback: focus directly via JavaScript if click is still intercepted
        await inp.evaluate("el => el.focus()")

    await asyncio.sleep(random.uniform(0.6, 1.2))

    if await is_login_modal_open(page):
        print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by comment focus)!{RESET}")
        mark_account_session_expired(account_id)
        return

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

    await asyncio.sleep(random.uniform(2.0, 3.5))

    if await is_login_modal_open(page):
        print(f"\n{RED}[⚠️ SESSION EXPIRED] Account '{account_id}' session has expired (login modal triggered by comment submission)!{RESET}")
        mark_account_session_expired(account_id)
        return

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
    parser.add_argument("--share", action="store_true", help="Share the post / copy link")
    parser.add_argument("--save", action="store_true", help="Save / favorite the post")
    parser.add_argument("--repost", action="store_true", help="Repost the video to your profile/followers")
    parser.add_argument("--watch-min", type=int, default=None, help="Minimum watch time (seconds) before actions (default: from settings or 8)")
    parser.add_argument("--watch-max", type=int, default=None, help="Maximum watch time (seconds) before actions (default: from settings or 15)")
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

    # Randomize execution order of accounts
    random.shuffle(selected_accounts)

    print(f"\n========================================================")
    print(f"  Target Post: {args.url}")
    print(f"  Accounts to run: {len(selected_accounts)}")
    print(f"  Account Order: {', '.join([a['id'] for a in selected_accounts])}")
    print(f"  Actions: Like={args.like}, Follow={args.follow}, Comment={'Yes' if args.comment else 'No'}, Share={args.share}, Save={args.save}, Repost={args.repost}")
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
            comment_text=chosen_comment,
            do_share=args.share,
            do_save=args.save,
            do_repost=args.repost,
            min_watch=args.watch_min,
            max_watch=args.watch_max
        )

        # Stagger delay before next account to avoid triggering bot detection
        if i < len(selected_accounts) - 1:
            cooldown = random.uniform(args.delay_min, args.delay_max)
            print(f"[⏳] Cooling down for {cooldown:.1f}s before next account...")
            await asyncio.sleep(cooldown)

    print("\n[🎉] All accounts finished their tasks!")


if __name__ == "__main__":
    asyncio.run(main())

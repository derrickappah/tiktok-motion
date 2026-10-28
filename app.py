"""
====================================================================
           TIKTOK MOTION BY DEE - TERMINAL APPLICATION
====================================================================
Interactive Multi-Account Automation Suite for TikTok
"""

from __future__ import annotations

import os
import sys
import json
import time
import random
import asyncio
import subprocess
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
COMMENTS_FILE = BASE_DIR / "comments.txt"
SETTINGS_FILE = BASE_DIR / "settings.json"
PROXIES_FILE = BASE_DIR / "proxies.txt"
PROFILES_DIR = BASE_DIR / "profiles"

# Colors for terminal styling (ANSI)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    clear_screen()
    print(f"{CYAN}{BOLD}")
    print(r"""
  ████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗
  ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝
     ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝ 
     ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗ 
     ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗
     ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝ 
        ███╗   ███╗ ██████╗ ████████╗██╗ ██████╗ ███╗   ██╗
        ████╗ ████║██╔═══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
        ██╔████╔██║██║   ██║   ██║   ██║██║   ██║██╔██╗ ██║
        ██║╚██╔╝██║██║   ██║   ██║   ██║██║   ██║██║╚██╗██║
        ██║ ╚═╝ ██║╚██████╔╝   ██║   ██║╚██████╔╝██║ ╚████║
        ╚═╝     ╚═╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
    """)
    print(f"             {MAGENTA}★ TikTok Motion by Dee ★{RESET}")
    print(f"{CYAN}  ════════════════════════════════════════════════════════{RESET}\n")


# -------------------------------------------------------------
# Data Managers (Accounts, Comments, Settings)
# -------------------------------------------------------------

def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)


def is_account_logged_in(account_id):
    """
    Checks if an account profile actually contains a logged-in TikTok session cookie.
    Handles Chrome locked databases, WAL journals, and multiple cookie locations cross-platform.
    Automatically clears stale .session_expired if login session cookies are detected.
    """
    profile_path = PROFILES_DIR / account_id
    if not profile_path.exists():
        if str(account_id).isdigit() and (PROFILES_DIR / f"acc_{account_id}").exists():
            profile_path = PROFILES_DIR / f"acc_{account_id}"
        elif str(account_id).startswith("acc_") and (PROFILES_DIR / account_id[4:]).exists():
            profile_path = PROFILES_DIR / account_id[4:]
        else:
            return False

    cookie_candidates = [
        profile_path / "Default" / "Network" / "Cookies",
        profile_path / "Default" / "Cookies",
        profile_path / "Network" / "Cookies",
        profile_path / "Cookies",
    ]
    cookie_file = next((c for c in cookie_candidates if c.exists()), None)
    if not cookie_file:
        return False

    import sqlite3
    import shutil
    import tempfile

    names = []
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_cookie = Path(tmp_dir) / "Cookies"
            shutil.copy2(cookie_file, tmp_cookie)
            wal_file = cookie_file.parent / (cookie_file.name + "-wal")
            if wal_file.exists():
                shutil.copy2(wal_file, Path(tmp_dir) / (tmp_cookie.name + "-wal"))
            shm_file = cookie_file.parent / (cookie_file.name + "-shm")
            if shm_file.exists():
                shutil.copy2(shm_file, Path(tmp_dir) / (tmp_cookie.name + "-shm"))

            conn = sqlite3.connect(str(tmp_cookie), timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%tiktok.com%'")
            names = [r[0].lower() for r in cursor.fetchall()]
            conn.close()
    except Exception:
        try:
            uri = f"file:{cookie_file.resolve()}?mode=ro&immutable=1"
            conn = sqlite3.connect(uri, uri=True, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%tiktok.com%'")
            names = [r[0].lower() for r in cursor.fetchall()]
            conn.close()
        except Exception:
            pass

    login_markers = [
        "sessionid", "sessionid_ss", "sid_guard", "sid_tt", 
        "uid_tt", "uid_tt_ss", "multi_sids", "last_login_method", 
        "living_user_id", "passport_csrf_token"
    ]
    if any(marker in n for n in names for marker in login_markers):
        try:
            (profile_path / ".session_expired").unlink(missing_ok=True)
        except Exception:
            pass
        return True

    if (profile_path / ".session_expired").exists():
        return False

    return False


def is_telegram_bot_running() -> bool:
    """Checks whether the companion Telegram bot process is currently active."""
    pid_file = BASE_DIR / ".bot_pid"
    if not pid_file.exists():
        if os.name != "nt":
            try:
                res = subprocess.run(["pgrep", "-f", "telegram_bot.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            except Exception:
                pass
        return False
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        if os.name == "nt":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def load_comments():
    if not COMMENTS_FILE.exists():
        return ["Awesome video! 🔥", "Loved this one 🙌", "Great content, keep it up!"]
    with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        return lines if lines else ["Awesome video! 🔥"]


def save_comments(comments):
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(c.strip() + "\n")


def load_proxies():
    if not PROXIES_FILE.exists():
        return []
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def save_proxies(proxies):
    with open(PROXIES_FILE, "w", encoding="utf-8") as f:
        for p in proxies:
            f.write(p.strip() + "\n")


def load_settings():
    default_settings = {
        "delay_min": 15,
        "delay_max": 45,
        "default_actions": {
            "like": True,
            "follow": False,
            "comment": True
        }
    }
    if not SETTINGS_FILE.exists():
        return default_settings
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_settings


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def prompt_for_urls():
    """Prompts user to paste one or multiple TikTok links, running top to bottom."""
    print(f"{YELLOW}Paste TikTok Video Link(s):{RESET}")
    print(f"{CYAN}💡 You can paste a single link, OR paste multiple links (one per line).{RESET}")
    print(f"{CYAN}   When pasting multiple links, type 'DONE' or press Enter on an empty line when finished:{RESET}\n")

    urls = []
    first_input = input("Link 1: ").strip()
    if not first_input:
        return []

    # If user pasted multiple links in a single block or single line
    for piece in first_input.split():
        if "tiktok.com" in piece:
            urls.append(piece)

    # Allow continuous multiline paste
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if not line or line.upper() == "DONE":
            break
        for piece in line.split():
            if "tiktok.com" in piece and piece not in urls:
                urls.append(piece)

    # Filter for duplicate / already engaged videos
    if urls:
        from tiktok_auto import is_video_already_engaged
        already_engaged = []
        new_urls = []
        for u in urls:
            is_eng, entry = is_video_already_engaged(u)
            if is_eng:
                already_engaged.append((u, entry))
            else:
                new_urls.append(u)

        if already_engaged:
            print(f"\n{YELLOW}[⚠️ NOTICE] {len(already_engaged)} video(s) have already been engaged with previously:{RESET}")
            for u, entry in already_engaged:
                ts = entry.get("last_engaged_at", "previously") if entry else "previously"
                act = entry.get("last_action", "N/A") if entry else "N/A"
                print(f"  • {u} (Action: {act.upper()} | Date: {ts})")

            skip = input(f"\n{YELLOW}Skip already engaged video(s)? [Y/n]: {RESET}").strip().lower()
            if skip != "n":
                if not new_urls:
                    print(f"{RED}[!] All entered video(s) have already been engaged with. Queue cancelled.{RESET}")
                    return []
                print(f"{GREEN}[+] Skipped {len(already_engaged)} duplicate(s). Proceeding with {len(new_urls)} fresh video(s).{RESET}")
                urls = new_urls

    return urls


# -------------------------------------------------------------
# Feature 1: Run Post Engagement
# -------------------------------------------------------------

def run_engagement_menu():
    print_banner()
    print(f"{BOLD}[1] 🚀 ENGAGE TIKTOK POST{RESET}\n")

    accounts = load_accounts()
    if not accounts:
        print(f"{RED}[!] No accounts found. Please add accounts first.{RESET}")
        input("\nPress ENTER to continue...")
        return

    urls = prompt_for_urls()
    if not urls:
        print(f"{RED}[!] No valid TikTok links provided.{RESET}")
        input("\nPress ENTER to continue...")
        return

    print(f"\n{GREEN}[+] Loaded {len(urls)} target video(s) into queue:{RESET}")
    for idx, u in enumerate(urls, 1):
        print(f"  {idx}. {u}")

    # Account selection
    print(f"\n{BOLD}Select accounts to run:{RESET}")
    print("  [A] All accounts")
    for i, acc in enumerate(accounts, 1):
        status = "✅ Ready" if is_account_logged_in(acc['id']) else "⚠️ Not logged in"
        print(f"  [{i}] {acc['id']} ({acc.get('name', 'N/A')}) - {status}")

    acc_choice = input(f"\n{YELLOW}Choose accounts (e.g. 'A' or '1,2,3'):{RESET} ").strip().upper()
    if acc_choice == "A":
        target_accounts = accounts
    else:
        try:
            indexes = [int(x.strip()) - 1 for x in acc_choice.split(",") if x.strip().isdigit()]
            target_accounts = [accounts[i] for i in indexes if 0 <= i < len(accounts)]
        except Exception:
            target_accounts = accounts

    if not target_accounts:
        print(f"{RED}[!] No valid accounts selected.{RESET}")
        input("\nPress ENTER to continue...")
        return

    # Actions selection
    settings = load_settings()
    print(f"\n{BOLD}Choose Actions to Perform:{RESET}")
    do_like = input(f"Like the video? (Y/n) [{ 'Y' if settings['default_actions']['like'] else 'N' }]: ").strip().lower()
    do_like = (do_like != "n") if settings['default_actions']['like'] else (do_like == "y")

    do_follow = input(f"Follow the creator? (y/N) [{ 'Y' if settings['default_actions']['follow'] else 'N' }]: ").strip().lower()
    do_follow = (do_follow == "y") if not settings['default_actions']['follow'] else (do_follow != "n")

    do_comment = input(f"Leave a comment? (Y/n) [{ 'Y' if settings['default_actions']['comment'] else 'N' }]: ").strip().lower()
    do_comment = (do_comment != "n") if settings['default_actions']['comment'] else (do_comment == "y")

    do_share = input(f"Share / Copy link? (y/N): ").strip().lower() == "y"
    do_save = input(f"Save / Bookmark video? (y/N): ").strip().lower() == "y"
    do_repost = input(f"Repost video to followers? (y/N): ").strip().lower() == "y"

    comment_choice = None
    if do_comment:
        comments = load_comments()
        print(f"\n{BOLD}Comment Options:{RESET}")
        print("  [1] 🤖 AI Auto-Generated (From Video Caption)")
        print("  [2] 🎲 Random from Comment Templates Library")
        print("  [3] ✍️  Enter custom comment for all accounts")
        c_mode = input(f"{YELLOW}Select comment mode [1-3]:{RESET} ").strip()
        if c_mode == "1":
            comment_choice = "ai"
        elif c_mode == "3":
            comment_choice = input("Enter your custom comment: ").strip()
        else:
            comment_choice = "random"

    # Execution summary
    concurrency_limit = settings.get("concurrency", 5)
    watch_min = settings.get("watch_time_min", 8)
    watch_max = settings.get("watch_time_max", 15)
    print(f"\n{CYAN}========================================================")
    print(f"  Target Videos in Queue: {len(urls)}")
    print(f"  Accounts per Video: {len(target_accounts)}")
    print(f"  Concurrent Accounts (Parallel): {min(concurrency_limit, len(target_accounts))}")
    print(f"  Watch Time before actions: {watch_min}s - {watch_max}s")
    print(f"  Actions: Like={do_like}, Follow={do_follow}, Comment={do_comment}, Share={do_share}, Save={do_save}, Repost={do_repost}")
    print(f"  Delays: {settings['delay_min']}s - {settings['delay_max']}s")
    print(f"========================================================{RESET}\n")

    confirm = input("Start engagement queue now? (Y/n): ").strip().lower()
    if confirm == "n":
        return

    # Import and run engine
    from tiktok_auto import engage_post

    async def execute_all():
        sem = asyncio.Semaphore(concurrency_limit)

        for u_idx, post_url in enumerate(urls, 1):
            print(f"\n{MAGENTA}{BOLD}========================================================")
            print(f"  ▶️ Processing Video [{u_idx}/{len(urls)}]: {post_url}")
            print(f"  🚀 Concurrency: Running up to {concurrency_limit} accounts at the same time")
            print(f"========================================================{RESET}")

            # Randomize order of accounts for each video
            exec_accounts = list(target_accounts)
            random.shuffle(exec_accounts)
            print(f"{CYAN}[🎲] Account order: {', '.join([a['id'] for a in exec_accounts])}{RESET}")

            async def run_single_acc(acc, acc_index):
                # Stagger launch slightly so windows don't clash simultaneously on startup
                stagger_delay = (acc_index % concurrency_limit) * 1.5
                if stagger_delay > 0:
                    await asyncio.sleep(stagger_delay)

                async with sem:
                    comment_text = comment_choice
                    if comment_choice == "random":
                        comment_text = random.choice(load_comments())

                    print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc {acc_index+1}/{len(exec_accounts)}] 🚀 Launching {acc['id']}...{RESET}")
                    res = await engage_post(
                        account=acc,
                        post_url=post_url,
                        do_like=do_like,
                        do_follow=do_follow,
                        comment_text=comment_text if do_comment else None,
                        do_share=do_share,
                        do_save=do_save,
                        do_repost=do_repost,
                        min_watch=watch_min,
                        max_watch=watch_max
                    )
                    return res

            batch_start_metrics = None
            last_result = None

            if len(exec_accounts) == 1:
                only_acc = exec_accounts[0]
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc 1/1] 🚀 Launching {only_acc['id']} (Tracking Count Shifts)...{RESET}")
                comment_text = comment_choice
                if comment_choice == "random":
                    comment_text = random.choice(load_comments())

                last_result = await engage_post(
                    account=only_acc,
                    post_url=post_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text if do_comment else None,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )
                if isinstance(last_result, dict):
                    batch_start_metrics = last_result.get("start_metrics")
            else:
                # 1. Launch first account to capture video starting baseline before actions
                first_acc = exec_accounts[0]
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc 1/{len(exec_accounts)}] 🚀 Launching FIRST account {first_acc['id']} (Capturing Baseline Counts)...{RESET}")
                comment_text = comment_choice
                if comment_choice == "random":
                    comment_text = random.choice(load_comments())

                first_res = await engage_post(
                    account=first_acc,
                    post_url=post_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text if do_comment else None,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )
                if isinstance(first_res, dict):
                    batch_start_metrics = first_res.get("start_metrics")

                # 2. Launch intermediate accounts concurrently
                if len(exec_accounts) > 2:
                    tasks = [run_single_acc(acc, idx) for idx, acc in enumerate(exec_accounts[1:-1], 1)]
                    await asyncio.gather(*tasks)

                # 3. Launch last account to capture final end counts
                last_acc = exec_accounts[-1]
                last_idx = len(exec_accounts) - 1
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc {last_idx+1}/{len(exec_accounts)}] 🚀 Launching LAST account {last_acc['id']} (Capturing Final Counts)...{RESET}")
                comment_text = comment_choice
                if comment_choice == "random":
                    comment_text = random.choice(load_comments())

                last_result = await engage_post(
                    account=last_acc,
                    post_url=post_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text if do_comment else None,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )

            # Display Engagement Metric Shift Report
            if isinstance(last_result, dict):
                start_m = batch_start_metrics or last_result.get("start_metrics") or {}
                end_m = last_result.get("end_metrics") or {}
                print(f"\n{CYAN}========================================================")
                print(f"  📊 VIDEO METRIC SHIFT REPORT [Video {u_idx}/{len(urls)}]")
                print(f"  Target: {post_url}")
                print(f"  ────────────────────────────────────────────────────────")
                print(f"  ❤️ Likes:     {start_m.get('likes') or 'N/A'}  ➡️  {GREEN}{end_m.get('likes') or 'N/A'}{RESET}")
                print(f"  💬 Comments:  {start_m.get('comments') or 'N/A'}  ➡️  {GREEN}{end_m.get('comments') or 'N/A'}{RESET}")
                print(f"  🔖 Saves:     {start_m.get('saves') or 'N/A'}  ➡️  {GREEN}{end_m.get('saves') or 'N/A'}{RESET}")
                print(f"  🔄 Shares:    {start_m.get('shares') or 'N/A'}  ➡️  {GREEN}{end_m.get('shares') or 'N/A'}{RESET}")
                print(f"========================================================{RESET}\n")

            from tiktok_auto import mark_video_engaged
            canon = last_result.get("canonical_url") if isinstance(last_result, dict) else None
            mark_video_engaged(url=post_url, canonical_url=canon, action="all")

            if u_idx < len(urls):
                print(f"\n{CYAN}[⏸️] Completed video {u_idx}. Waiting 5s before starting next video in queue...{RESET}")
                await asyncio.sleep(5.0)

        print(f"\n{GREEN}{BOLD}[🎉] All {len(urls)} videos completed across all selected accounts!{RESET}")

    asyncio.run(execute_all())
    input("\nPress ENTER to return to menu...")


def run_single_action_flow(action_type):
    """Executes a single focused action (like, comment, follow, share, or save) across selected accounts."""
    action_titles = {
        "like": "❤️ LIKE POST ONLY",
        "comment": "💬 COMMENT ON POST ONLY",
        "follow": "👤 FOLLOW CREATOR ONLY",
        "share": "🔄 SHARE / COPY LINK ONLY",
        "save": "🔖 SAVE / FAVORITE POST ONLY",
        "repost": "🔁 REPOST VIDEO ONLY"
    }


    print_banner()
    print(f"{BOLD}[{action_titles.get(action_type, 'ENGAGEMENT')}]{RESET}\n")

    accounts = load_accounts()
    if not accounts:
        print(f"{RED}[!] No accounts found. Please add accounts first.{RESET}")
        input("\nPress ENTER to continue...")
        return

    urls = prompt_for_urls()
    if not urls:
        print(f"{RED}[!] No valid TikTok links provided.{RESET}")
        input("\nPress ENTER to continue...")
        return

    print(f"\n{GREEN}[+] Loaded {len(urls)} target video(s) into queue:{RESET}")
    for idx, u in enumerate(urls, 1):
        print(f"  {idx}. {u}")

    # Account selection
    print(f"\n{BOLD}Select accounts to run:{RESET}")
    print("  [A] All accounts")
    for i, acc in enumerate(accounts, 1):
        status = "✅ Ready" if is_account_logged_in(acc['id']) else "⚠️ Not logged in"
        print(f"  [{i}] {acc['id']} ({acc.get('name', 'N/A')}) - {status}")

    acc_choice = input(f"\n{YELLOW}Choose accounts (e.g. 'A' or '1,2,3'):{RESET} ").strip().upper()
    if acc_choice == "A":
        target_accounts = accounts
    else:
        try:
            indexes = [int(x.strip()) - 1 for x in acc_choice.split(",") if x.strip().isdigit()]
            target_accounts = [accounts[i] for i in indexes if 0 <= i < len(accounts)]
        except Exception:
            target_accounts = accounts

    if not target_accounts:
        print(f"{RED}[!] No valid accounts selected.{RESET}")
        input("\nPress ENTER to continue...")
        return

    # Specific setup for comments
    comment_choice = None
    if action_type == "comment":
        comments = load_comments()
        print(f"\n{BOLD}Comment Options:{RESET}")
        print("  [1] 🤖 AI Auto-Generated (Reads video caption & writes custom comment)")
        print("  [2] 🎲 Random from Comment Templates Library")
        print("  [3] ✍️  Enter custom comment for all accounts")
        c_mode = input(f"{YELLOW}Select comment mode [1-3]:{RESET} ").strip()
        if c_mode == "1":
            comment_choice = "ai"
        elif c_mode == "3":
            comment_choice = input("Enter your custom comment: ").strip()
        else:
            comment_choice = "random"

    settings = load_settings()
    concurrency_limit = settings.get("concurrency", 5)
    watch_min = settings.get("watch_time_min", 8)
    watch_max = settings.get("watch_time_max", 15)
    print(f"\n{CYAN}========================================================")
    print(f"  Target Videos in Queue: {len(urls)}")
    print(f"  Action: {action_titles.get(action_type)}")
    print(f"  Accounts per Video: {len(target_accounts)}")
    print(f"  Concurrent Accounts (Parallel): {min(concurrency_limit, len(target_accounts))}")
    print(f"  Watch Time before actions: {watch_min}s - {watch_max}s")
    print(f"  Delays: {settings['delay_min']}s - {settings['delay_max']}s")
    print(f"========================================================{RESET}\n")

    confirm = input("Start now? (Y/n): ").strip().lower()
    if confirm == "n":
        return

    from tiktok_auto import engage_post

    async def execute():
        sem = asyncio.Semaphore(concurrency_limit)

        for u_idx, post_url in enumerate(urls, 1):
            print(f"\n{MAGENTA}{BOLD}========================================================")
            print(f"  ▶️ Processing Video [{u_idx}/{len(urls)}]: {post_url}")
            print(f"  🚀 Concurrency: Running up to {concurrency_limit} accounts at the same time")
            print(f"========================================================{RESET}")

            # Randomize order of accounts for each video
            exec_accounts = list(target_accounts)
            random.shuffle(exec_accounts)
            print(f"{CYAN}[🎲] Account order: {', '.join([a['id'] for a in exec_accounts])}{RESET}")

            async def run_single_acc(acc, acc_index):
                # Stagger launch slightly
                stagger_delay = (acc_index % concurrency_limit) * 1.5
                if stagger_delay > 0:
                    await asyncio.sleep(stagger_delay)

                async with sem:
                    c_text = None
                    if action_type == "comment":
                        c_text = random.choice(load_comments()) if comment_choice == "random" else comment_choice

                    print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc {acc_index+1}/{len(exec_accounts)}] 🚀 Launching {acc['id']} ({action_type})...{RESET}")
                    res = await engage_post(
                        account=acc,
                        post_url=post_url,
                        do_like=(action_type == "like"),
                        do_follow=(action_type == "follow"),
                        comment_text=c_text,
                        do_share=(action_type == "share"),
                        do_save=(action_type == "save"),
                        do_repost=(action_type == "repost"),
                        min_watch=watch_min,
                        max_watch=watch_max
                    )
                    return res

            batch_start_metrics = None
            last_result = None

            if len(exec_accounts) == 1:
                only_acc = exec_accounts[0]
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc 1/1] 🚀 Launching {only_acc['id']} ({action_type}) (Tracking Count Shifts)...{RESET}")
                c_text = None
                if action_type == "comment":
                    c_text = random.choice(load_comments()) if comment_choice == "random" else comment_choice

                last_result = await engage_post(
                    account=only_acc,
                    post_url=post_url,
                    do_like=(action_type == "like"),
                    do_follow=(action_type == "follow"),
                    comment_text=c_text,
                    do_share=(action_type == "share"),
                    do_save=(action_type == "save"),
                    do_repost=(action_type == "repost"),
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )
                if isinstance(last_result, dict):
                    batch_start_metrics = last_result.get("start_metrics")
            else:
                # 1. Launch first account to capture video starting baseline before actions
                first_acc = exec_accounts[0]
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc 1/{len(exec_accounts)}] 🚀 Launching FIRST account {first_acc['id']} (Capturing Baseline Counts)...{RESET}")
                c_text = None
                if action_type == "comment":
                    c_text = random.choice(load_comments()) if comment_choice == "random" else comment_choice

                first_res = await engage_post(
                    account=first_acc,
                    post_url=post_url,
                    do_like=(action_type == "like"),
                    do_follow=(action_type == "follow"),
                    comment_text=c_text,
                    do_share=(action_type == "share"),
                    do_save=(action_type == "save"),
                    do_repost=(action_type == "repost"),
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )
                if isinstance(first_res, dict):
                    batch_start_metrics = first_res.get("start_metrics")

                # 2. Launch intermediate accounts concurrently
                if len(exec_accounts) > 2:
                    tasks = [run_single_acc(acc, idx) for idx, acc in enumerate(exec_accounts[1:-1], 1)]
                    await asyncio.gather(*tasks)

                # 3. Launch last account to capture final end counts
                last_acc = exec_accounts[-1]
                last_idx = len(exec_accounts) - 1
                print(f"\n{BOLD}[Video {u_idx}/{len(urls)} | Acc {last_idx+1}/{len(exec_accounts)}] 🚀 Launching LAST account {last_acc['id']} (Capturing Final Counts)...{RESET}")
                c_text = None
                if action_type == "comment":
                    c_text = random.choice(load_comments()) if comment_choice == "random" else comment_choice

                last_result = await engage_post(
                    account=last_acc,
                    post_url=post_url,
                    do_like=(action_type == "like"),
                    do_follow=(action_type == "follow"),
                    comment_text=c_text,
                    do_share=(action_type == "share"),
                    do_save=(action_type == "save"),
                    do_repost=(action_type == "repost"),
                    min_watch=watch_min,
                    max_watch=watch_max,
                    return_metrics=True
                )

            # Display Engagement Metric Shift Report
            if isinstance(last_result, dict):
                start_m = batch_start_metrics or last_result.get("start_metrics") or {}
                end_m = last_result.get("end_metrics") or {}
                print(f"\n{CYAN}========================================================")
                print(f"  📊 VIDEO METRIC SHIFT REPORT [Video {u_idx}/{len(urls)}]")
                print(f"  Target: {post_url}")
                print(f"  ────────────────────────────────────────────────────────")
                print(f"  ❤️ Likes:     {start_m.get('likes') or 'N/A'}  ➡️  {GREEN}{end_m.get('likes') or 'N/A'}{RESET}")
                print(f"  💬 Comments:  {start_m.get('comments') or 'N/A'}  ➡️  {GREEN}{end_m.get('comments') or 'N/A'}{RESET}")
                print(f"  🔖 Saves:     {start_m.get('saves') or 'N/A'}  ➡️  {GREEN}{end_m.get('saves') or 'N/A'}{RESET}")
                print(f"  🔄 Shares:    {start_m.get('shares') or 'N/A'}  ➡️  {GREEN}{end_m.get('shares') or 'N/A'}{RESET}")
                print(f"========================================================{RESET}\n")

            from tiktok_auto import mark_video_engaged
            canon = last_result.get("canonical_url") if isinstance(last_result, dict) else None
            mark_video_engaged(url=post_url, canonical_url=canon, action=action_type)

            if u_idx < len(urls):
                print(f"\n{CYAN}[⏸️] Completed video {u_idx}. Waiting 5s before next video in queue...{RESET}")
                await asyncio.sleep(5.0)

        print(f"\n{GREEN}{BOLD}[🎉] Task finished for all {len(urls)} videos across selected accounts!{RESET}")

    asyncio.run(execute())
    input("\nPress ENTER to return to menu...")



# -------------------------------------------------------------
# Feature 2: Account Manager & Health Check
# -------------------------------------------------------------

def account_manager_menu():
    while True:
        print_banner()
        print(f"{BOLD}[2] 👤 ACCOUNT MANAGER & HEALTH CHECK{RESET}\n")

        accounts = load_accounts()
        if not accounts:
            print(f"{YELLOW}No accounts registered yet.{RESET}\n")
        else:
            print(f"{'#':<4} {'ID':<12} {'NAME':<18} {'PROXY':<25} {'STATUS':<15}")
            print("─" * 75)
            for i, acc in enumerate(accounts, 1):
                logged_in = is_account_logged_in(acc['id'])
                status = f"{GREEN}Ready (Logged In){RESET}" if logged_in else f"{RED}Needs Login{RESET}"
                proxy_str = acc.get('proxy', '')
                if not proxy_str:
                    proxy_display = f"{CYAN}None (Direct){RESET}"
                else:
                    proxy_display = proxy_str[:22] + "..." if len(proxy_str) > 22 else proxy_str
                print(f"{i:<4} {acc['id']:<12} {acc.get('name', 'N/A')[:16]:<18} {proxy_display:<34} {status}")

        print(f"\n{BOLD}Actions:{RESET}")
        print("  [1] Add New Account")
        print("  [2] Delete an Account")
        print("  [3] Edit Account Proxy")
        print("  [0] Back to Main Menu")

        choice = input(f"\n{YELLOW}Select an option:{RESET} ").strip()

        if choice == "1":
            new_id = input("Enter new Account ID (e.g. acc_11): ").strip()
            if not new_id:
                continue
            if any(a['id'] == new_id for a in accounts):
                print(f"{RED}[!] Account ID already exists.{RESET}")
                time.sleep(1.5)
                continue
            name = input("Enter nickname / display name: ").strip() or new_id
            proxy = input("Enter proxy (optional, press ENTER to skip): ").strip()
            accounts.append({"id": new_id, "name": name, "proxy": proxy})
            save_accounts(accounts)
            print(f"{GREEN}[+] Account {new_id} added!{RESET}")
            time.sleep(1.2)

        elif choice == "2":
            del_id = input("Enter Account ID to delete: ").strip()
            new_list = [a for a in accounts if a['id'] != del_id]
            if len(new_list) < len(accounts):
                save_accounts(new_list)
                print(f"{GREEN}[+] Account {del_id} deleted.{RESET}")
            else:
                print(f"{RED}[!] Account ID not found.{RESET}")
            time.sleep(1.2)

        elif choice == "3":
            target_id = input("Enter Account ID to configure proxy: ").strip()
            target_acc = next((a for a in accounts if a['id'] == target_id), None)
            if target_acc:
                print(f"Current proxy: {target_acc.get('proxy') or 'None'}")
                new_px = input("Enter new proxy (or leave blank to remove): ").strip()
                target_acc["proxy"] = new_px
                save_accounts(accounts)
                print(f"{GREEN}[+] Proxy updated for {target_id}!{RESET}")
            else:
                print(f"{RED}[!] Account not found.{RESET}")
            time.sleep(1.2)

        elif choice == "0":
            break


# -------------------------------------------------------------
# Feature 3: Real Chrome Login Assistant
# -------------------------------------------------------------

def login_assistant_menu():
    print_banner()
    print(f"{BOLD}[3] 🔑 LOG INTO AN ACCOUNT (REAL CHROME){RESET}\n")

    accounts = load_accounts()
    if not accounts:
        print(f"{RED}[!] No accounts registered yet.{RESET}")
        input("\nPress ENTER to continue...")
        return

    for i, acc in enumerate(accounts, 1):
        status = f"{GREEN}[Logged In]{RESET}" if is_account_logged_in(acc['id']) else f"{RED}[Not Logged In]{RESET}"
        print(f"  [{i}] {acc['id']} - {acc.get('name', 'N/A')} {status}")

    choice = input(f"\n{YELLOW}Select account to log into (1-{len(accounts)}):{RESET} ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(accounts):
        return

    selected_account = accounts[int(choice) - 1]
    account_id = selected_account['id']

    from tiktok_auto import setup_login_session
    asyncio.run(setup_login_session(account_id))
    input("\nPress ENTER to return to menu...")


# -------------------------------------------------------------
# Feature 4: Comment Templates Library
# -------------------------------------------------------------

def comment_library_menu():
    while True:
        print_banner()
        print(f"{BOLD}[4] 💬 COMMENT TEMPLATES LIBRARY{RESET}\n")

        comments = load_comments()
        print(f"Registered comments ({len(comments)} total):\n")
        for i, c in enumerate(comments, 1):
            print(f"  [{i:2d}] {c}")

        print(f"\n{BOLD}Actions:{RESET}")
        print("  [1] Add New Comment Template")
        print("  [2] Delete a Comment Template")
        print("  [3] Clear All and Load Defaults")
        print("  [0] Back to Main Menu")

        choice = input(f"\n{YELLOW}Select an option:{RESET} ").strip()

        if choice == "1":
            new_c = input("Enter comment text: ").strip()
            if new_c:
                comments.append(new_c)
                save_comments(comments)
                print(f"{GREEN}[+] Added comment!{RESET}")
                time.sleep(1.0)

        elif choice == "2":
            idx = input(f"Enter comment number to delete (1-{len(comments)}): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(comments):
                removed = comments.pop(int(idx) - 1)
                save_comments(comments)
                print(f"{GREEN}[+] Removed: \"{removed}\"{RESET}")
                time.sleep(1.0)

        elif choice == "3":
            defaults = [
                "Awesome video! 🔥", "Loved this one 🙌", "Great content, keep it up!",
                "So true haha 😂", "Nice post! 👍", "This is pure gold ✨",
                "Super interesting perspective 👏", "Saved for later!"
            ]
            save_comments(defaults)
            print(f"{GREEN}[+] Reset comments to defaults!{RESET}")
            time.sleep(1.0)

        elif choice == "0":
            break


# -------------------------------------------------------------
# Proxy Pool Manager
# -------------------------------------------------------------

def proxy_manager_menu():
    while True:
        print_banner()
        print(f"{BOLD}[🌐 PROXY POOL MANAGER]{RESET}\n")

        proxies = load_proxies()
        print(f"Total Proxies in Pool: {CYAN}{len(proxies)}{RESET}")
        if proxies:
            print(f"Sample Proxies (First 5):")
            for p in proxies[:5]:
                print(f"  • {p}")
            if len(proxies) > 5:
                print(f"  ...and {len(proxies) - 5} more.")
        else:
            print(f"{YELLOW}⚠️ No proxies loaded. Accounts will use direct local connection.{RESET}")

        print(f"\n{BOLD}Actions:{RESET}")
        print("  [1] 📋 Paste / Add Proxy List (Append to Pool)")
        print("  [2] 🔄 Replace Entire Proxy Pool (Paste New List)")
        print("  [3] 📂 Import Proxies from Custom File Path")
        print("  [4] 👁️  View All Proxies")
        print("  [5] 🗑️  Clear All Proxies")
        print("  [0] 🔙 Back to Main Menu")

        choice = input(f"\n{YELLOW}Select an option [0-5]:{RESET} ").strip()

        if choice == "1":
            print(f"\n{CYAN}Paste your proxies below (one per line, e.g. IP:PORT).{RESET}")
            print(f"{YELLOW}Type 'DONE' or press Enter on an empty line when finished:{RESET}\n")
            new_list = []
            while True:
                try:
                    line = input().strip()
                except EOFError:
                    break
                if not line or line.upper() == "DONE":
                    break
                if ":" in line and not line.startswith("#"):
                    new_list.append(line)
            if new_list:
                current_proxies = load_proxies()
                current_proxies.extend(new_list)
                # Deduplicate while preserving order
                unique_proxies = list(dict.fromkeys(current_proxies))
                save_proxies(unique_proxies)
                print(f"\n{GREEN}[+] Added {len(new_list)} proxies! Total in pool: {len(unique_proxies)}{RESET}")
            else:
                print(f"\n{YELLOW}[!] No proxies entered.{RESET}")
            time.sleep(1.5)

        elif choice == "2":
            print(f"\n{CYAN}Paste your new proxy list below to REPLACE the current pool.{RESET}")
            print(f"{YELLOW}Type 'DONE' or press Enter on an empty line when finished:{RESET}\n")
            new_list = []
            while True:
                try:
                    line = input().strip()
                except EOFError:
                    break
                if not line or line.upper() == "DONE":
                    break
                if ":" in line and not line.startswith("#"):
                    new_list.append(line)
            if new_list:
                unique_proxies = list(dict.fromkeys(new_list))
                save_proxies(unique_proxies)
                print(f"\n{GREEN}[+] Replaced proxy pool with {len(unique_proxies)} proxies!{RESET}")
            else:
                print(f"\n{YELLOW}[!] Cancelled. No proxies entered.{RESET}")
            time.sleep(1.5)

        elif choice == "3":
            file_path = input("\nEnter path to proxy .txt file: ").strip().strip('"')
            p_path = Path(file_path)
            if p_path.exists() and p_path.is_file():
                try:
                    with open(p_path, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip() and ":" in l and not l.startswith("#")]
                    if lines:
                        current_proxies = load_proxies()
                        current_proxies.extend(lines)
                        unique_proxies = list(dict.fromkeys(current_proxies))
                        save_proxies(unique_proxies)
                        print(f"\n{GREEN}[+] Imported {len(lines)} proxies from file! Total pool: {len(unique_proxies)}{RESET}")
                    else:
                        print(f"\n{YELLOW}[!] No valid proxies found in file.{RESET}")
                except Exception as e:
                    print(f"\n{RED}[!] Error reading file: {e}{RESET}")
            else:
                print(f"\n{RED}[!] File not found: {file_path}{RESET}")
            time.sleep(1.5)

        elif choice == "4":
            print_banner()
            print(f"{BOLD}[👁️ ALL REGISTERED PROXIES ({len(proxies)})]{RESET}\n")
            for i, p in enumerate(proxies, 1):
                print(f"  [{i:3d}] {p}")
            input(f"\n{CYAN}Press ENTER to return...{RESET}")

        elif choice == "5":
            confirm = input(f"\n{RED}Are you sure you want to delete all proxies? (y/N): {RESET}").strip().lower()
            if confirm == "y":
                save_proxies([])
                print(f"{GREEN}[+] Proxy pool cleared!{RESET}")
                time.sleep(1.2)

        elif choice == "0":
            break


# -------------------------------------------------------------
# Feature 5: Speed & Delay Settings
# -------------------------------------------------------------

def settings_menu():
    while True:
        print_banner()
        print(f"{BOLD}[5] ⚙️ SPEED & DELAY SETTINGS{RESET}\n")

        settings = load_settings()
        concurrency = settings.get("concurrency", 5)
        watch_min = settings.get("watch_time_min", 8)
        watch_max = settings.get("watch_time_max", 15)
        print(f"  Concurrent Accounts (Parallel): {CYAN}{concurrency}{RESET}")
        print(f"  Watch Time before actions:      {CYAN}{watch_min}s - {watch_max}s{RESET}")
        print(f"  Minimum Delay between accounts: {CYAN}{settings['delay_min']} seconds{RESET}")
        print(f"  Maximum Delay between accounts: {CYAN}{settings['delay_max']} seconds{RESET}")
        print(f"  Default Like:    {CYAN}{settings['default_actions']['like']}{RESET}")
        print(f"  Default Follow:  {CYAN}{settings['default_actions']['follow']}{RESET}")
        print(f"  Default Comment: {CYAN}{settings['default_actions']['comment']}{RESET}")

        print(f"\n{BOLD}Actions:{RESET}")
        print("  [1] Change Delays (Cooldown between accounts)")
        print("  [2] Configure Gemini API Key (AI Comments)")
        print("  [3] Configure Telegram Bot (Remote Control)")
        print("  [4] Change Concurrency (Number of accounts to launch at a time)")
        print("  [5] Change Watch Time (Seconds to watch video before liking)")
        print("  [0] Back to Main Menu")

        choice = input(f"\n{YELLOW}Select an option:{RESET} ").strip()

        if choice == "1":
            try:
                min_d = int(input("Enter minimum delay (seconds): "))
                max_d = int(input("Enter maximum delay (seconds): "))
                if min_d > 0 and max_d >= min_d:
                    settings["delay_min"] = min_d
                    settings["delay_max"] = max_d
                    save_settings(settings)
                    print(f"{GREEN}[+] Delays updated!{RESET}")
                else:
                    print(f"{RED}[!] Maximum must be greater than minimum.{RESET}")
            except ValueError:
                print(f"{RED}[!] Please enter valid numbers.{RESET}")
            time.sleep(1.2)

        elif choice == "2":
            curr = settings.get("gemini_api_key", "")
            print(f"Current Gemini API Key: {curr[:8]}... (or blank)" if curr else "None")
            new_key = input("Enter Gemini API Key (or leave blank to remove): ").strip()
            settings["gemini_api_key"] = new_key
            save_settings(settings)
            print(f"{GREEN}[+] Gemini API Key saved!{RESET}")
            time.sleep(1.2)

        elif choice == "3":
            print(f"Current Bot Token: {settings.get('telegram_bot_token', 'None')}")
            new_tok = input("Enter Telegram Bot Token: ").strip()
            if new_tok:
                settings["telegram_bot_token"] = new_tok
            new_cid = input("Enter your allowed Telegram Chat ID (optional, press Enter to allow anyone): ").strip()
            settings["telegram_chat_id"] = new_cid
            save_settings(settings)
            print(f"{GREEN}[+] Telegram settings saved!{RESET}")
            time.sleep(1.2)

        elif choice == "4":
            try:
                new_conc = int(input("Enter number of accounts to launch concurrently (e.g. 1-10) [default 5]: ").strip() or "5")
                if 1 <= new_conc <= 20:
                    settings["concurrency"] = new_conc
                    save_settings(settings)
                    print(f"{GREEN}[+] Concurrency set to {new_conc} accounts at a time!{RESET}")
                else:
                    print(f"{RED}[!] Please choose a value between 1 and 20.{RESET}")
            except ValueError:
                print(f"{RED}[!] Please enter a valid number.{RESET}")
            time.sleep(1.2)

        elif choice == "5":
            try:
                w_min = int(input("Enter minimum seconds to watch before liking (e.g. 5): ").strip())
                w_max = int(input("Enter maximum seconds to watch before liking (e.g. 15): ").strip())
                if w_min >= 0 and w_max >= w_min:
                    settings["watch_time_min"] = w_min
                    settings["watch_time_max"] = w_max
                    save_settings(settings)
                    print(f"{GREEN}[+] Watch time set to {w_min}s - {w_max}s!{RESET}")
                else:
                    print(f"{RED}[!] Maximum watch time must be greater than or equal to minimum.{RESET}")
            except ValueError:
                print(f"{RED}[!] Please enter valid numbers.{RESET}")
            time.sleep(1.2)

        elif choice == "0":
            break


def run_warmup_flow():
    """Warms up accounts by scrolling the For You Page and watching random videos."""
    print_banner()
    print(f"{BOLD}[🧘 FOR YOU PAGE WARM-UP MODE]{RESET}\n")

    accounts = load_accounts()
    if not accounts:
        print(f"{RED}[!] No accounts found.{RESET}")
        input("\nPress ENTER to continue...")
        return

    print("Warming up simulates real human behavior by surfing TikTok's FYP, watching clips, and liking random videos.")
    print("This builds high account trust score and protects accounts from shadowbans.\n")

    print(f"{BOLD}Select accounts to warm up:{RESET}")
    print("  [A] All accounts")
    for i, acc in enumerate(accounts, 1):
        status = "✅ Ready" if is_account_logged_in(acc['id']) else "⚠️ Not logged in"
        print(f"  [{i}] {acc['id']} - {status}")

    choice = input(f"\n{YELLOW}Choose accounts (e.g. 'A' or '1'):{RESET} ").strip().upper()
    if choice == "A":
        target = accounts
    else:
        try:
            indexes = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
            target = [accounts[i] for i in indexes if 0 <= i < len(accounts)]
        except Exception:
            target = accounts

    try:
        minutes = float(input(f"\nEnter warm-up duration per account in minutes [default: 3]: ").strip() or "3")
    except ValueError:
        minutes = 3.0

    from tiktok_auto import warmup_account

    # Randomize order of accounts for warmup
    exec_target = list(target)
    random.shuffle(exec_target)
    print(f"{CYAN}[🎲] Randomized warmup order: {', '.join([a['id'] for a in exec_target])}{RESET}")

    async def execute():
        for i, acc in enumerate(exec_target):
            print(f"\n{BOLD}[{i+1}/{len(exec_target)}] Warming up {acc['id']} for {minutes:.1f} mins...{RESET}")
            await warmup_account(acc, minutes=minutes)
            if i < len(exec_target) - 1:
                await asyncio.sleep(random.uniform(5, 10))
        print(f"\n{GREEN}{BOLD}[🎉] All accounts successfully warmed up!{RESET}")

    asyncio.run(execute())
    input("\nPress ENTER to return to menu...")


def run_telegram_bot_flow():
    """Starts the Telegram bot listener in a separate window or directly."""
    print_banner()
    print(f"{BOLD}[📲 TELEGRAM REMOTE TRIGGER BOT]{RESET}\n")

    settings = load_settings()
    token = settings.get("telegram_bot_token")
    if not token:
        print(f"{YELLOW}[!] Telegram bot token not configured yet.{RESET}")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot to create a bot and copy your token.")
        print("3. Enter your token below:\n")
        new_tok = input("Enter Telegram Bot Token: ").strip()
        if not new_tok:
            return
        settings["telegram_bot_token"] = new_tok
        save_settings(settings)

    print(f"\n{GREEN}[*] Launching Telegram Listener in a new terminal window...{RESET}")
    import subprocess
    import platform
    sys_plat = platform.system()
    if sys_plat == "Windows":
        cmd = [
            "cmd.exe", "/c", "start", "TikTok Motion Telegram Bot",
            sys.executable,
            "telegram_bot.py"
        ]
        subprocess.Popen(cmd)
    elif sys_plat == "Darwin":
        cmd = [
            "osascript", "-e",
            f'tell application "Terminal" to do script "cd \\"{os.getcwd()}\\" && \\"{sys.executable}\\" telegram_bot.py"'
        ]
        try:
            subprocess.Popen(cmd)
        except Exception:
            subprocess.Popen([sys.executable, "telegram_bot.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    else:
        subprocess.Popen([sys.executable, "telegram_bot.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    print(f"{CYAN}[+] Bot is running in the background! Send links from your phone anytime.{RESET}")
    input("\nPress ENTER to return to menu...")


def engaged_history_menu():
    while True:
        print_banner()
        print(f"{BOLD}[15] 📜 ENGAGED VIDEOS HISTORY{RESET}\n")
        from tiktok_auto import load_engaged_videos, clear_engaged_history
        data = load_engaged_videos()
        print(f"Total videos engaged: {CYAN}{len(data)}{RESET}\n")

        if not data:
            print(f"{YELLOW}No videos have been recorded in history yet.{RESET}\n")
        else:
            items = list(data.values())[-15:]
            print(f"{'#':<4} {'ACTION':<14} {'DATE':<20} {'URL':<45}")
            print("─" * 85)
            for i, it in enumerate(reversed(items), 1):
                url = it.get("primary_url") or it.get("normalized_url") or "Unknown"
                if len(url) > 42:
                    url = url[:39] + "..."
                act = (it.get("last_action") or "N/A").upper()
                dt = it.get("last_engaged_at") or "N/A"
                print(f"{i:<4} {act:<14} {dt:<20} {url:<45}")

        print(f"\n{BOLD}Options:{RESET}")
        print("  [C] Clear / Reset History")
        print("  [0] Back to Main Menu\n")
        ch = input(f"{YELLOW}Choose option:{RESET} ").strip().upper()
        if ch == "0":
            break
        elif ch == "C":
            confirm = input(f"{RED}Are you sure you want to clear all engaged history? (y/N): {RESET}").strip().lower()
            if confirm == "y":
                c = clear_engaged_history()
                print(f"{GREEN}[+] Cleared {c} record(s)!{RESET}")
                input("\nPress ENTER to continue...")


# -------------------------------------------------------------
# Main Application Loop
# -------------------------------------------------------------

def main():
    while True:
        print_banner()
        accounts = load_accounts()
        ready_count = sum(1 for a in accounts if is_account_logged_in(a['id']))
        proxies = load_proxies()
        bot_online = is_telegram_bot_running()
        bot_badge = f"{GREEN}🟢 ONLINE{RESET}" if bot_online else f"{YELLOW}⚪ Stopped{RESET}"

        print(f"  Accounts: {CYAN}{len(accounts)}{RESET} (Logged In: {GREEN}{ready_count}{RESET}) | Proxies: {MAGENTA}{len(proxies)}{RESET} | Telegram: {bot_badge}\n")
        print(f"  {BOLD}--- ACTIONS ON POST ---{RESET}")
        print(f"  {BOLD}[1]{RESET} ❤️  Like Post Only")
        print(f"  {BOLD}[2]{RESET} 💬 Comment on Post Only (Presets or AI)")
        print(f"  {BOLD}[3]{RESET} 👤 Follow Creator Only")
        print(f"  {BOLD}[4]{RESET} 🔄 Share / Copy Link Only")
        print(f"  {BOLD}[5]{RESET} 🔖 Save / Favorite Post Only")
        print(f"  {BOLD}[6]{RESET} 🔁 Repost Video to Followers Only")
        print(f"  {BOLD}[7]{RESET} 🚀 Custom Multi-Action (Combine Any Actions)")
        print(f"\n  {BOLD}--- AUTOMATION & SAFETY ---{RESET}")
        print(f"  {BOLD}[8]{RESET} 🧘 FYP Warm-up Mode (Surfs feed, builds trust)")
        print(f"  {BOLD}[9]{RESET} 📲 Start Telegram Remote Bot (Send links via phone)")
        print(f"\n  {BOLD}--- MANAGEMENT ---{RESET}")
        print(f"  {BOLD}[10]{RESET} 📋 Account Manager & Health Check")
        print(f"  {BOLD}[11]{RESET} 🔑 Log Into an Account (Real Chrome)")
        print(f"  {BOLD}[12]{RESET} 💬 Comment Templates Library")
        print(f"  {BOLD}[13]{RESET} ⚙️ Settings (Delays, AI Keys, Telegram)")
        print(f"  {BOLD}[14]{RESET} 🌐 Proxy Pool Manager ({len(proxies)} loaded)")
        print(f"  {BOLD}[15]{RESET} 📜 Engaged Videos History (View / Clear)")
        print(f"  {BOLD}[0]{RESET} 🚪 Exit\n")

        choice = input(f"{YELLOW}Select an option [0-15]:{RESET} ").strip()

        if choice == "1":
            run_single_action_flow("like")
        elif choice == "2":
            run_single_action_flow("comment")
        elif choice == "3":
            run_single_action_flow("follow")
        elif choice == "4":
            run_single_action_flow("share")
        elif choice == "5":
            run_single_action_flow("save")
        elif choice == "6":
            run_single_action_flow("repost")
        elif choice == "7":
            run_engagement_menu()
        elif choice == "8":
            run_warmup_flow()
        elif choice == "9":
            run_telegram_bot_flow()
        elif choice == "10":
            account_manager_menu()
        elif choice == "11":
            login_assistant_menu()
        elif choice == "12":
            comment_library_menu()
        elif choice == "13":
            settings_menu()
        elif choice == "14":
            proxy_manager_menu()
        elif choice == "15":
            engaged_history_menu()
        elif choice == "0":
            print(f"\n{CYAN}Thanks for using TikTok Motion by Dee! Goodbye.{RESET}\n")
            sys.exit(0)





if __name__ == "__main__":
    main()

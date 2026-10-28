"""
====================================================================
           TIKTOK MOTION - ADD & MANAGE ACCOUNTS
====================================================================
Script to interactively add, configure, and log into TikTok accounts.
Supports single-account creation, bulk creation, listing status, and instant login.
"""

from __future__ import annotations

import os
import sys
import json
import re
import asyncio
import argparse
from typing import Optional, List, Dict, Any
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Paths
BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
PROFILES_DIR = BASE_DIR / "profiles"

# Colors (ANSI)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_accounts() -> List[Dict[str, Any]]:
    """Loads accounts from accounts.json safely."""
    if not ACCOUNTS_FILE.exists():
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"{RED}[!] Error loading accounts.json: {e}{RESET}")
        return []


def save_accounts(accounts: List[Dict[str, Any]]) -> bool:
    """Saves accounts to accounts.json with clean formatting."""
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"{RED}[!] Error saving accounts.json: {e}{RESET}")
        return False


def is_account_logged_in(account_id: str) -> bool:
    """Checks if an account profile has a valid saved TikTok cookie session."""
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
        return profile_path.exists()


def get_next_suggested_id(accounts: List[Dict[str, Any]]) -> str:
    """Computes the next logical account ID like acc_51 based on existing accounts."""
    highest_num = 0
    for acc in accounts:
        aid = str(acc.get("id", ""))
        # Check if matches acc_N or plain integer
        m = re.search(r'(?:acc_)?(\d+)', aid)
        if m:
            val = int(m.group(1))
            if val > highest_num:
                highest_num = val
    return f"acc_{highest_num + 1}"


def list_accounts_status(accounts: List[Dict[str, Any]]):
    """Prints a styled table of all accounts and their login health."""
    print(f"\n{BOLD}{CYAN}=== Registered Accounts ({len(accounts)} total) ==={RESET}")
    if not accounts:
        print(f"{YELLOW}No accounts registered yet.{RESET}\n")
        return

    ready_count = 0
    for i, acc in enumerate(accounts, 1):
        aid = acc.get("id", "N/A")
        name = acc.get("name", "")
        proxy = acc.get("proxy", "") or "Direct (No Proxy)"
        logged_in = is_account_logged_in(aid)
        if logged_in:
            ready_count += 1
            status_badge = f"{GREEN}🟢 READY (Logged In){RESET}"
        else:
            status_badge = f"{RED}🔴 NEEDS LOGIN{RESET}"

        print(f" {i:2d}. {BOLD}{aid:10s}{RESET} | Name: {name:15s} | Proxy: {proxy:25s} | Status: {status_badge}")

    print(f"\nSummary: {GREEN}{ready_count} Logged In{RESET} / {RED}{len(accounts) - ready_count} Needs Login{RESET}\n")


def login_account(account_id: str):
    """Launches Google Chrome for the user to log in and save cookies."""
    print(f"\n{CYAN}[*] Starting Chrome login session for: {BOLD}{account_id}{RESET}...")
    try:
        from tiktok_auto import setup_login_session
        asyncio.run(setup_login_session(account_id))
        if is_account_logged_in(account_id):
            print(f"\n{GREEN}{BOLD}✅ Success! Account '{account_id}' is now logged in and ready for automations.{RESET}\n")
        else:
            print(f"\n{YELLOW}⚠️ Note: Account '{account_id}' was closed. If you didn't finish logging in, you can log in anytime later.{RESET}\n")
    except Exception as e:
        print(f"{RED}[!] Login session error: {e}{RESET}")


def interactive_add_account():
    """Interactive CLI wizard to add accounts step by step."""
    while True:
        accounts = load_accounts()
        suggested_id = get_next_suggested_id(accounts)

        print("\n" + "="*56)
        print(f"        {BOLD}{CYAN}TikTok Motion - Add New Account{RESET}")
        print("="*56)
        print(f"Existing Accounts: {len(accounts)}")
        print(f"Suggested Next ID: {BOLD}{GREEN}{suggested_id}{RESET}\n")

        # 1. Account ID
        acc_id_input = input(f"Enter Account ID [default: {suggested_id}]: ").strip()
        account_id = acc_id_input if acc_id_input else suggested_id

        # Check uniqueness
        if any(a.get("id") == account_id for a in accounts):
            print(f"{RED}[!] Account ID '{account_id}' already exists! Please choose a different ID.{RESET}")
            continue

        # 2. Account Name / Label
        default_name = f"Account {suggested_id.replace('acc_', '')}"
        name_input = input(f"Enter Friendly Name / Label [default: {default_name}]: ").strip()
        name = name_input if name_input else default_name

        # 3. Proxy
        print(f"\n{BOLD}Proxy Configuration (Optional):{RESET}")
        print("Format: http://username:password@ip:port OR ip:port:user:pass")
        print("Leave empty if this account uses direct local connection.")
        proxy_input = input("Enter Proxy [press ENTER for none]: ").strip()

        new_entry = {
            "id": account_id,
            "name": name,
            "proxy": proxy_input
        }

        accounts.append(new_entry)
        if save_accounts(accounts):
            print(f"\n{GREEN}{BOLD}🎉 Account '{account_id}' ({name}) successfully added to accounts.json!{RESET}")
        else:
            print(f"{RED}[!] Failed to save account.{RESET}")
            return

        # 4. Prompt to log in immediately
        do_login = input(f"\n👉 Do you want to open Chrome to log into '{account_id}' right now? (Y/n) [default: Y]: ").strip().lower()
        if do_login == "" or do_login == "y" or do_login == "yes":
            login_account(account_id)

        # 5. Ask to add another
        another = input("Do you want to add another account? (y/N) [default: N]: ").strip().lower()
        if another != "y" and another != "yes":
            print(f"\n{GREEN}Done! You now have {len(load_accounts())} registered accounts.{RESET}")
            break


def bulk_add_accounts(count: int):
    """Quickly adds multiple placeholder accounts in sequence."""
    accounts = load_accounts()
    added = []
    for _ in range(count):
        nid = get_next_suggested_id(accounts + added)
        num = nid.replace("acc_", "")
        new_entry = {
            "id": nid,
            "name": f"Account {num}",
            "proxy": ""
        }
        added.append(new_entry)

    accounts.extend(added)
    if save_accounts(accounts):
        print(f"\n{GREEN}{BOLD}✅ Successfully added {count} accounts: {[a['id'] for a in added]}{RESET}")
        print(f"Total accounts in file: {len(accounts)}")
        print(f"You can log into each account using: python add_account.py --login-only <account_id>")
    else:
        print(f"{RED}[!] Failed to save accounts.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="TikTok Motion - Add & Manage Accounts")
    parser.add_argument("--id", type=str, help="Account ID to add (e.g. acc_51)")
    parser.add_argument("--name", type=str, help="Account Name / Label")
    parser.add_argument("--proxy", type=str, default="", help="Proxy URL for this account")
    parser.add_argument("--login", action="store_true", help="Launch Chrome login session immediately after adding")
    parser.add_argument("--login-only", type=str, metavar="ACC_ID", help="Launch Chrome login session for an existing account ID")
    parser.add_argument("--bulk", type=int, metavar="COUNT", help="Bulk create N accounts in sequence (e.g. --bulk 5)")
    parser.add_argument("--list", action="store_true", help="List all accounts and their login status")

    args = parser.parse_args()

    # Mode 1: List status
    if args.list:
        list_accounts_status(load_accounts())
        return

    # Mode 2: Log into existing account
    if args.login_only:
        accounts = load_accounts()
        acc = next((a for a in accounts if a.get("id") == args.login_only), None)
        if not acc:
            print(f"{RED}[!] Account '{args.login_only}' not found in accounts.json.{RESET}")
            print(f"Available IDs: {[a.get('id') for a in accounts]}")
            return
        login_account(args.login_only)
        return

    # Mode 3: Bulk create accounts
    if args.bulk:
        if args.bulk <= 0:
            print(f"{RED}[!] Bulk count must be greater than 0.{RESET}")
            return
        bulk_add_accounts(args.bulk)
        return

    # Mode 4: Non-interactive add via CLI arguments
    if args.id:
        accounts = load_accounts()
        if any(a.get("id") == args.id for a in accounts):
            print(f"{RED}[!] Account ID '{args.id}' already exists in accounts.json!{RESET}")
            return
        name = args.name or f"Account {args.id.replace('acc_', '')}"
        new_entry = {
            "id": args.id,
            "name": name,
            "proxy": args.proxy
        }
        accounts.append(new_entry)
        if save_accounts(accounts):
            print(f"{GREEN}[+] Account '{args.id}' ({name}) added successfully!{RESET}")
            if args.login:
                login_account(args.id)
        return

    # Mode 5: Interactive wizard (Default)
    interactive_add_account()


if __name__ == "__main__":
    main()

"""
TikTok Motion - PC Automation Background Worker
Listens for new orders from the SMM Panel (Supabase), automatically executes
Likes or Saves using local TikTok account profiles via Playwright, and updates
the order status and Telegram alerts in real-time.
"""

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
PROFILES_DIR = BASE_DIR / "profiles"

# Import engagement automation functions
try:
    from tiktok_auto import engage_post
except ImportError:
    print("[!] Could not import engage_post from tiktok_auto. Ensure you run from tiktok-motion folder.")
    sys.exit(1)


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error loading settings: {e}")
    return {}


def load_accounts() -> list:
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error loading accounts: {e}")
    return []


def send_telegram(text: str):
    settings = load_settings()
    token = settings.get("telegram_bot_token")
    chat_id = settings.get("telegram_chat_id")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[!] Failed sending Telegram notification: {e}")


def query_pending_orders(settings: dict) -> list:
    url = settings.get("supabase_url")
    key = settings.get("supabase_key")
    if not url or not key:
        return []

    endpoint = f"{url.rstrip('/')}/rest/v1/orders?dynamic_provider=eq.tiktok_motion&status=eq.processing&order=created_at.asc&limit=5"
    req = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[!] Error querying Supabase orders: {e}")
    return []


def update_order_status(order_id: str, new_status: str, error_msg: str = None) -> bool:
    settings = load_settings()
    url = settings.get("supabase_url")
    key = settings.get("supabase_key")
    if not url or not key:
        return False

    endpoint = f"{url.rstrip('/')}/rest/v1/orders?id=eq.{order_id}"
    update_data = {
        "status": new_status,
        "last_status_check": datetime.utcnow().isoformat() + "Z"
    }
    if new_status in ["completed", "partial"]:
        update_data["completed_at"] = datetime.utcnow().isoformat() + "Z"
    if error_msg:
        update_data["last_provider_error"] = str(error_msg)[:500]

    payload = json.dumps(update_data).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status in [200, 204]
    except Exception as e:
        print(f"[!] Error updating order #{order_id} in Supabase: {e}")
        return False


async def process_order(order: dict):
    order_id = order.get("id")
    raw_link = order.get("link", "").strip()
    quantity = int(order.get("quantity") or 1)
    service_name = order.get("service_name") or "TikTok Motion"
    comments_field = (order.get("comments") or "").lower()

    # Determine action: like or save
    if "save" in comments_field or "save" in service_name.lower() or "favorite" in service_name.lower():
        action = "save"
        emoji = "🔖"
    else:
        action = "like"
        emoji = "❤️"

    short_id = order_id[:8] if order_id else "unknown"
    print(f"\n{'='*60}")
    print(f"[*] PICKED UP ORDER #{short_id}")
    print(f"[*] Action: {action.upper()} | Target: {raw_link} | Quantity: {quantity}")
    print(f"{'='*60}")

    send_telegram(
        f"⚡ <b>PC Worker Started Execution!</b>\n\n"
        f"🆔 <b>Order:</b> <code>#{short_id}</code>\n"
        f"{emoji} <b>Action:</b> <b>{action.upper()}</b>\n"
        f"🎯 <b>Target Qty:</b> {quantity} accounts\n"
        f"🔗 <b>Link:</b> <a href=\"{raw_link}\">{raw_link}</a>"
    )

    all_accounts = load_accounts()
    if not all_accounts:
        err = "No accounts configured in accounts.json"
        print(f"[!] {err}")
        update_order_status(order_id, "failed", err)
        send_telegram(f"❌ <b>Order #{short_id} Failed:</b> {err}")
        return

    # Select accounts up to requested quantity
    selected_accounts = all_accounts[:quantity]
    print(f"[*] Selected {len(selected_accounts)} accounts to execute {action.upper()}.")

    settings = load_settings()
    delay_min = settings.get("delay_min", 5)
    delay_max = settings.get("delay_max", 10)

    success_count = 0
    fail_count = 0

    for idx, acc in enumerate(selected_accounts, start=1):
        acc_id = acc.get("id")
        acc_name = acc.get("name", acc_id)
        print(f"\n[{idx}/{len(selected_accounts)}] Executing on {acc_name} ({acc_id})...")

        try:
            res = await engage_post(
                account=acc,
                post_url=raw_link,
                do_like=(action == "like"),
                do_follow=False,
                comment_text=None,
                do_share=False,
                do_save=(action == "save"),
                do_repost=False
            )
            # res is boolean or dict depending on configuration
            is_success = res is True or (isinstance(res, dict) and res.get("success") is True)
            if is_success:
                success_count += 1
                print(f"[+] Account {acc_name} ({acc_id}) successfully performed {action.upper()}!")
            else:
                fail_count += 1
                print(f"[-] Account {acc_name} ({acc_id}) failed {action.upper()}.")
        except Exception as e:
            fail_count += 1
            print(f"[!] Exception running account {acc_name}: {e}")

        # Account spacing delay
        if idx < len(selected_accounts):
            wait_sec = delay_min if delay_min == delay_max else (delay_min + (idx % (delay_max - delay_min + 1)))
            print(f"[*] Waiting {wait_sec}s before next account...")
            await asyncio.sleep(wait_sec)

    # Final status determination
    if success_count >= quantity:
        final_status = "completed"
    elif success_count > 0:
        final_status = "partial"
    else:
        final_status = "failed"

    update_order_status(order_id, final_status)

    status_icon = "✅" if final_status == "completed" else "⚠️" if final_status == "partial" else "❌"
    print(f"\n{status_icon} ORDER #{short_id} FINISHED: {final_status.upper()} ({success_count}/{quantity} succeeded)")

    send_telegram(
        f"{status_icon} <b>PC Automation Order Finished!</b>\n\n"
        f"🆔 <b>Order:</b> <code>#{short_id}</code>\n"
        f"{emoji} <b>Action:</b> <b>{action.upper()}</b>\n"
        f"📊 <b>Delivered:</b> <b>{success_count} / {quantity}</b> accounts\n"
        f"🏆 <b>Final Status:</b> <code>{final_status.upper()}</code>\n"
        f"🔗 <b>Post:</b> <a href=\"{raw_link}\">{raw_link}</a>"
    )


async def main_loop():
    print("=" * 60)
    print("      TIKTOK MOTION - PC AUTOMATION BACKGROUND WORKER")
    print("      Listening for SMM Panel orders in real-time...")
    print("=" * 60)

    settings = load_settings()
    if not settings.get("supabase_url") or not settings.get("supabase_key"):
        print("[!] CRITICAL: Supabase URL and Key not configured in settings.json!")
        return

    processed_ids = set()

    while True:
        try:
            pending = query_pending_orders(settings)
            for order in pending:
                oid = order.get("id")
                if oid and oid not in processed_ids:
                    processed_ids.add(oid)
                    await process_order(order)
        except Exception as loop_err:
            print(f"[!] Main loop error: {loop_err}")

        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n[!] PC Automation Worker stopped by user.")

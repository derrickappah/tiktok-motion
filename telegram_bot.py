"""
TikTok Motion - Telegram Remote Trigger Bot
Allows sending TikTok links directly from your phone to trigger engagement across your accounts!
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
PROFILES_DIR = BASE_DIR / "profiles"

def get_config():
    if not SETTINGS_FILE.exists():
        return {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    msg = (
        "👋 Welcome to *TikTok Motion Remote Bot*!\n\n"
        "Send me any TikTok link to trigger automation across your accounts.\n\n"
        f"Your Chat ID: `{user_id}`\n\n"
        "*Commands:*\n"
        "• `/status` - Check logged-in accounts\n"
        "• Send a TikTok URL directly to run engagement\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ACCOUNTS_FILE.exists():
        await update.message.reply_text("No accounts registered yet.")
        return
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)
    ready = sum(1 for a in accounts if (PROFILES_DIR / a['id']).exists())
    await update.message.reply_text(
        f"📊 *Account Status:*\nTotal Accounts: {len(accounts)}\nActive Logged In: {ready}",
        parse_mode="Markdown"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "tiktok.com" not in text:
        await update.message.reply_text("Please send a valid TikTok video link (e.g. https://vt.tiktok.com/...).")
        return

    config = get_config()
    allowed_chat = config.get("telegram_chat_id")
    if allowed_chat and str(update.effective_chat.id) != str(allowed_chat):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    # Extract clean URL
    url = [part for part in text.split() if "tiktok.com" in part][0]
    await update.message.reply_text(f"⏳ *Received TikTok URL:* {url}\nStarting engagement pipeline across active accounts...", parse_mode="Markdown")

    from tiktok_auto import load_accounts, engage_post
    accounts = load_accounts()
    active_accounts = [a for a in accounts if (PROFILES_DIR / a['id']).exists()]

    if not active_accounts:
        await update.message.reply_text("❌ No logged-in accounts available. Please log in via terminal first.")
        return

    success_count = 0
    for i, acc in enumerate(active_accounts):
        await update.message.reply_text(f"Running account {i+1}/{len(active_accounts)}: `{acc['id']}`...")
        res = await engage_post(
            account=acc,
            post_url=url,
            do_like=True,
            do_follow=False,
            comment_text="ai", # Uses AI comment by default
            do_share=True
        )
        if res:
            success_count += 1
        await asyncio.sleep(config.get("delay_min", 15))

    await update.message.reply_text(f"🎉 *Finished!* Successfully engaged on {success_count}/{len(active_accounts)} accounts.")

def main():
    config = get_config()
    token = config.get("telegram_bot_token")
    if not token:
        print("[!] Telegram Bot Token not set. Please set it in Settings [9].")
        return

    print("========================================================")
    print("  TikTok Motion Telegram Bot Listener is RUNNING")
    print("  Send any TikTok link from your phone to start automation!")
    print("========================================================")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()

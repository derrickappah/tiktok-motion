"""
TikTok Motion - Telegram Remote Trigger Bot
Interactive Telegram Bot with inline keyboard buttons and full feature menu!
"""

import os
import sys
import json
import random
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"
ACCOUNTS_FILE = BASE_DIR / "accounts.json"
COMMENTS_FILE = BASE_DIR / "comments.txt"
PROXIES_FILE = BASE_DIR / "proxies.txt"
PROFILES_DIR = BASE_DIR / "profiles"

# Temporary memory store for user state: {chat_id: {"state": ..., "data": ...}}
USER_STATES = {}


def get_config():
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def is_authorized(update: Update) -> bool:
    config = get_config()
    allowed_chat = config.get("telegram_chat_id")
    if not allowed_chat:
        return True  # If no specific chat ID locked, anyone with the bot link can use it
    user_id = str(update.effective_chat.id)
    return str(allowed_chat).strip() == user_id


def build_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("❤️ Like Only", callback_data="act_like"),
            InlineKeyboardButton("💬 Comment Only", callback_data="act_comment"),
        ],
        [
            InlineKeyboardButton("👤 Follow Only", callback_data="act_follow"),
            InlineKeyboardButton("🔄 Share Only", callback_data="act_share"),
        ],
        [
            InlineKeyboardButton("🔖 Save / Favorite Only", callback_data="act_save"),
            InlineKeyboardButton("🔁 Repost Only", callback_data="act_repost"),
        ],
        [
            InlineKeyboardButton("🚀 Multi-Action (All)", callback_data="act_all"),
            InlineKeyboardButton("🧘 FYP Warm-Up", callback_data="act_warmup"),
        ],
        [
            InlineKeyboardButton("🌐 Proxy Pool", callback_data="cmd_proxies"),
            InlineKeyboardButton("💬 Comments", callback_data="cmd_comments"),
        ],
        [
            InlineKeyboardButton("📊 Accounts Health", callback_data="cmd_status"),
            InlineKeyboardButton("⚙️ Settings / Delays", callback_data="cmd_settings"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    user_id = update.effective_chat.id
    welcome_text = (
        "★ *TIKTOK MOTION BY DEE - TELEGRAM CONTROL* ★\n\n"
        "Control all your TikTok accounts directly from your phone!\n\n"
        f"📱 *Your Chat ID:* `{user_id}`\n\n"
        "👉 *Choose an action below* or simply paste any TikTok link directly into this chat!"
    )
    await update.message.reply_text(welcome_text, reply_markup=build_main_menu(), parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(update):
        await query.edit_message_text("⛔ Unauthorized.")
        return

    data = query.data
    chat_id = update.effective_chat.id

    if data.startswith("act_"):
        action_map = {
            "act_like": ("Like Only", "like"),
            "act_comment": ("Comment Only", "comment"),
            "act_follow": ("Follow Only", "follow"),
            "act_share": ("Share Only", "share"),
            "act_save": ("Save Only", "save"),
            "act_repost": ("Repost Only", "repost"),
            "act_all": ("Multi-Action (Like + Comment + Share + Save + Repost)", "all"),
            "act_warmup": ("FYP Warm-Up", "warmup")
        }
        title, act_type = action_map.get(data, ("Engagement", "all"))

        if act_type == "warmup":
            USER_STATES[chat_id] = {"action": "warmup"}
            kb = [
                [InlineKeyboardButton("⚡ 2 Minutes per Account", callback_data="warm_2")],
                [InlineKeyboardButton("☕ 3 Minutes per Account", callback_data="warm_3")],
                [InlineKeyboardButton("🔥 5 Minutes per Account", callback_data="warm_5")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_home")]
            ]
            await query.edit_message_text(
                "🧘 *FYP Warm-Up Mode*\n\nSurfs the For You Page, watches random clips, and likes naturally to build account trust.\n\nChoose duration:",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
            return

        # Prepare for URL input
        USER_STATES[chat_id] = {"action": act_type}
        kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_home")]]
        await query.edit_message_text(
            f"🎯 *Selected:* `{title}`\n\n🔗 *Now send the TikTok video link below:*\n\n_(or tap Back to choose another action)_",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

    elif data.startswith("warm_"):
        duration = int(data.split("_")[1])
        await query.edit_message_text(f"🧘 Starting FYP Warm-Up for *{duration} minutes* per account...\nWatch your PC run!", parse_mode="Markdown")
        asyncio.create_task(run_warmup_pipeline(chat_id, context, duration))


    elif data == "cmd_status":
        accounts = []
        if ACCOUNTS_FILE.exists():
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        ready = sum(1 for a in accounts if (PROFILES_DIR / a['id']).exists())
        status_msg = (
            f"📊 *Accounts Dashboard:*\n\n"
            f"• Total Accounts in file: *{len(accounts)}*\n"
            f"• Logged In & Ready: *{ready}*\n"
            f"• Pending Login: *{len(accounts) - ready}*\n\n"
        )
        for i, a in enumerate(accounts[:10], 1):
            is_ready = (PROFILES_DIR / a['id']).exists()
            icon = "✅" if is_ready else "⚠️"
            status_msg += f"{icon} `{a['id']}` - {a.get('name', 'N/A')}\n"

        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(status_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "cmd_comments":
        comments = []
        if COMMENTS_FILE.exists():
            with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
                comments = [line.strip() for line in f if line.strip()]
        msg = f"💬 *Comment Templates Library ({len(comments)} items):*\n\n"
        for i, c in enumerate(comments[:8], 1):
            msg += f"{i}. {c}\n"
        if len(comments) > 8:
            msg += f"_...and {len(comments) - 8} more._\n"
        msg += "\n💡 You can edit or add more templates in the desktop menu or `comments.txt`."

        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "cmd_proxies":
        proxies = []
        if PROXIES_FILE.exists():
            with open(PROXIES_FILE, "r", encoding="utf-8") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        msg = (
            f"🌐 *Proxy Pool Status:*\n\n"
            f"• Total Loaded: *{len(proxies)}*\n"
            f"• Mode: *Random Proxy per Account/Action*\n\n"
        )
        if proxies:
            msg += "*Sample Proxies:*\n"
            for i, p in enumerate(proxies[:6], 1):
                msg += f"`{i}.` `{p}`\n"
            if len(proxies) > 6:
                msg += f"_...and {len(proxies) - 6} more._\n"
        else:
            msg += "⚠️ _No proxies loaded. Direct local connection is used._\n"

        msg += "\n💡 _Tip: You can paste or import new proxy lists anytime in the Motion terminal [13]._ "

        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "cmd_settings":
        cfg = get_config()
        msg = (
            f"⚙️ *Current Settings:*\n\n"
            f"• Concurrent Accounts: *{cfg.get('concurrency', 5)} at a time*\n"
            f"• Minimum Delay: *{cfg.get('delay_min', 15)}s*\n"
            f"• Maximum Delay: *{cfg.get('delay_max', 45)}s*\n"
            f"• AI Comments: *{'Enabled (Gemini)' if cfg.get('gemini_api_key') else 'Disabled (Preset Fallback)'}*\n"
        )
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "menu_home":
        USER_STATES[chat_id] = {}
        await query.edit_message_text(
            "★ *TIKTOK MOTION BY DEE - TELEGRAM CONTROL* ★\n\nChoose an action below or send a TikTok link directly:",
            reply_markup=build_main_menu(),
            parse_mode="Markdown"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_state = USER_STATES.get(chat_id, {})
    chosen_action = user_state.get("action", "all")

    urls = []
    for line in text.splitlines():
        for piece in line.split():
            if "tiktok.com" in piece and piece not in urls:
                urls.append(piece)

    if not urls:
        await update.message.reply_text(
            "⚠️ Please send valid TikTok video URL(s) (e.g., https://vt.tiktok.com/...).",
            reply_markup=build_main_menu()
        )
        return

    # Reset state
    USER_STATES[chat_id] = {}

    action_names = {
        "like": "❤️ Like Only",
        "comment": "💬 Comment Only",
        "follow": "👤 Follow Only",
        "share": "🔄 Share Only",
        "save": "🔖 Save Only",
        "repost": "🔁 Repost Only",
        "all": "🚀 Multi-Action (Like + Comment + Share + Save + Repost)"
    }
    action_label = action_names.get(chosen_action, "Custom Engagement")

    config = get_config()
    conc = config.get("concurrency", 5)

    url_summary = "\n".join([f"• `{u}`" for u in urls[:5]])
    if len(urls) > 5:
        url_summary += f"\n_...and {len(urls) - 5} more._"

    await update.message.reply_text(
        f"⚡ *Task Received!*\n\n"
        f"• *Queue Size:* {len(urls)} video(s)\n"
        f"• *Action:* `{action_label}`\n"
        f"• *Parallel Mode:* `{conc} accounts at once`\n\n"
        f"*Target Queue:*\n{url_summary}\n\n"
        f"Starting execution...",
        parse_mode="Markdown"
    )

    asyncio.create_task(run_engagement_pipeline(chat_id, context, urls, chosen_action))



async def run_engagement_pipeline(chat_id: int, context: ContextTypes.DEFAULT_TYPE, urls: list[str], action_type: str):
    from tiktok_auto import load_accounts, engage_post
    accounts = load_accounts()
    active_accounts = [a for a in accounts if (PROFILES_DIR / a['id']).exists()]

    if not active_accounts:
        await context.bot.send_message(chat_id=chat_id, text="❌ No logged-in accounts found. Please log in via `motion.bat` first.", parse_mode="Markdown")
        return

    config = get_config()
    concurrency_limit = config.get("concurrency", 5)

    do_like = action_type in ["like", "all"]
    do_follow = action_type in ["follow"]
    do_share = action_type in ["share", "all"]
    do_save = action_type in ["save", "all"]
    do_repost = action_type in ["repost", "all"]
    comment_text = "ai" if action_type in ["comment", "all"] else None

    total_urls = len(urls)
    total_accs = len(active_accounts)

    sem = asyncio.Semaphore(concurrency_limit)

    for u_idx, current_url in enumerate(urls, 1):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"▶️ *Processing Video [{u_idx}/{total_urls}]:*\n`{current_url}`\n(🚀 Running up to {min(concurrency_limit, total_accs)} accounts concurrently)",
            parse_mode="Markdown"
        )

        # Randomize execution order of accounts for each video
        exec_accounts = list(active_accounts)
        random.shuffle(exec_accounts)

        async def run_acc(acc, idx):
            stagger = (idx % concurrency_limit) * 1.5
            if stagger > 0:
                await asyncio.sleep(stagger)

            async with sem:
                await context.bot.send_message(chat_id=chat_id, text=f"🚀 [Vid {u_idx}/{total_urls} | Acc {idx+1}/{total_accs}] Starting `{acc['id']}`...", parse_mode="Markdown")
                res = await engage_post(
                    account=acc,
                    post_url=current_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost
                )
                return res

        results = await asyncio.gather(*[run_acc(acc, i) for i, acc in enumerate(exec_accounts)])
        success_count = sum(1 for r in results if r)

        if u_idx < total_urls:
            await context.bot.send_message(chat_id=chat_id, text=f"⏸️ Video {u_idx} completed ({success_count}/{total_accs} success). Cooling down 5s before next video...", parse_mode="Markdown")
            await asyncio.sleep(5.0)

    done_msg = (
        f"🎉 *Queue Completed!*\n\n"
        f"• Videos processed: *{total_urls}*\n"
        f"• Action: `{action_type.upper()}`\n"
        f"• Concurrency: *{concurrency_limit} parallel*\n\n"
        f"Ready for your next link(s)!"
    )
    await context.bot.send_message(chat_id=chat_id, text=done_msg, reply_markup=build_main_menu(), parse_mode="Markdown")


async def run_warmup_pipeline(chat_id: int, context: ContextTypes.DEFAULT_TYPE, duration_mins: int):
    from tiktok_auto import load_accounts, warmup_account
    accounts = load_accounts()
    active_accounts = [a for a in accounts if (PROFILES_DIR / a['id']).exists()]

    if not active_accounts:
        await context.bot.send_message(chat_id=chat_id, text="❌ No logged-in accounts found.", parse_mode="Markdown")
        return

    # Randomize warmup order across accounts
    random.shuffle(active_accounts)

    total = len(active_accounts)
    for i, acc in enumerate(active_accounts):
        await context.bot.send_message(chat_id=chat_id, text=f"🧘 [{i+1}/{total}] Warming up `{acc['id']}` for {duration_mins} mins...", parse_mode="Markdown")
        await warmup_account(acc, minutes=duration_mins)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎉 *Warm-Up Finished!*\nAll {total} accounts completed their FYP session.",
        reply_markup=build_main_menu(),
        parse_mode="Markdown"
    )



def main():
    config = get_config()
    token = config.get("telegram_bot_token")
    if not token:
        print("\n[!] Telegram Bot Token not set.")
        print("Please set your bot token in Settings via motion.bat (option [12]) or in settings.json.")
        print("\nNote: settings.json is not synced to GitHub for security, so each new device needs the token set once.")
        input("\nPress ENTER to exit...")
        return

    print("========================================================")
    print("  TikTok Motion Telegram Bot is LIVE with Interactive UI")
    print("  Open Telegram on your phone and tap Start!")
    print("========================================================")

    try:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("menu", start_cmd))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
    except Exception as e:
        print(f"\n[❌] Telegram Bot crashed: {e}")
        input("\nPress ENTER to exit...")


if __name__ == "__main__":
    main()

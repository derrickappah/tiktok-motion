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
ACTIVE_RUNNING_TASKS = {}  # chat_id -> asyncio.Task
STOP_REQUESTED = set()     # set of chat_ids that requested stop


def is_task_running(chat_id: int) -> bool:
    """Checks if there is an active engagement or warm-up automation currently running for this chat."""
    task = ACTIVE_RUNNING_TASKS.get(chat_id)
    return task is not None and not task.done()


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


def build_main_menu(chat_id: int = None):
    keyboard = []
    # If an automation is actively running, show a prominent STOP button right at the top
    if chat_id and is_task_running(chat_id):
        keyboard.append([
            InlineKeyboardButton("🛑 STOP RUNNING AUTOMATION", callback_data="stop_pipeline")
        ])

    keyboard.extend([
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
            InlineKeyboardButton("📜 Engaged History", callback_data="cmd_history"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings / Delays", callback_data="cmd_settings"),
        ]
    ])
    return InlineKeyboardMarkup(keyboard)


async def stop_current_automation(chat_id: int, context: ContextTypes.DEFAULT_TYPE, message_to_edit=None):
    """Immediately stops and terminates all active automation tasks and Chrome processes."""
    from tiktok_auto import stop_all_active_automations
    STOP_REQUESTED.add(chat_id)
    task = ACTIVE_RUNNING_TASKS.pop(chat_id, None)
    if task and not task.done():
        task.cancel()

    # Immediately terminate any active Chrome browser processes
    stop_all_active_automations()

    stop_text = (
        "🛑 *AUTOMATION STOPPED*\n\n"
        "• All pending videos and accounts have been halted.\n"
        "• All active browser sessions have been closed.\n\n"
        "Choose an action below when you are ready to resume:"
    )
    if message_to_edit:
        try:
            await message_to_edit.edit_text(stop_text, reply_markup=build_main_menu(chat_id), parse_mode="Markdown")
            return
        except Exception:
            pass
    await context.bot.send_message(chat_id=chat_id, text=stop_text, reply_markup=build_main_menu(chat_id), parse_mode="Markdown")


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler for /stop and /cancel."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return
    chat_id = update.effective_chat.id
    if is_task_running(chat_id):
        await stop_current_automation(chat_id, context)
    else:
        from tiktok_auto import stop_all_active_automations
        stop_all_active_automations()
        await update.message.reply_text(
            "ℹ️ No automation is currently running.\nAll browser sessions are cleared.",
            reply_markup=build_main_menu(chat_id)
        )


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler for /history to view engaged video history."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return
    from tiktok_auto import load_engaged_videos
    data = load_engaged_videos()
    total = len(data)
    if total == 0:
        await update.message.reply_text(
            "📜 *Engaged Videos History*\n\n_No videos have been engaged with yet._",
            reply_markup=build_main_menu(update.effective_chat.id),
            parse_mode="Markdown"
        )
        return

    items = list(data.values())[-10:]
    lines = []
    for it in reversed(items):
        url = it.get("primary_url") or it.get("normalized_url") or "Unknown"
        ts = it.get("last_engaged_at", "N/A")
        act = it.get("last_action", "N/A")
        lines.append(f"• `{url}`\n  _Action: {act.upper()} | Date: {ts}_")

    msg = f"📜 *ENGAGED VIDEOS HISTORY ({total} total)*\n\n" + "\n\n".join(lines)
    kb = [
        [InlineKeyboardButton("🗑️ Clear History", callback_data="history_clear_confirm")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def clear_history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler for /clear_history to reset engaged video records."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return
    from tiktok_auto import clear_engaged_history
    count = clear_engaged_history()
    await update.message.reply_text(
        f"🗑️ *Engaged Videos History Cleared!*\n\nRemoved *{count}* recorded video(s).\nYou can now re-engage any links.",
        reply_markup=build_main_menu(update.effective_chat.id),
        parse_mode="Markdown"
    )


def remember_chat_id(chat_id: int):
    """Automatically saves the active chat_id so the bot can push startup notifications directly."""
    try:
        cfg = get_config()
        if str(cfg.get("telegram_chat_id") or "") != str(chat_id):
            cfg["telegram_chat_id"] = str(chat_id)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            print(f"[+] Remembered active Telegram chat_id: {chat_id}")
    except Exception:
        pass


async def on_startup(application):
    """Pushes the interactive Telegram menu to the user as soon as the bot boots up."""
    config = get_config()
    chat_id = config.get("telegram_chat_id")
    if chat_id:
        try:
            welcome_text = (
                "🟢 *TikTok Motion Bot is Online & Ready!*\n\n"
                "⚡ System is active and listening for your links.\n"
                "👉 *Choose an action below* or paste any TikTok link directly into this chat:"
            )
            await application.bot.send_message(
                chat_id=int(chat_id),
                text=welcome_text,
                reply_markup=build_main_menu(int(chat_id)),
                parse_mode="Markdown"
            )
            print(f"[+] Sent startup notification to Telegram chat: {chat_id}")
        except Exception as e:
            print(f"[-] Could not send automatic startup message: {e}")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    user_id = update.effective_chat.id
    remember_chat_id(user_id)
    welcome_text = (
        "★ *TIKTOK MOTION BY DEE - TELEGRAM CONTROL* ★\n\n"
        "Control all your TikTok accounts directly from your phone!\n\n"
        f"📱 *Your Chat ID:* `{user_id}`\n\n"
        "👉 *Choose an action below* or simply paste any TikTok link directly into this chat!"
    )
    await update.message.reply_text(welcome_text, reply_markup=build_main_menu(user_id), parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(update):
        await query.edit_message_text("⛔ Unauthorized.")
        return

    data = query.data
    chat_id = update.effective_chat.id
    remember_chat_id(chat_id)

    if data == "stop_pipeline":
        await stop_current_automation(chat_id, context, message_to_edit=query.message)
        return

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
        STOP_REQUESTED.discard(chat_id)
        stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Warm-Up", callback_data="stop_pipeline")]])
        await query.edit_message_text(
            f"🧘 Starting FYP Warm-Up for *{duration} minutes* per account...\nWatch your PC run!",
            reply_markup=stop_kb,
            parse_mode="Markdown"
        )
        task = asyncio.create_task(run_warmup_pipeline(chat_id, context, duration))
        ACTIVE_RUNNING_TASKS[chat_id] = task


    elif data == "cmd_status":
        accounts = []
        if ACCOUNTS_FILE.exists():
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        ready = sum(1 for a in accounts if is_account_logged_in(a['id']))
        status_msg = (
            f"📊 *Accounts Dashboard:*\n\n"
            f"• Total Accounts in file: *{len(accounts)}*\n"
            f"• Logged In & Ready: *{ready}*\n"
            f"• Pending / Expired Login: *{len(accounts) - ready}*\n\n"
        )
        for i, a in enumerate(accounts[:10], 1):
            is_ready = is_account_logged_in(a['id'])
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
            f"• Watch Time Before Liking: *{cfg.get('watch_time_min', 8)}s - {cfg.get('watch_time_max', 15)}s*\n"
            f"• Minimum Delay: *{cfg.get('delay_min', 15)}s*\n"
            f"• Maximum Delay: *{cfg.get('delay_max', 45)}s*\n"
            f"• AI Comments: *{'Enabled (Gemini)' if cfg.get('gemini_api_key') else 'Disabled (Preset Fallback)'}*\n"
        )
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "cmd_history":
        from tiktok_auto import load_engaged_videos
        data_dict = load_engaged_videos()
        total = len(data_dict)
        if total == 0:
            kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
            await query.edit_message_text(
                "📜 *Engaged Videos History*\n\n_No videos have been engaged with yet._",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
            return

        items = list(data_dict.values())[-8:]
        lines = []
        for it in reversed(items):
            url = it.get("primary_url") or it.get("normalized_url") or "Unknown"
            ts = it.get("last_engaged_at", "N/A")
            act = it.get("last_action", "N/A")
            lines.append(f"• `{url}`\n  _Action: {act.upper()} | Date: {ts}_")

        msg = f"📜 *ENGAGED VIDEOS HISTORY ({total} total)*\n\n" + "\n\n".join(lines)
        kb = [
            [InlineKeyboardButton("🗑️ Clear History", callback_data="history_clear_confirm")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "history_clear_confirm":
        from tiktok_auto import clear_engaged_history
        count = clear_engaged_history()
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_home")]]
        await query.edit_message_text(
            f"🗑️ *Engaged Videos History Cleared!*\n\nRemoved *{count}* recorded video(s).\nYou can now re-engage any links.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

    elif data == "menu_home":
        USER_STATES[chat_id] = {}
        await query.edit_message_text(
            "★ *TIKTOK MOTION BY DEE - TELEGRAM CONTROL* ★\n\nChoose an action below or send a TikTok link directly:",
            reply_markup=build_main_menu(chat_id),
            parse_mode="Markdown"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized user.")
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    remember_chat_id(chat_id)

    # Check for text stop / cancel command
    if text.lower() in ["stop", "/stop", "cancel", "/cancel", "halt", "quit"]:
        if is_task_running(chat_id):
            await stop_current_automation(chat_id, context)
            return
        else:
            from tiktok_auto import stop_all_active_automations
            stop_all_active_automations()
            await update.message.reply_text(
                "ℹ️ No active automation is currently running.\nAll browser sessions are cleared.",
                reply_markup=build_main_menu(chat_id)
            )
            return

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
            reply_markup=build_main_menu(chat_id)
        )
        return

    # Filter for duplicate / already engaged videos
    from tiktok_auto import is_video_already_engaged
    new_urls = []
    already_engaged = []

    for u in urls:
        is_engaged, entry = is_video_already_engaged(u)
        if is_engaged:
            already_engaged.append((u, entry))
        else:
            new_urls.append(u)

    if already_engaged and not new_urls:
        USER_STATES[chat_id] = {}
        if len(already_engaged) == 1:
            u, entry = already_engaged[0]
            engaged_at = entry.get("last_engaged_at", "previously") if entry else "previously"
            action_done = entry.get("last_action", "actions") if entry else "actions"
            await update.message.reply_text(
                f"⚠️ *This video has already been engaged with!*\n\n"
                f"• *Link:* `{u}`\n"
                f"• *Action Taken:* `{action_done.upper()}`\n"
                f"• *Completed At:* `{engaged_at}`\n\n"
                f"_To prevent duplicate actions on the same video, this link was skipped._\n"
                f"_Tip: Use /clear_history if you wish to reset engaged history._",
                reply_markup=build_main_menu(chat_id),
                parse_mode="Markdown"
            )
        else:
            list_text = "\n".join([f"• `{u}` (_engaged {entry.get('last_engaged_at', '')}_)" for u, entry in already_engaged])
            await update.message.reply_text(
                f"⚠️ *All submitted videos have already been engaged with!*\n\n"
                f"{list_text}\n\n"
                f"_To prevent duplicate actions, the queue was not started._\n"
                f"_Tip: Use /clear_history if you wish to reset engaged history._",
                reply_markup=build_main_menu(chat_id),
                parse_mode="Markdown"
            )
        return

    if already_engaged and new_urls:
        list_text = "\n".join([f"• `{u}`" for u, _ in already_engaged])
        await update.message.reply_text(
            f"ℹ️ *Notice:* {len(already_engaged)} video(s) were already engaged with previously and skipped:\n"
            f"{list_text}\n\n"
            f"⏩ Proceeding with {len(new_urls)} fresh video(s)...",
            parse_mode="Markdown"
        )
        urls = new_urls

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

    STOP_REQUESTED.discard(chat_id)
    stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Automation", callback_data="stop_pipeline")]])

    await update.message.reply_text(
        f"⚡ *Task Received!*\n\n"
        f"• *Queue Size:* {len(urls)} video(s)\n"
        f"• *Action:* `{action_label}`\n"
        f"• *Parallel Mode:* `{conc} accounts at once`\n\n"
        f"*Target Queue:*\n{url_summary}\n\n"
        f"Starting execution...",
        reply_markup=stop_kb,
        parse_mode="Markdown"
    )

    task = asyncio.create_task(run_engagement_pipeline(chat_id, context, urls, chosen_action))
    ACTIVE_RUNNING_TASKS[chat_id] = task



async def run_engagement_pipeline(chat_id: int, context: ContextTypes.DEFAULT_TYPE, urls: list[str], action_type: str):
    from tiktok_auto import load_accounts, engage_post, stop_all_active_automations
    try:
        accounts = load_accounts()
        active_accounts = [a for a in accounts if is_account_logged_in(a['id'])]

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
        stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Automation", callback_data="stop_pipeline")]])

        async def safe_send_message(text: str, reply_markup=None):
            try:
                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception as e:
                print(f"[Telegram Notice] Could not send message: {e}")

        for u_idx, current_url in enumerate(urls, 1):
            if chat_id in STOP_REQUESTED:
                break

            await safe_send_message(
                f"▶️ *Processing Video [{u_idx}/{total_urls}]:*\n`{current_url}`\n(🚀 Running up to {min(concurrency_limit, total_accs)} accounts concurrently)",
                reply_markup=stop_kb
            )

            # Filter active accounts dynamically in case any were marked expired on previous videos
            exec_accounts = [a for a in active_accounts if is_account_logged_in(a['id'])]
            if not exec_accounts:
                await safe_send_message("⚠️ All accounts have expired sessions or are logged out. Please log in via `motion.bat`.")
                break

            random.shuffle(exec_accounts)
            curr_total_accs = len(exec_accounts)

            async def run_acc(acc, idx):
                if chat_id in STOP_REQUESTED:
                    return False
                stagger = (idx % concurrency_limit) * 1.5
                if stagger > 0:
                    await asyncio.sleep(stagger)

                if chat_id in STOP_REQUESTED:
                    return False

                async with sem:
                    if chat_id in STOP_REQUESTED:
                        return False
                    await safe_send_message(f"🚀 [Vid {u_idx}/{total_urls} | Acc {idx+1}/{curr_total_accs}] Starting `{acc['id']}`...", reply_markup=stop_kb)
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
                    if not is_account_logged_in(acc['id']):
                        await safe_send_message(f"⚠️ *Session Expired:* Account `{acc['id']}` session expired/invalidated! Marked as 'Needs Login'.")
                    return res

            # Run all intermediate accounts concurrently
            results = []
            batch_start_metrics = None
            last_res = None

            if curr_total_accs == 1:
                # Single account run: captures both start and end metrics
                only_acc = exec_accounts[0]
                await safe_send_message(
                    f"🚀 [Vid {u_idx}/{total_urls} | Acc 1/1] Starting `{only_acc['id']}` (Capturing Count Shifts)...",
                    reply_markup=stop_kb
                )
                last_res = await engage_post(
                    account=only_acc,
                    post_url=current_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    return_metrics=True
                )
                if not is_account_logged_in(only_acc['id']):
                    await safe_send_message(f"⚠️ *Session Expired:* Account `{only_acc['id']}` session expired/invalidated! Marked as 'Needs Login'.")

                if isinstance(last_res, dict):
                    batch_start_metrics = last_res.get("start_metrics")
                    results.append(last_res.get("success", False))
                else:
                    results.append(bool(last_res))
            else:
                # Multi-account run:
                # 1. First account runs to capture video starting baseline before any actions occur
                first_acc = exec_accounts[0]
                await safe_send_message(
                    f"🚀 [Vid {u_idx}/{total_urls} | Acc 1/{curr_total_accs}] Starting FIRST `{first_acc['id']}` (Capturing Initial Counts)...",
                    reply_markup=stop_kb
                )
                first_res = await engage_post(
                    account=first_acc,
                    post_url=current_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    return_metrics=True
                )
                if not is_account_logged_in(first_acc['id']):
                    await safe_send_message(f"⚠️ *Session Expired:* Account `{first_acc['id']}` session expired/invalidated! Marked as 'Needs Login'.")

                if isinstance(first_res, dict):
                    batch_start_metrics = first_res.get("start_metrics")
                    results.append(first_res.get("success", False))
                else:
                    results.append(bool(first_res))

                if chat_id in STOP_REQUESTED:
                    break

                # 2. Intermediate accounts (accounts 1 to N-2) run concurrently
                if curr_total_accs > 2:
                    mid_accounts = exec_accounts[1:-1]
                    mid_results = await asyncio.gather(*[run_acc(acc, i) for i, acc in enumerate(mid_accounts, 1)])
                    for r in mid_results:
                        if isinstance(r, dict):
                            if batch_start_metrics is None or not any(batch_start_metrics.values()):
                                if r.get("start_metrics"):
                                    batch_start_metrics = r.get("start_metrics")
                            results.append(r.get("success", False))
                        else:
                            results.append(bool(r))

                if chat_id in STOP_REQUESTED:
                    break

                # 3. Last account runs with return_metrics=True to capture final end counts
                last_acc = exec_accounts[-1]
                last_idx = curr_total_accs - 1
                await safe_send_message(
                    f"🚀 [Vid {u_idx}/{total_urls} | Acc {last_idx+1}/{curr_total_accs}] Starting LAST `{last_acc['id']}` (Capturing Final Counts)...",
                    reply_markup=stop_kb
                )
                last_res = await engage_post(
                    account=last_acc,
                    post_url=current_url,
                    do_like=do_like,
                    do_follow=do_follow,
                    comment_text=comment_text,
                    do_share=do_share,
                    do_save=do_save,
                    do_repost=do_repost,
                    return_metrics=True
                )
                if not is_account_logged_in(last_acc['id']):
                    await safe_send_message(f"⚠️ *Session Expired:* Account `{last_acc['id']}` session expired/invalidated! Marked as 'Needs Login'.")

                if isinstance(last_res, dict):
                    results.append(last_res.get("success", False))
                else:
                    results.append(bool(last_res))

            # Send consolidated metrics report for this video
            if isinstance(last_res, dict):
                start_m = batch_start_metrics or last_res.get("start_metrics") or {}
                end_m = last_res.get("end_metrics") or {}
                metric_report = (
                    f"📊 *VIDEO METRICS REPORT [Vid {u_idx}/{total_urls}]*\n"
                    f"`{current_url}`\n\n"
                    f"• ❤️ Likes: *{start_m.get('likes') if start_m.get('likes') is not None else '0'}* ➡️ *{end_m.get('likes') if end_m.get('likes') is not None else '0'}*\n"
                    f"• 💬 Comments: *{start_m.get('comments') if start_m.get('comments') is not None else '0'}* ➡️ *{end_m.get('comments') if end_m.get('comments') is not None else '0'}*\n"
                    f"• 🔖 Saves: *{start_m.get('saves') if start_m.get('saves') is not None else '0'}* ➡️ *{end_m.get('saves') if end_m.get('saves') is not None else '0'}*\n"
                    f"• 🔄 Shares: *{start_m.get('shares') if start_m.get('shares') is not None else '0'}* ➡️ *{end_m.get('shares') if end_m.get('shares') is not None else '0'}*"
                )
                await safe_send_message(metric_report)
            elif curr_total_accs > 1 and isinstance(first_res, dict):
                start_m = batch_start_metrics or {}
                metric_report = (
                    f"📊 *VIDEO METRICS REPORT [Vid {u_idx}/{total_urls}]*\n"
                    f"`{current_url}`\n\n"
                    f"• ❤️ Likes: *{start_m.get('likes') if start_m.get('likes') is not None else '0'}* ➡️ *N/A*\n"
                    f"• 💬 Comments: *{start_m.get('comments') if start_m.get('comments') is not None else '0'}* ➡️ *N/A*\n"
                    f"• 🔖 Saves: *{start_m.get('saves') if start_m.get('saves') is not None else '0'}* ➡️ *N/A*\n"
                    f"• 🔄 Shares: *{start_m.get('shares') if start_m.get('shares') is not None else '0'}* ➡️ *N/A*"
                )
                await safe_send_message(metric_report)
            success_count = sum(1 for r in results if r)

            # Record video as engaged if at least 1 account succeeded
            if success_count > 0:
                from tiktok_auto import mark_video_engaged
                canon_url = None
                if isinstance(last_res, dict) and last_res.get("canonical_url"):
                    canon_url = last_res.get("canonical_url")
                elif curr_total_accs > 1 and isinstance(first_res, dict) and first_res.get("canonical_url"):
                    canon_url = first_res.get("canonical_url")
                mark_video_engaged(
                    url=current_url,
                    canonical_url=canon_url,
                    action=action_type,
                    success_count=success_count
                )

            if u_idx < total_urls and chat_id not in STOP_REQUESTED:
                await safe_send_message(f"⏸️ Video {u_idx} completed ({success_count}/{total_accs} success). Cooling down 5s before next video...", reply_markup=stop_kb)
                await asyncio.sleep(5.0)

        if chat_id not in STOP_REQUESTED:
            done_msg = (
                f"🎉 *Queue Completed!*\n\n"
                f"• Videos processed: *{total_urls}*\n"
                f"• Action: `{action_type.upper()}`\n"
                f"• Concurrency: *{concurrency_limit} parallel*\n\n"
                f"Ready for your next link(s)!"
            )
            await safe_send_message(done_msg, reply_markup=build_main_menu(chat_id))

    except asyncio.CancelledError:
        print(f"[Telegram Bot] Engagement pipeline cancelled for chat {chat_id}")
        stop_all_active_automations()
    finally:
        ACTIVE_RUNNING_TASKS.pop(chat_id, None)
        STOP_REQUESTED.discard(chat_id)


async def run_warmup_pipeline(chat_id: int, context: ContextTypes.DEFAULT_TYPE, duration_mins: int):
    from tiktok_auto import load_accounts, warmup_account, stop_all_active_automations
    try:
        accounts = load_accounts()
        active_accounts = [a for a in accounts if is_account_logged_in(a['id'])]

        if not active_accounts:
            await context.bot.send_message(chat_id=chat_id, text="❌ No logged-in accounts found.", parse_mode="Markdown")
            return

        # Randomize warmup order across accounts
        random.shuffle(active_accounts)

        total = len(active_accounts)
        stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Warm-Up", callback_data="stop_pipeline")]])

        for i, acc in enumerate(active_accounts):
            if chat_id in STOP_REQUESTED:
                break
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🧘 [{i+1}/{total}] Warming up `{acc['id']}` for {duration_mins} mins...",
                reply_markup=stop_kb,
                parse_mode="Markdown"
            )
            await warmup_account(acc, minutes=duration_mins)

        if chat_id not in STOP_REQUESTED:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🎉 *Warm-Up Finished!*\nAll {total} accounts completed their FYP session.",
                reply_markup=build_main_menu(chat_id),
                parse_mode="Markdown"
            )
    except asyncio.CancelledError:
        print(f"[Telegram Bot] Warm-up pipeline cancelled for chat {chat_id}")
        stop_all_active_automations()
    finally:
        ACTIVE_RUNNING_TASKS.pop(chat_id, None)
        STOP_REQUESTED.discard(chat_id)


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
        app = (
            ApplicationBuilder()
            .token(token)
            .post_init(on_startup)
            .connect_timeout(30.0)
            .read_timeout(30.0)
            .write_timeout(30.0)
            .pool_timeout(30.0)
            .build()
        )
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("menu", start_cmd))
        app.add_handler(CommandHandler("stop", stop_cmd))
        app.add_handler(CommandHandler("cancel", stop_cmd))
        app.add_handler(CommandHandler("history", history_cmd))
        app.add_handler(CommandHandler("clear_history", clear_history_cmd))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
    except Exception as e:
        print(f"\n[❌] Telegram Bot crashed: {e}")
        input("\nPress ENTER to exit...")


if __name__ == "__main__":
    main()

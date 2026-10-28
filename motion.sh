#!/usr/bin/env bash

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

OS_NAME="$(uname -s)"

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "/root/tiktok-motion/venv/bin/activate" ]; then
    source /root/tiktok-motion/venv/bin/activate
fi

# Locate Python binary
PYTHON_BIN="python3"
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
fi

RUN_CMD="$PYTHON_BIN"

# Linux headless display handling (Xvfb is only needed on Linux without a DISPLAY, never on macOS)
if [ "$OS_NAME" = "Linux" ] && [ -z "$DISPLAY" ]; then
    if command -v xvfb-run &> /dev/null; then
        RUN_CMD="xvfb-run -a -s '-screen 0 1920x1080x24' $PYTHON_BIN"
    else
        echo "⚠️ Warning: No DISPLAY detected and Xvfb is not installed."
        echo "Install it with: apt-get install -y xvfb"
    fi
fi

if [ "$1" = "menu" ] || [ "$1" = "cli" ] || [ "$1" = "app" ]; then
    echo "📋 Starting TikTok Motion Terminal Menu..."
    eval "$RUN_CMD app.py"

elif [ "$1" = "add" ] || [ "$1" = "account" ] || [ "$1" = "accounts" ] || [ "$1" = "add_account" ]; then
    shift
    eval "$RUN_CMD add_account.py $@"

elif [ "$1" = "login" ]; then
    shift
    eval "$RUN_CMD add_account.py --login-only $1"

elif [ "$1" = "bg" ] || [ "$1" = "daemon" ]; then
    # Stop any old instance first
    pkill -f "telegram_bot.py" 2>/dev/null || true
    sleep 1
    echo "🚀 Starting TikTok Motion Telegram Bot in 24/7 background mode..."
    nohup $RUN_CMD telegram_bot.py > bot.log 2>&1 &
    PID=$!
    echo "✅ Bot is running in background! (PID: $PID)"
    echo "📜 Logs are streaming to: bot.log"
    echo "👉 Check logs anytime with: ./motion.sh status"

elif [ "$1" = "status" ]; then
    if pgrep -f "telegram_bot.py" > /dev/null; then
        echo "🟢 Telegram Bot is RUNNING (PID: $(pgrep -f 'telegram_bot.py'))"
    else
        echo "🔴 Telegram Bot is NOT running."
    fi
    if [ -f "bot.log" ]; then
        echo ""
        echo "=== Recent bot.log ==="
        tail -n 15 bot.log
    fi

elif [ "$1" = "stop" ]; then
    echo "🛑 Stopping Telegram Bot..."
    pkill -f "telegram_bot.py" 2>/dev/null || true
    pkill -f "Google Chrome" 2>/dev/null || true
    pkill -f "Chromium" 2>/dev/null || true
    pkill -f "chrome" 2>/dev/null || true
    echo "✅ Bot and browser sessions stopped."

else
    # Default action: automatically run the Telegram Bot directly!
    # Terminate any duplicate local background bot instance to avoid Conflict errors
    pkill -f "telegram_bot.py" 2>/dev/null || true
    sleep 0.5
    echo "🚀 Starting TikTok Motion Telegram Bot..."
    eval "$RUN_CMD telegram_bot.py"
fi

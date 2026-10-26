#!/usr/bin/env bash

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if DISPLAY is available, otherwise wrap in xvfb-run
RUN_CMD="python3"
if [ -z "$DISPLAY" ]; then
    if command -v xvfb-run &> /dev/null; then
        RUN_CMD="xvfb-run -a -s '-screen 0 1920x1080x24' python3"
    else
        echo "⚠️ Warning: No DISPLAY detected and Xvfb is not installed."
        echo "Install it with: apt-get install -y xvfb"
    fi
fi

if [ "$1" = "bot" ]; then
    echo "🚀 Starting TikTok Motion Telegram Bot with virtual display..."
    eval "$RUN_CMD telegram_bot.py"
elif [ "$1" = "bg" ]; then
    echo "🚀 Starting Telegram Bot in background (nohup)..."
    nohup $RUN_CMD telegram_bot.py > bot.log 2>&1 &
    echo "✅ Bot running in background! Logs at bot.log (PID: $!)"
else
    eval "$RUN_CMD app.py"
fi

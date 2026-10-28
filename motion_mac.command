#!/usr/bin/env bash

# Resolve script directory (Finder opens .command files in $HOME by default)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo "    TikTok Motion - Bot & Terminal Menu (macOS)"
echo "========================================================"
echo "[*] Starting Telegram Bot in companion mode..."
echo "[*] Opening Interactive Menu in this window..."
echo ""

# Check if virtual environment exists; if not, run setup automatically
if [ ! -d "venv" ]; then
    echo "[*] First-time setup detected. Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install --upgrade pip setuptools wheel
    python3 -m pip install --prefer-binary --only-binary :all: cryptography 2>/dev/null || python3 -m pip install --prefer-binary cryptography
    python3 -m pip install --prefer-binary -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

# Stop any leftover local bot instance to prevent Telegram conflict
pkill -f "telegram_bot.py" 2>/dev/null || true
if [ -f ".bot_pid" ]; then
    kill $(cat .bot_pid) 2>/dev/null || true
    rm -f .bot_pid 2>/dev/null || true
fi
sleep 0.5

# 1. Launch Telegram Bot in companion window or background
if command -v osascript &>/dev/null; then
    osascript -e 'tell application "Terminal" to do script "cd \"'"$DIR"'\" && [ -f venv/bin/activate ] && source venv/bin/activate; python3 telegram_bot.py"' 2>/dev/null || (python3 telegram_bot.py > bot.log 2>&1 &)
else
    python3 telegram_bot.py > bot.log 2>&1 &
fi

sleep 1

# 2. Launch Interactive Terminal Menu directly in this window
python3 app.py

# When the menu exits, cleanly stop the companion bot
pkill -f "telegram_bot.py" 2>/dev/null || true
if [ -f ".bot_pid" ]; then
    kill $(cat .bot_pid) 2>/dev/null || true
    rm -f .bot_pid 2>/dev/null || true
fi

echo ""
echo "Session closed."

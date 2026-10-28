#!/usr/bin/env bash

# Resolve script directory (Finder opens .command files in $HOME by default)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo "    TikTok Motion - Telegram Bot Controller (macOS)"
echo "========================================================"
echo "Starting TikTok Motion Telegram Bot..."
echo "Telegram commands and interactive menu will be sent to your phone."
echo ""

# Check if virtual environment exists; if not, run setup automatically
if [ ! -d "venv" ]; then
    echo "[*] First-time setup detected. Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

python3 telegram_bot.py

echo ""
echo "Bot session stopped."
read -p "Press Enter to exit..."

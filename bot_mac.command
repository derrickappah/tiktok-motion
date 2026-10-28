#!/usr/bin/env bash

# Resolve script directory (Finder opens .command files in $HOME by default)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo "    TikTok Motion - Telegram Bot Controller (macOS)"
echo "========================================================"

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Locate python binary
PYTHON_BIN="python3"
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
fi

$PYTHON_BIN telegram_bot.py

echo ""
echo "Bot session stopped."
read -p "Press Enter to exit..."

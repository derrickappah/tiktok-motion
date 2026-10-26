#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  TikTok Motion - Debian / Ubuntu Automated VPS Setup"
echo "========================================================"

# 1. Update apt repositories and install dependencies
apt-get update -y
apt-get install -y curl wget git python3 python3-pip python3-venv xvfb libxi6 libgconf-2-4 libnss3 libasound2 libgbm1 libgtk-3-0

# 2. Install official Google Chrome Stable
if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null; then
    echo "[*] Installing Google Chrome Stable..."
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt-get install -y /tmp/chrome.deb || apt-get -f install -y
    rm -f /tmp/chrome.deb
fi

# 3. Setup Python Virtual Environment
echo "[*] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements & playwright
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium

echo ""
echo "========================================================"
echo "  ✅ Setup Complete!"
echo "  To launch interactive menu:    ./motion.sh"
echo "  To launch Telegram bot directly: ./motion.sh bot"
echo "  To run bot in background:      ./motion.sh bg"
echo "========================================================"

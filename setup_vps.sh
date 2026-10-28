#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  TikTok Motion - Debian / Ubuntu Automated VPS Setup"
echo "========================================================"

# 1. Update apt repositories and install base tools
apt-get update -y
apt-get install -y curl wget git python3 python3-full python3-pip python3-venv xvfb

# 2. Install official Google Chrome Stable
if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null; then
    echo "[*] Installing Google Chrome Stable..."
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt-get install -y /tmp/chrome.deb || apt --fix-broken install -y
    rm -f /tmp/chrome.deb
fi

# 3. Setup Python Virtual Environment
echo "[*] Setting up Python virtual environment..."
/usr/bin/python3 -m venv venv || python3 -m venv venv
source venv/bin/activate

# 4. Install requirements & playwright with all OS dependencies
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps

chmod +x motion.sh

echo ""
echo "========================================================"
echo "  ✅ Setup Complete!"
echo "  • Start Telegram Bot:      ./motion.sh"
echo "  • Run 24/7 in Background:  ./motion.sh bg"
echo "  • Check Status & Logs:     ./motion.sh status"
echo "  • Stop Bot:                ./motion.sh stop"
echo "  • Terminal Menu:           ./motion.sh menu"
echo "========================================================"

#!/usr/bin/env bash
set -e

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo "      TikTok Motion - macOS Automated Setup"
echo "========================================================"

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 was not found on your Mac."
    echo "   Please install it via Homebrew: brew install python3"
    echo "   Or install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# 2. Check Google Chrome
if [ -d "/Applications/Google Chrome.app" ] || [ -d "$HOME/Applications/Google Chrome.app" ]; then
    echo "✅ Google Chrome found in /Applications"
else
    echo "⚠️ Google Chrome was not found in /Applications."
    echo "   TikTok Motion works best with official Google Chrome."
    echo "   You can download it from: https://www.google.com/chrome"
    echo "   (Playwright's bundled Chromium will be installed as a fallback)."
fi

# 3. Create Python Virtual Environment
echo "[*] Setting up Python virtual environment (venv)..."
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
echo "[*] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install Playwright browser
echo "[*] Installing Playwright Chromium browser..."
playwright install chromium

# 6. Ensure executable permissions on all Mac & Unix scripts
chmod +x setup_mac.sh motion.sh motion_mac.command menu_mac.command 2>/dev/null || true

echo ""
echo "========================================================"
echo "  🎉 macOS Setup Complete!"
echo "========================================================"
echo "  How to run on your Mac:"
echo "  1. Double-click: 'motion_mac.command' (Finder)"
echo "  2. Or in Terminal: ./motion.sh"
echo "  3. Terminal Menu:  ./motion.sh menu"
echo "========================================================"

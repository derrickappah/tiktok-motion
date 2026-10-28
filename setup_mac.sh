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

# Set Homebrew OpenSSL and pkg-config if installed (prevents Rust/Cargo build errors)
if command -v brew &>/dev/null; then
    BREW_OPENSSL="$(brew --prefix openssl@3 2>/dev/null || brew --prefix openssl 2>/dev/null || true)"
    if [ -n "$BREW_OPENSSL" ] && [ -d "$BREW_OPENSSL" ]; then
        export OPENSSL_DIR="$BREW_OPENSSL"
        export PKG_CONFIG_PATH="$BREW_OPENSSL/lib/pkgconfig:$PKG_CONFIG_PATH"
    fi
fi

# 4. Install dependencies (upgrade pip & setuptools first so pre-built binary wheels are used)
echo "[*] Upgrading pip, setuptools, and wheel..."
python3 -m pip install --upgrade pip setuptools wheel

echo "[*] Installing Python dependencies (using pre-built wheels)..."
python3 -m pip install --prefer-binary --only-binary :all: cryptography 2>/dev/null || python3 -m pip install --prefer-binary cryptography
python3 -m pip install --prefer-binary -r requirements.txt

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

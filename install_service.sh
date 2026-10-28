#!/usr/bin/env bash
set -e

# Resolve absolute directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "========================================================"
echo "  TikTok Motion - Install 24/7 Systemd Background Service"
echo "========================================================"

SERVICE_FILE="/etc/systemd/system/tiktok-motion.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=TikTok Motion Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/xvfb-run -a -s "-screen 0 1920x1080x24" $DIR/venv/bin/python3 $DIR/telegram_bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tiktok-motion
systemctl restart tiktok-motion

echo ""
echo "========================================================"
echo "  ✅ Installed and Started as 24/7 Background Service!"
echo "  • The bot will now run automatically forever (even after reboot)."
echo "  • Check status:  systemctl status tiktok-motion"
echo "  • Live logs:     journalctl -u tiktok-motion -f"
echo "  • Restart bot:   systemctl restart tiktok-motion"
echo "  • Stop bot:      systemctl stop tiktok-motion"
echo "========================================================"

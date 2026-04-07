#!/usr/bin/env bash
# Deploy systemd services for auto-start on boot.
# Run as: bash scripts/deploy.sh

set -euo pipefail

SERVICE_DIR="/etc/systemd/system"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER="${SUDO_USER:-pi}"

echo "Deploying aoos_fishcount services..."
echo "  Repo: $REPO_DIR"
echo "  User: $USER"

# Inference service
cat > /tmp/aoos-fishcount.service << UNIT
[Unit]
Description=Salmon CV Inference Pipeline — Nalaquq LLC / KRITFC
After=network.target

[Service]
User=$USER
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/.venv/bin/python -m aoos_fishcount --config $REPO_DIR/config/my_site.yaml
Restart=always
RestartSec=10
WatchdogSec=120
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

# Push service (hourly timer)
cat > /tmp/aoos-push.service << UNIT
[Unit]
Description=Salmon CV Hourly Summary Push
After=network.target

[Service]
User=$USER
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/.venv/bin/python $REPO_DIR/scripts/push_summary.py --config $REPO_DIR/config/my_site.yaml
Type=oneshot
UNIT

cat > /tmp/aoos-push.timer << UNIT
[Unit]
Description=Run aoos-push.service hourly

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
UNIT

sudo cp /tmp/aoos-fishcount.service "$SERVICE_DIR/"
sudo cp /tmp/aoos-push.service "$SERVICE_DIR/"
sudo cp /tmp/aoos-push.timer "$SERVICE_DIR/"

sudo systemctl daemon-reload
sudo systemctl enable --now aoos-fishcount
sudo systemctl enable --now aoos-push.timer

echo ""
echo "Services deployed. Status:"
sudo systemctl status aoos-fishcount --no-pager -l || true

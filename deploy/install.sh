#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/gratefultime-v2-backend}"
SERVICE_NAME="${SERVICE_NAME:-gratefultime-v2-backend.service}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

cd "$APP_DIR"

if [ ! -f ".env" ]; then
  echo "Missing .env in $APP_DIR"
  exit 1
fi

chmod +x "$APP_DIR/setup.sh"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

mkdir -p "$HOME/.config/systemd/user"
cp "$APP_DIR/deploy/gratefultime-v2-backend.service" "$HOME/.config/systemd/user/$SERVICE_NAME"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"
systemctl --user status "$SERVICE_NAME" --no-pager

echo ""
echo "Running on 0.0.0.0:33540 via systemd ($SERVICE_NAME)"
echo "Command: setup.sh 33540 --service"
echo ""
echo "  systemctl --user restart gratefultime-v2-backend"
echo "  journalctl --user -u gratefultime-v2-backend -f"

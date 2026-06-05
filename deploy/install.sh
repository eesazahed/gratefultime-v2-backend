#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/gratefultime-v2-backend}"
PORT="${PORT:-33540}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
SERVICE_NAME="${SERVICE_NAME:-gratefultime-api.service}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

cd "$APP_DIR"

if [ ! -f ".env" ]; then
  echo "Missing .env in $APP_DIR"
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p "$HOME/.config/systemd/user"
cp "$APP_DIR/deploy/gratefultime-api.service" "$HOME/.config/systemd/user/$SERVICE_NAME"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"
systemctl --user status "$SERVICE_NAME" --no-pager

echo ""
echo "API listening on 127.0.0.1:$PORT"
echo "Add deploy/Caddyfile.snippet to ~/Caddyfile, then run:"
echo "  systemctl --user reload caddy"
echo ""
echo "Verify:"
echo "  curl -s https://gratefultime-v2.eesa.hackclub.app/api/v1/"

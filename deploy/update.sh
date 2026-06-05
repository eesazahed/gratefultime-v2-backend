#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/gratefultime-v2-backend}"

cd "$APP_DIR"
git pull
systemctl --user restart gratefultime-v2-backend

echo "Updated and restarted gratefultime-v2-backend"

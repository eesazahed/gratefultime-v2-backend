#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ./setup.sh PORT [--service]"
  exit 1
fi

PORT="$1"
SERVICE_MODE=false

if [ "${2:-}" = "--service" ]; then
  SERVICE_MODE=true
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
  echo "PORT must be a non-negative integer."
  exit 1
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if [ ! -f ".env" ]; then
  echo "Missing .env in $APP_DIR" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

if [ "$SERVICE_MODE" = false ] && command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti ":$PORT" || true)
  if [ -n "$PIDS" ]; then
    kill -9 $PIDS || true
  fi
fi

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

if [ "$SERVICE_MODE" = true ]; then
  echo "[gratefultime] starting uvicorn on 0.0.0.0:${PORT}" >&2
  exec .venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1
fi

uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload

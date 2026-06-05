#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./setup.sh PORT"
  exit 1
fi

PORT="$1"

if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
  echo "PORT must be a non-negative integer."
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti ":$PORT" || true)
  if [ -n "$PIDS" ]; then
    kill -9 $PIDS || true
  fi
fi

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload

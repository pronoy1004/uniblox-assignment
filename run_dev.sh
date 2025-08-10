#!/usr/bin/env bash
set -euo pipefail

# Simple dev runner for the backend API

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

cd "$BACKEND_DIR"

# Create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate venv and install deps
source venv/bin/activate
pip install -r requirements.txt

# Allow overriding host/port via env
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting backend on http://$HOST:$PORT (Ctrl+C to stop)"
exec python -m uvicorn app.main:app --reload --host "$HOST" --port "$PORT"


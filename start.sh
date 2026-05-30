#!/bin/bash
cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "Нет .venv — сначала запусти: ./setup.sh"
  exit 1
fi

exec "$PYTHON" backend/server.py

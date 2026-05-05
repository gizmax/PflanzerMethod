#!/usr/bin/env bash
# Spustí Pflanzer web hub lokálně:
#   - backend: FastAPI + uvicorn na :8000
#   - frontend: Vite dev server na :5173
#
# Otevři v prohlížeči: http://localhost:5173/method/

set -euo pipefail

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$REPO_ROOT"

# Apply DB schema if not yet applied
if [ ! -f data/pflanzer.db ]; then
  python3 tool/db/migrate.py
fi

# Backend (background)
(
  cd tool/web/backend
  if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install -q -e .
  fi
  exec .venv/bin/uvicorn main:app --reload --port 8000
) &
BACKEND_PID=$!

# Frontend
(
  cd tool/web/frontend
  if [ ! -d node_modules ]; then
    npm install
  fi
  exec npm run dev
) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT INT TERM

echo "─────────────────────────────────────────"
echo "Pflanzer web hub (local)"
echo "  Backend:  http://localhost:8000/api/docs"
echo "  Frontend: http://localhost:5173/method/"
echo "─────────────────────────────────────────"
echo "Stop: Ctrl-C"

wait

#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python backend/wsgi.py &
BACKEND_PID=$!
python -m http.server 5500 &
FRONTEND_PID=$!
trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' EXIT INT TERM
printf "Backend: http://127.0.0.1:5000/api/health\nFrontend: http://127.0.0.1:5500/frontend/index.html\n"
wait

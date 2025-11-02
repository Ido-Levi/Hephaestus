#!/usr/bin/env bash
set -euo pipefail

# Start local dev stack:
# - Qdrant (via docker compose if needed)
# - Initialize DB and Qdrant collections (via .venv)
# - Backend server and monitor (nohup)
# - Frontend (Vite on :5173, strictPort)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

LOG_DIR="$repo_root/logs"
mkdir -p "$LOG_DIR"

qdrant_health() {
  curl -s -o /dev/null -w "%{http_code}" http://localhost:6333/health || true
}

backend_health() {
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true
}

echo "[start] Repo root: $repo_root"

# 1) Qdrant
status=$(qdrant_health)
echo "[start] Qdrant health HTTP: ${status:-none}"
if [ "$status" != "200" ]; then
  echo "[start] Starting Qdrant via docker compose"
  if command -v docker >/dev/null 2>&1; then
    docker compose up -d qdrant || true
  else
    echo "[start] Docker not found; please start Qdrant manually (docker required)."; exit 1
  fi
  for i in $(seq 1 30); do
    sleep 1
    status=$(qdrant_health)
    [ "$status" = "200" ] && echo "[start] Qdrant healthy" && break
    echo "[start] Waiting for Qdrant... ($i)"
  done
fi

# 2) Init DB and Qdrant collections (uses repo .venv)
if [ -x "$repo_root/.venv/bin/python" ]; then
  echo "[start] Initializing DB and Qdrant collections"
  "$repo_root/.venv/bin/python" "$repo_root/scripts/init_db.py" | tee -a "$LOG_DIR/setup.out"
  "$repo_root/.venv/bin/python" "$repo_root/scripts/init_qdrant.py" | tee -a "$LOG_DIR/setup.out"
else
  echo "[start] Python venv not found at .venv. Please create it and install deps."; exit 1
fi

# 3) Backend server and monitor
if ! lsof -iTCP:8000 -sTCP:LISTEN -Pn >/dev/null 2>&1; then
  echo "[start] Starting backend server"
  nohup "$repo_root/.venv/bin/python" "$repo_root/run_server.py" > "$LOG_DIR/server.out" 2>&1 &
  sleep 2
fi

if ! pgrep -f "run_monitor.py" >/dev/null 2>&1; then
  echo "[start] Starting monitor"
  nohup "$repo_root/.venv/bin/python" "$repo_root/run_monitor.py" > "$LOG_DIR/monitor.out" 2>&1 &
  sleep 2
fi

for i in $(seq 1 30); do
  sleep 1
  code=$(backend_health)
  [ "$code" = "200" ] && echo "[start] Backend healthy" && break
  echo "[start] Waiting for backend health... ($i)"
done

# 4) Frontend (Vite)
FE_DIR="$repo_root/frontend"
if ! lsof -iTCP:5173 -sTCP:LISTEN -Pn >/dev/null 2>&1; then
  echo "[start] Starting frontend (Vite) on :5173"
  if [ -d "$FE_DIR/node_modules" ]; then
    echo "[start] node_modules present; skipping install"
  else
    echo "[start] Installing frontend deps (npm ci)"
    (cd "$FE_DIR" && npm ci)
  fi
  (cd "$FE_DIR" && nohup npm run dev -- --port 5173 --strictPort > "$LOG_DIR/frontend.out" 2>&1 &)
  sleep 1
fi

echo "[start] Summary:"
echo "  Backend:  http://localhost:8000/health"
echo "  Qdrant:   http://localhost:6333/health"
echo "  Frontend: http://localhost:5173/"
echo "  Logs:     $LOG_DIR"

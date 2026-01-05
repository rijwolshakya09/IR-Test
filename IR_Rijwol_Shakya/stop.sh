#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FLUTTER_PID_FILE="$PID_DIR/flutter.pid"
WEB_PID_FILE="$PID_DIR/flutter_web.pid"
SCHEDULER_PID_FILE="$PID_DIR/scheduler.pid"

kill_if_running() {
  local pid_file="$1"
  local label="$2"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file" || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $label (PID $pid)..."
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file" || true
  fi
}

kill_if_running "$SCHEDULER_PID_FILE" "crawler scheduler"
kill_if_running "$FLUTTER_PID_FILE" "flutter"
kill_if_running "$WEB_PID_FILE" "flutter web"
kill_if_running "$BACKEND_PID_FILE" "backend (uvicorn)"

# Fallbacks
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "flutter run" 2>/dev/null || true
pkill -f "schedule_crawler.py" 2>/dev/null || true

echo "Stopped."

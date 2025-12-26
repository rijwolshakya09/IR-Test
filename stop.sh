#!/bin/bash
set -euo pipefail

PID_DIR=".pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
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
kill_if_running "$BACKEND_PID_FILE" "backend (uvicorn)"
kill_if_running "$FRONTEND_PID_FILE" "frontend (next dev)"

# Fallback if pid files are missing
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

echo "Servers stopped."

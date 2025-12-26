#!/bin/bash

# Run script for Information Retrieval project
# Usage: bash run.sh

set -euo pipefail

# Prefer a modern Python; backend requirements need Python >= 3.10
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "${PYTHON_BIN:-}" ]; then
    for candidate in python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON_BIN="$candidate"
            break
        fi
    done
fi

if [ -z "${PYTHON_BIN:-}" ]; then
    echo "Error: Python 3 is not installed (need Python >= 3.10)." >&2
    exit 1
fi

PY_OK="$("$PYTHON_BIN" -c 'import sys; print(int(sys.version_info >= (3,10)))' 2>/dev/null || echo 0)"
if [ "$PY_OK" != "1" ]; then
    echo "Error: backend dependencies require Python >= 3.10 (found: $("$PYTHON_BIN" -V 2>&1))." >&2
    echo "Install Python 3.10+ and re-run. Example on macOS (Homebrew): brew install python@3.11" >&2
    exit 1
fi

# Backend setup
BACKEND_DIR="backend"
VENV_DIR=".venv"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"

# Frontend setup
FRONTEND_DIR="frontend"
PACKAGE_JSON="$FRONTEND_DIR/package.json"

PID_DIR=".pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
SCHEDULER_PID_FILE="$PID_DIR/scheduler.pid"

# Optional: start crawler scheduler (weekly job)
START_SCHEDULER="${START_SCHEDULER:-0}"

mkdir -p "$PID_DIR"

# 1. Backend: Create and activate virtual environment, install requirements
if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
    VENV_PY_OK="$("$VENV_DIR/bin/python" -c 'import sys; print(int(sys.version_info >= (3,10)))' 2>/dev/null || echo 0)"
    if [ "$VENV_PY_OK" != "1" ]; then
        echo "Error: existing venv '$VENV_DIR' uses $("$VENV_DIR/bin/python" -V 2>&1), but backend needs Python >= 3.10." >&2
        echo "Fix: remove the venv and re-run: rm -rf $VENV_DIR && bash run.sh" >&2
        exit 1
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing Python requirements..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: $REQUIREMENTS_FILE not found. Skipping Python requirements install."
fi

# 2. Frontend: Install node modules if not present
if [ -f "$PACKAGE_JSON" ]; then
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "Installing Node.js dependencies..."
        cd "$FRONTEND_DIR"
        npm install
        cd -
    fi
else
    echo "Warning: $PACKAGE_JSON not found. Skipping npm install."
fi

# 3. Optional: Start crawler scheduler (runs weekly; does not crawl immediately)
if [ "$START_SCHEDULER" = "1" ]; then
    echo "Starting crawler scheduler (weekly)..."
    nohup bash -c "source \"$VENV_DIR/bin/activate\" && exec python3 schedule_crawler.py" > crawler_scheduler.log 2>&1 &
    echo "$!" > "$SCHEDULER_PID_FILE"
    echo "Crawler Scheduler PID: $(cat "$SCHEDULER_PID_FILE") (logs: crawler_scheduler.log)"
else
    echo "Skipping crawler scheduler (set START_SCHEDULER=1 to enable)."
fi

# 4. Start backend (FastAPI)
echo "Starting backend server..."
nohup bash -c "cd \"$BACKEND_DIR\" && exec uvicorn main:app --reload --host 0.0.0.0 --port 8000" > backend.log 2>&1 &
echo "$!" > "$BACKEND_PID_FILE"

# 5. Start frontend (Next.js)
echo "Starting frontend server..."
nohup bash -c "cd \"$FRONTEND_DIR\" && exec npm run dev" > frontend.log 2>&1 &
echo "$!" > "$FRONTEND_PID_FILE"


# 6. Show status
echo "Backend PID: $(cat "$BACKEND_PID_FILE") (logs: backend.log)"
echo "Frontend PID: $(cat "$FRONTEND_PID_FILE") (logs: frontend.log)"
echo "Servers are starting. Access frontend at http://localhost:3000 and backend at http://localhost:8000"
echo "To stop the servers, run: ./stop.sh"

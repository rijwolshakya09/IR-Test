#!/bin/bash

set -euo pipefail

# Prefer a modern Python; backend requirements need Python >= 3.10
PYTHON_BIN="${PYTHON_BIN:-}"
PYTHON_CMD=()
if [ -z "${PYTHON_BIN:-}" ]; then
    if command -v py >/dev/null 2>&1; then
        PYTHON_CMD=(py -3)
    else
        for candidate in python3.12 python3.11 python3.10 python3 python; do
            if command -v "$candidate" >/dev/null 2>&1; then
                PYTHON_CMD=("$candidate")
                break
            fi
        done
    fi
else
    PYTHON_CMD=("$PYTHON_BIN")
fi

if [ "${#PYTHON_CMD[@]}" -eq 0 ]; then
    echo "Error: Python 3 is not installed (need Python >= 3.10)." >&2
    exit 1
fi

PY_OK="$("${PYTHON_CMD[@]}" -c 'import sys; print(int(sys.version_info >= (3,10)))' 2>/dev/null || echo 0)"
if [ "$PY_OK" != "1" ]; then
    echo "Error: backend dependencies require Python >= 3.10 (found: $("${PYTHON_CMD[@]}" -V 2>&1))." >&2
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNAME_OUT="$(uname -s 2>/dev/null || echo "")"
IS_WINDOWS=0
case "$UNAME_OUT" in
    MINGW*|MSYS*|CYGWIN*)
        IS_WINDOWS=1
        ;;
esac
BACKEND_DIR="$ROOT_DIR/backend"
MOBILE_DIR="$ROOT_DIR/mobile"
WEB_DIR="$ROOT_DIR/flutter_web"
CRAWLER_DIR="$ROOT_DIR/crawler"
VENV_DIR="$ROOT_DIR/.venv"
VENV_BIN="bin"
if [ "$IS_WINDOWS" = "1" ]; then
    VENV_BIN="Scripts"
fi
FLUTTER_CMD="flutter"
if [ "$IS_WINDOWS" = "1" ] && command -v flutter.bat >/dev/null 2>&1; then
    FLUTTER_CMD="flutter.bat"
fi
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
PID_DIR="$ROOT_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FLUTTER_PID_FILE="$PID_DIR/flutter.pid"
WEB_PID_FILE="$PID_DIR/flutter_web.pid"
SCHEDULER_PID_FILE="$PID_DIR/scheduler.pid"

mkdir -p "$PID_DIR"

if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/$VENV_BIN/python" ]; then
    VENV_PY_OK="$("$VENV_DIR/$VENV_BIN/python" -c 'import sys; print(int(sys.version_info >= (3,10)))' 2>/dev/null || echo 0)"
    if [ "$VENV_PY_OK" != "1" ]; then
        echo "Error: existing venv '$VENV_DIR' uses $("$VENV_DIR/$VENV_BIN/python" -V 2>&1), but backend needs Python >= 3.10." >&2
        echo "Fix: remove the venv and re-run: rm -rf $VENV_DIR && bash run.sh" >&2
        exit 1
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    "${PYTHON_CMD[@]}" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/$VENV_BIN/activate"

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing Python requirements..."
    "$VENV_DIR/$VENV_BIN/python" -m pip install --upgrade pip
    "$VENV_DIR/$VENV_BIN/python" -m pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: $REQUIREMENTS_FILE not found. Skipping Python requirements install."
fi

# Start crawler scheduler (optional)
START_SCHEDULER="${START_SCHEDULER:-0}"
if [ "$START_SCHEDULER" = "1" ]; then
    echo "Starting crawler scheduler..."
    nohup bash -c "source \"$VENV_DIR/$VENV_BIN/activate\" && exec python3 \"$CRAWLER_DIR/schedule_crawler.py\"" > "$ROOT_DIR/crawler_scheduler.log" 2>&1 &
    echo "$!" > "$SCHEDULER_PID_FILE"
    echo "Scheduler PID: $(cat "$SCHEDULER_PID_FILE") (logs: crawler_scheduler.log)"
else
    echo "Skipping crawler scheduler (set START_SCHEDULER=1 to enable)."
fi

# Start backend
export DATA_DIR="${DATA_DIR:-$ROOT_DIR/data}"
export SEARCH_CACHE_TTL="${SEARCH_CACHE_TTL:-60}"
export SEARCH_CACHE_MAX="${SEARCH_CACHE_MAX:-128}"

if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
    echo "Backend already running (PID $(cat "$BACKEND_PID_FILE"))."
else
    echo "Starting backend server..."
    nohup bash -c "cd \"$BACKEND_DIR\" && exec uvicorn main:app --reload --host 0.0.0.0 --port 8000" > "$ROOT_DIR/backend.log" 2>&1 &
    echo "$!" > "$BACKEND_PID_FILE"
fi

# Start Flutter app (optional)
START_FLUTTER="${START_FLUTTER:-0}"
DEVICE_ID="${DEVICE_ID:-}"
API_BASE_URL="${API_BASE_URL:-}"
AUTO_START_EMULATOR="${AUTO_START_EMULATOR:-1}"

if [ "$START_FLUTTER" = "1" ]; then
    echo "Starting Flutter app..."
    if [ -z "$DEVICE_ID" ] && [ "$AUTO_START_EMULATOR" = "1" ]; then
        if command -v xcrun >/dev/null 2>&1; then
            IOS_DEVICE_ID="$(python3 - <<'PY'
import json, subprocess, sys
out = subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "-j"]).decode()
data = json.loads(out)
for runtime, devices in data.get("devices", {}).items():
    if "iOS" not in runtime:
        continue
    for d in devices:
        if d.get("isAvailable"):
            print(d.get("udid") or "")
            sys.exit(0)
print("")
PY
)"
            if [ -n "$IOS_DEVICE_ID" ]; then
                echo "Booting iOS Simulator ($IOS_DEVICE_ID)..."
                xcrun simctl boot "$IOS_DEVICE_ID" >/dev/null 2>&1 || true
                open -a Simulator >/dev/null 2>&1 || true
                DEVICE_ID="$IOS_DEVICE_ID"
            fi
        fi

        if [ -z "$DEVICE_ID" ] && command -v emulator >/dev/null 2>&1; then
            ANDROID_AVD="$(emulator -list-avds | head -n 1)"
            if [ -n "$ANDROID_AVD" ]; then
                echo "Starting Android emulator ($ANDROID_AVD)..."
                nohup emulator -avd "$ANDROID_AVD" > "$ROOT_DIR/emulator.log" 2>&1 &
                sleep 5
            fi
        fi
    fi
    cd "$MOBILE_DIR"
    "$FLUTTER_CMD" pub get
    RUN_CMD=("$FLUTTER_CMD" run)
    if [ -z "$API_BASE_URL" ]; then
        if [ -n "$DEVICE_ID" ]; then
            # iOS simulator should use localhost; Android emulator uses 10.0.2.2
            if echo "$DEVICE_ID" | rg -q -i 'ios|iphone|ipad|sim'; then
                API_BASE_URL="http://localhost:8000"
            else
                API_BASE_URL="http://10.0.2.2:8000"
            fi
        else
            API_BASE_URL="http://localhost:8000"
        fi
    fi
    if [ -n "$DEVICE_ID" ]; then
        RUN_CMD+=( -d "$DEVICE_ID" )
    fi
    if [ -n "$API_BASE_URL" ]; then
        RUN_CMD+=( --dart-define=API_BASE_URL="$API_BASE_URL" )
    fi
    nohup "${RUN_CMD[@]}" > "$ROOT_DIR/flutter.log" 2>&1 &
    echo "$!" > "$FLUTTER_PID_FILE"
    cd - >/dev/null
else
    echo "Skipping Flutter (set START_FLUTTER=1 to enable)."
fi

# Start Flutter web app (optional)
START_WEB="${START_WEB:-0}"
WEB_DEVICE="${WEB_DEVICE:-chrome}"
WEB_API_BASE_URL="${WEB_API_BASE_URL:-http://localhost:8000}"

if [ "$START_WEB" = "1" ]; then
    if [ -d "$WEB_DIR" ]; then
        if [ -f "$WEB_PID_FILE" ] && kill -0 "$(cat "$WEB_PID_FILE")" 2>/dev/null; then
            echo "Flutter web already running (PID $(cat "$WEB_PID_FILE"))."
        else
            echo "Starting Flutter web app..."
            cd "$WEB_DIR"
            "$FLUTTER_CMD" pub get
            nohup "$FLUTTER_CMD" run -d "$WEB_DEVICE" --dart-define=API_BASE_URL="$WEB_API_BASE_URL" > "$ROOT_DIR/flutter_web.log" 2>&1 &
            echo "$!" > "$WEB_PID_FILE"
            cd - >/dev/null
        fi
    else
        echo "Warning: $WEB_DIR not found. Skipping Flutter web."
    fi
else
    echo "Skipping Flutter web (set START_WEB=1 to enable)."
fi

echo "Backend PID: $(cat "$BACKEND_PID_FILE") (logs: backend.log)"
if [ -f "$SCHEDULER_PID_FILE" ]; then
    echo "Scheduler PID: $(cat "$SCHEDULER_PID_FILE") (logs: crawler_scheduler.log)"
fi
if [ -f "$FLUTTER_PID_FILE" ]; then
    echo "Flutter PID: $(cat "$FLUTTER_PID_FILE") (logs: flutter.log)"
fi
if [ -f "$WEB_PID_FILE" ]; then
    echo "Flutter web PID: $(cat "$WEB_PID_FILE") (logs: flutter_web.log)"
fi

echo "Backend: http://localhost:8000"

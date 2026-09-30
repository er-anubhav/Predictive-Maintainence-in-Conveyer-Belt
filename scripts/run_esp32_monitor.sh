#!/usr/bin/env bash
# ==============================================================================
# SIH 26008 — ESP32 Conveyor Live Serial Monitor Launcher
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Locate Python Interpreter with pyserial
PYTHON_BIN=""

if [ -f "$PROJECT_ROOT/backend/api/venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_ROOT/backend/api/venv/bin/python3"
elif [ -f "$HOME/.local/share/pipx/venvs/platformio/bin/python" ]; then
    PYTHON_BIN="$HOME/.local/share/pipx/venvs/platformio/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[-] Error: No Python 3 interpreter found."
    exit 1
fi

# 2. Check pyserial availability
if ! "$PYTHON_BIN" -c "import serial" 2>/dev/null; then
    echo "[!] 'pyserial' not found in $PYTHON_BIN."
    echo "[*] Installing pyserial..."
    "$PYTHON_BIN" -m pip install pyserial
fi

# 3. Auto-detect Serial Port if not provided
PORT_ARG=""
if [ -z "$1" ]; then
    for candidate in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
        if [ -e "$candidate" ]; then
            PORT_ARG="--port $candidate"
            echo "[+] Found ESP32 serial interface: $candidate"
            break
        fi
    done
fi

# 4. Launch Monitor
echo "[*] Launching ESP32 Conveyor Live Hardware Monitor..."
exec "$PYTHON_BIN" "$SCRIPT_DIR/monitor_esp32_serial.py" $PORT_ARG "$@"

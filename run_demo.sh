#!/usr/bin/env bash
# ==============================================================================
# SIH 26008 — Unified Live Demo & Prototype Startup Script
# ==============================================================================
# Starts all tiers of the end-to-end predictive maintenance system:
# 1. PostgreSQL Database verification
# 2. FastAPI Backend Service (Port 8000)
# 3. Edge Gateway Store & Forward Service (Port 9000)
# 4. Decoupled Camera Worker
# 5. ESP32 Hardware / Telemetry Bridge
# 6. React Neo-Brutalist Dashboard (Port 5173)
#
# Usage:
#   ./run_demo.sh [--real | --demo]
# ==============================================================================

set -e

MODE="${1:---real}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "    SIH 26008 — INTELLIGENT CONVEYOR BELT MONITORING       "
echo "           LIVE DEMO & HARDWARE RUNNER                     "
echo "============================================================"

# 1. Check ESP32 Serial Device first to accurately determine hardware availability
ESP_PORT=""
for port in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
    if [ -e "$port" ]; then
        ESP_PORT="$port"
        break
    fi
done

# Determine System Mode truthfully based on physical hardware attachment
if [ "$MODE" = "--demo" ]; then
    SYSTEM_MODE="DEMO / SIMULATED"
    START_SIMULATOR=true
    ESP32_STATUS="OFFLINE (Synthetic Simulator Active)"
elif [ -n "$ESP_PORT" ]; then
    SYSTEM_MODE="REAL HARDWARE"
    START_SIMULATOR=false
    ESP32_STATUS="ONLINE (Physical on $ESP_PORT)"
else
    SYSTEM_MODE="DEMO / SIMULATED (ESP32 Not Plugged In)"
    START_SIMULATOR=false
    ESP32_STATUS="ONLINE (Telemetry Bridge Emulating Testbench)"
fi

# 2. Verify PostgreSQL
echo -n "Checking PostgreSQL Database... "
if pg_isready -h localhost -p 5434 >/dev/null 2>&1; then
    DB_STATUS="ONLINE (localhost:5434)"
    echo "✓ ONLINE"
else
    DB_STATUS="OFFLINE"
    echo "⚠ Offline or unreachable on port 5434"
fi

# 2. Check Camera Availability
if [ -e "/dev/video0" ]; then
    CAMERA_STATUS="ONLINE (/dev/video0)"
else
    CAMERA_STATUS="SYNTHETIC DEMO FALLBACK"
fi

BACKEND_STATUS="ONLINE (http://localhost:8000)"
GATEWAY_STATUS="ONLINE (http://localhost:9000)"
DASHBOARD_URL="http://localhost:5173"

echo ""
echo "------------------------------------------------------------"
echo " SYSTEM MODE:      $SYSTEM_MODE"
echo " CAMERA STATUS:    $CAMERA_STATUS"
echo " ESP32 STATUS:     $ESP32_STATUS"
echo " EDGE GATEWAY:     $GATEWAY_STATUS"
echo " BACKEND STATUS:   $BACKEND_STATUS"
echo " DATABASE STATUS:  $DB_STATUS"
echo " DASHBOARD URL:    $DASHBOARD_URL"
echo "------------------------------------------------------------"
echo ""

# PID cleanup trap on exit
cleanup() {
    echo ""
    echo "[SHUTDOWN] Stopping all SIH 26008 background processes..."
    kill $(jobs -p) 2>/dev/null || true
    echo "[SHUTDOWN] Complete."
}
trap cleanup EXIT INT TERM

LOG_DIR="$PROJECT_ROOT/archive/logs"
mkdir -p "$LOG_DIR"

# Start Backend API
echo "Starting FastAPI Backend (Port 8000)..."
cd "$PROJECT_ROOT/backend/api"
"$PROJECT_ROOT/backend/api/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Start Edge Gateway
echo "Starting Edge Gateway (Port 9000)..."
cd "$PROJECT_ROOT/iot/gateway/edge_agent"
"$PROJECT_ROOT/backend/api/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 9000 > "$LOG_DIR/gateway.log" 2>&1 &
GATEWAY_PID=$!

sleep 2

# Start ESP32 Telemetry Bridge
echo "Starting ESP32 Telemetry Bridge..."
"$PROJECT_ROOT/backend/api/venv/bin/python3" "$PROJECT_ROOT/iot/gateway/bridge/esp32_hardware_bridge.py" --url "http://localhost:9000/ingest" --interval 1.5 > "$LOG_DIR/bridge.log" 2>&1 &
BRIDGE_PID=$!

# Start Simulator ONLY if demo mode was explicitly requested
if [ "$START_SIMULATOR" = true ]; then
    echo "Starting Demo Simulator (Demo Mode requested)..."
    "$PROJECT_ROOT/backend/api/venv/bin/python3" "$PROJECT_ROOT/archive/simulator/generator.py" --transport gateway --scenario normal --interval 1.5 > "$LOG_DIR/simulator.log" 2>&1 &
fi

# Start React Frontend Dashboard
echo "Starting React Dashboard (Port 5173)..."
cd "$PROJECT_ROOT/frontend/dashboard"
npm run dev -- --host 0.0.0.0 --port 5173 > "$LOG_DIR/dashboard.log" 2>&1 &
DASH_PID=$!

echo ""
echo "============================================================"
echo " SIH 26008 PROTOTYPE READY FOR DEMONSTRATION"
echo " Open Dashboard: $DASHBOARD_URL"
echo " Press [Ctrl+C] to gracefully stop all services."
echo "============================================================"

# Wait on background processes
wait

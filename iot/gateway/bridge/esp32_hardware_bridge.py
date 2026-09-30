#!/usr/bin/env python3
"""
SIH 26008 — ESP32 Telemetry Bridge.

Provides a physical/virtual bridge for transmitting sensor telemetry packets from
connected hardware (or simulated hardware testbenches) through the Edge Gateway (port 9000)
or directly to the FastAPI Backend (port 8000).

Strict Semantics Enforced:
- ACTUAL PHYSICAL ESP32 DATA: source = "REAL_HARDWARE", is_simulated = False
- GENERATED / TESTBENCH DATA: source = "DEMO_SIMULATED", is_simulated = True
"""

import os
import sys
import time
import math
import json
import argparse
from datetime import datetime, timezone
import requests

try:
    import serial
except ImportError:
    serial = None

DEFAULT_GATEWAY_URL = "http://localhost:9000/ingest"
DEFAULT_BACKEND_URL = "http://localhost:8000/api/v1/telemetry"
PULLEY_DIAMETER_METERS = 0.50


def derive_speed_from_rpm(rpm: float, diameter_m: float = PULLEY_DIAMETER_METERS) -> float:
    return float((math.pi * diameter_m * rpm) / 60.0)


def derive_rpm_from_speed(speed_mps: float, diameter_m: float = PULLEY_DIAMETER_METERS) -> float:
    return float((speed_mps * 60.0) / (math.pi * diameter_m))


def detect_serial_device() -> str:
    for port in ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]:
        if os.path.exists(port):
            return port
    return ""


def build_canonical_packet(
    node_id: str,
    conveyor_id: str,
    sequence: int,
    source: str = "DEMO_SIMULATED",
    is_simulated: bool = True,
    scenario: str = "NORMAL",
) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()

    if scenario == "NORMAL":
        rms, peak, kurt, cf, dom, en = 0.38, 0.95, 3.1, 2.5, 14.5, 48.0
        temp = 42.0
        speed = 2.80
        load = 75.0
        track = 0.4
    elif scenario == "BEARING_FAULT":
        rms, peak, kurt, cf, dom, en = 1.95, 5.20, 18.5, 5.8, 38.0, 260.0
        temp = 53.0
        speed = 2.75
        load = 76.0
        track = -1.2
    elif scenario == "THERMAL_FAULT":
        rms, peak, kurt, cf, dom, en = 0.72, 1.65, 5.1, 2.8, 26.0, 95.0
        temp = 83.5
        speed = 2.65
        load = 82.0
        track = 2.5
    elif scenario == "MISALIGNMENT":
        rms, peak, kurt, cf, dom, en = 0.55, 1.35, 3.9, 2.45, 9.0, 68.0
        temp = 46.5
        speed = 2.70
        load = 74.0
        track = 17.5
    else:
        rms, peak, kurt, cf, dom, en = 0.38, 0.95, 3.1, 2.5, 14.5, 48.0
        temp = 42.0
        speed = 2.80
        load = 75.0
        track = 0.0

    rpm = derive_rpm_from_speed(speed)

    packet = {
        "schema_version": "1.0",
        "node_id": node_id,
        "conveyor_id": conveyor_id,
        "timestamp": now_iso,
        "sequence": sequence,
        "vibration": {
            "rms": rms,
            "peak": peak,
            "kurtosis": kurt,
            "crest_factor": cf,
            "dominant_frequency_hz": dom,
            "spectral_energy": en,
        },
        "acoustic": {
            "rms": 0.35,
        },
        "temperature": temp,
        "belt_speed": speed,
        "rpm": round(rpm, 1),
        "load": load,
        "tracking_position": track,
        "source": source,
        "is_simulated": is_simulated,
    }
    return packet


def run_bridge(
    target_url: str = DEFAULT_GATEWAY_URL,
    node_id: str = "NODE-001",
    conveyor_id: str = "Conveyor-01",
    interval: float = 1.0,
    burst_count: int = 0,
    scenario: str = "NORMAL",
    force_simulate: bool = False,
):
    print("=" * 65)
    print("SIH 26008 — ESP32 TELEMETRY BRIDGE ACTIVE")
    print("=" * 65)
    serial_port = "" if force_simulate else detect_serial_device()
    is_physical = bool(serial_port and serial)

    ser_conn = None
    if is_physical:
        try:
            ser_conn = serial.Serial(serial_port, 115200, timeout=1.0)
            print(f"  [HARDWARE] Physical ESP32 connected on {serial_port}.")
            print("  [HARDWARE] Forwarding authentic telemetry (Source: REAL_HARDWARE, is_simulated: false)")
        except Exception as e:
            print(f"  [WARN] Failed to open {serial_port}: {e}. Falling back to emulated testbench.")
            ser_conn = None
            is_physical = False

    if not is_physical:
        print("  [BRIDGE] No active physical serial microcontroller detected.")
        print(f"  [BRIDGE] Running emulated ESP32 testbench (Source: DEMO_SIMULATED, is_simulated: true, Node: {node_id})")

    print(f"  [TARGET]   Transmitting to: {target_url}")
    print(f"  [RATE]     Transmission interval: {interval}s")
    print(f"  [SCENARIO] Initial mode: {scenario}")
    print("=" * 65)

    seq = 1000
    count = 0

    while True:
        seq += 1
        count += 1
        packet = None

        if ser_conn and ser_conn.is_open:
            try:
                line = ser_conn.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        raw_data = json.loads(line)
                        if "sequence" in raw_data or "node_id" in raw_data:
                            packet = raw_data
                            packet["source"] = "REAL_HARDWARE"
                            packet["is_simulated"] = False
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"  [WARN] Serial read error: {e}")

        # If not received from physical serial, generate canonical testbench packet
        if not packet:
            source_label = "DEMO_SIMULATED"
            is_sim = True
            packet = build_canonical_packet(
                node_id=node_id,
                conveyor_id=conveyor_id,
                sequence=seq,
                source=source_label,
                is_simulated=is_sim,
                scenario=scenario,
            )

        try:
            resp = requests.post(target_url, json=packet, timeout=3.0)
            status_code = resp.status_code
            status_txt = "QUEUED/SENT" if status_code in (200, 201, 202) else f"HTTP {status_code}"
            src_tag = packet.get("source", "UNKNOWN")
            sim_tag = "SIM" if packet.get("is_simulated") else "PHYSICAL"
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Packet #{packet.get('sequence', seq)} [{src_tag}:{sim_tag}] -> {status_txt} "
                f"| Vib RMS: {packet.get('vibration', {}).get('rms', 0.0):.2f}g | Temp: {packet.get('temperature', 0.0):.1f}°C | Speed: {packet.get('belt_speed', 0.0):.2f}m/s"
            )
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Packet #{seq} -> Transmission Error: {e}")

        if burst_count > 0 and count >= burst_count:
            print(f"\nCompleted burst transmission of {burst_count} packets.")
            break

        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIH 26008 ESP32 Telemetry Bridge")
    parser.add_argument("--url", default=DEFAULT_GATEWAY_URL, help="Ingestion URL (Gateway or FastAPI)")
    parser.add_argument("--node", default="NODE-001", help="Sensor Node ID")
    parser.add_argument("--conveyor", default="Conveyor-01", help="Conveyor ID")
    parser.add_argument("--interval", type=float, default=1.5, help="Transmission interval in seconds")
    parser.add_argument("--count", type=int, default=0, help="Number of packets to send (0 = infinite)")
    parser.add_argument("--scenario", default="NORMAL", help="NORMAL | BEARING_FAULT | THERMAL_FAULT | MISALIGNMENT")
    parser.add_argument("--simulate", action="store_true", help="Force synthetic testbench simulation even if serial connected")
    args = parser.parse_args()

    run_bridge(
        target_url=args.url,
        node_id=args.node,
        conveyor_id=args.conveyor,
        interval=args.interval,
        burst_count=args.count,
        scenario=args.scenario,
        force_simulate=args.simulate,
    )

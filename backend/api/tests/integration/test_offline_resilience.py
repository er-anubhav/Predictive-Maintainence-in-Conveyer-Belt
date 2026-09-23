#!/usr/bin/env python3
"""
Industrial Edge Gateway Offline Resilience & Deduplication Verification
SIH Problem Statement 26008

Demonstrates:
  1. Real-time edge ingestion via Edge Gateway (Port 9000) -> Central Backend (Port 8000)
  2. Local deduplication at Edge Gateway via (node_id, sequence)
  3. Seamless offline SQLite buffering when Central Backend goes down
  4. Automatic queue flushing and zero-data-loss recovery when Central Backend is restored
  5. Backend deduplication idempotency in PostgreSQL
"""

import sys
import time
import subprocess
import os
import signal
from pathlib import Path
from typing import List, Dict, Any
import requests

GATEWAY_URL = "http://localhost:9000"
BACKEND_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
PYTHON_EXE = PROJECT_ROOT / "backend" / "api" / "venv" / "bin" / "python3"

if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)


def print_step(title: str):
    print("\n" + "=" * 70)
    print(f">> {title}")
    print("=" * 70)


def create_packet(seq: int, node_id: str = "NODE-001") -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "node_id": node_id,
        "conveyor_id": "Conveyor-01",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sequence": seq,
        "vibration": {
            "rms": round(0.35 + (seq % 10) * 0.02, 3),
            "peak": round(1.10 + (seq % 10) * 0.05, 3),
            "kurtosis": 3.12,
        },
        "acoustic": {
            "rms": round(0.28 + (seq % 10) * 0.01, 3),
        },
        "temperature": round(42.0 + (seq % 5) * 0.5, 2),
        "belt_speed": 2.80,
        "load": 75.0,
        "tracking_position": round(0.2 - (seq % 3) * 0.1, 2),
    }


def wait_for_url(url: str, timeout: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def is_listening(port: int) -> bool:
    try:
        out = subprocess.check_output(
            ["lsof", "-ti", f":{port}", "-sTCP:LISTEN"], text=True
        ).strip()
        return len(out) > 0
    except subprocess.CalledProcessError:
        return False


def start_backend():
    print("[Action] Starting Central Backend on port 8000...")
    proc = subprocess.Popen(
        [
            str(PYTHON_EXE),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        cwd=str(PROJECT_ROOT / "backend" / "api"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not wait_for_url(f"{BACKEND_URL}/health", timeout=12.0):
        raise RuntimeError("Failed to start Central Backend on port 8000!")
    print("[Check] Central Backend is ONLINE.")
    return proc


def start_gateway():
    print("[Action] Starting Edge Gateway on port 9000...")
    proc = subprocess.Popen(
        [
            str(PYTHON_EXE),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
        ],
        cwd=str(PROJECT_ROOT / "iot" / "gateway" / "edge_agent"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not wait_for_url(f"{GATEWAY_URL}/health", timeout=12.0):
        raise RuntimeError("Failed to start Edge Gateway on port 9000!")
    print("[Check] Edge Gateway is ONLINE.")
    return proc


def kill_backend():
    print("[Action] Simulating Central Backend Outage (stopping port 8000 listener)...")
    try:
        pids_out = subprocess.check_output(
            ["lsof", "-ti", ":8000", "-sTCP:LISTEN"], text=True
        ).strip()
        if pids_out:
            for pid_str in pids_out.split():
                pid = int(pid_str)
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            time.sleep(1.0)
    except subprocess.CalledProcessError:
        pass
    print("[Check] Central Backend port 8000 is now OFFLINE.")


def main():
    print("======================================================================")
    print("  SIH 26008: EDGE GATEWAY RESILIENCE & OFFLINE BUFFERING VERIFICATION")
    print("======================================================================")

    # 0. Ensure both services are running
    print_step("STEP 0: Service Verification & Health Checks")
    if not is_listening(8000):
        start_backend()
    if not is_listening(9000):
        start_gateway()

    assert wait_for_url(f"{GATEWAY_URL}/health", timeout=5.0), "Edge Gateway (port 9000) is not running!"
    assert wait_for_url(f"{BACKEND_URL}/health", timeout=5.0), "Backend (port 8000) is not running!"
    
    gw_health = requests.get(f"{GATEWAY_URL}/health").json()
    print(f"Gateway Health: {gw_health}")
    assert gw_health["status"] == "ok"

    # 1. Normal Ingestion
    print_step("STEP 1: Live Ingestion (Gateway -> Backend)")
    base_seq = (int(time.time()) % 800000) + 10000
    test_seq_1 = base_seq
    packet_1 = create_packet(test_seq_1)
    res = requests.post(f"{GATEWAY_URL}/ingest", json=packet_1)
    print(f"POST /ingest (seq {test_seq_1}) -> HTTP {res.status_code}: {res.json()}")
    assert res.status_code == 202
    assert res.json()["status"] == "queued"

    # Allow forwarder to deliver
    time.sleep(1.5)
    telemetry_list = requests.get(f"{BACKEND_URL}/api/v1/telemetry/NODE-001?limit=10").json()
    sequences = [t.get("sequence") for t in telemetry_list]
    print(f"Backend sequences in PostgreSQL: {sequences[:5]}")
    assert test_seq_1 in sequences, f"Expected sequence {test_seq_1} in backend telemetry!"
    print(f"[SUCCESS] Packet {test_seq_1} forwarded and stored in PostgreSQL.")

    # 2. Gateway Deduplication
    print_step("STEP 2: Gateway Deduplication Verification")
    res_dup = requests.post(f"{GATEWAY_URL}/ingest", json=packet_1)
    print(f"Resending Sequence {test_seq_1} -> HTTP {res_dup.status_code}: {res_dup.json()}")
    assert res_dup.status_code == 202
    assert res_dup.json()["status"] == "duplicate"
    metrics = requests.get(f"{GATEWAY_URL}/metrics").json()
    print(f"Gateway Metrics: {metrics}")
    assert metrics["duplicate_packets"] >= 1
    print(f"[SUCCESS] Duplicate sequence {test_seq_1} correctly intercepted by Edge Gateway.")

    # 3. Simulate Backend Outage & Test Offline Buffering
    print_step("STEP 3: Offline Outage Simulation (Queue Buffering)")
    kill_backend()

    # Send 5 packets while backend is down
    buffered_seqs = [base_seq + 1, base_seq + 2, base_seq + 3, base_seq + 4, base_seq + 5]
    print(f"Sending packets during outage: {buffered_seqs}...")
    for seq in buffered_seqs:
        p = create_packet(seq)
        r = requests.post(f"{GATEWAY_URL}/ingest", json=p)
        assert r.status_code == 202
        assert r.json()["status"] == "queued"
        print(f"  Ingested Sequence {seq} into Edge SQLite buffer (HTTP {r.status_code})")

    # Verify Gateway reports queue accumulation
    time.sleep(1.5)
    gw_offline_health = requests.get(f"{GATEWAY_URL}/health").json()
    print(f"\nGateway Health During Outage: {gw_offline_health}")
    assert gw_offline_health["queue_size"] >= 5, f"Expected queue >= 5, got {gw_offline_health['queue_size']}"
    assert gw_offline_health["backend_connected"] is False, "Expected backend_connected to be False during outage"
    print(f"[SUCCESS] Edge Gateway successfully buffered {gw_offline_health['queue_size']} packets in SQLite without backend.")

    # 4. Backend Restoration & Buffer Drain
    print_step("STEP 4: Central Backend Restoration & Resilient Drain")
    backend_proc = start_backend()

    # Wait for forwarder to drain buffer
    print("Waiting for Gateway forwarder background worker to drain buffer...")
    flushed = False
    for attempt in range(25):
        time.sleep(1.0)
        h = requests.get(f"{GATEWAY_URL}/health").json()
        print(f"  T+{attempt+1}s: Gateway Queue Size = {h['queue_size']}, Uplink Connected = {h['backend_connected']}")
        if h["queue_size"] == 0 and h["backend_connected"] is True:
            flushed = True
            break

    assert flushed, "Gateway queue failed to drain after backend restoration!"
    print("[SUCCESS] All buffered frames drained from SQLite queue to 0.")

    # 5. Verify Zero Data Loss in Backend
    print_step("STEP 5: Zero Data Loss & Deduplication Verification")
    time.sleep(1.0)
    db_telemetry = requests.get(f"{BACKEND_URL}/api/v1/telemetry/NODE-001?limit=30").json()
    db_seqs = [t.get("sequence") for t in db_telemetry]
    print(f"Recent sequences stored in PostgreSQL: {db_seqs[:10]}")

    for seq in buffered_seqs:
        assert seq in db_seqs, f"Data loss detected! Sequence {seq} missing from PostgreSQL!"
    print(f"[SUCCESS] All {len(buffered_seqs)} outage packets {buffered_seqs} recovered in PostgreSQL without loss!")

    # Verify backend deduplication
    print_step("STEP 6: Backend Deduplication Check")
    dedup_check_seq = base_seq + 1
    backend_res = requests.post(f"{BACKEND_URL}/api/v1/telemetry", json=create_packet(dedup_check_seq))
    print(f"Direct Backend Resend of Sequence {dedup_check_seq} -> HTTP {backend_res.status_code}")
    assert backend_res.status_code == 201

    # Ensure count for dedup_check_seq did not duplicate
    occurrences = sum(1 for t in requests.get(f"{BACKEND_URL}/api/v1/telemetry/NODE-001?limit=50").json() if t.get("sequence") == dedup_check_seq)
    print(f"Occurrences of Sequence {dedup_check_seq} in PostgreSQL: {occurrences}")
    assert occurrences == 1, f"Expected exactly 1 record for sequence {dedup_check_seq}, found {occurrences}"

    print("\n" + "=" * 70)
    print("  ALL MILESTONE 2 RESILIENCE & DEDUPLICATION TESTS PASSED!")
    print("======================================================================")


if __name__ == "__main__":
    main()

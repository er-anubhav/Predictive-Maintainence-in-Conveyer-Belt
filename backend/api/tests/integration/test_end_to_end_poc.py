#!/usr/bin/env python3
"""
SIH 26008 — End-to-End POC Integration & Verification Test.

Validates the full chain:
Simulator / Scenarios
  -> HTTP POST /api/v1/telemetry
  -> FastAPI Backend
  -> Actual Frozen IF-v0.3.1 Model Execution
  -> Local Commissioning (v0.5)
  -> Temporal Persistence (v0.6.1)
  -> Database Insertion (with all ML fields)
  -> HTTP GET /api/v1/telemetry history
"""

from pathlib import Path
import sys, os, time, json
from datetime import datetime, timezone
import requests
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = Path(__file__).resolve().parents[2]
SIMULATOR_DIR = PROJECT_ROOT / "archive" / "simulator"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SIMULATOR_DIR))

from app.main import app
# pyrefly: ignore [missing-import]
from scenarios import get_scenario

def run_test():
    print("=" * 65)
    print("SIH 26008 — END-TO-END POC INTEGRATION & VERIFICATION TEST")
    print("=" * 65)

    client = TestClient(app)

    # 1. Health check
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
    print("✓ FastAPI Backend Health: OK")

    # 2. Setup mine, conveyor, sensor node
    m_res = client.post("/api/v1/mines", json={"name": "POC Integration Mine", "location": "Sector POC"})
    mine_id = m_res.json()["id"]

    c_res = client.post(
        "/api/v1/conveyors",
        json={"mine_id": mine_id, "name": "POC Overland CV-01", "belt_type": "Steel Cord", "length": 500.0, "width": 1.4, "status": "OPERATIONAL"}
    )
    conveyor_id = c_res.json()["id"]

    node_code = f"NODE-POC-{int(time.time()) % 10000}"
    d_res = client.post(
        "/api/v1/devices",
        json={"conveyor_id": conveyor_id, "node_code": node_code, "location": "Head Drive Pulley", "firmware_version": "v1.0.0", "status": "ONLINE"}
    )
    assert d_res.status_code == 201
    print(f"✓ Created test sensor node: {node_code}")

    # 3. Test Scenarios: NORMAL -> BELT DRIFT -> BEARING SHOCK
    scenarios_to_test = [
        ("normal", 5),
        ("misalignment", 5),
        ("mechanical_abnormality", 7)
    ]

    seq = 1000
    results_summary = []

    for sc_name, count in scenarios_to_test:
        sc_obj = get_scenario(sc_name)
        print(f"\n--- Testing Scenario: {sc_name.upper()} ({count} windows) ---")
        for step in range(1, count + 1):
            seq += 1
            metrics = sc_obj.generate(step)
            ts = datetime.now(timezone.utc).isoformat()
            
            payload = {
                "node_id": node_code,
                "timestamp": ts,
                "sequence": seq,
                "vibration": {
                    "rms": metrics["vibration_rms"],
                    "peak": metrics["vibration_peak"],
                    "kurtosis": metrics["vibration_kurtosis"],
                },
                "acoustic": {"rms": metrics["acoustic_rms"]},
                "temperature": metrics["temperature"],
                "belt_speed": metrics["belt_speed"],
                "load": metrics["load"],
                "tracking_position": metrics["tracking_position"]
            }

            res = client.post("/api/v1/telemetry", json=payload)
            assert res.status_code == 201, f"Failed ingestion: {res.text}"
            data = res.json()

            # Assertions on returned ML evidence
            assert data["model_version"] == "IF-v0.3.1"
            assert data["commissioning_version"] == "v0.5"
            assert data["decision_layer_version"] == "v0.6.1"
            assert data["anomaly_score"] is not None
            assert data["composite_z_deviation"] is not None
            assert data["alert_state"] is not None

            print(f"  Step {step}: AnomalyScore={data['anomaly_score']:.3f} | CompZ={data['composite_z_deviation']:.2f}σ | 3-of-5={data['persistence_3of5']} | 5-of-9={data['persistence_5of9']} | State={data['alert_state']}")
            results_summary.append((sc_name, data["alert_state"], data["anomaly_score"], data["persistence_3of5"], data["persistence_5of9"]))

    # 4. Verify Database Persistence via GET endpoint
    print("\n--- Verifying Database Query & History Retrieval ---")
    get_res = client.get(f"/api/v1/telemetry/{node_code}?limit=50")
    assert get_res.status_code == 200
    history = get_res.json()
    print(f"✓ Retrieved {len(history)} records from database for {node_code}")
    latest = history[0]
    print(f"  Latest record: Model={latest['model_version']} | AnomalyScore={latest['anomaly_score']} | AlertState={latest['alert_state']} | Persistence3of5={latest['persistence_3of5']}")
    assert latest["model_version"] == "IF-v0.3.1"
    assert latest["anomaly_score"] is not None

    # Check alert state transition:
    # Normal scenario should start in NORMAL
    assert results_summary[0][1] in ["NORMAL", "WATCH"]
    # Mechanical abnormality sequence should escalate to WARNING or HIGH_SEVERITY
    final_alert = results_summary[-1][1]
    print(f"\nFinal Alert State after Mechanical Abnormality: {final_alert}")
    assert final_alert in ["WARNING", "HIGH_SEVERITY"]

    print("\n" + "=" * 65)
    print("END-TO-END VERIFICATION RESULT: PASS")
    print("Simulator -> API -> IF-v0.3.1 -> Persistence -> DB -> UI Query")
    print("=" * 65)

if __name__ == "__main__":
    run_test()

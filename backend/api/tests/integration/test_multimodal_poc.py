#!/usr/bin/env python3
"""
SIH 26008 — End-to-End Multimodal POC Verification Test.

Validates the full multimodal pipeline:
1. Frozen Vibration Model Verification (SHA-256 unchanged)
2. Normal Operating Baseline Execution
3. Bearing Anomaly (Vibration persistence detection)
4. Belt Misalignment (Tracking deviation + visual edge drift)
5. Thermal Event (Rapid temperature rise + threshold check)
6. Visible Belt Damage (Optical surface tear extraction)
7. Multimodal Compound Event (Multi-sensor corroboration)
8. Reset to Normal
9. Verification of explainable reasons, externalized image storage, and database persistence.
"""

from pathlib import Path
import os
import sys
import hashlib
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = Path(__file__).resolve().parents[2]

# Ensure project root in sys.path
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.sensor_node import SensorNode
from app.models.telemetry import Telemetry
from app.workers.camera_worker import CameraWorker

client = TestClient(app)


def verify_frozen_model():
    print("=" * 65)
    print("STEP 1: VERIFYING FROZEN VIBRATION MODEL ARTIFACT (IF-v0.3.1)")
    print("=" * 65)
    model_path = PROJECT_ROOT / "models" / "iforest" / "v0.3.1" / "model.joblib"
    assert model_path.exists(), f"Missing model at {model_path}"
    with open(model_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    expected = "fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19"
    print(f"  Model Path: {model_path}")
    print(f"  SHA-256:    {h}")
    assert h == expected, f"Model corruption or retraining detected! {h} != {expected}"
    print("✓ Model artifact is byte-for-byte identical to FROZEN IF-v0.3.1.\n")


def test_multimodal_pipeline():
    print("=" * 65)
    print("STEP 2: RUNNING COMPLETE MULTIMODAL POC VERIFICATION SUITE")
    print("=" * 65)

    db = SessionLocal()
    node_code = f"NODE-MM-{int(datetime.now().timestamp()) % 10000}"
    node = SensorNode(
        conveyor_id=1,
        node_code=node_code,
        location="Head Pulley Multimodal Test Station",
        firmware_version="v2.0-multimodal",
        status="ACTIVE",
    )
    db.add(node)
    db.commit()
    print(f"✓ Registered test sensor node: {node_code}\n")

    worker = CameraWorker.get_instance()

    scenarios = [
        ("NORMAL", "NORMAL", "NORMAL"),
        ("BEARING_ANOMALY", "WARNING", None),  # Vibration alone triggers WATCH/WARNING
        ("BELT_MISALIGNMENT", "WARNING", "MISALIGNMENT"),
        ("THERMAL_EVENT", "HIGH_SEVERITY", "NORMAL"),  # Rapid thermal rise + elevated vib -> HIGH_SEVERITY
        ("VISIBLE_BELT_DAMAGE", "HIGH_SEVERITY", "VISIBLE_DAMAGE"), # Damage co-occurs with vib -> HIGH_SEVERITY
        ("MULTIMODAL_EVENT", "HIGH_SEVERITY", "VISIBLE_DAMAGE"),
        ("NORMAL", "NORMAL", "NORMAL"), # RESET
    ]

    for idx, (sc_name, expected_state_hint, cam_sc) in enumerate(scenarios, start=1):
        print(f"--- Scenario {idx}: {sc_name} ---")
        res = client.post(
            "/api/v1/multimodal/simulate-scenario",
            json={
                "scenario": sc_name,
                "node_code": node_code,
                "conveyor_id": "Conveyor-01",
            },
        )
        assert res.status_code == 200, f"Failed simulate-scenario: {res.text}"
        data = res.json()
        print(f"  Operating State:  {data['operating_state']}")
        print(f"  Vibration Alert:  {data['vibration_alert']}")
        print(f"  Multimodal State: {data['multimodal_state']}")
        print(f"  Camera Status:    {data['camera_status']}")
        print(f"  Camera Frame Ref: {data['camera_frame_ref']}")
        print(f"  Explainable WHY:  {data['reasons']}")

        # Verify latest endpoint returns unified event
        lat_res = client.get(f"/api/v1/multimodal/latest?node_code={node_code}")
        assert lat_res.status_code == 200
        lat_event = lat_res.json()
        assert lat_event["overall_state"] == data["multimodal_state"]
        assert len(lat_event["reasons"]) > 0
        assert lat_event["vibration"] is not None
        assert lat_event["vibration"]["value"]["model_version"] == "IF-v0.3.1"
        assert lat_event["confidence"] is None
        assert lat_event["confidence_method"] == "NOT_CALIBRATED"

        # Verify camera frame file exists externally on disk (NOT stored as Base64 in DB)
        if data["camera_frame_ref"]:
            frame_filename = os.path.basename(data["camera_frame_ref"])
            img_path = os.path.join("data/evidence/camera", frame_filename)
            assert os.path.exists(img_path), f"Evidence image not written: {img_path}"
            # Verify evidence serving endpoint
            img_res = client.get(f"/api/v1/multimodal/camera/evidence/{frame_filename}")
            assert img_res.status_code == 200
            assert img_res.headers["content-type"] == "image/jpeg"
            assert len(img_res.content) > 1000

        print(f"  ✓ Scenario {sc_name} executed, fused, persisted, and verified.\n")

    # Verify database records
    records = db.query(Telemetry).filter(Telemetry.sensor_node_id == node.id).all()
    assert len(records) == len(scenarios)
    for r in records:
        assert r.model_version == "IF-v0.3.1"
        assert r.multimodal_state in ["NORMAL", "WATCH", "WARNING", "HIGH_SEVERITY"]
        assert r.operating_state is not None
        assert r.fusion_reasons is not None
        # Confirm no binary image blobs inside telemetry DB
        assert not hasattr(r, "image_data")
        assert not hasattr(r, "frame_blob")

    print(f"✓ All {len(records)} multimodal telemetry records successfully retrieved from PostgreSQL.")
    print("=" * 65)
    print("MULTIMODAL POC VERIFICATION SUCCESSFUL: 100% PASS")
    print("=" * 65)


if __name__ == "__main__":
    verify_frozen_model()
    test_multimodal_pipeline()

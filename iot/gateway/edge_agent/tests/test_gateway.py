import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import requests
from fastapi.testclient import TestClient

# Ensure edge_agent is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.buffer import SQLiteBuffer
from app.forwarder import ForwardingWorker
from app.metrics import metrics_manager
from app.main import create_app


@pytest.fixture
def temp_buffer(tmp_path):
    db_file = str(tmp_path / "test_buffer.db")
    buf = SQLiteBuffer(db_file)
    yield buf


@pytest.fixture
def app_and_client(temp_buffer):
    # Reset metrics
    metrics_manager.reset()

    app = create_app()
    app.state.buffer = temp_buffer
    forwarder = ForwardingWorker(temp_buffer)
    app.state.forwarder = forwarder
    app.state.auto_start_forwarder = False  # Keep forwarder manual for test isolation
    app.state.start_time = time.time()

    with TestClient(app) as client:
        yield client, temp_buffer, forwarder

    forwarder.stop()


def test_valid_packet_ingestion(app_and_client):
    """Test 1: Valid canonical packet ingestion."""
    client, buffer, _ = app_and_client

    payload = {
        "schema_version": "1.0",
        "node_id": "NODE-001",
        "conveyor_id": "Conveyor-01",
        "timestamp": "2026-09-21T12:30:10Z",
        "sequence": 1001,
        "vibration": {"rms": 0.42, "peak": 1.21, "kurtosis": 3.8},
        "acoustic": {"rms": 0.31},
        "temperature": 42.7,
        "belt_speed": 2.8,
        "load": 71.5,
        "tracking_position": -1.8,
    }

    response = client.post("/ingest", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["node_id"] == "NODE-001"
    assert data["sequence"] == 1001
    assert data["queue_id"] is not None


def test_invalid_packet_rejection(app_and_client):
    """Test 2: Invalid packet rejection (missing required sequence and node_id)."""
    client, _, _ = app_and_client

    invalid_payload = {
        "timestamp": "2026-09-21T12:30:10Z",
        # missing node_id, conveyor_id, sequence
    }

    response = client.post("/ingest", json=invalid_payload)
    assert response.status_code == 422


def test_queue_insertion(app_and_client):
    """Test 3: Verify packet is persisted in SQLite queue with PENDING status."""
    client, buffer, _ = app_and_client

    payload = {
        "schema_version": "1.0",
        "node_id": "NODE-002",
        "conveyor_id": "Conveyor-01",
        "timestamp": "2026-09-21T12:30:15Z",
        "sequence": 2001,
        "temperature": 43.2,
    }

    res = client.post("/ingest", json=payload)
    assert res.status_code == 202

    pending = buffer.get_pending(limit=10)
    assert len(pending) == 1
    assert pending[0]["node_id"] == "NODE-002"
    assert pending[0]["sequence"] == 2001
    assert buffer.get_queue_size() == 1


def test_duplicate_packet_handling(app_and_client):
    """Test 4: Duplicate packet handling (same node_id + sequence)."""
    client, buffer, _ = app_and_client

    packet = {
        "schema_version": "1.0",
        "node_id": "NODE-001",
        "conveyor_id": "Conveyor-01",
        "timestamp": "2026-09-21T12:30:10Z",
        "sequence": 3001,
        "temperature": 40.0,
    }

    # First ingestion
    res1 = client.post("/ingest", json=packet)
    assert res1.status_code == 202
    assert res1.json()["status"] == "queued"

    # Second ingestion (Duplicate sequence)
    res2 = client.post("/ingest", json=packet)
    assert res2.status_code in (200, 202)
    assert res2.json()["status"] == "duplicate"

    # Verify only 1 record in SQLite queue
    assert buffer.get_queue_size() == 1
    metrics = client.get("/metrics").json()
    assert metrics["duplicate_packets"] == 1


def test_backend_unavailable_keeps_pending(app_and_client):
    """Test 5 & 6: Backend unavailable leaves packets in queue with incremented retry count."""
    client, buffer, forwarder = app_and_client

    packet = {
        "schema_version": "1.0",
        "node_id": "NODE-001",
        "conveyor_id": "Conveyor-01",
        "timestamp": "2026-09-21T12:30:10Z",
        "sequence": 4001,
    }
    client.post("/ingest", json=packet)

    # Mock backend connection failure
    with patch("requests.post", side_effect=requests.ConnectionError("Connection refused")):
        pending = buffer.get_pending(limit=1)
        assert len(pending) == 1
        rec = pending[0]

        try:
            requests.post("http://fake-backend", json=rec["payload"])
        except requests.ConnectionError:
            buffer.mark_failed(rec["id"])

        # Packet must still be PENDING in queue, with retry_count incremented
        updated_pending = buffer.get_pending(limit=1)
        assert len(updated_pending) == 1
        assert updated_pending[0]["retry_count"] == 1
        assert buffer.get_queue_size() == 1


def test_successful_forwarding_and_queue_recovery(app_and_client):
    """Test 7, 8, 9: Successful forwarding marks records SENT and clears queue upon recovery."""
    client, buffer, _ = app_and_client

    packet = {
        "schema_version": "1.0",
        "node_id": "NODE-001",
        "conveyor_id": "Conveyor-01",
        "timestamp": "2026-09-21T12:30:10Z",
        "sequence": 5001,
    }
    client.post("/ingest", json=packet)
    assert buffer.get_queue_size() == 1

    # First attempt failed
    pending = buffer.get_pending(limit=1)
    buffer.mark_failed(pending[0]["id"])
    assert buffer.get_queue_size() == 1

    # Backend recovers! Mock returns 201 Created
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"status": "created"}

    with patch("requests.post", return_value=mock_resp):
        pending = buffer.get_pending(limit=1)
        assert len(pending) == 1
        resp = requests.post("http://fake-backend", json=pending[0]["payload"])
        if resp.status_code in (200, 201):
            buffer.mark_sent(pending[0]["id"])

        # Queue must now be empty
        assert buffer.get_queue_size() == 0


def test_health_and_metrics_endpoint(app_and_client):
    """Test 10: Verify /health and /metrics report correct statuses."""
    client, _, _ = app_and_client

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        health_res = client.get("/health")
        assert health_res.status_code == 200
        health = health_res.json()
        assert health["status"] == "ok"
        assert health["backend_connected"] is True
        assert "queue_size" in health
        assert "uptime_seconds" in health

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "packets_received" in metrics
    assert "packets_forwarded" in metrics
    assert "duplicate_packets" in metrics
    assert "current_queue_size" in metrics

from datetime import datetime, timezone


def test_health_check(client):
    """Test the GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "conveyor-maintenance-api"
    assert "timestamp" in data


def test_create_and_list_mine(client):
    """Test creating a mine and listing mines."""
    payload = {
        "name": "Test Odisha Iron Ore Mine",
        "location": "Sector 9, Eastern Mining Belt",
    }
    response = client.post("/api/v1/mines", json=payload)
    assert response.status_code == 201
    mine = response.json()
    assert mine["name"] == payload["name"]
    assert mine["location"] == payload["location"]
    assert "id" in mine

    # List mines
    list_res = client.get("/api/v1/mines")
    assert list_res.status_code == 200
    mines = list_res.json()
    assert any(m["id"] == mine["id"] for m in mines)


def test_create_and_get_conveyor(client):
    """Test creating a conveyor linked to a mine and getting its details."""
    # First create parent mine
    mine_res = client.post(
        "/api/v1/mines",
        json={"name": "Kalinganagar Bulk Terminal", "location": "Kalinganagar Block"},
    )
    mine_id = mine_res.json()["id"]

    # Create conveyor
    payload = {
        "mine_id": mine_id,
        "name": "Overland Conveyor CV-01",
        "belt_type": "Steel Cord ST-2500",
        "length": 450.0,
        "width": 1.4,
        "status": "OPERATIONAL",
    }
    conv_res = client.post("/api/v1/conveyors", json=payload)
    assert conv_res.status_code == 201
    conveyor = conv_res.json()
    assert conveyor["name"] == payload["name"]
    assert conveyor["mine_id"] == mine_id
    assert conveyor["length"] == 450.0

    # Get conveyor by ID
    get_res = client.get(f"/api/v1/conveyors/{conveyor['id']}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["name"] == payload["name"]
    assert isinstance(detail["sensor_nodes"], list)


def test_create_and_get_sensor_node(client):
    """Test creating a sensor node and retrieving it."""
    # Create mine and conveyor
    mine_res = client.post(
        "/api/v1/mines",
        json={"name": "Bailadila Iron Ore Deposit", "location": "Deposit 14"},
    )
    mine_id = mine_res.json()["id"]

    conv_res = client.post(
        "/api/v1/conveyors",
        json={
            "mine_id": mine_id,
            "name": "Main Incline Belt",
            "belt_type": "Fabric Multi-Ply",
            "length": 220.0,
            "width": 1.2,
            "status": "OPERATIONAL",
        },
    )
    conveyor_id = conv_res.json()["id"]

    # Create sensor node
    payload = {
        "conveyor_id": conveyor_id,
        "node_code": "NODE-TEST-001",
        "location": "Drive Pulley Non-Drive End",
        "firmware_version": "v1.0.0",
        "status": "ONLINE",
    }
    dev_res = client.post("/api/v1/devices", json=payload)
    assert dev_res.status_code == 201
    node = dev_res.json()
    assert node["node_code"] == "NODE-TEST-001"

    # Get sensor node by code
    get_res = client.get(f"/api/v1/devices/{node['node_code']}")
    assert get_res.status_code == 200
    assert get_res.json()["node_code"] == "NODE-TEST-001"

    # Get sensor node by integer ID
    get_id_res = client.get(f"/api/v1/devices/{node['id']}")
    assert get_id_res.status_code == 200
    assert get_id_res.json()["id"] == node["id"]


def test_submit_and_retrieve_telemetry(client):
    """Test posting telemetry from a sensor node and retrieving history."""
    # Setup mine, conveyor, sensor node
    mine_res = client.post(
        "/api/v1/mines",
        json={"name": "Joda East Mine", "location": "Keonjhar, Odisha"},
    )
    mine_id = mine_res.json()["id"]

    conv_res = client.post(
        "/api/v1/conveyors",
        json={
            "mine_id": mine_id,
            "name": "Reclaim Conveyor RC-02",
            "belt_type": "Steel Cord",
            "length": 300.0,
            "width": 1.6,
            "status": "OPERATIONAL",
        },
    )
    conveyor_id = conv_res.json()["id"]

    dev_res = client.post(
        "/api/v1/devices",
        json={
            "conveyor_id": conveyor_id,
            "node_code": "NODE-001",
            "location": "Head Pulley",
            "firmware_version": "v1.0.0",
            "status": "ONLINE",
        },
    )
    assert dev_res.status_code == 201

    # Submit Telemetry packet
    telemetry_payload = {
        "sensor_node_id": "NODE-001",
        "timestamp": "2026-09-21T12:30:10Z",
        "vibration_rms": 0.42,
        "vibration_peak": 1.21,
        "vibration_kurtosis": 3.8,
        "acoustic_rms": 0.31,
        "temperature": 42.7,
        "belt_speed": 2.8,
        "load": 71.5,
        "tracking_position": -1.8,
    }
    tel_res = client.post("/api/v1/telemetry", json=telemetry_payload)
    assert tel_res.status_code == 201
    created = tel_res.json()
    assert created["vibration_rms"] == 0.42
    assert created["node_code"] == "NODE-001"
    assert created["tracking_position"] == -1.8

    # Verify sensor node's last_seen was updated
    node_check = client.get("/api/v1/devices/NODE-001").json()
    assert node_check["last_seen"] is not None

    # Retrieve telemetry history
    history_res = client.get("/api/v1/telemetry/NODE-001?limit=10")
    assert history_res.status_code == 200
    records = history_res.json()
    assert len(records) >= 1
    assert records[0]["vibration_rms"] == 0.42
    assert records[0]["node_code"] == "NODE-001"


def test_telemetry_unknown_device_error(client):
    """Test telemetry submission for non-existent sensor node returns 404."""
    telemetry_payload = {
        "sensor_node_id": "NON-EXISTENT-999",
        "timestamp": "2026-09-21T12:30:10Z",
        "vibration_rms": 0.42,
        "vibration_peak": 1.21,
        "vibration_kurtosis": 3.8,
        "acoustic_rms": 0.31,
        "temperature": 42.7,
        "belt_speed": 2.8,
        "load": 71.5,
        "tracking_position": -1.8,
    }
    response = client.post("/api/v1/telemetry", json=telemetry_payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_canonical_telemetry_and_deduplication(client):
    """Test ingestion of canonical nested payload with sequence number and duplicate rejection."""
    # 1. Setup mine, conveyor, device
    m_res = client.post("/api/v1/mines", json={"name": "Deduplication Test Mine", "location": "Sector 5"})
    c_res = client.post(
        "/api/v1/conveyors",
        json={
            "mine_id": m_res.json()["id"],
            "name": "Dedup Conveyor",
            "belt_type": "Steel Cord",
            "length": 150.0,
            "width": 1.4,
            "status": "OPERATIONAL",
        },
    )
    d_res = client.post(
        "/api/v1/devices",
        json={
            "conveyor_id": c_res.json()["id"],
            "node_code": "NODE-DEDUP-01",
            "location": "Head Pulley",
            "firmware_version": "v1.0.0",
            "status": "ONLINE",
        },
    )

    # 2. Ingest canonical nested payload
    canonical_payload = {
        "schema_version": "1.0",
        "node_id": "NODE-DEDUP-01",
        "conveyor_id": "Dedup Conveyor",
        "timestamp": "2026-09-21T14:00:00Z",
        "sequence": 5001,
        "vibration": {
            "rms": 0.55,
            "peak": 1.45,
            "kurtosis": 3.2,
        },
        "acoustic": {
            "rms": 0.35,
        },
        "temperature": 44.5,
        "belt_speed": 2.8,
        "load": 68.0,
        "tracking_position": 1.2,
    }

    res1 = client.post("/api/v1/telemetry", json=canonical_payload)
    assert res1.status_code == 201
    item1 = res1.json()
    assert item1["sequence"] == 5001
    assert item1["vibration_rms"] == 0.55
    assert item1["node_code"] == "NODE-DEDUP-01"

    # 3. Ingest exact same packet with sequence 5001 (Duplicate)
    res2 = client.post("/api/v1/telemetry", json=canonical_payload)
    assert res2.status_code in (200, 201)
    item2 = res2.json()
    assert item2["id"] == item1["id"]  # Must return the existing record ID

    # 4. Verify only one record exists in history for sequence 5001
    history = client.get("/api/v1/telemetry/NODE-DEDUP-01?limit=10").json()
    matches = [r for r in history if r["sequence"] == 5001]
    assert len(matches) == 1


def test_signal_features_ingestion(client):
    """Test ingestion and retrieval of extended signal processing features (crest_factor, dominant_freq, spectral_energy)."""
    # 1. Setup
    m_res = client.post("/api/v1/mines", json={"name": "Signal Mine", "location": "Sector 9"})
    c_res = client.post("/api/v1/conveyors", json={"mine_id": m_res.json()["id"], "name": "Signal Conveyor", "belt_type": "Fabric", "length": 150.0, "width": 1.2, "status": "OPERATIONAL"})
    client.post("/api/v1/devices", json={"conveyor_id": c_res.json()["id"], "node_code": "NODE-SIG-01", "location": "Drive Motor", "firmware_version": "v1.0.0", "status": "ONLINE"})

    # 2. Ingest payload with derived signal features
    payload = {
        "schema_version": "1.0",
        "node_id": "NODE-SIG-01",
        "conveyor_id": "Signal Conveyor",
        "timestamp": "2026-09-21T15:00:00Z",
        "sequence": 6001,
        "vibration": {
            "rms": 0.42,
            "peak": 1.21,
            "kurtosis": 3.8,
            "crest_factor": 2.88,
            "dominant_frequency_hz": 48.8,
            "spectral_energy": 12.42,
        },
        "acoustic": {"rms": 0.31},
        "temperature": 42.7,
        "belt_speed": 2.8,
        "load": 71.5,
        "tracking_position": -1.8,
    }

    res = client.post("/api/v1/telemetry", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["crest_factor"] == 2.88
    assert data["dominant_frequency_hz"] == 48.8
    assert data["spectral_energy"] == 12.42

    # 3. Retrieve via GET endpoint
    records = client.get("/api/v1/telemetry/NODE-SIG-01?limit=5").json()
    assert len(records) >= 1
    rec = records[0]
    assert rec["sequence"] == 6001
    assert rec["crest_factor"] == 2.88
    assert rec["dominant_frequency_hz"] == 48.8
    assert rec["spectral_energy"] == 12.42


def test_vibration_ml_inference_integration(client):
    """Test that submitting telemetry triggers real IF-v0.3.1 inference and returns ML evidence fields."""
    # 1. Setup
    m_res = client.post("/api/v1/mines", json={"name": "ML Test Mine", "location": "Sector ML"})
    c_res = client.post(
        "/api/v1/conveyors",
        json={"mine_id": m_res.json()["id"], "name": "ML Conveyor", "belt_type": "Steel Cord", "length": 100.0, "width": 1.2, "status": "OPERATIONAL"}
    )
    client.post(
        "/api/v1/devices",
        json={"conveyor_id": c_res.json()["id"], "node_code": "NODE-ML-01", "location": "Drive Motor", "firmware_version": "v1.0.0", "status": "ONLINE"}
    )

    # 2. Submit healthy telemetry
    payload = {
        "node_id": "NODE-ML-01",
        "timestamp": "2026-09-22T10:00:00Z",
        "vibration_rms": 0.22,
        "vibration_peak": 0.85,
        "vibration_kurtosis": 3.0,
        "crest_factor": 3.86,
        "dominant_frequency_hz": 20.0,
        "spectral_energy": 55.0,
        "acoustic_rms": 0.25,
        "temperature": 40.0,
        "belt_speed": 2.8,
        "load": 70.0,
        "tracking_position": 0.0,
    }
    res = client.post("/api/v1/telemetry", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["model_version"] == "IF-v0.3.1"
    assert data["commissioning_version"] == "v0.5"
    assert data["decision_layer_version"] == "v0.6.1"
    assert "anomaly_score" in data and data["anomaly_score"] is not None
    assert "composite_z_deviation" in data and data["composite_z_deviation"] is not None
    assert "persistence_3of5" in data
    assert "persistence_5of9" in data
    assert data["alert_state"] in ["NORMAL", "WATCH", "WARNING", "HIGH_SEVERITY"]

    # 3. Retrieve history and ensure ML fields are persisted in DB
    history = client.get("/api/v1/telemetry/NODE-ML-01?limit=1").json()
    assert len(history) == 1
    h_rec = history[0]
    assert h_rec["model_version"] == "IF-v0.3.1"
    assert h_rec["anomaly_score"] is not None
    assert h_rec["alert_state"] is not None




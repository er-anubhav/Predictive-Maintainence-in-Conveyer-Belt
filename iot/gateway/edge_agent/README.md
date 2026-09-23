# Edge Gateway Agent — SIH 26008

## Overview

The Edge Gateway Agent represents the local compute and store-and-forward tier in the **Intelligent Conveyor Belt Health & Predictive Maintenance** architecture.

Operating on low-power industrial gateway hardware (e.g. Raspberry Pi 4 / CM4, Advantech edge computers, or industrial Linux gateways positioned along conveyor galleries), the gateway decouples edge sensor nodes from direct internet/cloud dependencies.

---

## Key Capabilities

1. **Local Network Ingestion (`POST /ingest`)**:
   Exposes a high-throughput local HTTP endpoint for ESP32 edge nodes.
2. **Persistent Offline Buffer (SQLite)**:
   Ingested frames are immediately saved to a local SQLite database (`telemetry_queue`) before acknowledging the edge node, ensuring zero telemetry loss during mining network dropouts.
3. **Sequence Tracking & Deduplication**:
   Enforces logical packet uniqueness using `(node_id, sequence)` to reject redundant network re-transmissions.
4. **Resilient Forwarding Worker**:
   A dedicated background daemon polls the SQLite queue and streams pending packets to the central FastAPI backend (`POST /api/v1/telemetry`) with exponential backoff and automatic recovery.
5. **Observability & Diagnostics**:
   Exposes `/health` and `/metrics` for real-time local monitoring and dashboard telemetry.

---

## API Endpoints

### 1. Ingestion Endpoint
- **URL:** `POST /ingest`
- **Port:** `9000`
- **Status:** `202 Accepted` (New packet queued) / `200 OK` (Duplicate detected)
- **Payload:** Canonical Telemetry JSON (see [docs/telemetry-contract.md](../../../docs/telemetry-contract.md))

### 2. Gateway Health Check
- **URL:** `GET /health`
- **Response:**
  ```json
  {
    "status": "ok",
    "backend_connected": true,
    "queue_size": 0,
    "last_forwarded_at": "2026-09-21T12:30:11Z",
    "uptime_seconds": 3600.5
  }
  ```

### 3. Diagnostic Metrics
- **URL:** `GET /metrics`
- **Response:**
  ```json
  {
    "packets_received": 1420,
    "packets_queued": 1418,
    "packets_forwarded": 1418,
    "packets_failed": 0,
    "duplicate_packets": 2,
    "current_queue_size": 0
  }
  ```

---

## Running the Gateway

```bash
cd iot/gateway/edge_agent

# Run with Uvicorn (Host: 0.0.0.0, Port: 9000)
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

---

## Running Gateway Tests

```bash
cd iot/gateway/edge_agent
../../../backend/api/venv/bin/pytest tests/ -v
```

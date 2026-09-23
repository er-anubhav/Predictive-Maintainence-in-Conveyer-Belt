# Intelligent Conveyor Belt Health & Predictive Maintenance
**Smart India Hackathon (SIH) 2026 — Problem Statement: 26008**
**Domain: Iron Ore Mining**

---

## 1. Project Overview

In harsh industrial environments like iron ore mining, conveyor belts are mission-critical bulk material handling assets. Unexpected conveyor belt tears, joint/splice failures, idler roller seizures, and tracking misalignments result in catastrophic operational downtime, safety hazards, and multimillion-rupee production losses.

This project delivers an end-to-end, low-cost distributed monitoring and predictive maintenance system engineered specifically for iron ore mining conveyor systems. By coupling rugged distributed sensor nodes, edge vibration and acoustic analysis, an offline-resilient store-and-forward edge gateway, and a centralized monitoring platform, it enables early detection of mechanical anomalies before catastrophic failure occurs.

---

## 2. SIH 26008 Context & Problem Scope

- **Problem Statement ID:** 26008
- **Target Domain:** Iron Ore Mining & Heavy Bulk Material Handling
- **Core Challenge:** Remote mine sites and extended conveyor galleries suffer frequent WAN/cellular outages, harsh RF attenuation, and dust/moisture interference. Conventional maintenance relies either on infrequent manual visual inspections or expensive proprietary vibration monitoring systems that lose data during internet connectivity loss.
- **Solution Strategy:**
  1. **ESP32 Distributed Edge Nodes:** Low-cost nodes capturing tri-axial vibration, acoustic emission, surface temperature, speed, load, and tracking alignment with monotonic sequence numbering.
  2. **Edge Gateway Store-and-Forward Tier:** Local gateway with persistent SQLite buffering (`telemetry_queue`), preventing data loss during uplink dropouts and deduplicating retries via `(node_id, sequence)`.
  3. **Central Backend API:** FastAPI service with SQLAlchemy 2.x and PostgreSQL storage supporting both canonical edge packets and legacy formats.
  4. **Industrial Control Dashboard:** High-contrast, dense dark industrial web dashboard providing real-time edge gateway status, conveyor summary, sensor health metrics, time-series charts, and telemetry logs.

---

## 3. End-to-End Architecture (Milestone 2)

```
┌───────────────────────────────┐
│     ESP32 Sensor Node /       │
│     Telemetry Simulator       │
│ (Vib, Temp, Acoustic, Track)  │
└───────────────┬───────────────┘
                │ Local Network (HTTP POST /ingest)
                │ Schema v1.0 Contract + Monotonic Sequence
                ▼
┌───────────────────────────────┐
│       Edge Gateway Agent      │
│  (Port 9000, Python / FastAPI)│
│ ┌───────────────────────────┐ │
│ │ SQLite Persistent Buffer  │ │ <── Offline queue during WAN outage
│ │ (telemetry_queue table)   │ │ <── Unique (node_id, sequence) dedup
│ └─────────────┬─────────────┘ │
│ ┌─────────────▼─────────────┐ │
│ │ Resilient Forwarder Worker│ │ <── Background worker + exponential backoff
│ └─────────────┬─────────────┘ │
└───────────────┼───────────────┘
                │ Central Uplink (HTTP POST /api/v1/telemetry)
                ▼
┌───────────────────────────────┐
│      FastAPI Backend API      │
│          (Port 8000)          │
│  - Idempotent deduplication   │
│  - SQLAlchemy 2.x + Alembic   │
└───────────────┬───────────────┘
                │ Relational Persistence
                ▼
┌───────────────────────────────┐       HTTP GET / Proxy        ┌───────────────────────────────┐
│      PostgreSQL Database      │ <───────────────────────────  │     React Web Dashboard       │
│   (Port 5434 in Docker)       │                               │   (Port 5173, Vite + React)   │
│ - (sensor_node_id, sequence)  │                               │ - Edge Gateway Status Card    │
│   indexed for fast dedup      │                               │ - Conveyor & Sensor Telemetry │
└───────────────────────────────┘                               └───────────────────────────────┘
```

---

## 4. Why the Edge Gateway Exists

In iron ore mines, conveyor galleries extend for kilometers through underground tunnels, transfer towers, and remote overland terrain where internet and cellular connectivity is notoriously unreliable.

- **Offline Buffering:** If the central server or WAN drops for minutes or hours, the Edge Gateway buffers every packet into an ACID-compliant local SQLite database (`storage/buffer.db`).
- **Resilient Automatic Drain:** When connectivity is restored, a background forwarding worker automatically drains the queue to the central backend with zero packet loss.
- **Sequence Deduplication:** Wireless edge transmissions often produce retries. Both the Edge Gateway and Central Backend enforce duplicate detection using `(node_id, sequence)`, returning HTTP 202 `duplicate` without polluting databases or charts.
- **Edge Decoupling:** Sensor nodes only need to reach the local edge gateway over low-power WiFi/LAN, keeping battery usage minimal and firmware simple.

---

## 5. Canonical Telemetry Contract (v1.0)

Documented in detail in [`docs/telemetry-contract.md`](file:///home/anubhavtripathi/Documents/Projects/SIH26008/docs/telemetry-contract.md).

```json
{
  "schema_version": "1.0",
  "node_id": "NODE-001",
  "conveyor_id": "Conveyor-01",
  "timestamp": "2026-09-21T12:30:10Z",
  "sequence": 1001,
  "vibration": {
    "rms": 0.42,
    "peak": 1.21,
    "kurtosis": 3.8
  },
  "acoustic": {
    "rms": 0.31
  },
  "temperature": 42.7,
  "belt_speed": 2.8,
  "load": 71.5,
  "tracking_position": -1.8
}
```

---

## 6. Repository Structure

```
sih-26008/
├── backend/
│   └── api/
│       ├── alembic/              # Database migration scripts (001_initial, 002_add_telemetry_sequence)
│       ├── app/
│       │   ├── api/v1/           # Mines, Conveyors, Devices, Telemetry routes
│       │   ├── models/           # SQLAlchemy models with sequence & compound dedup index
│       │   ├── schemas/          # Canonical v1.0 & flat backward-compatible schemas
│       │   ├── services/         # Telemetry service with idempotent deduplication
│       │   └── main.py           # FastAPI server
│       ├── tests/test_api.py     # Backend unit & integration test suite
│       └── requirements.txt
├── iot/
│   ├── firmware/
│   │   └── esp32/                # ESP32 C++ Sensor Node Firmware (PlatformIO)
│   │       ├── platformio.ini    # PlatformIO build configuration
│   │       ├── src/
│   │       │   ├── config.h      # WiFi credentials, gateway endpoint, interval
│   │       │   ├── sensors/      # HAL interfaces for Vibration, Temp, Speed, Load, Tracking
│   │       │   ├── packet/       # Canonical v1.0 JSON packet serializer
│   │       │   └── main.cpp      # Setup and autonomous sampling/transmission loop
│   │       └── README.md
│   └── gateway/
│       ├── edge_agent/           # Edge Store-and-Forward Service (Port 9000)
│       │   ├── app/              # FastAPI buffer & forwarder application
│       │   ├── storage/          # SQLite database file (buffer.db)
│       │   └── tests/            # Gateway offline buffering & dedup unit tests
│       └── bridge/
│           └── esp32_hardware_bridge.py # Physical USB ESP32 serial bridge & telemetry runner
├── frontend/
│   └── dashboard/                # Industrial React Dashboard
│       ├── src/
│       │   ├── components/dashboard/
│       │   │   ├── GatewayStatusCard.tsx  # Live Edge Gateway buffer & uplink status
│       │   │   ├── ConveyorSummary.tsx
│       │   │   ├── SensorCards.tsx
│       │   │   ├── TelemetryCharts.tsx
│       │   │   └── TelemetryTable.tsx
│       │   ├── services/api.ts   # Backend & Gateway API clients
│       │   └── App.tsx           # Main monitoring shell with dual polling
│       └── vite.config.ts        # Vite proxy for /api and /api/gateway
├── models/
│   └── iforest/v0.3.1/           # Frozen Isolation Forest model artifact & metadata
├── config/
│   └── poc_thresholds.yaml       # Physical sensor limits and alert thresholds
├── docs/
│   ├── telemetry-contract.md     # Canonical telemetry contract v1.0 specification
│   └── real_hardware_integration_status.md # Hardware sensor inventory and specs
├── archive/                      # Historical ML research, datasets, notebooks & logs
├── docker-compose.yml            # PostgreSQL container (Port 5434)
├── run_demo.sh                   # Unified one-command system runner
└── README.md
```

---

## 7. Quick Start & Execution Instructions

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- Docker & Docker Compose

### 1. Start PostgreSQL Database
```bash
docker compose up -d
```
*(Runs PostgreSQL 16 on port `5434`).*

### 2. Start FastAPI Central Backend (Port 8000)
```bash
cd backend/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Health Check: `http://localhost:8000/health`
- Swagger Docs: `http://localhost:8000/docs`

### 3. Start Edge Gateway Agent (Port 9000)
In a separate terminal:
```bash
cd iot/gateway/edge_agent
# Uses the same virtualenv or its own
../../../backend/api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000
```
- Gateway Health: `http://localhost:9000/health`
- Gateway Metrics: `http://localhost:9000/metrics`

### 4. Start React Industrial Dashboard (Port 5173)
In another terminal:
```bash
cd frontend/dashboard
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. The **EDGE GATEWAY STORE-AND-FORWARD TIER** card at the top will indicate gateway health, buffer queue size, forwarded packet counts, uplink status, and registered sensor nodes.

### 5. Stream Real-Time Telemetry via Simulator
In a separate terminal:
```bash
# Transmit through Edge Gateway (Port 9000)
python simulator/generator.py --transport gateway --scenario normal --interval 2.0

# Or simulate tracking misalignment through Gateway
python simulator/generator.py --transport gateway --scenario misalignment --interval 1.5

# Or direct to Backend (Milestone 1 backward compatibility)
python simulator/generator.py --transport direct --scenario normal
```

---

## 8. Verification & Automated Testing

### Backend Unit Tests (FastAPI + PostgreSQL Schema + Deduplication)
```bash
cd backend/api
pytest tests/ -v
```

### Edge Gateway Unit Tests (SQLite Buffer + Deduplication + Outage Drain)
```bash
cd iot/gateway/edge_agent
../../../backend/api/venv/bin/pytest tests/ -v
```

### Full Offline Resilience & Outage Recovery Test
Simulates a live central backend outage, sends packets to the gateway, proves SQLite queue accumulation, restores the backend, and validates automatic drain with zero data loss and no duplicates:
```bash
backend/api/venv/bin/python3 backend/api/tests/integration/test_offline_resilience.py
```

### Frontend Typecheck & Production Build
```bash
cd frontend/dashboard
npm run build
```

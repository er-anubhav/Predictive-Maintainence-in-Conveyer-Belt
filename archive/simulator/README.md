# Conveyor Belt Health Telemetry Simulator

## Overview

The simulator reproduces multi-modal edge sensor telemetry emitted by industrial IoT monitoring nodes along mining conveyor systems.

In Milestone 2, it supports **dual transport modes**:
1. **Direct Mode (`--transport direct`)**: Directly targets the central FastAPI backend (`POST /api/v1/telemetry` on port 8000).
2. **Gateway Mode (`--transport gateway`)**: Acts as a virtual ESP32 sensor node, formatting payloads according to the **Canonical Telemetry Contract (v1.0)** with monotonic sequence numbers and transmitting to the Edge Gateway (`POST /ingest` on port 9000).

---

## Simulated Fault Scenarios

### 1. `normal`
- **Description:** Standard steady-state bulk iron ore transport.
- **Characteristics:** Stable vibration RMS (~0.37 – 0.43 g), Gaussian kurtosis (~3.0), thermal equilibrium (~41 – 43 °C).

### 2. `misalignment`
- **Description:** Conveyor belt lateral edge drift inducing roller flange rubbing and friction.
- **Characteristics:** Tracking position drifts from 0 mm to $>16\text{ mm}$, acoustic emission RMS increases steeply, modest thermal heating.

### 3. `mechanical_abnormality`
- **Description:** Bearing raceway pitting, roller seizure, and splice fastener failure.
- **Characteristics:** Severe impulsive vibration with kurtosis spikes ($6.0 \dots 8.0+$), peak acceleration shocks, acoustic friction, and thermal runaway ($42^\circ\text{C} \to 75^\circ\text{C}+$).

---

## Usage & CLI Commands

```bash
# 1. Stream via Edge Gateway (Port 9000) using Canonical v1.0 Schema
python simulator/generator.py --transport gateway --scenario normal --interval 2.0

# 2. Simulate Conveyor Belt Misalignment via Edge Gateway
python simulator/generator.py --transport gateway --scenario misalignment --interval 2.0

# 3. Simulate Mechanical Abnormality via Edge Gateway
python simulator/generator.py --transport gateway --scenario mechanical_abnormality --interval 1.5

# 4. Stream Directly to Central FastAPI Backend (Port 8000)
python simulator/generator.py --transport direct --scenario normal --interval 2.0

# 5. Transmit a fixed count of packets with a specific initial sequence number
python simulator/generator.py --transport gateway --node-id NODE-002 --start-sequence 5000 --count 25
```

### CLI Parameters

| Flag | Default | Description |
|---|---|---|
| `--transport` | `direct` | Ingestion target: `direct` (FastAPI :8000) or `gateway` (Edge Gateway :9000) |
| `--scenario` | `normal` | Operational scenario (`normal`, `misalignment`, `mechanical_abnormality`) |
| `--node-id`, `--sensor-node-id` | `NODE-001` | Target sensor node code registered in the database |
| `--conveyor-id` | `Conveyor-01` | Associated conveyor asset identifier |
| `--start-sequence` | `1001` | Initial monotonic sequence number for duplicate detection |
| `--interval` | `2.0` | Emission cadence in seconds |
| `--api-url` | Automatic | Custom destination URL override |
| `--count` | `None` (Continuous) | Number of packets to send before terminating |

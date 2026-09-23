# Canonical Telemetry Contract — SIH 26008

## Schema Specification (`schema_version: "1.0"`)

This document defines the canonical JSON telemetry contract shared across the entire SIH 26008 ecosystem:
- **ESP32 Edge Sensor Nodes** (`firmware/esp32/`)
- **Edge Gateway Agent** (`gateway/edge_agent/`)
- **Central FastAPI Backend** (`backend/api/`)
- **Diagnostic Telemetry Simulator** (`simulator/`)

---

## 1. Canonical JSON Structure

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
    "kurtosis": 3.8,
    "crest_factor": 2.88,
    "dominant_frequency_hz": 20.0,
    "spectral_energy": 0.1764
  },

  "acoustic": {
    "rms": 0.31
  },

  "temperature": 42.7,
  "belt_speed": 2.8,
  "load": 71.5,
  "tracking_position": -1.8,
  "processing_version": "0.1",
  "feature_version": "0.1"
}
```

---

## 2. Field Definitions & Constraints

### 2.1 Envelope Fields (Required)

| Field | Type | Description | Example |
|---|---|---|---|
| `schema_version` | String | Semantic contract version. Must be `"1.0"`. | `"1.0"` |
| `node_id` | String | Unique hardware code of the edge sensor unit. | `"NODE-001"` |
| `conveyor_id` | String / Integer | Identifier or name of the monitored conveyor belt system. | `"Conveyor-01"` |
| `timestamp` | String | ISO 8601 UTC timestamp of sample acquisition. Format: `YYYY-MM-DDTHH:MM:SSZ`. | `"2026-09-21T12:30:10Z"` |
| `sequence` | Integer | Monotonically increasing packet counter per `node_id` ($1 \le \text{seq} \le 2^{63}-1$). | `1001` |

### 2.2 Modular Sensor Payload (Optional / Dependent on Attached Hardware)

| Block / Field | Type | Unit | Range | Description |
|---|---|---|---|---|
| `vibration.rms` | Float | $\text{g}$ / $\text{mm/s}$ | $0.0 \dots 50.0$ | Tri-axial velocity / acceleration root-mean-square. |
| `vibration.peak` | Float | $\text{g}$ | $0.0 \dots 100.0$ | Maximum absolute peak acceleration in sampling window. |
| `vibration.kurtosis`| Float | Dimensionless | $1.0 \dots 50.0$ | Statistical kurtosis ($\mu_4 / \sigma^4$) indicating mechanical shock impacts. Gaussian baseline $\sim 3.0$. |
| `vibration.crest_factor` | Float | Dimensionless | $0.0 \dots 50.0$ | Ratio of peak acceleration to RMS ($\text{Peak} / \text{RMS}$). Sensitive to early impulsive bearing/splice faults. |
| `vibration.dominant_frequency_hz` | Float | $\text{Hz}$ | $0.0 \dots 500.0$ | Peak spectral frequency from real FFT (excluding DC component). |
| `vibration.spectral_energy` | Float | $\text{g}^2$ | $0.0 \dots 10000.0$ | Total power spectral density energy across all frequency bins ($\sum |X_k|^2 / N$). |
| `acoustic.rms` | Float | Volts ($\text{V}$) | $0.0 \dots 5.0$ | High-frequency acoustic emission RMS (20 kHz – 100 kHz) indicating edge rubbing or bearing friction. |
| `temperature` | Float | Celsius ($^\circ\text{C}$) | $-20.0 \dots 150.0$ | Bearing shell or conveyor belt surface temperature. |
| `belt_speed` | Float | $\text{m/s}$ | $0.0 \dots 15.0$ | Linear surface velocity of the conveyor belt. |
| `load` | Float | Percentage ($\%$) | $0.0 \dots 100.0$ | Conveyor belt material loading percentage (weightometer). |
| `tracking_position` | Float | Millimeters ($\text{mm}$) | $-100.0 \dots +100.0$ | Lateral belt edge deviation from center axis. $0 = \text{centered}$, $(-)$ = Left, $(+)$ = Right. |
| `processing_version` | String | Metadata | e.g. `"0.1"` | Pipeline release version that produced derived features. |
| `feature_version` | String | Metadata | e.g. `"0.1"` | Feature schema version definition. |

---

## 2.3 Raw Edge Signal Contract (Pre-Aggregation)

Before features are aggregated into the canonical telemetry frame, edge nodes capture high-rate time series. High-frequency raw sensor arrays are **processed locally on edge gateways/nodes and never continuously streamed to the cloud/PostgreSQL database**.

### Raw Vibration Representation
- **Channels**: Synchronized 3-Axis: `x` (longitudinal), `y` (transverse/lateral), `z` (vertical/normal).
- **Sampling Frequency ($f_s$)**: Standard $1000\text{ Hz}$ ($1\text{ ms}$ interval) for vibration; $2000\text{ Hz}$ for acoustic emission.
- **Window Length ($N$)**: 1024 samples per window ($\approx 1.024\text{ seconds}$ at $1000\text{ Hz}$).
- **Overlap**: 50% sliding overlap (512 step shift) ensuring transient captures are not truncated at window boundaries.
- **Windowing Function**: Hann or Hamming window applied prior to FFT computations to mitigate spectral leakage.
- **Filtering**: 4th order zero-phase Butterworth bandpass filter ($2.0\text{ Hz} - 450.0\text{ Hz}$) with linear detrending and DC removal.

### Raw Signal Storage Schema (`datasets/*.npz`)
Raw development and benchmark datasets are archived locally in compressed NumPy `.npz` container format:
```python
{
    "samples_x": np.ndarray[float64],       # Shape (N,)
    "samples_y": np.ndarray[float64],       # Shape (N,)
    "samples_z": np.ndarray[float64],       # Shape (N,)
    "metadata": {
        "node_id": "NODE-001",
        "conveyor_id": "Conveyor-01",
        "sample_rate_hz": 1000.0,
        "scenario": "mechanical_impulse",
        "timestamp_start": "2026-09-21T12:30:10Z",
        "processing_version": "0.1"
    }
}
```

---

## 3. Sequence Number & Deduplication Semantics

1. **Logical Packet Identity**:
   Every packet is uniquely identified by the tuple:
   $$\text{Packet ID} = (\text{node\_id}, \text{sequence})$$
2. **Monotonic Progression**:
   Sensor nodes increment `sequence` by $+1$ for each generated telemetry frame.
3. **Gateway Deduplication**:
   If an edge node retransmits a packet due to an unacknowledged WiFi timeout, the Edge Gateway checks its local SQLite buffer. If $(\text{node\_id}, \text{sequence})$ already exists:
   - The Gateway accepts the packet idempotently (HTTP 200/202).
   - The duplicate packet counter (`duplicate_packets`) is incremented.
   - The duplicate is **not** duplicated in the local SQLite queue.
4. **Backend Deduplication**:
   When the Gateway forwards packets to the FastAPI backend, the backend verifies $(\text{sensor\_node\_id}, \text{sequence})$ against PostgreSQL to prevent duplicate database rows.

---

## 4. Null & Missing Field Handling

- Nodes without specific sensors (e.g., an idler station with only vibration and temperature) omit missing blocks entirely or provide `null`.
- Ingestion services must treat all sensor metric fields as nullable/optional, only requiring the envelope fields (`node_id`, `conveyor_id`, `timestamp`, `sequence`).
- When stored in PostgreSQL, omitted metrics are stored as `NULL` or mapped to default sensor readings if required.

---

## 5. Forward Compatibility

To support future SIH phases (such as raw FFT frequency bins, multi-channel acoustic spectra, or GPS coordinates for mobile overland hoppers):
- Gateway and backend parsers **must ignore extra unknown fields** rather than rejecting the payload.
- Schema version increments:
  - **Minor increments** (`1.1`, `1.2`): Add optional fields; fully backward-compatible.
  - **Major increments** (`2.0`): Breaking alterations to envelope or timestamp formats.

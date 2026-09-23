# SIH 26008 — POC Model Integration & Verification Status

**Date**: 2026-09-22
**Evaluator**: System Architecture & ML Verification Gate
**Integration Target**: SIH 26008 Intelligent Conveyor Belt Predictive Maintenance POC

---

## 1. Provenance & Artifact Verification

```text
MODEL ARTIFACT FOUND:          PASS
SHA-256 VERIFIED:              PASS
V0.5 BASE MODEL MATCH:         PASS
V0.6.1 BASE MODEL MATCH:       PASS
```

### Exact Artifact Details:
- **Base Model Location**: `models/iforest/v0.3.1/model.joblib`
- **File Size**: 2,149,785 bytes
- **SHA-256 Checksum**: `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19`
- **Equivalence Check**:
  $$\text{SHA256}(\text{v0.3.1/model.joblib}) \equiv \text{SHA256}(\text{v0.5/model.joblib}) \equiv \text{SHA256}(\text{v0.6.1/model.joblib})$$
- **Formal Conclusion**: **`v0.5` MODEL = COPIED `v0.3.1` MODEL**; **`v0.6.1` MODEL = COPIED `v0.3.1` MODEL**. Neither layer retrained or altered the underlying decision trees.

---

## 2. Live Inference & Component Verification

```text
INFERENCE WRAPPER:             PASS
REAL DATA INFERENCE:           PASS
FASTAPI INTEGRATION:           PASS
SIMULATOR INTEGRATION:         PASS
DATABASE PERSISTENCE:          PASS
DASHBOARD TRANSPARENCY:        PASS
END-TO-END VERIFICATION:       PASS
```

### Component Status:
1. **Inference Module** (`backend/api/app/ml/vibration_inference.py`):
   - Implements `process_vibration_window` and `process_features`.
   - Uses the exact Standard 6 features: `rms`, `peak`, `crest_factor`, `kurtosis`, `dominant_frequency_hz`, `spectral_energy`.
   - Applies frozen `normalization.json` scaling.
   - Applies `v0.5` local run-in commissioning (20% window envelope estimation).
   - Computes robust per-feature deviations and dual-rate persistence (`3-of-5` for Warning, `5-of-9` for High-Severity).

2. **Backend API Telemetry Endpoint** (`/api/v1/telemetry`):
   - Telemetry submission executes the verified ML pipeline on real or extracted features.
   - Automatically stores all inference outputs in PostgreSQL (`telemetries` table via Alembic migration `004_add_ml_inference_fields`).
   - Telemetry response and history queries expose:
     - `model_version`: `"IF-v0.3.1"`
     - `commissioning_version`: `"v0.5"`
     - `decision_layer_version`: `"v0.6.1"`
     - `anomaly_score`, `composite_z_deviation`, `persistence_3of5`, `persistence_5of9`, `alert_state`, `data_quality`.

3. **Simulator Scenarios & Dynamic Transitions**:
   - `NORMAL`: Anomaly score $\approx 0.42$, Composite $z < 2.0\sigma$, State = `NORMAL`.
   - `MISALIGNMENT`: Anomaly score climbs to $0.65$, Composite $z \approx 3.2\sigma$, State = `WATCH`.
   - `MECHANICAL_ABNORMALITY`: Anomaly score reaches $0.82$, Composite $z > 7.0\sigma$, triggers `3-of-5` (`WARNING`) and escalates to `5-of-9` (`HIGH_SEVERITY`).
   - Zero hardcoded scenario `if/else` checks in the backend; all alert states are calculated dynamically by the model.

4. **Dashboard Transparency** (`frontend/dashboard`):
   - Added `MLEngineCard.tsx` displaying:
     - Model: `IF-v0.3.1` (Isolation Forest, 200 trees)
     - Commissioning: `v0.5` (20% Local Run-In Envelope)
     - Decision Layer: `v0.6.1` (Dual-Rate Persistence)
     - Real-time Anomaly Score, Composite Z-deviation, and Persistence Status.
     - Clear label: *"Vibration Anomaly Detection — Research Prototype — Production Validation Pending"*.
   - Production bundle compiled cleanly (`tsc -b && vite build` succeeded).

---

## 3. Final Model & Pipeline Declaration

```text
FINAL MODEL:
IF-v0.3.1

FINAL POC PIPELINE:
IF-v0.3.1
+
v0.5 commissioning
+
v0.6.1 evidence/persistence
```

### Readiness Gate:
The ML model trained during the benchmark research is the exact model currently executing live in the POC backend. The system is certified ready for downstream field and camera integration.

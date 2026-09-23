# SIH 26008 — POC Integration Model Card: IF-v0.3.1

**Model Name**: `IF-v0.3.1` Anomaly Detection Pipeline
**Date**: 2026-09-22
**Integration Target**: SIH 26008 Intelligent Conveyor Belt Predictive Maintenance POC
**Status**: RESEARCH EXPERIMENT & CANDIDATE PROTOTYPE (NOT PRODUCTION CERTIFIED)

---

## 1. Model Summary & Architecture

- **Model Type**: Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Last Trained Base Model**: `IF-v0.3.1` (Trained on 2026-09-22 14:04:59 UTC)
- **Parameters**:
  - `n_estimators`: 200
  - `contamination`: 0.03
  - `random_state`: 42
  - `max_samples`: "auto"
- **Artifact Path**: `models/iforest/v0.3.1/model.joblib`
- **SHA-256 Checksum**: `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19`

---

## 2. Training Data & Representation

- **Training Pool**: 13,170 windows
  - **CWRU Normal**: `97.mat`, `98.mat` (12 kHz drive-end healthy baseline)
  - **Paderborn Normal**: K001 healthy runs 1 through 50 (64 kHz piezoelectric accelerometer)
- **Core Standard 6 Features**:
  1. `rms`: Root-mean-square acceleration
  2. `peak`: Peak absolute acceleration amplitude
  3. `crest_factor`: Peak-to-RMS ratio
  4. `kurtosis`: 4th standardized moment (impulsiveness)
  5. `dominant_frequency_hz`: Peak frequency in FFT spectrum
  6. `spectral_energy`: Total energy computed across the FFT spectrum
- **Normalization**: Z-score standardized using frozen `normalization.json` parameters derived strictly from the training pool.

---

## 3. Recorded Evaluation Metrics (Benchmark Truth)

> [!IMPORTANT]
> **This is NOT an "accuracy" model.** Anomaly detection on uncalibrated cross-domain streams experiences domain shifts. The verified historical benchmark metrics are:

### A. IF-v0.3.1 Benchmark Evaluation
- **CWRU Test Set**:
  - `F1 Score`: **0.5448**
  - `Healthy FPR`: **0.3911** (39.11% false alarm rate on held-out CWRU healthy runs)
- **Paderborn Test Set**:
  - `F1 Score`: **0.7180**
  - `Healthy FPR`: **0.0493** (4.93% false alarm rate on held-out Paderborn K001 runs)

### B. Conveyor Claim Boundary
> **CRITICAL SCIENTIFIC NOTATION**:
> These benchmark metrics were evaluated on **laboratory bearing test-stands** (CWRU and Paderborn).
> **These are NOT production conveyor metrics.** They do NOT establish detection performance for belt splice tearing, idler roll seizure, dynamic material loading, or overland chute blockages.

---

## 4. Layer Decoupling & Component Roles

The live POC pipeline integrates three decoupled layers:

| Layer Component | Implementation Version | Exact Role in POC | Retrained? |
| :--- | :--- | :--- | :--- |
| **Base Anomaly Estimator** | `IF-v0.3.1` | Generates standardized feature space and tree-partition isolation scores. | **No** (Frozen) |
| **Local Commissioning Envelope** | `v0.5` | Calculates machine-specific robust median and IQR during first 20% run-in to eliminate cross-machine sensor offsets. | **No** (Protocol) |
| **Temporal Persistence & Evidence** | `v0.6.1` | Dual-rate sliding filter (3-of-5 for Warning, 5-of-9 for High-Severity) and structured feature deviation extraction. | **No** (Logic) |

> **Note**: Neither `v0.5` nor `v0.6.1` represent newly trained Isolation Forests. They are commissioning and temporal inference layers that operate on top of the frozen `IF-v0.3.1` base estimator.

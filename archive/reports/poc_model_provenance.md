# SIH 26008 — POC Model Provenance & Verification Report

**Verification Date**: 2026-09-22
**Evaluator**: System Architecture & ML Verification Gate
**Integration Target**: SIH 26008 Intelligent Conveyor Belt Predictive Maintenance POC

---

## 1. Exact Model Artifact Locations

The exact model files have been located in the repository and cross-verified against Google Colab Drive (`/content/drive/MyDrive/SIH26008_ML/`):

- **Primary Base Model Artifact**: `models/iforest/v0.3.1/model.joblib`
- **Associated Normalization Parameters**: `models/iforest/v0.3.1/normalization.json`
- **Associated Threshold Configuration**: `models/iforest/v0.3.1/threshold_config.json`
- **Associated Metadata & Specification**: `models/iforest/v0.3.1/metadata.json`, `models/iforest/v0.3.1/model_card.md`
- **Local Commissioning Configuration**: `models/iforest/v0.5/model_card.md`
- **Persistence & Evidence Configuration**: `models/iforest/v0.6.1/v0.6.1_config.json`, `models/iforest/v0.6.1/model_card.md`

---

## 2. SHA-256 Hash Verification & Base Model Equivalence

Bit-level SHA-256 hashes were calculated directly on the filesystem:

| Artifact Path | File Size | SHA-256 Checksum | Base Model Identity |
| :--- | :--- | :--- | :--- |
| `models/iforest/v0.3.1/model.joblib` | 2,149,785 bytes | `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19` | **Original Trained Base Representation** |
| `models/iforest/v0.5/model.joblib` | 2,149,785 bytes | `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19` | **Exact Replica of v0.3.1** |
| `models/iforest/v0.6.1/model.joblib` | 2,149,785 bytes | `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19` | **Exact Replica of v0.3.1** |

### Equivalence Finding:
$$\text{SHA256}(\text{v0.3.1/model.joblib}) \equiv \text{SHA256}(\text{v0.5/model.joblib}) \equiv \text{SHA256}(\text{v0.6.1/model.joblib})$$

> **OFFICIAL PROVENANCE STATEMENT**:
> **`v0.5` MODEL = COPIED `v0.3.1` MODEL**
> **`v0.6.1` MODEL = COPIED `v0.3.1` MODEL**
>
> Neither `v0.5` nor `v0.6.1` retrained the Isolation Forest or modified its decision trees. They are commissioning and temporal persistence decision layers that wrap the immutable `IF-v0.3.1` base estimator.

---

## 3. Training & Architectural Details

- **Model Architecture**: Scikit-Learn `IsolationForest`
  - `n_estimators`: 200
  - `contamination`: 0.03
  - `random_state`: 42
  - `max_samples`: "auto"
- **Last Trained Base Version**: `IF-v0.3.1` (Trained 2026-09-22 14:04:59 UTC)
- **Training Samples**: 13,170 windows
- **Training Data**:
  - CWRU Normal: `97.mat`, `98.mat`
  - Paderborn: K001 healthy runs 1 to 50
- **Feature Set (Standard 6 Features)**:
  1. `rms` (Root Mean Square acceleration)
  2. `peak` (Peak absolute acceleration)
  3. `crest_factor` (Ratio of peak to RMS)
  4. `kurtosis` (4th statistical moment / impulsiveness)
  5. `dominant_frequency_hz` (Peak FFT spectral frequency)
  6. `spectral_energy` (Total normalized FFT energy)

---

## 4. Normalization & Decision Configurations

### A. Normalization (`models/iforest/v0.3.1/normalization.json`)
Features are standardized using Z-score transforms with mean and standard deviation computed strictly over the training pool:
- `rms`: Mean = $0.21262$, Std = $0.11639$
- `peak`: Mean = $0.92793$, Std = $0.51669$
- `crest_factor`: Mean = $4.39544$, Std = $0.80075$
- `kurtosis`: Mean = $4.99844$, Std = $1.71292$
- `dominant_frequency_hz`: Mean = $769.43566$, Std = $1275.06665$
- `spectral_energy`: Mean = $62.03460$, Std = $101.88781$

### B. Decision Logic (`models/iforest/v0.3.1/threshold_config.json` + `v0.6.1_config.json`)
- Decision score min-max calibration span: $s_{\min} = 0.35322$, $s_{\max} = 0.69405$
- Anomaly Threshold: $0.59$ (instantaneous raw score boundary)
- Statistical Deviation Boundary: $z \ge 3.0$
- Temporal Persistence:
  - **3-of-5 Rule**: Warning / Maintenance Alert Candidate
  - **5-of-9 Rule**: High-Severity Alert Candidate

---

## 5. Final POC Model Selection

The production-candidate model for the SIH 26008 POC backend is:
- **Base Anomaly Estimator**: `IF-v0.3.1` (`models/iforest/v0.3.1/model.joblib`)
- **Local Calibration Layer**: `v0.5` Machine-Agnostic Run-In Baseline
- **Persistence & Evidence Layer**: `v0.6.1` Dual-Rate Persistence Filter

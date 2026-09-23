# SIH 26008 — Multimodal Evidence Fusion & Camera Architecture

**Project**: Smart India Hackathon (SIH 26008) — Predictive Maintenance for Mining Conveyor Belts  
**Architecture Status**: POC Multimodal Evidence Fusion Complete  
**Vibration Modality**: **FROZEN** (`IF-v0.3.1` + `v0.5` + `v0.6.1`)  

---

## 1. High-Level Architecture

```
                                  CONVEYOR BELT POC
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   │                      │                      │
             SENSOR TELEMETRY       CAMERA WORKER             CONTEXT
                   │                      │                      │
                   ▼                      ▼                      ▼
           ┌──────────────┐       ┌──────────────┐          Speed / Load
           │ Vibration    │       │ Visual       │        Operating State
           │ IF-v0.3.1    │       │ Evidence     │
           │ + v0.5       │       │ Pipeline     │
           │ + v0.6.1     │       └──────────────┘
           └──────────────┘               │
                   │                      │
                   ├── Temperature ───────┤
                   ├── Tracking ──────────┤
                   └── Speed / Load ──────┤
                                          ▼
                               EVIDENCE FUSION ENGINE
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                       NORMAL           WATCH           WARNING
                                                           │
                                                           ▼
                                                    HIGH_SEVERITY
                                          │
                                          ▼
                               WHY? Explainable Reasons
                                          │
                             ┌────────────┴────────────┐
                             ▼                         ▼
                        PostgreSQL               React Dashboard
```

---

## 2. Modality Specifications

### 2.1 Vibration Modality (FROZEN)
- **Model Artifact**: `models/iforest/v0.3.1/model.joblib`
- **SHA-256**: `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19`
- **Features**: Standard 6 (RMS, Peak, Crest Factor, Kurtosis, Dominant Frequency, Spectral Energy)
- **Local Commissioning**: `v0.5` (First 20% healthy run-in window establishes median and IQR)
- **Persistence Decision Layer**: `v0.6.1` (Instantaneous $\rightarrow$ 3-of-5 Warning $\rightarrow$ 5-of-9 High Severity)
- **Status**: Immutably frozen. Never retrained or modified during multimodal integration.

### 2.2 Thermal Intelligence
- **Implementation**: `backend/api/app/ml/thermal_intelligence.py`
- **Inputs**: Bearing surface / idler shell temperature (°C)
- **Detection Method**: Deterministic thresholding + rate-of-rise tracking (°C/min) + persistence window.
- **Wording**: Evidence-based ("temperature rise is elevated relative to configured POC threshold").

### 2.3 Operating Context Engine
- **Implementation**: `backend/api/app/ml/operating_context.py`
- **Inputs**: Belt speed ($m/s$), Load percentage ($0-100\%$), speed trend.
- **States**: `STOPPED`, `STARTING`, `IDLE`, `EMPTY_RUNNING`, `LOADED_RUNNING`, `STOPPING`.
- **Function**: Suppresses false mechanical alarms during normal dynamic transients (startup / shutdown).

### 2.4 Tracking & Alignment Intelligence
- **Implementation**: `backend/api/app/ml/tracking_intelligence.py`
- **Inputs**: Lateral tracking deviation ($\text{mm}$).
- **Detection Method**: Edge displacement vs configurable POC thresholds ($\pm 5 \text{ mm}$ normal, $\pm 12 \text{ mm}$ watch, $\pm 20 \text{ mm}$ warning).

### 2.5 Optical Camera Subsystem & Decoupled Worker
- **Implementation**: `backend/api/app/ml/camera_service.py` & `backend/api/app/workers/camera_worker.py`
- **Architecture**: Decoupled asynchronous worker. Ingesting telemetry does **NOT** synchronously trigger camera capture.
- **Capabilities**:
  1. Belt ROI extraction and segmentation
  2. Edge geometry and lateral tracking deviation measurement
  3. Surface anomaly extraction (tear / rip / splice defect gradient clusters)
  4. External image storage (`data/evidence/camera/`) serving JPEG images via HTTP
  5. Mandatory `DEMO / SIMULATED` watermark on synthetic demonstration frames.

---

## 3. Explainable Rule-Based Fusion Engine

- **Implementation**: `backend/api/app/ml/fusion_engine.py`
- **Philosophy**: No black-box secondary neural network. Fusion is transparent and auditable.
- **Heuristic Severity**: $0.0 - 1.0$ rule-derived indicator. Explicitly **NOT** a failure probability or safety rating.
- **Core Rules**:
  1. *Rule 1 (Multimodal Mechanical)*: Persistent vibration anomaly + visual belt abnormality $\rightarrow$ `HIGH_SEVERITY`
  2. *Rule 2 (Thermal + Vibration)*: Rapid temperature rise + elevated vibration $\rightarrow$ `HIGH_SEVERITY`
  3. *Rule 3 (Tracking + Vibration)*: Lateral drift + vibration abnormality during loaded run $\rightarrow$ `WARNING`
  4. *Rule 4 (Vibration Persistence)*: Isolated 3-of-5 $\rightarrow$ `WARNING`; isolated 5-of-9 $\rightarrow$ `HIGH_SEVERITY`
  5. *Rule 5 (Startup Transient)*: Vibration spike during `STARTING`/`STOPPING` operating state $\rightarrow$ `WATCH`
  6. *Rule 6 (Nominal)*: All sensors within configured boundaries $\rightarrow$ `NORMAL`

---

## 4. Database & Storage Architecture

- **PostgreSQL (`telemetries` table)**:
  - Extended with: `operating_state`, `multimodal_state`, `fusion_reasons`, `camera_status`, `camera_frame_ref`, `camera_is_simulated`.
  - Storing massive Base64 blobs in the database is strictly prohibited.
- **External Image Store**:
  - `data/evidence/camera/<frame_id>.jpg`
  - Served via endpoint: `GET /api/v1/multimodal/camera/evidence/{frame_id}`.

# SIH 26008 — Project Archive

This directory stores historical, offline research, intermediate artifacts, and experimental assets to keep the project root clean, structured, and focused strictly on the production runtime codebase.

---

## Directory Inventory

| Item | Original Purpose | Reason for Archival |
|---|---|---|
| **`SIH26008_ML/`** | Google Colab Jupyter Notebooks (01 to 08) | Used during initial model training & dataset exploration on Google Colab. The final model is frozen in `models/iforest/v0.3.1/model.joblib`. |
| **`ml/`** | Offline ML training, feature extraction, and benchmark scripts | Offline research pipelines for bearing fault classification. Central production inference is served via `backend/api/app/ml/vibration_inference.py`. |
| **`datasets/`** | Raw & processed CWRU bearing dataset samples | Historical experimental data. Production system operates on live real hardware telemetry and edge sensor ingestion. |
| **`reports/`** | ML evaluation reports, model cards, artifact hashes | Research verification documents produced during Milestone ML modeling phases. |
| **`scripts/`** | Offline Colab dispatch, model downloaders, and research runners | 27 historical automation scripts used during experimental phases. |
| **`simulator/`** | Early standalone python simulator scripts | Early prototyping scripts, superseded by `iot/gateway/bridge/esp32_hardware_bridge.py` and the backend multimodal engine. |
| **`logs/`** | System runtime logs (`backend.log`, `gateway.log`, etc.) | Kept isolated to avoid cluttering the repository root during demo execution. |
| **`ChatGPT Image ...`** | Reference UI & sensor layout mockups | Concept visual reference from initial ideation. |
| **`real_hardware_integration_status.md`** | Hardware audit and sensor inventory | Preserved reference (primary documentation maintained in `docs/`). |

---

## Active Root Structure

The root directory maintains only the active production tiers:
- **`backend/`**: FastAPI high-performance API server & Multimodal Fusion Engine (with `tests/integration/`).
- **`frontend/`**: React 19 + TypeScript + Vite Neo-Brutalist real-time dashboard.
- **`iot/`**: Unified IoT tier containing:
  - **`firmware/`**: ESP32 C++ Hardware Abstraction Layer for physical industrial sensors.
  - **`gateway/`**: Edge Agent store-and-forward service with offline resilience buffer (`edge_agent/`) and physical bridge (`bridge/`).
- **`config/`**: POC demonstration thresholds and physical parameters (`poc_thresholds.yaml`).
- **`models/`**: Production Isolation Forest vibration model (`models/iforest/v0.3.1/model.joblib`).
- **`docs/`**: Production architecture and system documentation.
- **`docker-compose.yml`**: Central PostgreSQL container stack.
- **`run_demo.sh`**: Unified one-command system runner.

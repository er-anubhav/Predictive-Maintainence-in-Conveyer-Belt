# SIH 26008 — Final SIH Presentation & Demonstration Script

**Project Title:** Smart Multi-Modal IoT Edge Sensing & Explainable Predictive Maintenance for Conveyor Belts  
**Target Duration:** ~5 Minutes  
**Audience:** SIH Evaluation Panel / Industry Judges  

---

## 1. System Architecture Overview (0:00 – 0:45)

1. **Highlight the Problem:**
   - Conveyor belt failures in mining cause millions in unscheduled downtime, catastrophic splice tears, and thermal fire risks.
   - Traditional threshold-only or single-sensor monitoring produces excessive false alarms or fails to give operators actionable explanations.

2. **The 3-Tier Solution:**
   - **Edge Sensor Tier:** ESP32 microcontrollers sampling multi-axial vibration, bearing temperature, drive pulley tachometer/RPM, and lateral tracking.
   - **Edge Gateway Tier:** Store-and-Forward persistent SQLite buffer guaranteeing zero packet loss during network dropouts in underground galleries.
   - **Multimodal Intelligence Tier:** Decoupled optical camera inspection running asynchronously alongside the **frozen IF-v0.3.1 machine learning vibration model**, v0.5 commissioning, and v0.6.1 persistence layer, synthesized by a transparent rule-based fusion engine into PostgreSQL and React.

---

## 2. Live Demo Step-by-Step Flow (0:45 – 4:15)

### Step 1: Start in REAL HARDWARE Mode (0:45 – 1:15)
- Open terminal and execute:
  ```bash
  ./run_demo.sh --real
  ```
- Point out the terminal banner:
  - `SYSTEM MODE: REAL HARDWARE`
  - `CAMERA STATUS: ONLINE (/dev/video0)`
  - `ESP32 STATUS: ONLINE`
  - `EDGE GATEWAY: ONLINE (Port 9000)`
  - `BACKEND STATUS: ONLINE (Port 8000)`
- Open the dashboard at `http://localhost:5173`.
- **Key Observation for Judges:**
  - System Mode badge reads **REAL HARDWARE** (Lime).
  - Health Tray shows all modalities: `ESP32: ONLINE`, `Vib: GOOD`, `Temp: GOOD`, `RPM: GOOD`, `Track: GOOD`, `Cam: ONLINE`.
  - Overall Condition is **NORMAL** (Emerald).
  - Each sensor card displays a transparent source pill: `REAL` for Vibration, Thermal, Speed/RPM, and Camera, and `SIMULATED` for lateral tracking.

### Step 2: Frozen Model & Commissioning Provenance (1:15 – 1:45)
- Open the **ML Engine Card** and **Multimodal Monitor Card**:
  - Show the frozen model tag: **IF-v0.3.1**.
  - Explain that the ML model is strictly frozen and cryptographically verified (`SHA-256: fb33d9...`).
  - Explain that machine-agnostic commissioning (**v0.5**) adapts to the machine's individual healthy envelope without requiring pre-labeled training data from that specific mine.
  - Explain dual persistence (**v0.6.1**): requiring 3-of-5 consecutive window confirmations filters out random mechanical shocks or rock drops from triggering false plant shutdowns.

### Step 3: Trigger Controlled Anomaly 1 — Vibration Transient (1:45 – 2:30)
- In the top-left Demo Control dropdown, select **Bearing Anomaly**.
- Watch the live telemetry feed:
  - Instantaneous vibration spikes to $\sim 1.85\text{ g}$.
  - Notice that on the 1st anomalous window, the state remains **WATCH** (not an immediate shutdown panic).
  - On 3 consecutive elevated windows, the 3-of-5 persistence rule triggers, promoting state to **WARNING**.
  - Show the **"WHY? Supporting Evidence"** box:
    - *"Persistent vibration anomaly detected by the frozen vibration monitoring pipeline (3-of-5 confirmation)."*

### Step 4: Introduce Supporting Modality — Multimodal Fusion (2:30 – 3:30)
- In Demo Control, select **Multimodal Event** (elevated vibration + rapid temperature rise + optical belt damage).
- Observe the immediate fusion response:
  - Multimodal state transitions from **WARNING** $\rightarrow$ **HIGH SEVERITY**.
  - The **Optical Evidence** panel captures the visual tear in the belt splice.
  - Show the **"WHY? Supporting Evidence"** explainability list:
    - *"Persistent vibration anomaly co-occurs with visual belt-surface abnormality."*
    - *"Rapid temperature rise co-occurs with elevated vibration."*
  - **Crucial Distinction for Judges:**
    - Explain that severity is an explainable heuristic indicator (0.0 to 1.0) grounded in physical corroboration, NOT an opaque black-box probability.

### Step 5: Network Resiliency & Reconnect (3:30 – 4:00)
- Explain the Edge Gateway (Port 9000):
  - If central uplink or WiFi disconnects, the gateway buffers packets locally in SQLite.
  - When connection restores, packets sync seamlessly with zero data loss and sequence deduplication.
  - Even if the camera disconnects, the camera status safely degrades to `STALE` without crashing the conveyor monitoring pipeline.

### Step 6: Return to Normal Baseline (4:00 – 4:30)
- In Demo Control, select **Normal Operation** (or click Reset).
- Watch the system return to **NORMAL**.
- Show the PostgreSQL raw logs table with audit trail of sequences, timestamps, and model hashes.

---

## 3. Concluding Summary & Impact (4:30 – 5:00)

- **Zero Black-Box Guesswork:** Operators see exactly *which* sensors corroborating an alarm and *why*.
- **Hardware-Ready:** Plugs directly into industrial micro-controllers, local optical cameras, and plant SCADA.
- **Scientific Rigor:** Frozen vetted model, machine-agnostic baseline commissioning, and temporal persistence filtering.

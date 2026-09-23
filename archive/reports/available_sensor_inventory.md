# SIH 26008 — Available Sensor & Input Inventory
**Generated**: 2026-09-22
**Modality Status**: Vibration FROZEN (`IF-v0.3.1` + `v0.5` + `v0.6.1`). Camera & Multimodal integration active.

---

## 1. Executive Summary

This inventory documents all existing sensor, firmware, simulator, and edge interfaces identified in the SIH 26008 repository prior to multimodal fusion.

No existing interfaces have been fabricated. Real interfaces, simulator interfaces, and firmware abstractions are explicitly distinguished.

---

## 2. Sensor & Input Inventory Table

| Sensor / Input Name | Modality | Current Source | Protocol / Interface | Data Format | Units | Sampling / Update Rate | Hardware vs Simulated | Connected to FastAPI? | Visible in Dashboard? | POC Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **Tri-Axial Accelerometer (Piezo / MEMS)** | Vibration | `firmware/esp32/src/sensors/vibration_sensor.h`, `simulator/generator.py` | I2C / SPI / Direct ADC / JSON over HTTP | Standard 6 metrics: RMS, Peak, Kurtosis, Crest Factor, Dominant Freq, Spectral Energy | $g$ / $\text{mm/s}$ | 1000 Hz raw, 1 Hz feature window | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`MLEngineCard`, `SensorCards`, `TelemetryCharts`) | **FROZEN & VERIFIED** (IF-v0.3.1, SHA-256: `fb33d9e0...`) |
| **Bearing Shell / Surface Temp (MLX90614 / PT100)** | Temperature | `firmware/esp32/src/sensors/temperature_sensor.h`, `simulator/generator.py` | I2C / SPI (MAX31865) / JSON over HTTP | Float (`temperature`) | °C | 1 Hz | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`SensorCards`, `TelemetryCharts`) | **Integrating Thermal Intelligence** (threshold, rate-of-rise, persistence) |
| **Belt Tachometer / Proximity Pickup** | Belt Speed | `firmware/esp32/src/sensors/speed_sensor.h`, `simulator/generator.py` | Pulse count / GPIO Interrupt / JSON over HTTP | Float (`belt_speed`) | m/s | 1 Hz | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`SensorCards`, `TelemetryCharts`) | **Integrating Operating Context Engine** (`STOPPED`, `STARTING`, `IDLE`, `LOADED_RUNNING`, etc.) |
| **Idler Strain Gauge / Weightometer (HX711)** | Load | `firmware/esp32/src/sensors/load_sensor.h`, `simulator/generator.py` | 24-bit ADC (HX711) / JSON over HTTP | Float (`load`) | % (0–100%) | 1 Hz | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`SensorCards`) | **Integrating Operating Context Engine** (determines loaded vs empty running) |
| **Laser / Ultrasonic Edge Distance (VL53L1X)** | Belt Tracking | `firmware/esp32/src/sensors/tracking_sensor.h`, `simulator/generator.py` | I2C / Time-of-Flight / JSON over HTTP | Float (`tracking_position`) | mm lateral deviation | 1 Hz | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`SensorCards`, `TelemetryCharts`) | **Integrating Tracking Intelligence** (threshold, edge drift, persistence) |
| **Piezoelectric Acoustic Emission (AE)** | Acoustic | `firmware/esp32/src/sensors/acoustic_sensor.h`, `simulator/generator.py` | Analog RMS Envelope / JSON over HTTP | Float (`acoustic_rms`) | V | 1 Hz | Hardware abstraction + Synthetic generator | Yes (`/api/v1/telemetry`) | Yes (`SensorCards`) | Active auxiliary acoustic evidence |
| **Visual Optical Camera (USB / RTSP / Simulated)** | Visual / Camera | None previously implemented in backend; mock frames in dashboard | Video stream / MJPEG / HTTP Base64 / File / Webcam | Base64 JPEG frame + VisualEvidence metadata | Pixels / Bounding Box / Severity | 1–5 FPS / on-demand snapshot | Simulated frames with USB webcam/video file adapter | Now integrating in Phase 6–8 | **Implementing Visual Pipeline** (ROI, edge geometry drift, surface damage, annotated frames) |

---

## 3. Findings & Architectural Decisions

1. **Vibration Pipeline**:
   - Model artifact: `models/iforest/v0.3.1/model.joblib` (SHA-256: `fb33d9e01da559bec2fd1e2b06546835d8b3112bbaaa69fb18a7aedff89e4a19`).
   - Remains byte-for-byte FROZEN and intact.
2. **Thermal Intelligence**:
   - Temperature telemetry already exists in database and schemas.
   - Requires dynamic rate-of-rise (°C/min) tracking, absolute upper thresholds (e.g. 65°C warning, 80°C alert), and temporal persistence.
3. **Operating Context**:
   - Belt Speed (m/s) and Load (%) determine conveyor dynamic state (`STOPPED`, `STARTING`, `IDLE`, `EMPTY_RUNNING`, `LOADED_RUNNING`, `STOPPING`).
   - Normal transients during startup/stopping will be suppressed from triggering false fault alarms.
4. **Tracking Intelligence**:
   - Lateral deviation (`tracking_position` in mm) determines belt alignment health (`NORMAL`, `WATCH`, `WARNING`, `ALERT`).
5. **Camera Subsystem**:
   - OpenCV and Pillow will be installed in `backend/api/venv`.
   - A clean multi-source visual pipeline (`CameraService`) will accept USB webcam, video file, RTSP, or deterministic synthetic frames.
   - It will perform belt ROI segmentation, edge misalignment measurement, and visible surface/joint damage detection.
   - For simulated frames, clear label `DEMO / SIMULATED` will be enforced.
6. **Transparent Rule-Based Fusion**:
   - Evidence rules will aggregate Vibration, Thermal, Context, Tracking, and Camera into a unified event state with explainable "WHY?" bullets.

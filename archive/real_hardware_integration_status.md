# SIH 26008 — Real Hardware Integration Status & Sensor Inventory

**Date**: 2026-09-23  
**Modality Status**: Vibration FROZEN (`IF-v0.3.1` + `v0.5` + `v0.6.1`). Camera & Multimodal Pipeline Operational.  
**Objective**: Inventory physical and firmware hardware interfaces, differentiate real vs. simulated telemetry, and establish live hardware readiness for SIH.

---

## 1. Physical Hardware Discovery & System Audit

During host environment hardware inspection on Linux (`/dev` scan and Python OpenCV probe):
- **Live Optical Video Device**: `/dev/video0` and `/dev/video1` detected.
  - Device probe `cv2.VideoCapture(0)` confirmed active hardware webcam capturing live frames at $640 \times 480 \times 3$.
- **Serial / USB Sensor Microcontrollers**: No active `/dev/ttyUSB*` or `/dev/ttyACM*` devices currently plugged into this specific host.
- **Embedded Firmware HAL (`firmware/esp32/`)**: Full C++ Hardware Abstraction Layer implemented for ESP32 with PlatformIO build configuration.
- **Edge Gateway (`gateway/edge_agent/`)**: Operational FastAPI edge buffer and forwarder connecting ESP32 to central FastAPI backend.

---

## 2. Sensor & Interface Inventory Table

| Sensor / Module Name | Modality | Physical Interface | Pin / Port Config | Expected Units | Sampling / Update Rate | Current Firmware Status | Current Backend Status | Physical Hardware Available Now? |
|---|---|---|---|---|---|---|---|---|
| **Integrated / USB Webcam (V4L2)** | Visual / Camera | USB 2.0 / UVC (`/dev/video0`) | `/dev/video0` | Pixels ($640\times480$), JPEG | 0.5–2 Hz (decoupled worker) | N/A (Direct Linux V4L2) | **OPERATIONAL** (`CameraWorker` + `CameraService` + `data/evidence/camera/`) | **YES** (`/dev/video0` tested & verified live) |
| **Tri-Axial MEMS Accelerometer (ADXL355 / MPU6050)** | Vibration | I2C / SPI | I2C (SDA: GPIO 21, SCL: GPIO 22) or SPI | $g$ (RMS, Peak, Kurtosis, Crest Factor, Dominant Freq, Energy) | 1000 Hz raw, 1 Hz feature window | Implemented in `firmware/esp32/src/sensors/vibration_sensor.h` (HAL + Mock) | **FROZEN & VERIFIED** (`VibrationInferenceEngine` `IF-v0.3.1` + `v0.5` + `v0.6.1`) | **Emulated Hardware Bridge** (ESP32 / Fixture Bridge over HTTP/Serial) |
| **Infrared / RTD Surface Temp (MLX90614 / PT100)** | Temperature | I2C / SPI (MAX31865) | I2C (SDA: GPIO 21, SCL: GPIO 22) | °C | 1 Hz | Implemented in `firmware/esp32/src/sensors/temperature_sensor.h` | **OPERATIONAL** (`ThermalIntelligence` with rate-of-rise & persistence) | **Emulated Hardware Bridge** (ESP32 / Fixture Bridge) |
| **Proximity Pickup / Hall Encoder** | Speed / RPM | GPIO Pulse Interrupt | GPIO 18 (Interrupt on rising edge) | Pulses/sec, RPM, m/s | 1 Hz | Implemented in `firmware/esp32/src/sensors/speed_sensor.h` | **OPERATIONAL** (`OperatingContextEngine` with pulse conversion) | **Emulated Hardware Bridge** (ESP32 / Fixture Bridge) |
| **Idler Strain Gauge (HX711)** | Conveyance Load | 24-bit Serial ADC | GPIO 4 (DT), GPIO 5 (SCK) | % load (0–100%) | 1 Hz | Implemented in `firmware/esp32/src/sensors/load_sensor.h` | **OPERATIONAL** (`OperatingContextEngine` load interpretation) | **Emulated Hardware Bridge** (ESP32 / Fixture Bridge) |
| **Laser / Ultrasonic Edge Sensor (VL53L1X)** | Belt Tracking | I2C | I2C (SDA: GPIO 21, SCL: GPIO 22) | mm lateral deviation | 1 Hz | Implemented in `firmware/esp32/src/sensors/tracking_sensor.h` | **OPERATIONAL** (`TrackingIntelligence` lateral drift logic) | **Emulated Hardware Bridge** (ESP32 / Fixture Bridge) |

---

## 3. Real vs. Simulated Distinction & System Modes

To ensure complete scientific integrity for the SIH judges:
1. **Live Camera**:
   - Running against `/dev/video0` captures authentic, un-watermarked frames.
   - When configured in demo/simulated mode, synthetic frames are watermarked with `"DEMO / SIMULATED"`.
2. **Telemetry Sources**:
   - `REAL_HARDWARE`: Telemetry arriving from physical ESP32 or live serial bridge.
   - `DEMO / SIMULATED`: Telemetry arriving from synthetic scenario injector.
   - Modality contracts explicitly report `source` and `is_simulated`.
3. **Hardware Health Monitoring**:
   - Independent hardware status (`ONLINE`, `OFFLINE`, `STALE`) reported for each sensor channel, decoupled from conveyor fault status.

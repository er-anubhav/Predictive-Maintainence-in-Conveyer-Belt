# Industrial IoT Tier (`iot/`)

The `iot/` directory houses the complete field-level hardware and edge compute stack for the SIH 26008 Intelligent Conveyor Belt Monitoring System.

---

## Architecture Overview

```
[ Field Sensors ] ──(ADC / I2C / GPIO)──> [ iot/firmware/ (ESP32 C++) ]
                                                      │
                                                      │ (WiFi / Serial / RS-485)
                                                      ▼
[ Central Backend ] <──(Store-and-Forward)── [ iot/gateway/ (Edge Agent & Bridge) ]
```

---

## Subdirectories

### 1. `iot/firmware/` (Level 1: Field Device & Sensor HAL)
- **Target Hardware**: ESP32 microcontroller (Xtensa dual-core, 240 MHz).
- **Stack**: C++ / Arduino / PlatformIO.
- **Responsibilities**:
  - Direct hardware interfacing with tri-axial vibration accelerometers, infrared temperature sensors, pulse counters for belt speed/RPM, strain gauge load cells, and laser tracking sensors.
  - Assembles readings into canonical v1.0 JSON packets.
  - Low-latency edge transmission to local gateway.

### 2. `iot/gateway/` (Level 2: Edge Computing & Supervisory Gateway)
- **Target Hardware**: Industrial Edge PC / Raspberry Pi / On-Site Gateway.
- **Stack**: Python 3.12 / FastAPI / SQLite / Uvicorn.
- **Components**:
  - **`edge_agent/`**: High-performance HTTP ingest server (Port 9000). Features a persistent SQLite store-and-forward queue with zero-data-loss recovery during network outages and local packet deduplication.
  - **`bridge/`**: `esp32_hardware_bridge.py` for physical USB serial interface (/dev/ttyUSB0, /dev/ttyACM0) and testbench signal routing.

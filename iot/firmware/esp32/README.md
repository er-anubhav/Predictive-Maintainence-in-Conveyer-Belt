# ESP32 Edge Sensor Node Firmware — SIH 26008

## Overview

This module houses the embedded firmware for the distributed IoT monitoring nodes positioned along mining conveyor systems. Built on the ESP32 microcontroller platform using the Arduino/FreeRTOS framework and PlatformIO.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                   ESP32 Sensor Node                    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Sensor Hardware Abstraction Layer         │  │
│  │   [Vibration]  [Acoustic]  [Temp]  [Speed] [Load]│  │
│  └──────────────────────────┬───────────────────────┘  │
│                             │                          │
│                             ▼                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │     Packet Builder (Monotonic Sequence Counter)  │  │
│  │     Canonical Telemetry JSON (v1.0)              │  │
│  └──────────────────────────┬───────────────────────┘  │
│                             │                          │
│                             ▼                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Network Manager (HTTP POST)             │  │
│  └──────────────────────────┬───────────────────────┘  │
└─────────────────────────────┼──────────────────────────┘
                              │ Local WiFi / RS-485
                              ▼
                 ┌─────────────────────────┐
                 │    Edge Gateway Agent   │
                 │      (POST /ingest)     │
                 └─────────────────────────┘
```

---

## Key Design Principles

1. **Decoupled from Central Infrastructure**:
   The ESP32 communicates exclusively with the local **Edge Gateway** (`POST http://gateway-ip:9000/ingest`). It has zero dependencies on PostgreSQL, internet uplinks, or cloud endpoints.
2. **Sensor Hardware Abstraction Layer (HAL)**:
   Clear C++ interfaces (`VibrationSensor`, `TemperatureSensor`, etc.) allow rapid switching from development mocks to physical industrial sensors (ADXL355, MLX90614, piezoelectric pickups) without rewriting sampling or networking logic.
3. **Monotonic Sequence Numbering**:
   Every transmission increments a 32-bit sequence counter (`sequence`). The combination of `(node_id, sequence)` uniquely identifies each telemetry frame, preventing duplicates during intermittent wireless link retransmissions.
4. **Resilient Autonomous Operation**:
   If the local gateway or WiFi drops, the ESP32 continues its operational loop and retry cadence without blocking or memory leakage.

---

## Source Tree

```
iot/firmware/esp32/
├── platformio.ini               # PlatformIO board & dependency manifest
├── src/
│   ├── config.h                 # WiFi credentials, gateway endpoint, node ID
│   ├── network.h / .cpp         # WiFi lifecycle & HTTP client
│   ├── telemetry.h / .cpp       # Multi-sensor coordinator
│   ├── sensors/
│   │   ├── vibration_sensor.h   # Tri-axial vibration HAL & Mock
│   │   ├── temperature_sensor.h # Infrared/contact temperature HAL & Mock
│   │   ├── acoustic_sensor.h    # High-frequency acoustic emission HAL & Mock
│   │   ├── speed_sensor.h       # Proximity belt speed HAL & Mock
│   │   ├── load_sensor.h        # Weightometer load HAL & Mock
│   │   └── tracking_sensor.h    # Lateral belt tracking HAL & Mock
│   ├── packet/
│   │   ├── packet_builder.h     # Packet builder definition
│   │   └── packet_builder.cpp   # Canonical v1.0 JSON serializer
│   └── main.cpp                 # Main setup and loop routines
└── README.md
```

---

## Building and Flashing

### Using PlatformIO CLI

```bash
cd iot/firmware/esp32

# Compile the firmware
pio run

# Flash to connected ESP32 via USB
pio run --target upload

# Open Serial Monitor (115200 baud)
pio device monitor
```

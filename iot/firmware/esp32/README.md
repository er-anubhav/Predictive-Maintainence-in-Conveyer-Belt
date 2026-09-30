# ESP32 Edge Sensor Node Firmware — SIH 26008

The ESP32 node samples conveyor-condition sensors, computes vibration features locally, and sends canonical v1.0 JSON to the local Edge Gateway at `/ingest`.

## Current hardware-oriented sources

| Modality | Firmware source | Default |
|---|---|---|
| Vibration | ADXL345 over I2C or simulated fixture | SIMULATED |
| Temperature | MLX90614 over I2C or simulated fixture | SIMULATED |
| RPM / belt speed | GPIO pulse input or simulated RPM | REAL_HARDWARE |
| Load | Analog torque/current proxy or simulated load | REAL_HARDWARE |
| Tracking | Digital IR edge proxy or simulated deviation | REAL_HARDWARE |
| Acoustic | Existing HAL retained for schema compatibility | SIMULATED |

The project deliberately reports per-sensor source labels as `REAL_HARDWARE`, `SIMULATED`, or `UNAVAILABLE`. This avoids presenting development mocks as field measurements.

## Default ESP32 pins

- I2C SDA: GPIO 21
- I2C SCL: GPIO 22
- RPM pulse input: GPIO 18
- Load analog proxy: GPIO 34
- Tracking digital input: GPIO 27
- ADXL345 default address: `0x53`
- MLX90614 default address: `0x5A`
- **L298N Motor Driver Control (12V DC Geared Conveyor Motor)**:
  - ENA (PWM Speed): GPIO 25 (ESP32 LEDC channel 0, 5 kHz)
  - IN1 (Direction 1): GPIO 26
  - IN2 (Direction 2): GPIO 33
  - **Electrical Safety & Isolation**:
    - 12V PSU (+) -> L298N 12V VCC terminal.
    - 12V PSU (-) -> L298N GND terminal.
    - ESP32 GND -> L298N GND terminal (Common ground reference for logic thresholds).
    - ESP32 logic is 3.3V. L298N TTL inputs accept 3.3V logic high (>2.3V).
    - **ESP32 must NEVER connect directly to 12V supply**.

Verify the actual sensor and motor driver wiring, electrical levels, calibration and mechanical mounting before field deployment.

## Telemetry path

```
Sensor drivers
    ↓
TelemetryCollector
    ↓
PacketBuilder
    ↓
WiFi / HTTP
    ↓
Edge Gateway POST /ingest
    ↓
FastAPI telemetry service
    ↓
Frozen ML + commissioning + persistence layers
```

Raw vibration samples are transmitted in `raw_samples` with `sample_rate_hz` so the existing backend inference engine can extract the frozen Standard-6 feature representation.

The packet also includes:

- `sequence` with NVS-backed reserved blocks to avoid reuse after reboot
- NTP-derived UTC timestamp when available
- `timestamp_source`
- `sensor_sources`
- `device_health` with WiFi RSSI, uptime, heap and firmware version
- vibration features for observability

## Credentials

Create:

```
iot/firmware/esp32/src/secrets.h
```

from:

```
iot/firmware/esp32/src/secrets.h.example
```

`secrets.h` is gitignored.

## Build and flash

```bash
cd iot/firmware/esp32

pio run
pio run --target upload
pio device monitor
```

Serial monitor: **115200 baud**.

## Switching to physical vibration

In `src/config.h`:

```cpp
#define VIBRATION_SOURCE 1
```

Then verify the ADXL345 is detected at the configured I2C address. Do not describe the resulting telemetry as validated industrial measurements until the sensor is physically installed, calibrated and tested against the actual conveyor/machine.

## Notes

The current load and tracking implementations are deliberately simple POC interfaces. They provide hardware data paths, not industrial calibration. The frozen ML benchmark/model lineage is not retrained or modified by this firmware work.

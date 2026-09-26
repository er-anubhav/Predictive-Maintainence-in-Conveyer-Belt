#pragma once
#include <Arduino.h>
#include "../config.h"

class SpeedSensor {
public:
    virtual ~SpeedSensor() = default;
    virtual bool begin() = 0;
    virtual float readRpm() = 0;
    virtual float readSpeed() = 0;
    virtual uint32_t pulseCount() const = 0;
    virtual const char* source() const = 0;
};

class MockSpeedSensor final : public SpeedSensor {
public:
    explicit MockSpeedSensor(float rpm = 1500.0f) : baseRpm(rpm) {}
    bool begin() override { Serial.println("[RPM] SIMULATED source initialized."); return true; }
    float readRpm() override { return baseRpm + static_cast<float>(random(-10, 11)); }
    float readSpeed() override { return PI * PULLEY_DIAMETER_M * readRpm() / 60.0f; }
    uint32_t pulseCount() const override { return 0; }
    const char* source() const override { return SENSOR_SOURCE_SIMULATED; }
private:
    float baseRpm;
};

class IRPulseSpeedSensor final : public SpeedSensor {
public:
    bool begin() override;
    float readRpm() override;
    float readSpeed() override;
    uint32_t pulseCount() const override;
    const char* source() const override;

private:
    static void IRAM_ATTR onPulseISR();
    volatile uint32_t totalPulses = 0;
    volatile uint32_t lastPulseMicros = 0;
    uint32_t previousPulses = 0;
    uint32_t previousReadMicros = 0;
    float cachedRpm = 0.0f;
    bool ready = false;
};

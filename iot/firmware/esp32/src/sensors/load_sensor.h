#pragma once
#include <Arduino.h>
#include "../config.h"

class LoadSensor {
public:
    virtual ~LoadSensor() = default;
    virtual bool begin() = 0;
    virtual float readLoad() = 0;
    virtual const char* source() const = 0;
};

class MockLoadSensor final : public LoadSensor {
public:
    explicit MockLoadSensor(float load = 70.0f) : baseLoad(load) {}
    bool begin() override { Serial.println("[LOAD] SIMULATED source initialized."); return true; }
    float readLoad() override {
        return constrain(baseLoad + static_cast<float>(random(-15, 16)) / 10.0f, 0.0f, 100.0f);
    }
    const char* source() const override { return SENSOR_SOURCE_SIMULATED; }
private:
    float baseLoad;
};

class AnalogTorqueLoadProxy final : public LoadSensor {
public:
    bool begin() override {
        pinMode(LOAD_INPUT_PIN, INPUT);
        analogReadResolution(12);
        ready = true;
        Serial.printf("[LOAD] REAL_HARDWARE analog proxy on GPIO %d.\n", LOAD_INPUT_PIN);
        return true;
    }

    float readLoad() override {
        if (!ready) return NAN;
        const int raw = analogRead(LOAD_INPUT_PIN);
        const float voltage = static_cast<float>(raw) * LOAD_INPUT_VOLTAGE / LOAD_ADC_MAX;
        const float span = LOAD_FULL_SCALE_V - LOAD_ZERO_V;
        if (span <= 0.0f) return NAN;
        return constrain((voltage - LOAD_ZERO_V) / span * LOAD_FULL_SCALE_PERCENT,
                         0.0f, LOAD_FULL_SCALE_PERCENT);
    }

    const char* source() const override {
        return ready ? SENSOR_SOURCE_REAL : SENSOR_SOURCE_UNAVAILABLE;
    }
private:
    bool ready = false;
};

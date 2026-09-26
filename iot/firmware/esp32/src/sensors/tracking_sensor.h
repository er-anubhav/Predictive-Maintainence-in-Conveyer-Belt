#pragma once
#include <Arduino.h>
#include "../config.h"

class TrackingSensor {
public:
    virtual ~TrackingSensor() = default;
    virtual bool begin() = 0;
    virtual float readTrackingDeviation() = 0;
    virtual const char* source() const = 0;
};

class MockTrackingSensor final : public TrackingSensor {
public:
    explicit MockTrackingSensor(float deviation = 0.0f) : baseDeviation(deviation) {}
    bool begin() override { Serial.println("[TRACK] SIMULATED source initialized."); return true; }
    float readTrackingDeviation() override { return baseDeviation; }
    const char* source() const override { return SENSOR_SOURCE_SIMULATED; }
private:
    float baseDeviation;
};

class DigitalIRTrackingSensor final : public TrackingSensor {
public:
    bool begin() override {
        pinMode(TRACKING_INPUT_PIN, INPUT_PULLUP);
        ready = true;
        Serial.printf("[TRACK] REAL_HARDWARE IR input on GPIO %d.\n", TRACKING_INPUT_PIN);
        return true;
    }

    float readTrackingDeviation() override {
        if (!ready) return NAN;
        const int value = digitalRead(TRACKING_INPUT_PIN);
        const bool active = TRACKING_ACTIVE_LOW ? value == LOW : value == HIGH;
        return active ? TRACKING_ACTIVE_SIGN * TRACKING_ACTIVE_DEVIATION_MM : 0.0f;
    }

    const char* source() const override {
        return ready ? SENSOR_SOURCE_REAL : SENSOR_SOURCE_UNAVAILABLE;
    }
private:
    bool ready = false;
};

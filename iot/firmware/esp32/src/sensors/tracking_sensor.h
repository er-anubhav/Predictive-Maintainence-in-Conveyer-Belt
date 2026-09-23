#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for Lateral Belt Tracking Sensor
 * (Target Hardware: Dual Ultrasonic / Time-of-Flight Edge Distance Sensors VL53L1X)
 */
class TrackingSensor {
public:
    virtual ~TrackingSensor() = default;
    virtual bool begin() = 0;
    virtual float readTrackingDeviation() = 0;
};

class MockTrackingSensor : public TrackingSensor {
private:
    float baseDeviation;

public:
    MockTrackingSensor(float dev = -0.5f) : baseDeviation(dev) {}

    bool begin() override {
        Serial.println("[TRACK] Mock Lateral Tracking Sensor initialized.");
        return true;
    }

    float readTrackingDeviation() override {
        float noise = ((float)(random(-10, 10)) / 10.0f);
        return baseDeviation + noise;
    }
};

#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for Belt Velocity / Speed Sensor
 * (Target Hardware: Inductive Proximity Pulse Pickup on Non-Drive Pulley)
 */
class SpeedSensor {
public:
    virtual ~SpeedSensor() = default;
    virtual bool begin() = 0;
    virtual float readSpeed() = 0;
};

class MockSpeedSensor : public SpeedSensor {
private:
    float baseSpeed;

public:
    MockSpeedSensor(float speed = 2.80f) : baseSpeed(speed) {}

    bool begin() override {
        Serial.println("[SPEED] Mock Belt Speed Sensor initialized.");
        return true;
    }

    float readSpeed() override {
        float noise = ((float)(random(-20, 20)) / 1000.0f);
        return max(0.0f, baseSpeed + noise);
    }
};

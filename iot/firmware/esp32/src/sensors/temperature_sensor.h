#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for Bearing/Surface Temperature Sensor
 * (Target Hardware: MLX90614 Contactless IR or PT100/MAX31865 RTD)
 */
class TemperatureSensor {
public:
    virtual ~TemperatureSensor() = default;
    virtual bool begin() = 0;
    virtual float readTemperature() = 0;
};

class MockTemperatureSensor : public TemperatureSensor {
private:
    float baseTemp;

public:
    MockTemperatureSensor(float temp = 42.5f) : baseTemp(temp) {}

    bool begin() override {
        Serial.println("[TEMP] Mock Temperature Sensor initialized.");
        return true;
    }

    float readTemperature() override {
        float noise = ((float)(random(-50, 50)) / 100.0f);
        return baseTemp + noise;
    }
};

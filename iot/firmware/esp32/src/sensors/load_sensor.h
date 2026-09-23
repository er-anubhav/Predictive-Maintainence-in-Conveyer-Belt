#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for Material Conveyance Load Sensor
 * (Target Hardware: Idler Weigh-Scale / Strain Gauge with HX711 ADC)
 */
class LoadSensor {
public:
    virtual ~LoadSensor() = default;
    virtual bool begin() = 0;
    virtual float readLoad() = 0;
};

class MockLoadSensor : public LoadSensor {
private:
    float baseLoad;

public:
    MockLoadSensor(float load = 71.5f) : baseLoad(load) {}

    bool begin() override {
        Serial.println("[LOAD] Mock Belt Load Sensor initialized.");
        return true;
    }

    float readLoad() override {
        float noise = ((float)(random(-15, 15)) / 10.0f);
        return max(0.0f, min(100.0f, baseLoad + noise));
    }
};

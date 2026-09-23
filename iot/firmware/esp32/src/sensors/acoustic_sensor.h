#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for High-Frequency Acoustic Emission Sensor
 * (Target Hardware: Piezoelectric Transducer with RMS Envelope Detector)
 */
class AcousticSensor {
public:
    virtual ~AcousticSensor() = default;
    virtual bool begin() = 0;
    virtual float readAcousticRms() = 0;
};

class MockAcousticSensor : public AcousticSensor {
private:
    float baseAcousticRms;

public:
    MockAcousticSensor(float rms = 0.28f) : baseAcousticRms(rms) {}

    bool begin() override {
        Serial.println("[AE] Mock Acoustic Sensor initialized.");
        return true;
    }

    float readAcousticRms() override {
        float noise = ((float)(random(-20, 20)) / 1000.0f);
        return max(0.01f, baseAcousticRms + noise);
    }
};

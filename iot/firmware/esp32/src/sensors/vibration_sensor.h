#pragma once
#include <Arduino.h>

/**
 * Hardware Abstraction Interface for Tri-Axial Vibration Sensor
 * (Target Hardware: ADXL355 / MPU6050 over SPI or I2C)
 */
class VibrationSensor {
public:
    virtual ~VibrationSensor() = default;
    virtual bool begin() = 0;
    virtual float readRms() = 0;
    virtual float readPeak() = 0;
    virtual float readKurtosis() = 0;
};

/**
 * Mock Vibration Sensor Implementation for testing without physical MEMS sensors
 */
class MockVibrationSensor : public VibrationSensor {
private:
    float baseRms;
    float basePeak;
    float baseKurtosis;
    int tick;

public:
    MockVibrationSensor(float rms = 0.42f, float peak = 1.18f, float kurtosis = 3.02f)
        : baseRms(rms), basePeak(peak), baseKurtosis(kurtosis), tick(0) {}

    bool begin() override {
        Serial.println("[VIB] Mock Vibration Sensor initialized.");
        return true;
    }

    float readRms() override {
        tick++;
        float noise = ((float)(random(-30, 30)) / 1000.0f);
        return max(0.01f, baseRms + noise);
    }

    float readPeak() override {
        float noise = ((float)(random(-50, 50)) / 1000.0f);
        return max(0.05f, basePeak + noise);
    }

    float readKurtosis() override {
        float noise = ((float)(random(-100, 100)) / 1000.0f);
        return max(1.5f, baseKurtosis + noise);
    }
};

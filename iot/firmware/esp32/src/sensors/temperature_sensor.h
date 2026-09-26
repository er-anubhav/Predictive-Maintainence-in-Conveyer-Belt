#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "../config.h"

class TemperatureSensor {
public:
    virtual ~TemperatureSensor() = default;
    virtual bool begin() = 0;
    virtual float readTemperature() = 0;
    virtual const char* source() const = 0;
};

class MockTemperatureSensor final : public TemperatureSensor {
public:
    explicit MockTemperatureSensor(float temp = 42.5f) : baseTemp(temp) {}
    bool begin() override { Serial.println("[TEMP] SIMULATED source initialized."); return true; }
    float readTemperature() override {
        return baseTemp + static_cast<float>(random(-50, 51)) / 100.0f;
    }
    const char* source() const override { return SENSOR_SOURCE_SIMULATED; }
private:
    float baseTemp;
};

class MLX90614TemperatureSensor final : public TemperatureSensor {
public:
    explicit MLX90614TemperatureSensor(uint8_t address = MLX90614_I2C_ADDRESS) : address(address) {}

    bool begin() override {
        Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
        Wire.beginTransmission(address);
        ready = (Wire.endTransmission() == 0);
        Serial.printf("[TEMP] MLX90614 %s.\n", ready ? "ready" : "not detected");
        return ready;
    }

    float readTemperature() override {
        if (!ready) return NAN;
        uint16_t raw = 0;
        if (!read16(0x07, raw)) return NAN;
        const float c = static_cast<float>(raw) * 0.02f - 273.15f;
        return (c >= -40.0f && c <= 300.0f) ? c : NAN;
    }

    const char* source() const override {
        return ready ? SENSOR_SOURCE_REAL : SENSOR_SOURCE_UNAVAILABLE;
    }

private:
    uint8_t address;
    bool ready = false;

    bool read16(uint8_t reg, uint16_t& value) {
        Wire.beginTransmission(address);
        Wire.write(reg);
        if (Wire.endTransmission(false) != 0) return false;
        if (Wire.requestFrom(address, static_cast<uint8_t>(3)) < 2) return false;
        const uint8_t lo = Wire.read();
        const uint8_t hi = Wire.read();
        if (Wire.available()) Wire.read();
        value = static_cast<uint16_t>(lo) | (static_cast<uint16_t>(hi) << 8);
        return true;
    }
};

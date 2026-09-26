#pragma once

#include <Arduino.h>
#include <Wire.h>
#include "../config.h"

struct VibrationWindow {
    float samples[VIBRATION_WINDOW_SAMPLES];
    size_t count;
    float rms;
    float peak;
    float crestFactor;
    float kurtosis;
    float dominantFrequencyHz;
    float spectralEnergy;
    const char* source;
    bool valid;

    VibrationWindow()
        : count(0),
          rms(0.0f),
          peak(0.0f),
          crestFactor(0.0f),
          kurtosis(3.0f),
          dominantFrequencyHz(0.0f),
          spectralEnergy(0.0f),
          source(SENSOR_SOURCE_UNAVAILABLE),
          valid(false) {}
};

class VibrationSensor {
public:
    virtual ~VibrationSensor() = default;
    virtual bool begin() = 0;
    virtual bool captureWindow(VibrationWindow& out) = 0;
    virtual const char* source() const = 0;
};

class MockVibrationSensor final : public VibrationSensor {
private:
    int tick = 0;

public:
    bool begin() override {
        randomSeed(static_cast<unsigned long>(micros()));
        Serial.println("[VIB] Simulated vibration source initialized.");
        return true;
    }

    bool captureWindow(VibrationWindow& out) override {
        tick++;
        out = VibrationWindow{};
        out.source = SENSOR_SOURCE_SIMULATED;
        out.count = VIBRATION_WINDOW_SAMPLES;

        const bool anomaly = (VIBRATION_SIM_MODE == VIBRATION_SIM_MODE_ANOMALY) || (tick % 20 >= 15);
        const float base = anomaly ? 0.68f : 0.30f;
        const float impulseAmp = anomaly ? 1.55f : 0.35f;
        const float f = anomaly ? 72.0f : 35.0f;

        for (size_t i = 0; i < out.count; ++i) {
            const float t = static_cast<float>(i) / static_cast<float>(VIBRATION_SAMPLE_RATE_HZ);
            float sample = base * sinf(2.0f * PI * f * t);
            sample += static_cast<float>(random(-40, 41)) / 1000.0f;
            if (anomaly && (i % 97 == 0 || i % 193 == 0)) {
                sample += impulseAmp;
            }
            out.samples[i] = sample;
        }

        computeFeatures(out);
        return out.valid;
    }

    const char* source() const override {
        return SENSOR_SOURCE_SIMULATED;
    }

private:
    static void computeFeatures(VibrationWindow& out) {
        if (out.count == 0) return;

        double sum = 0.0;
        double sumSq = 0.0;
        float peak = 0.0f;

        for (size_t i = 0; i < out.count; ++i) {
            const float x = out.samples[i];
            sum += x;
            sumSq += static_cast<double>(x) * static_cast<double>(x);
            peak = max(peak, fabsf(x));
        }

        const double mean = sum / static_cast<double>(out.count);
        const double variance = max(
            1e-12,
            (sumSq / static_cast<double>(out.count)) - (mean * mean)
        );

        double m4 = 0.0;
        for (size_t i = 0; i < out.count; ++i) {
            const double d = static_cast<double>(out.samples[i]) - mean;
            m4 += d * d * d * d;
        }
        const double fourthMoment = m4 / static_cast<double>(out.count);

        out.rms = sqrtf(static_cast<float>(sumSq / static_cast<double>(out.count)));
        out.peak = peak;
        out.crestFactor = peak / max(out.rms, 1e-6f);
        out.kurtosis = static_cast<float>(fourthMoment / (variance * variance));

        estimateFrequencyAndEnergy(out);

        out.valid = isfinite(out.rms) &&
                    isfinite(out.peak) &&
                    isfinite(out.crestFactor) &&
                    isfinite(out.kurtosis) &&
                    isfinite(out.dominantFrequencyHz) &&
                    isfinite(out.spectralEnergy);
    }

    static void estimateFrequencyAndEnergy(VibrationWindow& out) {
        // Lightweight DFT over a bounded frequency band. This keeps the ESP32
        // dependency-free and provides useful evidence for the current POC.
        const size_t n = out.count;
        float bestMagnitude = 0.0f;
        float bestHz = 0.0f;
        double energy = 0.0;

        const float maxHz = min(200.0f, VIBRATION_SAMPLE_RATE_HZ / 2.0f);
        for (int bin = 1; bin <= 200; ++bin) {
            const float freq = (static_cast<float>(bin) * maxHz) / 200.0f;
            const float omega = 2.0f * PI * freq / static_cast<float>(VIBRATION_SAMPLE_RATE_HZ);
            float realPart = 0.0f;
            float imagPart = 0.0f;

            for (size_t i = 0; i < n; ++i) {
                const float phase = omega * static_cast<float>(i);
                realPart += out.samples[i] * cosf(phase);
                imagPart -= out.samples[i] * sinf(phase);
            }

            const float mag2 = realPart * realPart + imagPart * imagPart;
            energy += static_cast<double>(mag2);

            if (mag2 > bestMagnitude) {
                bestMagnitude = mag2;
                bestHz = freq;
            }
        }

        out.dominantFrequencyHz = bestHz;
        out.spectralEnergy = static_cast<float>(energy / static_cast<double>(n));
    }
};

class ADXL345VibrationSensor final : public VibrationSensor {
private:
    uint8_t address;
    bool ready = false;

public:
    explicit ADXL345VibrationSensor(uint8_t i2cAddress = VIBRATION_I2C_ADDRESS)
        : address(i2cAddress) {}

    bool begin() override {
        Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
        Wire.beginTransmission(address);
        if (Wire.endTransmission() != 0) {
            Serial.printf("[VIB] ADXL345 not detected at 0x%02X.\\n", address);
            ready = false;
            return false;
        }

        writeRegister(0x2D, 0x08); // Measure mode
        writeRegister(0x31, 0x08); // Full resolution, +/-4 g
        writeRegister(0x2C, 0x0D); // 800 Hz output data rate

        const uint8_t deviceId = readRegister(0x00);
        ready = (deviceId == 0xE5);
        Serial.printf("[VIB] ADXL345 %s (DEVID=0x%02X).\\n", ready ? "ready" : "invalid", deviceId);
        return ready;
    }

    bool captureWindow(VibrationWindow& out) override {
        out = VibrationWindow{};
        out.source = ready ? SENSOR_SOURCE_REAL : SENSOR_SOURCE_UNAVAILABLE;

        if (!ready) {
            return false;
        }

        const uint32_t samplePeriodUs = 1000000UL / VIBRATION_SAMPLE_RATE_HZ;
        uint32_t nextSample = micros();

        for (size_t i = 0; i < VIBRATION_WINDOW_SAMPLES; ++i) {
            while (static_cast<int32_t>(micros() - nextSample) < 0) {
                delayMicroseconds(20);
            }

            int16_t xRaw = 0;
            int16_t yRaw = 0;
            int16_t zRaw = 0;
            if (!readAxes(xRaw, yRaw, zRaw)) {
                return false;
            }

            // Use the configured X axis for the POC. Mount the sensor so the
            // monitored mechanical axis is aligned with X.
            out.samples[i] = static_cast<float>(xRaw) * 0.0039f;
            out.count = i + 1;
            nextSample += samplePeriodUs;
        }

        MockVibrationSensor::computeFeatures(out);
        out.source = SENSOR_SOURCE_REAL;
        return out.valid;
    }

    const char* source() const override {
        return ready ? SENSOR_SOURCE_REAL : SENSOR_SOURCE_UNAVAILABLE;
    }

private:
    void writeRegister(uint8_t reg, uint8_t value) {
        Wire.beginTransmission(address);
        Wire.write(reg);
        Wire.write(value);
        Wire.endTransmission();
    }

    uint8_t readRegister(uint8_t reg) {
        Wire.beginTransmission(address);
        Wire.write(reg);
        Wire.endTransmission(false);
        Wire.requestFrom(address, static_cast<uint8_t>(1));

        return Wire.available() ? Wire.read() : 0x00;
    }

    bool readAxes(int16_t& x, int16_t& y, int16_t& z) {
        Wire.beginTransmission(address);
        Wire.write(0x32);
        if (Wire.endTransmission(false) != 0) {
            return false;
        }

        if (Wire.requestFrom(address, static_cast<uint8_t>(6)) != 6) {
            return false;
        }

        x = static_cast<int16_t>(Wire.read() | (Wire.read() << 8));
        y = static_cast<int16_t>(Wire.read() | (Wire.read() << 8));
        z = static_cast<int16_t>(Wire.read() | (Wire.read() << 8));
        return true;
    }
};

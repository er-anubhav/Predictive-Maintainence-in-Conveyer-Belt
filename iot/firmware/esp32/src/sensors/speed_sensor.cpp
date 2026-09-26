#include "speed_sensor.h"

static IRPulseSpeedSensor* g_speedSensor = nullptr;

void IRAM_ATTR IRPulseSpeedSensor::onPulseISR() {
    if (!g_speedSensor) return;

    const uint32_t now = micros();
    const uint32_t last = g_speedSensor->lastPulseMicros;

    if (last == 0 || (now - last) >= RPM_DEBOUNCE_US) {
        g_speedSensor->totalPulses++;
        g_speedSensor->lastPulseMicros = now;
    }
}

bool IRPulseSpeedSensor::begin() {
    g_speedSensor = this;
    pinMode(RPM_INPUT_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(RPM_INPUT_PIN), onPulseISR, RISING);

    previousReadMicros = micros();
    ready = true;

    Serial.printf("[RPM] REAL_HARDWARE pulse input on GPIO %d.\n",
                  RPM_INPUT_PIN);
    return true;
}

float IRPulseSpeedSensor::readRpm() {
    if (!ready) return NAN;

    const uint32_t now = micros();
    const uint32_t elapsed = now - previousReadMicros;

    if (elapsed < 250000UL) return cachedRpm;

    noInterrupts();
    const uint32_t pulses = totalPulses;
    const uint32_t lastPulse = lastPulseMicros;
    interrupts();

    const uint32_t delta = pulses - previousPulses;
    const float seconds = static_cast<float>(elapsed) / 1000000.0f;

    if (seconds > 0.0f) {
        cachedRpm =
            (static_cast<float>(delta) / seconds) *
            (60.0f / PULSES_PER_REVOLUTION);
    }

    previousPulses = pulses;
    previousReadMicros = now;

    if (lastPulse != 0 && (now - lastPulse) > 2000000UL) {
        cachedRpm = 0.0f;
    }

    return cachedRpm;
}

float IRPulseSpeedSensor::readSpeed() {
    const float rpm = readRpm();
    return isfinite(rpm)
        ? PI * PULLEY_DIAMETER_M * rpm / 60.0f
        : NAN;
}

uint32_t IRPulseSpeedSensor::pulseCount() const {
    noInterrupts();
    const uint32_t pulses = totalPulses;
    interrupts();
    return pulses;
}

const char* IRPulseSpeedSensor::source() const {
    return ready ? SENSOR_SOURCE_REAL
                 : SENSOR_SOURCE_UNAVAILABLE;
}

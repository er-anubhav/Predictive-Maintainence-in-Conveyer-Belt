#include "telemetry.h"

TelemetryCollector::TelemetryCollector(
    VibrationSensor* vib,
    TemperatureSensor* temp,
    AcousticSensor* acoustic,
    SpeedSensor* speed,
    LoadSensor* load,
    TrackingSensor* tracking
) : vibSensor(vib), tempSensor(temp), acousticSensor(acoustic),
    speedSensor(speed), loadSensor(load), trackingSensor(tracking) {}

bool TelemetryCollector::begin() {
    bool ok = true;
    if (vibSensor) ok &= vibSensor->begin();
    if (tempSensor) ok &= tempSensor->begin();
    if (acousticSensor) ok &= acousticSensor->begin();
    if (speedSensor) ok &= speedSensor->begin();
    if (loadSensor) ok &= loadSensor->begin();
    if (trackingSensor) ok &= trackingSensor->begin();
    return ok;
}

SensorReadings TelemetryCollector::sampleAll() {
    SensorReadings readings;

    if (vibSensor) {
        readings.vibration.valid = vibSensor->captureWindow(readings.vibration);
        readings.vibrationSource = vibSensor->source();
    }

    if (acousticSensor) readings.acousticRms = acousticSensor->readAcousticRms();

    if (tempSensor) {
        readings.temperature = tempSensor->readTemperature();
        readings.temperatureSource = tempSensor->source();
    }

    if (speedSensor) {
        readings.rpm = speedSensor->readRpm();
        readings.beltSpeed = speedSensor->readSpeed();
        readings.pulseCount = speedSensor->pulseCount();
        readings.rpmSource = speedSensor->source();
    }

    if (loadSensor) {
        readings.load = loadSensor->readLoad();
        readings.loadSource = loadSensor->source();
    }

    if (trackingSensor) {
        readings.trackingPosition = trackingSensor->readTrackingDeviation();
        readings.trackingSource = trackingSensor->source();
    }

    return readings;
}

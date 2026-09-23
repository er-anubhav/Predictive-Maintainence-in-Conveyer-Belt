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
        readings.vibRms = vibSensor->readRms();
        readings.vibPeak = vibSensor->readPeak();
        readings.vibKurtosis = vibSensor->readKurtosis();
    } else {
        readings.vibRms = 0.0f; readings.vibPeak = 0.0f; readings.vibKurtosis = 3.0f;
    }

    readings.acousticRms = acousticSensor ? acousticSensor->readAcousticRms() : 0.0f;
    readings.temperature = tempSensor ? tempSensor->readTemperature() : 25.0f;
    readings.beltSpeed = speedSensor ? speedSensor->readSpeed() : 0.0f;
    readings.load = loadSensor ? loadSensor->readLoad() : 0.0f;
    readings.trackingPosition = trackingSensor ? trackingSensor->readTrackingDeviation() : 0.0f;

    return readings;
}

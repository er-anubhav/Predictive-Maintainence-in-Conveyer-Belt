#pragma once
#include <Arduino.h>
#include "sensors/vibration_sensor.h"
#include "sensors/temperature_sensor.h"
#include "sensors/acoustic_sensor.h"
#include "sensors/speed_sensor.h"
#include "sensors/load_sensor.h"
#include "sensors/tracking_sensor.h"

struct SensorReadings {
    VibrationWindow vibration;
    float acousticRms = NAN;
    float temperature = NAN;
    float rpm = NAN;
    float beltSpeed = NAN;
    uint32_t pulseCount = 0;
    float load = NAN;
    float trackingPosition = NAN;

    const char* vibrationSource = SENSOR_SOURCE_UNAVAILABLE;
    const char* temperatureSource = SENSOR_SOURCE_UNAVAILABLE;
    const char* rpmSource = SENSOR_SOURCE_UNAVAILABLE;
    const char* loadSource = SENSOR_SOURCE_UNAVAILABLE;
    const char* trackingSource = SENSOR_SOURCE_UNAVAILABLE;
};

class TelemetryCollector {
public:
    TelemetryCollector(VibrationSensor*, TemperatureSensor*, AcousticSensor*,
                       SpeedSensor*, LoadSensor*, TrackingSensor*);
    bool begin();
    SensorReadings sampleAll();

private:
    VibrationSensor* vibSensor;
    TemperatureSensor* tempSensor;
    AcousticSensor* acousticSensor;
    SpeedSensor* speedSensor;
    LoadSensor* loadSensor;
    TrackingSensor* trackingSensor;
};

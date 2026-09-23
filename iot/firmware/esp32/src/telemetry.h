#pragma once
#include "sensors/vibration_sensor.h"
#include "sensors/temperature_sensor.h"
#include "sensors/acoustic_sensor.h"
#include "sensors/speed_sensor.h"
#include "sensors/load_sensor.h"
#include "sensors/tracking_sensor.h"
#include "packet/packet_builder.h"

class TelemetryCollector {
private:
    VibrationSensor* vibSensor;
    TemperatureSensor* tempSensor;
    AcousticSensor* acousticSensor;
    SpeedSensor* speedSensor;
    LoadSensor* loadSensor;
    TrackingSensor* trackingSensor;

public:
    TelemetryCollector(
        VibrationSensor* vib,
        TemperatureSensor* temp,
        AcousticSensor* acoustic,
        SpeedSensor* speed,
        LoadSensor* load,
        TrackingSensor* tracking
    );

    bool begin();
    SensorReadings sampleAll();
};

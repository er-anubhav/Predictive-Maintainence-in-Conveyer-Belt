#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

struct SensorReadings {
    float vibRms;
    float vibPeak;
    float vibKurtosis;
    float acousticRms;
    float temperature;
    float beltSpeed;
    float load;
    float trackingPosition;
};

class PacketBuilder {
private:
    const char* nodeId;
    const char* conveyorId;
    uint32_t sequence;

public:
    PacketBuilder(const char* nId, const char* cId, uint32_t initialSequence = 1000);

    // Increments sequence and builds Canonical JSON string (version "1.0")
    String buildTelemetryPacket(const SensorReadings& readings, const char* isoTimestamp = nullptr);

    uint32_t getCurrentSequence() const { return sequence; }
};

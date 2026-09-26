#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include "../telemetry.h"

class PacketBuilder {
public:
    PacketBuilder(const char* nodeId, const char* conveyorId);
    bool begin();
    String buildTelemetryPacket(const SensorReadings&, int wifiRssi, bool wifiConnected);
    uint32_t getCurrentSequence() const { return sequence; }

private:
    const char* nodeId;
    const char* conveyorId;
    uint32_t sequence = 0;
    uint32_t reservedUntil = 0;
    Preferences preferences;
    bool ready = false;
    void reserveSequenceBlock();
};

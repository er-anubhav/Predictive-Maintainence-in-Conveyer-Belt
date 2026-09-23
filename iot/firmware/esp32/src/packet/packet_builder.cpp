#include "packet_builder.h"
#include "../config.h"

PacketBuilder::PacketBuilder(const char* nId, const char* cId, uint32_t initialSequence)
    : nodeId(nId), conveyorId(cId), sequence(initialSequence) {}

String PacketBuilder::buildTelemetryPacket(const SensorReadings& readings, const char* isoTimestamp) {
    sequence++;

    JsonDocument doc;

    doc["schema_version"] = SCHEMA_VERSION;
    doc["node_id"] = nodeId;
    doc["conveyor_id"] = conveyorId;

    if (isoTimestamp && strlen(isoTimestamp) > 0) {
        doc["timestamp"] = isoTimestamp;
    } else {
        // Fallback epoch representation or uptime marker
        char timeBuf[32];
        unsigned long sec = millis() / 1000;
        snprintf(timeBuf, sizeof(timeBuf), "2026-09-21T%02lu:%02lu:%02luZ", (sec / 3600) % 24, (sec / 60) % 60, sec % 60);
        doc["timestamp"] = timeBuf;
    }

    doc["sequence"] = sequence;

    // Vibration block
    JsonObject vib = doc["vibration"].to<JsonObject>();
    vib["rms"] = round(readings.vibRms * 1000.0) / 1000.0;
    vib["peak"] = round(readings.vibPeak * 100.0) / 100.0;
    vib["kurtosis"] = round(readings.vibKurtosis * 100.0) / 100.0;

    // Acoustic block
    JsonObject acoustic = doc["acoustic"].to<JsonObject>();
    acoustic["rms"] = round(readings.acousticRms * 1000.0) / 1000.0;

    // Direct metrics
    doc["temperature"] = round(readings.temperature * 10.0) / 10.0;
    doc["belt_speed"] = round(readings.beltSpeed * 100.0) / 100.0;
    doc["load"] = round(readings.load * 10.0) / 10.0;
    doc["tracking_position"] = round(readings.trackingPosition * 10.0) / 10.0;

    String output;
    serializeJson(doc, output);
    return output;
}

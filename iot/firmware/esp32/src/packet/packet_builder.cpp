#include "packet_builder.h"
#include "../config.h"
#include <time.h>
#include <math.h>

PacketBuilder::PacketBuilder(const char* id, const char* conv)
    : nodeId(id), conveyorId(conv) {}

bool PacketBuilder::begin() {
    if (!preferences.begin(SEQUENCE_NAMESPACE, false)) {
        Serial.println("[SEQ] NVS unavailable; using volatile sequence.");
        sequence = 1000;
        reservedUntil = 0;
        ready = false;
        return false;
    }

    sequence = preferences.getULong("next_seq", 1000000UL);
    if (sequence < 1000000UL) {
        sequence = 1000000UL;
    }
    reservedUntil = sequence + SEQUENCE_BLOCK_SIZE - 1;
    preferences.putULong("next_seq", reservedUntil + 1);
    ready = true;

    Serial.printf("[SEQ] Reserved block %lu-%lu.\n",
                  static_cast<unsigned long>(sequence),
                  static_cast<unsigned long>(reservedUntil));
    return true;
}

void PacketBuilder::reserveSequenceBlock() {
    sequence = preferences.getULong("next_seq", reservedUntil + 1);
    reservedUntil = sequence + SEQUENCE_BLOCK_SIZE - 1;
    preferences.putULong("next_seq", reservedUntil + 1);
}

String PacketBuilder::buildTelemetryPacket(
    const SensorReadings& readings,
    int wifiRssi,
    bool wifiConnected
) {
    if (ready && sequence >= reservedUntil) reserveSequenceBlock();
    ++sequence;

    const time_t now = time(nullptr);
    const bool synced = now >= 1700000000;

    char timestamp[32];
    if (synced) {
        struct tm utc;
        gmtime_r(&now, &utc);
        strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", &utc);
    } else {
        strcpy(timestamp, "1970-01-01T00:00:00Z");
    }

    JsonDocument doc;
    doc["schema_version"] = SCHEMA_VERSION;
    doc["node_id"] = nodeId;
    doc["conveyor_id"] = conveyorId;
    doc["timestamp"] = timestamp;
    doc["timestamp_source"] = synced ? "NTP" : "UNSYNCED";
    doc["sequence"] = sequence;

    JsonObject vib = doc["vibration"].to<JsonObject>();
    if (readings.vibration.valid) {
        vib["rms"] = readings.vibration.rms;
        vib["peak"] = readings.vibration.peak;
        vib["kurtosis"] = readings.vibration.kurtosis;
        vib["crest_factor"] = readings.vibration.crestFactor;
        vib["dominant_frequency_hz"] = readings.vibration.dominantFrequencyHz;
        vib["spectral_energy"] = readings.vibration.spectralEnergy;
        vib["sample_rate_hz"] = VIBRATION_SAMPLE_RATE_HZ;
    } else {
        vib["quality"] = "UNAVAILABLE";
    }

#if TRANSMIT_RAW_VIBRATION
    JsonArray raw = doc["raw_samples"].to<JsonArray>();
    const size_t count = min(readings.vibration.count,
                             static_cast<size_t>(MAX_RAW_VIBRATION_SAMPLES));
    for (size_t i = 0; i < count; ++i) raw.add(readings.vibration.samples[i]);
    doc["sample_rate_hz"] = VIBRATION_SAMPLE_RATE_HZ;
#endif

    if (isfinite(readings.acousticRms)) doc["acoustic_rms"] = readings.acousticRms;
    if (isfinite(readings.temperature)) doc["temperature"] = readings.temperature;
    if (isfinite(readings.rpm)) doc["rpm"] = readings.rpm;
    doc["pulse_count"] = readings.pulseCount;
    if (isfinite(readings.beltSpeed)) doc["belt_speed"] = readings.beltSpeed;
    if (isfinite(readings.load)) doc["load"] = readings.load;
    if (isfinite(readings.trackingPosition)) doc["tracking_position"] = readings.trackingPosition;

    doc["source"] = readings.vibrationSource;

    JsonObject sources = doc["sensor_sources"].to<JsonObject>();
    sources["vibration"] = readings.vibrationSource;
    sources["temperature"] = readings.temperatureSource;
    sources["rpm"] = readings.rpmSource;
    sources["load"] = readings.loadSource;
    sources["tracking"] = readings.trackingSource;

    JsonObject health = doc["device_health"].to<JsonObject>();
    health["wifi_rssi"] = wifiRssi;
    health["wifi_connected"] = wifiConnected;
    health["uptime_ms"] = millis();
    health["free_heap"] = ESP.getFreeHeap();
    health["firmware_version"] = FIRMWARE_VERSION;

    String output;
    serializeJson(doc, output);
    return output;
}

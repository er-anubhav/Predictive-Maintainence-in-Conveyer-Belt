#include <Arduino.h>
#include "config.h"
#include "network.h"
#include "telemetry.h"
#include "packet/packet_builder.h"

// Instantiate sensor drivers (Mocks for Phase 2 hardware development)
MockVibrationSensor mockVibration(0.41f, 1.20f, 3.05f);
MockTemperatureSensor mockTemperature(42.5f);
MockAcousticSensor mockAcoustic(0.28f);
MockSpeedSensor mockSpeed(2.80f);
MockLoadSensor mockLoad(72.0f);
MockTrackingSensor mockTracking(0.2f);

// Instantiate subsystem managers
TelemetryCollector collector(
    &mockVibration,
    &mockTemperature,
    &mockAcoustic,
    &mockSpeed,
    &mockLoad,
    &mockTracking
);

PacketBuilder packetBuilder(NODE_ID, CONVEYOR_ID, 1000);
NetworkManager network(WIFI_SSID, WIFI_PASSWORD, GATEWAY_HOST, GATEWAY_PORT, GATEWAY_INGEST_PATH);

unsigned long lastSampleTime = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("==================================================");
    Serial.println(" SIH 26008: ESP32 CONVEYOR SENSOR NODE FIRMWARE  ");
    Serial.printf(" Node ID: %s | Conveyor: %s | Schema: %s\n", NODE_ID, CONVEYOR_ID, SCHEMA_VERSION);
    Serial.println("==================================================");

    // 1. Initialize sensor hardware interfaces
    if (!collector.begin()) {
        Serial.println("[ERR] One or more sensor drivers failed initialization.");
    }

    // 2. Connect to local mining gallery network / gateway access point
    network.connectWiFi();

    Serial.println("[READY] Entering autonomous edge sampling loop...");
}

void loop() {
    unsigned long now = millis();

    if (now - lastSampleTime >= SAMPLING_INTERVAL_MS) {
        lastSampleTime = now;

        // 1. Sample all attached sensors
        SensorReadings readings = collector.sampleAll();

        // 2. Build canonical JSON packet (sequence incremented automatically)
        String packetJson = packetBuilder.buildTelemetryPacket(readings);
        uint32_t currentSeq = packetBuilder.getCurrentSequence();

        Serial.printf("\n[SAMPLE #%u] Vib RMS: %.3fg | Temp: %.1fC | Speed: %.2fm/s | Load: %.1f%% | Track: %+.1fmm\n",
            currentSeq, readings.vibRms, readings.temperature, readings.beltSpeed, readings.load, readings.trackingPosition);

        // 3. Transmit packet to local Edge Gateway
        int httpCode = network.sendTelemetryToGateway(packetJson);

        if (httpCode == 202) {
            Serial.printf("[STATUS] Sequence #%u Queued by Gateway for central uplink.\n", currentSeq);
        } else if (httpCode == 200) {
            Serial.printf("[STATUS] Sequence #%u Acknowledged as duplicate by Gateway.\n", currentSeq);
        } else {
            Serial.printf("[WARN] Gateway unreachable (Code: %d). Continuing sampling autonomously.\n", httpCode);
        }
    }

    // Yield to FreeRTOS scheduler
    delay(10);
}

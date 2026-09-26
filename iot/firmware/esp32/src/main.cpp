#include <Arduino.h>
#include <esp_system.h>

#include "config.h"
#include "network.h"
#include "telemetry.h"
#include "packet/packet_builder.h"

#if VIBRATION_SOURCE == 1
ADXL345VibrationSensor vibrationSensor;
#else
MockVibrationSensor vibrationSensor;
#endif

#if TEMPERATURE_SOURCE == 1
MLX90614TemperatureSensor temperatureSensor;
#else
MockTemperatureSensor temperatureSensor;
#endif

MockAcousticSensor acousticSensor;

#if SPEED_SOURCE == 1
IRPulseSpeedSensor speedSensor;
#else
MockSpeedSensor speedSensor;
#endif

#if LOAD_SOURCE == 1
AnalogTorqueLoadProxy loadSensor;
#else
MockLoadSensor loadSensor;
#endif

#if TRACKING_SOURCE == 1
DigitalIRTrackingSensor trackingSensor;
#else
MockTrackingSensor trackingSensor;
#endif

TelemetryCollector collector(
    &vibrationSensor, &temperatureSensor, &acousticSensor,
    &speedSensor, &loadSensor, &trackingSensor
);

PacketBuilder packetBuilder(NODE_ID, CONVEYOR_ID);

NetworkManager network(
    WIFI_SSID, WIFI_PASSWORD,
    GATEWAY_HOST, GATEWAY_PORT, GATEWAY_INGEST_PATH
);

unsigned long lastTelemetryMs = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("==================================================");
    Serial.println(" SIH 26008 ESP32 CONVEYOR SENSOR NODE");
    Serial.println("==================================================");
    Serial.printf("Firmware=%s Node=%s Conveyor=%s\n",
                  FIRMWARE_VERSION, NODE_ID, CONVEYOR_ID);
    Serial.printf("Vibration=%s Temperature=%s RPM=%s Load=%s Tracking=%s\n",
                  vibrationSensor.source(), temperatureSensor.source(),
                  speedSensor.source(), loadSensor.source(),
                  trackingSensor.source());

    randomSeed(esp_random());

    const bool sensorsOk = collector.begin();
    Serial.printf("[BOOT] Sensor initialization: %s\n",
                  sensorsOk ? "PASS" : "PARTIAL / CHECK SOURCES");

    packetBuilder.begin();
    network.connectWiFi();

    Serial.println("[READY] Sampling loop started.");
}

void loop() {
    const unsigned long now = millis();
    if (now - lastTelemetryMs < TELEMETRY_INTERVAL_MS) {
        delay(5);
        return;
    }
    lastTelemetryMs = now;

    SensorReadings readings = collector.sampleAll();

    const String packet = packetBuilder.buildTelemetryPacket(
        readings, network.wifiRssi(), network.isConnected()
    );

    const uint32_t sequence = packetBuilder.getCurrentSequence();

    Serial.printf(
        "[SAMPLE #%lu] source=%s vib_rms=%.3f peak=%.3f kurt=%.2f "
        "temp=%.2f rpm=%.1f speed=%.2f load=%.1f track=%+.1f\n",
        static_cast<unsigned long>(sequence),
        readings.vibrationSource,
        readings.vibration.rms,
        readings.vibration.peak,
        readings.vibration.kurtosis,
        readings.temperature,
        readings.rpm,
        readings.beltSpeed,
        readings.load,
        readings.trackingPosition
    );

    const int code = network.sendTelemetryToGateway(packet);

    if (code == 202) {
        Serial.printf("[STATUS] Sequence #%lu accepted by gateway.\n",
                      static_cast<unsigned long>(sequence));
    } else if (code == 200) {
        Serial.printf("[STATUS] Sequence #%lu duplicate acknowledged.\n",
                      static_cast<unsigned long>(sequence));
    } else {
        Serial.printf("[WARN] Uplink unavailable (HTTP=%d); sample retained in RAM only.\n",
                      code);
    }
}

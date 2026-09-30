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

#if MOTOR_CONTROL_ENABLED == 1
#include "motor_driver.h"
L298NMotorDriver conveyorMotor(MOTOR_ENA_PIN, MOTOR_IN1_PIN, MOTOR_IN2_PIN);
#endif

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

#if MOTOR_CONTROL_ENABLED == 1
    conveyorMotor.begin();
    conveyorMotor.forward(MOTOR_DEFAULT_SPEED);
#endif

    packetBuilder.begin();
    network.begin();

    Serial.println("[READY] Initialization complete.");
}

void loop() {
    if (network.isProvisioning()) {
        network.handlePortal();
    } else {
        network.maintainConnection();
    }

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

    // Emit canonical JSON telemetry packet over Serial
    Serial.println(packet);

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

    if (network.isConnected()) {
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
}

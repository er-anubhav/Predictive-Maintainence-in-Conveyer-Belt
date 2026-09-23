# Edge Gateway Module

## Future Purpose
The `gateway/` module represents the industrial IoT edge compute tier connecting distributed field nodes to the central backend.

In subsequent phases, this component will:
- Collect real-time telemetry from multiple ESP32 sensor nodes over RS-485 / Industrial LoRa / BLE Mesh / WiFi.
- Perform local buffering and offline store-and-forward when mine network connectivity is intermittent.
- Run edge ingestion services (MQTT broker client, Kafka/Pulsar producers, or HTTPS batch forwarders).
- Execute lightweight edge signal preprocessing and fast-trip emergency stop alarms.

*Note: In Milestone 1, telemetry is injected via the software simulator directly into the FastAPI backend.*

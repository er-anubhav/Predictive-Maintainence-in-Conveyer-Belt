#pragma once

// Network Configuration
#define WIFI_SSID "Mining_Gallery_Mesh_04"
#define WIFI_PASSWORD "IndustrialSecurePass2026"
#define WIFI_CONNECT_TIMEOUT_MS 10000

// Edge Gateway Configuration (Local Ingestion Tier)
#define GATEWAY_HOST "192.168.1.100"
#define GATEWAY_PORT 9000
#define GATEWAY_INGEST_PATH "/ingest"
#define HTTP_TIMEOUT_MS 3000

// Node Identity & Assignment
#define NODE_ID "NODE-001"
#define CONVEYOR_ID "Conveyor-01"
#define SCHEMA_VERSION "1.0"

// Telemetry Sampling Configuration
#define SAMPLING_INTERVAL_MS 2000
#define RETRY_BACKOFF_MS 1000

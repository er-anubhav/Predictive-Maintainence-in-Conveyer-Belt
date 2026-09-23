#pragma once
#include <Arduino.h>

class NetworkManager {
private:
    const char* ssid;
    const char* password;
    const char* gatewayHost;
    int gatewayPort;
    const char* ingestPath;

public:
    NetworkManager(const char* s, const char* p, const char* gHost, int gPort, const char* path);

    bool connectWiFi();
    bool isConnected();

    // Sends serialized telemetry JSON to Gateway /ingest endpoint
    // Returns HTTP status code (e.g. 202, 200) or negative on error
    int sendTelemetryToGateway(const String& jsonPayload);
};

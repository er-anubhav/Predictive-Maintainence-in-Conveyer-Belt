#pragma once
#include <Arduino.h>

class NetworkManager {
public:
    NetworkManager(const char* ssid, const char* password,
                   const char* host, int port, const char* path);
    bool connectWiFi();
    bool maintainConnection();
    bool isConnected() const;
    int wifiRssi() const;
    int sendTelemetryToGateway(const String& jsonPayload);

private:
    const char* ssid;
    const char* password;
    const char* gatewayHost;
    int gatewayPort;
    const char* ingestPath;
    unsigned long lastReconnectAttempt = 0;
};

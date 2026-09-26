#pragma once
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <Preferences.h>

class NetworkManager {
public:
    NetworkManager(const char* defaultSsid, const char* defaultPassword,
                   const char* defaultHost, int defaultPort, const char* path);

    bool begin();
    bool connectWiFi();
    bool maintainConnection();
    bool isConnected() const;
    int wifiRssi() const;
    int sendTelemetryToGateway(const String& jsonPayload);

    // Captive Portal & Web Provisioning
    void startProvisioningPortal();
    void handlePortal();
    bool isProvisioning() const { return provisioningMode; }
    void stopProvisioningPortal();
    void resetStoredCredentials();

    String getActiveSsid() const { return activeSsid; }
    String getGatewayHost() const { return activeGatewayHost; }
    int getGatewayPort() const { return activeGatewayPort; }

private:
    const char* fallbackSsid;
    const char* fallbackPassword;
    const char* fallbackHost;
    int fallbackPort;
    const char* ingestPath;

    String activeSsid;
    String activePassword;
    String activeGatewayHost;
    int activeGatewayPort;

    bool provisioningMode = false;
    bool shouldConnectAfterSave = false;
    unsigned long lastReconnectAttempt = 0;

    WebServer server{80};
    DNSServer dnsServer;
    Preferences preferences;

    void setupWebServer();
    void handleRoot();
    void handleSave();
    void handleNotFound();
    String buildPortalHtml();
};

#include "network.h"
#include "config.h"
#include <WiFi.h>
#include <HTTPClient.h>

NetworkManager::NetworkManager(const char* s, const char* p, const char* gHost, int gPort, const char* path)
    : ssid(s), password(p), gatewayHost(gHost), gatewayPort(gPort), ingestPath(path) {}

bool NetworkManager::connectWiFi() {
    Serial.printf("[NET] Connecting to WiFi SSID: %s ...\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_CONNECT_TIMEOUT_MS) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[NET] WiFi Connected successfully!");
        Serial.printf("[NET] IP Address: %s | RSSI: %d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
        return true;
    } else {
        Serial.println("\n[NET] WiFi Connection Timed out. Operating in offline/retry mode.");
        return false;
    }
}

bool NetworkManager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

int NetworkManager::sendTelemetryToGateway(const String& jsonPayload) {
    if (!isConnected()) {
        Serial.println("[NET] WiFi disconnected. Skipping uplink transmission.");
        return -1;
    }

    HTTPClient http;
    String url = String("http://") + gatewayHost + ":" + gatewayPort + ingestPath;

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    int httpCode = http.POST(jsonPayload);

    if (httpCode > 0) {
        String responseBody = http.getString();
        Serial.printf("[UPLINK] Gateway responded HTTP %d: %s\n", httpCode, responseBody.c_str());
    } else {
        Serial.printf("[UPLINK] Failed to connect to Gateway at %s (Error: %s)\n", url.c_str(), http.errorToString(httpCode).c_str());
    }

    http.end();
    return httpCode;
}

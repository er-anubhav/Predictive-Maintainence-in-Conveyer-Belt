#include "network.h"
#include "config.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>

NetworkManager::NetworkManager(const char* s, const char* p,
                               const char* host, int port, const char* path)
    : ssid(s), password(p), gatewayHost(host), gatewayPort(port), ingestPath(path) {}

bool NetworkManager::connectWiFi() {
    if (!ssid || strlen(ssid) == 0) {
        Serial.println("[NET] WiFi credentials not configured.");
        return false;
    }

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    const unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED &&
           millis() - start < WIFI_CONNECT_TIMEOUT_MS) {
        delay(250);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\n[NET] WiFi connection timeout; continuing offline.");
        return false;
    }

    Serial.printf("\n[NET] WiFi connected: %s RSSI=%d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());

    configTime(0, 0, "pool.ntp.org", "time.nist.gov");

    const unsigned long ntpStart = millis();
    while (time(nullptr) < 1700000000 &&
           millis() - ntpStart < NTP_SYNC_TIMEOUT_MS) {
        delay(250);
    }

    Serial.printf("[NET] NTP: %s\n",
                  time(nullptr) >= 1700000000 ? "SYNCED" : "NOT_SYNCED");
    lastReconnectAttempt = millis();
    return true;
}

bool NetworkManager::maintainConnection() {
    if (isConnected()) return true;
    const unsigned long now = millis();
    if (now - lastReconnectAttempt < WIFI_RETRY_INTERVAL_MS) return false;
    lastReconnectAttempt = now;
    return connectWiFi();
}

bool NetworkManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}

int NetworkManager::wifiRssi() const {
    return isConnected() ? WiFi.RSSI() : -127;
}

int NetworkManager::sendTelemetryToGateway(const String& jsonPayload) {
    if (!maintainConnection()) return -1;

    HTTPClient http;
    const String url = String("http://") + gatewayHost + ":" +
                       gatewayPort + ingestPath;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    const int code = http.POST(jsonPayload);
    if (code < 0) {
        Serial.printf("[UPLINK] %s\n", http.errorToString(code).c_str());
    } else {
        Serial.printf("[UPLINK] HTTP %d\n", code);
    }
    http.end();
    return code;
}

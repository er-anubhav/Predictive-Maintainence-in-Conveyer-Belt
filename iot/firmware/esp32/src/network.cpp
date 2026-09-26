#include "network.h"
#include "config.h"
#include <HTTPClient.h>
#include <time.h>

NetworkManager::NetworkManager(const char* defaultSsid, const char* defaultPassword,
                               const char* defaultHost, int defaultPort, const char* path)
    : fallbackSsid(defaultSsid), fallbackPassword(defaultPassword),
      fallbackHost(defaultHost), fallbackPort(defaultPort), ingestPath(path),
      activeSsid(defaultSsid ? defaultSsid : ""),
      activePassword(defaultPassword ? defaultPassword : ""),
      activeGatewayHost(defaultHost ? defaultHost : GATEWAY_HOST),
      activeGatewayPort(defaultPort > 0 ? defaultPort : 9000) {}

bool NetworkManager::begin() {
    preferences.begin(PROVISIONING_NAMESPACE, false);
    String storedSsid = preferences.getString("ssid", "");
    String storedPass = preferences.getString("pass", "");
    String storedHost = preferences.getString("host", "");
    int storedPort = preferences.getInt("port", 0);
    preferences.end();

    if (storedSsid.length() > 0) {
        activeSsid = storedSsid;
        activePassword = storedPass;
        if (storedHost.length() > 0) activeGatewayHost = storedHost;
        if (storedPort > 0) activeGatewayPort = storedPort;
        Serial.printf("[NET] Loaded stored credentials for SSID: '%s'\n", activeSsid.c_str());
    } else if (fallbackSsid && strlen(fallbackSsid) > 0) {
        activeSsid = String(fallbackSsid);
        activePassword = String(fallbackPassword ? fallbackPassword : "");
        activeGatewayHost = String(fallbackHost ? fallbackHost : GATEWAY_HOST);
        activeGatewayPort = fallbackPort;
        Serial.printf("[NET] Using fallback credentials for SSID: '%s'\n", activeSsid.c_str());
    }

    if (activeSsid.length() == 0) {
        Serial.println("[NET] No Wi-Fi credentials found. Launching Captive Portal...");
        startProvisioningPortal();
        return false;
    }

    Serial.printf("[NET] Attempting connection to '%s'...\n", activeSsid.c_str());
    if (!connectWiFi()) {
        Serial.println("[NET] Initial Wi-Fi connection failed. Launching Captive Portal...");
        startProvisioningPortal();
        return false;
    }

    return true;
}

bool NetworkManager::connectWiFi() {
    if (activeSsid.length() == 0) return false;

    WiFi.disconnect(true);
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.begin(activeSsid.c_str(), activePassword.c_str());

    Serial.printf("[NET] Connecting to Wi-Fi '%s'", activeSsid.c_str());
    const unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - start < WIFI_CONNECT_TIMEOUT_MS)) {
        delay(300);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\n[NET] Wi-Fi connection timed out.");
        return false;
    }

    Serial.printf("\n[NET] Wi-Fi connected! IP: %s (RSSI: %d dBm)\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());

    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    const unsigned long ntpStart = millis();
    while (time(nullptr) < 1700000000 && (millis() - ntpStart < NTP_SYNC_TIMEOUT_MS)) {
        delay(250);
    }

    Serial.printf("[NET] NTP Time: %s\n",
                  time(nullptr) >= 1700000000 ? "SYNCED" : "UNSYNCED");
    lastReconnectAttempt = millis();
    return true;
}

bool NetworkManager::maintainConnection() {
    if (provisioningMode) return false;
    if (isConnected()) return true;

    const unsigned long now = millis();
    if (now - lastReconnectAttempt < WIFI_RETRY_INTERVAL_MS) return false;
    lastReconnectAttempt = now;

    Serial.println("[NET] Reconnecting Wi-Fi...");
    return connectWiFi();
}

bool NetworkManager::isConnected() const {
    return !provisioningMode && (WiFi.status() == WL_CONNECTED);
}

int NetworkManager::wifiRssi() const {
    return isConnected() ? WiFi.RSSI() : -127;
}

int NetworkManager::sendTelemetryToGateway(const String& jsonPayload) {
    if (provisioningMode) return -1;
    if (!maintainConnection()) return -1;

    HTTPClient http;
    const String url = String("http://") + activeGatewayHost + ":" +
                       String(activeGatewayPort) + ingestPath;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    const int code = http.POST(jsonPayload);
    if (code < 0) {
        Serial.printf("[UPLINK] Failed url=%s Error: %s\n", url.c_str(), http.errorToString(code).c_str());
    } else {
        Serial.printf("[UPLINK] HTTP %d (Sent to %s)\n", code, url.c_str());
    }
    http.end();
    return code;
}

void NetworkManager::startProvisioningPortal() {
    provisioningMode = true;
    WiFi.disconnect(true);
    delay(100);

    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID_NAME, AP_PASSWORD);

    Serial.println("\n==================================================");
    Serial.println(" SIH 26008 WI-FI SETUP HOTSPOT ACTIVE");
    Serial.println("==================================================");
    Serial.printf(" 1. Connect your Phone/PC to Wi-Fi: '%s'\n", AP_SSID_NAME);
    Serial.println(" 2. Open your web browser at:      http://192.168.4.1");
    Serial.println(" 3. Select your Wi-Fi, enter password, and save.");
    Serial.println("==================================================\n");

    dnsServer.start(53, "*", WiFi.softAPIP());
    setupWebServer();
    server.begin();
}

void NetworkManager::handlePortal() {
    if (!provisioningMode) return;

    dnsServer.processNextRequest();
    server.handleClient();

    if (shouldConnectAfterSave) {
        delay(1500);
        shouldConnectAfterSave = false;
        stopProvisioningPortal();
        if (!connectWiFi()) {
            Serial.println("[NET] Failed to connect with new credentials. Reopening portal...");
            startProvisioningPortal();
        }
    }
}

void NetworkManager::stopProvisioningPortal() {
    server.stop();
    dnsServer.stop();
    WiFi.softAPdisconnect(true);
    provisioningMode = false;
    Serial.println("[PORTAL] Provisioning portal stopped. Returning to station mode.");
}

void NetworkManager::resetStoredCredentials() {
    preferences.begin(PROVISIONING_NAMESPACE, false);
    preferences.clear();
    preferences.end();
    Serial.println("[NET] Cleared stored Wi-Fi credentials from NVS.");
}

void NetworkManager::setupWebServer() {
    server.on("/", HTTP_GET, [this]() { handleRoot(); });
    server.on("/save", HTTP_POST, [this]() { handleSave(); });

    // Captive portal probe redirection
    server.on("/hotspot-detect.html", HTTP_GET, [this]() { handleRoot(); });
    server.on("/generate_204", HTTP_GET, [this]() { handleRoot(); });
    server.on("/gen_204", HTTP_GET, [this]() { handleRoot(); });
    server.on("/ncsi.txt", HTTP_GET, [this]() { handleRoot(); });
    server.on("/canonical.html", HTTP_GET, [this]() { handleRoot(); });

    server.onNotFound([this]() { handleNotFound(); });
}

void NetworkManager::handleNotFound() {
    if (provisioningMode) {
        server.sendHeader("Location", String("http://") + WiFi.softAPIP().toString() + "/", true);
        server.send(302, "text/plain", "");
    } else {
        server.send(404, "text/plain", "Not Found");
    }
}

String NetworkManager::buildPortalHtml() {
    int n = WiFi.scanNetworks();
    String wifiOptions = "";
    if (n == 0) {
        wifiOptions = "<option value=\"\">No networks found (Rescan)</option>";
    } else {
        for (int i = 0; i < n; ++i) {
            String ssidName = WiFi.SSID(i);
            if (ssidName.length() == 0) continue;
            int rssi = WiFi.RSSI(i);
            String enc = (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "🔓" : "🔒";
            wifiOptions += "<option value=\"" + ssidName + "\">" + enc + " " + ssidName + " (" + String(rssi) + " dBm)</option>";
        }
    }
    wifiOptions += "<option value=\"__custom__\">+ Enter Custom / Hidden SSID</option>";

    String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIH 26008 - Sensor Node Wi-Fi Setup</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0b0f19; color: #f1f5f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #131c2e; border: 3px solid #38bdf8; box-shadow: 6px 6px 0px #0284c7; width: 100%; max-width: 440px; padding: 28px; border-radius: 4px; }
        .badge { display: inline-block; background: #0284c7; color: #fff; font-size: 11px; font-weight: 800; letter-spacing: 1px; padding: 4px 8px; text-transform: uppercase; margin-bottom: 12px; }
        h1 { font-size: 22px; font-weight: 800; text-transform: uppercase; color: #ffffff; letter-spacing: 0.5px; margin-bottom: 8px; }
        p.subtitle { color: #94a3b8; font-size: 13px; line-height: 1.5; margin-bottom: 24px; border-bottom: 1px solid #1e293b; padding-bottom: 16px; }
        .field { margin-bottom: 18px; }
        label { display: block; font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px; }
        input, select { width: 100%; background: #0b0f19; border: 2px solid #334155; color: #f8fafc; font-size: 15px; padding: 12px 14px; outline: none; border-radius: 2px; transition: border-color 0.2s; }
        input:focus, select:focus { border-color: #38bdf8; }
        .row { display: flex; gap: 12px; }
        .row .field:first-child { flex: 2; }
        .row .field:last-child { flex: 1; }
        button { width: 100%; background: #38bdf8; color: #0b0f19; border: none; font-size: 15px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; padding: 14px; cursor: pointer; margin-top: 8px; box-shadow: 4px 4px 0px #0284c7; transition: transform 0.1s, box-shadow 0.1s; }
        button:hover { background: #7dd3fc; }
        button:active { transform: translate(2px, 2px); box-shadow: 2px 2px 0px #0284c7; }
        .hint { font-size: 11px; color: #64748b; margin-top: 4px; }
        #customSsidBox { display: none; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">SIH 26008 • Hardware Node</span>
        <h1>Wi-Fi & Gateway Setup</h1>
        <p class="subtitle">Configure local Wi-Fi and target edge gateway for <b>)rawliteral" + String(NODE_ID) + R"rawliteral(</b>.</p>

        <form action="/save" method="POST">
            <div class="field">
                <label>Select 2.4 GHz Network</label>
                <select name="ssid" id="ssidSelect" onchange="checkCustomSsid(this)">
                    )rawliteral" + wifiOptions + R"rawliteral(
                </select>
                <input type="text" name="custom_ssid" id="customSsidBox" placeholder="Type Hidden Wi-Fi Name">
            </div>

            <div class="field">
                <label>Wi-Fi Password</label>
                <input type="password" name="password" placeholder="Leave blank if open">
            </div>

            <div class="row">
                <div class="field">
                    <label>Gateway IP / Host</label>
                    <input type="text" name="host" value=")rawliteral" + activeGatewayHost + R"rawliteral(" required>
                    <div class="hint">PC running Edge Gateway</div>
                </div>
                <div class="field">
                    <label>Port</label>
                    <input type="number" name="port" value=")rawliteral" + String(activeGatewayPort) + R"rawliteral(" required>
                    <div class="hint">Default 9000</div>
                </div>
            </div>

            <button type="submit">Save & Connect to Cloud</button>
        </form>
    </div>

    <script>
        function checkCustomSsid(el) {
            var box = document.getElementById('customSsidBox');
            if (el.value === '__custom__') {
                box.style.display = 'block';
                box.required = true;
                box.focus();
            } else {
                box.style.display = 'none';
                box.required = false;
            }
        }
    </script>
</body>
</html>
)rawliteral";
    return html;
}

void NetworkManager::handleRoot() {
    server.send(200, "text/html", buildPortalHtml());
}

void NetworkManager::handleSave() {
    String selectedSsid = server.arg("ssid");
    if (selectedSsid == "__custom__") {
        selectedSsid = server.arg("custom_ssid");
    }
    String pass = server.arg("password");
    String host = server.arg("host");
    String portStr = server.arg("port");

    if (selectedSsid.length() == 0) {
        server.send(400, "text/html", "<h3>Error: SSID cannot be empty! <a href='/'>Go back</a></h3>");
        return;
    }

    activeSsid = selectedSsid;
    activePassword = pass;
    if (host.length() > 0) activeGatewayHost = host;
    if (portStr.toInt() > 0) activeGatewayPort = portStr.toInt();

    // Persist to NVS Flash
    preferences.begin(PROVISIONING_NAMESPACE, false);
    preferences.putString("ssid", activeSsid);
    preferences.putString("pass", activePassword);
    preferences.putString("host", activeGatewayHost);
    preferences.putInt("port", activeGatewayPort);
    preferences.end();

    Serial.printf("[PORTAL] Saved Configuration: SSID='%s', Host='%s', Port=%d\n",
                  activeSsid.c_str(), activeGatewayHost.c_str(), activeGatewayPort);

    String successHtml = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Configuration Saved</title>
    <style>
        body { background: #0b0f19; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #131c2e; border: 3px solid #10b981; box-shadow: 6px 6px 0px #059669; padding: 32px; border-radius: 4px; max-width: 440px; text-align: center; }
        h2 { color: #10b981; font-size: 24px; text-transform: uppercase; margin-bottom: 12px; }
        p { color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 8px; }
        code { color: #38bdf8; background: #0b0f19; padding: 4px 8px; border-radius: 2px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>✓ Configuration Saved!</h2>
        <p>Connecting to <b>)rawliteral" + activeSsid + R"rawliteral(</b>...</p>
        <p>Telemetry Destination: <code>http://)rawliteral" + activeGatewayHost + ":" + String(activeGatewayPort) + R"rawliteral(/ingest</code></p>
        <p style="margin-top: 16px; color: #64748b;">The ESP32 setup hotspot is shutting down. You can now close this tab.</p>
    </div>
</body>
</html>
)rawliteral";

    server.send(200, "text/html", successHtml);
    shouldConnectAfterSave = true;
}

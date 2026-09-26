#pragma once

#include <Arduino.h>

#if __has_include("secrets.h")
#include "secrets.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID ""
#endif

#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD ""
#endif

#define WIFI_CONNECT_TIMEOUT_MS 10000
#define NTP_SYNC_TIMEOUT_MS 5000
#define WIFI_RETRY_INTERVAL_MS 10000

#ifndef GATEWAY_HOST
#define GATEWAY_HOST "10.255.80.71"
#endif

#ifndef GATEWAY_PORT
#define GATEWAY_PORT 9000
#endif

#ifndef GATEWAY_INGEST_PATH
#define GATEWAY_INGEST_PATH "/ingest"
#endif
#define HTTP_TIMEOUT_MS 3000

#define AP_SSID_NAME "SIH26008-Setup"
#define AP_PASSWORD ""
#define PROVISIONING_NAMESPACE "sih_wifi"

#define NODE_ID "NODE-001"
#define CONVEYOR_ID "Conveyor-01"
#define SCHEMA_VERSION "1.0"
#define FIRMWARE_VERSION "1.1.0"

#define TELEMETRY_INTERVAL_MS 2000

// 0 = simulated, 1 = ADXL345 over I2C
#define VIBRATION_SOURCE 0
#define VIBRATION_SAMPLE_RATE_HZ 800
#define VIBRATION_WINDOW_SAMPLES 800
#define MAX_RAW_VIBRATION_SAMPLES VIBRATION_WINDOW_SAMPLES
#define TRANSMIT_RAW_VIBRATION 1
#define VIBRATION_I2C_ADDRESS 0x53

#define VIBRATION_SIM_MODE_NORMAL 0
#define VIBRATION_SIM_MODE_ANOMALY 1
#define VIBRATION_SIM_MODE VIBRATION_SIM_MODE_NORMAL

#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// 0 = simulated, 1 = MLX90614
#define TEMPERATURE_SOURCE 0
#define MLX90614_I2C_ADDRESS 0x5A

// 0 = simulated, 1 = GPIO pulse input
#define SPEED_SOURCE 1
#define RPM_INPUT_PIN 18
#define PULSES_PER_REVOLUTION 1.0f
#define PULLEY_DIAMETER_M 0.50f
#define RPM_DEBOUNCE_US 1000UL

// 0 = simulated, 1 = analog proxy
#define LOAD_SOURCE 1
#define LOAD_INPUT_PIN 34
#define LOAD_ADC_MAX 4095.0f
#define LOAD_INPUT_VOLTAGE 3.3f
#define LOAD_ZERO_V 0.20f
#define LOAD_FULL_SCALE_V 3.00f
#define LOAD_FULL_SCALE_PERCENT 100.0f

// 0 = simulated, 1 = digital IR edge proxy
#define TRACKING_SOURCE 1
#define TRACKING_INPUT_PIN 27
#define TRACKING_ACTIVE_LOW true
#define TRACKING_ACTIVE_DEVIATION_MM 15.0f
#define TRACKING_ACTIVE_SIGN 1.0f

#define ACOUSTIC_ENABLED 0

#define SENSOR_SOURCE_REAL "REAL_HARDWARE"
#define SENSOR_SOURCE_SIMULATED "SIMULATED"
#define SENSOR_SOURCE_UNAVAILABLE "UNAVAILABLE"

// NVS-reserved sequence blocks avoid reuse after ESP32 reboot.
#define SEQUENCE_NAMESPACE "sih26008"
#define SEQUENCE_BLOCK_SIZE 1000

#pragma once

#include <Arduino.h>
#if __has_include("secrets.h")
#include "secrets.h"
#else
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#endif

// Network
#define WIFI_CONNECT_TIMEOUT_MS 10000
#define NTP_SYNC_TIMEOUT_MS 5000
#define GATEWAY_HOST "192.168.1.100"
#define GATEWAY_PORT 9000
#define GATEWAY_INGEST_PATH "/ingest"
#define HTTP_TIMEOUT_MS 3000

// Node identity
#define NODE_ID "NODE-001"
#define CONVEYOR_ID "Conveyor-01"
#define SCHEMA_VERSION "1.0"
#define FIRMWARE_VERSION "1.1.0"

// Main telemetry cadence
#define TELEMETRY_INTERVAL_MS 2000

// Vibration source:
// 0 = simulated, 1 = ADXL345
#define VIBRATION_SOURCE 0
#define VIBRATION_SAMPLE_RATE_HZ 800
#define VIBRATION_WINDOW_SAMPLES 800
#define VIBRATION_I2C_ADDRESS 0x53
#define VIBRATION_RANGE_G 4.0f

// Simulated vibration profile
#define VIBRATION_SIM_MODE_NORMAL 0
#define VIBRATION_SIM_MODE_ANOMALY 1
#define VIBRATION_SIM_MODE VIBRATION_SIM_MODE_NORMAL

// Shared I2C bus
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// Temperature source:
// 0 = simulated, 1 = MLX90614
#define TEMPERATURE_SOURCE 0
#define MLX90614_I2C_ADDRESS 0x5A

// RPM / belt speed source:
// 0 = simulated, 1 = pulse input
#define SPEED_SOURCE 1
#define RPM_INPUT_PIN 18
#define PULSES_PER_REVOLUTION 1.0f
#define PULLEY_DIAMETER_M 0.50f
#define RPM_DEBOUNCE_US 1000UL

// Load proxy:
// 0 = simulated, 1 = analog torque/current proxy
#define LOAD_SOURCE 1
#define LOAD_INPUT_PIN 34
#define LOAD_ADC_MAX 4095.0f
#define LOAD_INPUT_VOLTAGE 3.3f
#define LOAD_ZERO_V 0.20f
#define LOAD_FULL_SCALE_V 3.00f
#define LOAD_FULL_SCALE_PERCENT 100.0f

// Belt tracking IR:
// 0 = simulated, 1 = digital IR edge detector
#define TRACKING_SOURCE 1
#define TRACKING_INPUT_PIN 27
#define TRACKING_ACTIVE_LOW true
#define TRACKING_ACTIVE_DEVIATION_MM 15.0f
#define TRACKING_ACTIVE_SIGN 1.0f

// Acoustic is retained in the v1.0 packet for backward compatibility.
// No physical acoustic sensor is required for the current POC.
#define ACOUSTIC_ENABLED 0

// Sensor source labels
#define SENSOR_SOURCE_REAL "REAL_HARDWARE"
#define SENSOR_SOURCE_SIMULATED "SIMULATED"
#define SENSOR_SOURCE_UNAVAILABLE "UNAVAILABLE"
#define PACKET_SOURCE "REAL_HARDWARE"

#ifndef SCHEMA_VERSION
#define SCHEMA_VERSION "1.0"
#endif

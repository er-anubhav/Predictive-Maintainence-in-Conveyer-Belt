#pragma once

#include <Arduino.h>
#include "config.h"

/**
 * SIH 26008 — L298N Dual H-Bridge Motor Driver Controller
 * 
 * Electrical Topology:
 * 12V External PSU (+) -----> L298N 12V Motor Power In
 * 12V External PSU (-) -----> L298N GND (Common Reference)
 * ESP32 GND            -----> L298N GND (Common Ground reference)
 * ESP32 3.3V GPIO 25   -----> L298N ENA (PWM Speed Control, 0-255)
 * ESP32 3.3V GPIO 26   -----> L298N IN1 (Direction Control 1)
 * ESP32 3.3V GPIO 33   -----> L298N IN2 (Direction Control 2)
 * L298N OUT1 & OUT2    -----> 12V DC Geared Conveyor Motor
 *
 * SAFETY NOTICE:
 * - ESP32 3.3V logic is strictly isolated from the 12V motor supply.
 * - ESP32 NEVER receives 12V.
 * - Common GND ensures reliable logic threshold detection (>2.3V TTL High).
 */

enum class MotorDirection {
    STOPPED,
    FORWARD,
    REVERSE
};

class L298NMotorDriver {
private:
    uint8_t enaPin;
    uint8_t in1Pin;
    uint8_t in2Pin;
    uint8_t currentSpeed;
    MotorDirection currentDirection;
    bool enabled;

    // ESP32 LEDC PWM Configuration for ENA
    const uint8_t pwmChannel = 0;
    const uint32_t pwmFreq = 5000; // 5 kHz PWM
    const uint8_t pwmResolution = 8; // 8-bit (0-255)

public:
    L298NMotorDriver(uint8_t ena = MOTOR_ENA_PIN, uint8_t in1 = MOTOR_IN1_PIN, uint8_t in2 = MOTOR_IN2_PIN)
        : enaPin(ena), in1Pin(in1), in2Pin(in2),
          currentSpeed(0), currentDirection(MotorDirection::STOPPED), enabled(false) {}

    bool begin() {
        pinMode(in1Pin, OUTPUT);
        pinMode(in2Pin, OUTPUT);
        digitalWrite(in1Pin, LOW);
        digitalWrite(in2Pin, LOW);

        // Configure PWM on ESP32
        ledcSetup(pwmChannel, pwmFreq, pwmResolution);
        ledcAttachPin(enaPin, pwmChannel);
        ledcWrite(pwmChannel, 0);

        enabled = true;
        Serial.printf("[MOTOR] L298N Driver Initialized: ENA=GPIO%d (PWM), IN1=GPIO%d, IN2=GPIO%d\n",
                      enaPin, in1Pin, in2Pin);
        return true;
    }

    void forward(uint8_t speed = 200) {
        if (!enabled) return;
        digitalWrite(in1Pin, HIGH);
        digitalWrite(in2Pin, LOW);
        ledcWrite(pwmChannel, speed);
        currentSpeed = speed;
        currentDirection = MotorDirection::FORWARD;
        Serial.printf("[MOTOR] FORWARD speed=%d/255\n", speed);
    }

    void reverse(uint8_t speed = 200) {
        if (!enabled) return;
        digitalWrite(in1Pin, LOW);
        digitalWrite(in2Pin, HIGH);
        ledcWrite(pwmChannel, speed);
        currentSpeed = speed;
        currentDirection = MotorDirection::REVERSE;
        Serial.printf("[MOTOR] REVERSE speed=%d/255\n", speed);
    }

    void setSpeed(uint8_t speed) {
        if (!enabled) return;
        currentSpeed = speed;
        ledcWrite(pwmChannel, speed);
    }

    void stop() {
        if (!enabled) return;
        digitalWrite(in1Pin, LOW);
        digitalWrite(in2Pin, LOW);
        ledcWrite(pwmChannel, 0);
        currentSpeed = 0;
        currentDirection = MotorDirection::STOPPED;
        Serial.println("[MOTOR] STOP");
    }

    uint8_t getSpeed() const { return currentSpeed; }
    MotorDirection getDirection() const { return currentDirection; }
    const char* getDirectionStr() const {
        switch (currentDirection) {
            case MotorDirection::FORWARD: return "FORWARD";
            case MotorDirection::REVERSE: return "REVERSE";
            default: return "STOPPED";
        }
    }
};

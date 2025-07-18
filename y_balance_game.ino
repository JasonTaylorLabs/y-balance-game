/*
y_balance_game.ino - Arduino Mega Firmware for Y-Balance Game
Reads three U8xLaser distance sensors, streams their readings over USB serial,
and responds to ON/OFF commands for sensor power control. Designed for robust
integration with a Raspberry Pi game UI. Includes command feedback and fault reporting.
Debugging Tips:
- Use the serial monitor to observe CSV output and command feedback.
- -99.99 in output indicates a sensor fault or power-off.
- Check wiring and sensor power if readings are always -99.99.
- Use command feedback (e.g., '1OFF OK') to verify host-Arduino communication.
Author: [Your Name]
*/
#include <U8xLaser.h>

// --- Pin/Serial Config ---
#define PWREN1 6
#define PWREN2 7
#define PWREN3 8
#define BAUD_USB    115200
#define BAUD_SENSOR 19200
#define LOOP_DELAY_MS 10  // ~100 Hz

U8xLaser laser1(Serial1, PWREN1);
U8xLaser laser2(Serial2, PWREN2);
U8xLaser laser3(Serial3, PWREN3);

// --- Helpers ---
float readCMFast(U8xLaser &laser, uint8_t pwrenPin) {
  // Returns the latest fast measurement in cm, or -1.0 if powered off or invalid.
  if (digitalRead(pwrenPin) == LOW) return -1.0;
  int32_t mm = laser.measureResult();
  return (mm > 0) ? (mm / 10.0) : -1.0;
}
void sendCommandFeedback(const String& cmd) {
  // Sends a confirmation string back to the host after processing a command.
  Serial.print(cmd); Serial.println(" OK");
}

// --- Setup ---
void setup() {
  Serial.begin(BAUD_USB);
  while (!Serial);
  pinMode(PWREN1, OUTPUT); digitalWrite(PWREN1, HIGH);
  pinMode(PWREN2, OUTPUT); digitalWrite(PWREN2, HIGH);
  pinMode(PWREN3, OUTPUT); digitalWrite(PWREN3, HIGH);
  Serial1.begin(BAUD_SENSOR);
  Serial2.begin(BAUD_SENSOR);
  Serial3.begin(BAUD_SENSOR);
  delay(100);
  laser1.begin(BAUD_SENSOR);
  laser2.begin(BAUD_SENSOR);
  laser3.begin(BAUD_SENSOR);
  laser1.startMeasureFast();
  laser2.startMeasureFast();
  laser3.startMeasureFast();
  Serial.println("Ready");
}

// --- Main Loop ---
void loop() {
  // 1) Handle ON/OFF commands
  while (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if      (cmd == "1OFF") { digitalWrite(PWREN1, LOW); sendCommandFeedback(cmd); }
    else if (cmd == "1ON")  { digitalWrite(PWREN1, HIGH); sendCommandFeedback(cmd); }
    else if (cmd == "2OFF") { digitalWrite(PWREN2, LOW); sendCommandFeedback(cmd); }
    else if (cmd == "2ON")  { digitalWrite(PWREN2, HIGH); sendCommandFeedback(cmd); }
    else if (cmd == "3OFF") { digitalWrite(PWREN3, LOW); sendCommandFeedback(cmd); }
    else if (cmd == "3ON")  { digitalWrite(PWREN3, HIGH); sendCommandFeedback(cmd); }
  }
  // 2) Read all three at high rate
  float d1 = readCMFast(laser1, PWREN1);
  float d2 = readCMFast(laser2, PWREN2);
  float d3 = readCMFast(laser3, PWREN3);
  // 3) Stream CSV: ID,VALUE (add error code -99.99 for sensor fault)
  Serial.print("1,"); Serial.println((d1 >= 0) ? d1 : -99.99, 2);
  Serial.print("2,"); Serial.println((d2 >= 0) ? d2 : -99.99, 2);
  Serial.print("3,"); Serial.println((d3 >= 0) ? d3 : -99.99, 2);
  delay(LOOP_DELAY_MS);
}
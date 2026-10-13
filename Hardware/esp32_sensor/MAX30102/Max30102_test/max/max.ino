
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 particleSensor;

// ESP32 I2C pins
const byte SDA_PIN = 21;
const byte SCL_PIN = 22;

// Finger detection threshold
const long FINGER_THRESHOLD = 10000;

// BPM averaging
const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
byte rateCount = 0;

unsigned long lastBeatTime = 0;
unsigned long lastPrintTime = 0;

float beatsPerMinute = 0;
float beatAvg = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  Serial.println("Initializing MAX30102...");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("ERROR: MAX30102 not found!");
    while (true) {
      delay(100);
    }
  }

  // LED current, sample averaging, LED mode,
  // sample rate, pulse width, ADC range
  particleSensor.setup(0x1F, 4, 2, 100, 411, 4096);

  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x1F);
  particleSensor.setPulseAmplitudeGreen(0x00);

  Serial.println("MAX30102 READY!");
  Serial.println("Place your finger steadily on the sensor.");
  Serial.println("IR,Status,BPM,Average_BPM");
}

void loop() {
  long irValue = particleSensor.getIR();
  unsigned long now = millis();

  bool beatDetected = false;
  const char* status;

  // Step 1: Finger detection
  if (irValue < FINGER_THRESHOLD) {
    status = "NO_FINGER";

    beatsPerMinute = 0;
    beatAvg = 0;
    rateCount = 0;
    rateSpot = 0;
    lastBeatTime = 0;
  } else {
    status = "FINGER_OK";

    // Step 2: Detect heartbeat
    if (checkForBeat((int32_t)irValue)) {
      beatDetected = true;

      if (lastBeatTime != 0) {
        unsigned long delta = now - lastBeatTime;

        if (delta > 0) {
          float measuredBPM = 60000.0f / delta;

          // Accept plausible adult resting/active heart rates
          if (measuredBPM >= 40 && measuredBPM <= 200) {
            beatsPerMinute = measuredBPM;

            rates[rateSpot] = (byte)measuredBPM;
            rateSpot = (rateSpot + 1) % RATE_SIZE;

            if (rateCount < RATE_SIZE) {
              rateCount++;
            }

            // Average only valid readings
            int total = 0;
            for (byte i = 0; i < rateCount; i++) {
              total += rates[i];
            }

            beatAvg = (float)total / rateCount;
          }
        }
      }

      lastBeatTime = now;
    }

    // Step 3: Reset stale reading if no beat arrives
    if (lastBeatTime != 0 && now - lastBeatTime > 5000) {
      beatsPerMinute = 0;
      beatAvg = 0;
      rateCount = 0;
      rateSpot = 0;
      lastBeatTime = 0;
    }
  }

  // Step 4: Print results every 100 ms
  if (now - lastPrintTime >= 100) {
    Serial.print(irValue);
    Serial.print(",");
    Serial.print(status);
    Serial.print(",");

    if (beatsPerMinute > 0) {
      Serial.print(beatsPerMinute, 1);
    } else {
      Serial.print("--");
    }

    Serial.print(",");

    if (beatAvg > 0) {
      Serial.println(beatAvg, 1);
    } else {
      Serial.println("--");
    }

    lastPrintTime = now;
  }

  delay(10);
}

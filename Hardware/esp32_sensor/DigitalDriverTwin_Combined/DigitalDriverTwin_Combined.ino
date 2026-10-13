
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

const byte SDA_PIN = 21;
const byte SCL_PIN = 22;
const byte MPU_ADDR = 0x68;

const int32_t GYRO_OFFSET_X = 157;
const int32_t GYRO_OFFSET_Y = 621;
const int32_t GYRO_OFFSET_Z = -82;
const long FINGER_THRESHOLD = 10000;

MAX30105 particleSensor;

const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
byte rateCount = 0;

unsigned long lastBeatTime = 0;
unsigned long lastMpuTime = 0;

float bpm = 0;
float avgBpm = 0;

bool readMPU(int16_t &ax, int16_t &ay, int16_t &az,
             int16_t &gx, int16_t &gy, int16_t &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, (uint8_t)14) != 14) {
    while (Wire.available()) Wire.read();
    return false;
  }

  byte d[14];
  for (int i = 0; i < 14; i++) d[i] = Wire.read();

  ax = (int16_t)((d[0] << 8) | d[1]);
  ay = (int16_t)((d[2] << 8) | d[3]);
  az = (int16_t)((d[4] << 8) | d[5]);
  gx = (int16_t)((d[8] << 8) | d[9]);
  gy = (int16_t)((d[10] << 8) | d[11]);
  gz = (int16_t)((d[12] << 8) | d[13]);

  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  // Initialise MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("ERROR: MAX30102 not found");
    while (true) delay(100);
  }

  particleSensor.setup(0x1F, 4, 2, 100, 411, 4096);
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x1F);
  particleSensor.setPulseAmplitudeGreen(0x00);

  // Wake and configure MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  if (Wire.endTransmission() != 0) {
    Serial.println("ERROR: MPU6050 not found");
    while (true) delay(100);
  }

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1B);
  Wire.write(0x00);
  Wire.endTransmission();

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);
  Wire.write(0x00);
  Wire.endTransmission();

  delay(500);

  // One CSV header only. No debug messages after this.
  Serial.println(
    "esp_ms,ax_raw,ay_raw,az_raw,"
    "gx_corrected,gy_corrected,gz_corrected,"
    "ir_raw,finger_status,bpm,avg_bpm"
  );
}

void loop() {
  unsigned long now = millis();

  // Read MAX30102 frequently
  long irValue = particleSensor.getIR();

  if (irValue < FINGER_THRESHOLD) {
    bpm = 0;
    avgBpm = 0;
    rateCount = 0;
    rateSpot = 0;
    lastBeatTime = 0;
  } else {
    if (checkForBeat((int32_t)irValue)) {
      if (lastBeatTime != 0) {
        unsigned long delta = now - lastBeatTime;
        if (delta > 0) {
          float measured = 60000.0f / delta;

          if (measured >= 40 && measured <= 200) {
            bpm = measured;
            rates[rateSpot] = (byte)measured;
            rateSpot = (rateSpot + 1) % RATE_SIZE;

            if (rateCount < RATE_SIZE) rateCount++;

            int total = 0;
            for (byte i = 0; i < rateCount; i++) {
              total += rates[i];
            }
            avgBpm = (float)total / rateCount;
          }
        }
      }
      lastBeatTime = now;
    }

    if (lastBeatTime != 0 && now - lastBeatTime > 5000) {
      bpm = 0;
      avgBpm = 0;
      rateCount = 0;
      rateSpot = 0;
      lastBeatTime = 0;
    }
  }

  // Output one synchronised row every 100 ms
  if (now - lastMpuTime >= 100) {
    lastMpuTime = now;

    int16_t ax, ay, az, gx, gy, gz;

    if (readMPU(ax, ay, az, gx, gy, gz)) {
      Serial.print(now);
      Serial.print(',');
      Serial.print(ax);
      Serial.print(',');
      Serial.print(ay);
      Serial.print(',');
      Serial.print(az);
      Serial.print(',');
      Serial.print((int32_t)gx - GYRO_OFFSET_X);
      Serial.print(',');
      Serial.print((int32_t)gy - GYRO_OFFSET_Y);
      Serial.print(',');
      Serial.print((int32_t)gz - GYRO_OFFSET_Z);
      Serial.print(',');
      Serial.print(irValue);
      Serial.print(',');
      Serial.print(irValue >= FINGER_THRESHOLD ? "FINGER_OK" : "NO_FINGER");
      Serial.print(',');
      Serial.print(bpm, 1);
      Serial.print(',');
      Serial.println(avgBpm, 1);
    } else {
      Serial.println("MPU_READ_ERROR");
    }
  }

  delay(5);
}

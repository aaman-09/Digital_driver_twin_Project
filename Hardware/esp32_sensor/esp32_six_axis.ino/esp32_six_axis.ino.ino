
#include <Wire.h>

const byte MPU_ADDR = 0x68;

// Gyroscope zero offsets from your calibration
const int32_t GYRO_OFFSET_X = 157;
const int32_t GYRO_OFFSET_Y = 621;
const int32_t GYRO_OFFSET_Z = -82;

void writeRegister(byte reg, byte value) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

bool readSixAxis(
  int16_t &ax, int16_t &ay, int16_t &az,
  int16_t &gx, int16_t &gy, int16_t &gz
) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(MPU_ADDR, (uint8_t)14) != 14) {
    while (Wire.available()) Wire.read();
    return false;
  }

  byte d[14];

  for (int i = 0; i < 14; i++) {
    d[i] = Wire.read();
  }

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
  Wire.begin(21, 22);

  delay(500);

  writeRegister(0x6B, 0x00); // Wake sensor
  writeRegister(0x1B, 0x00); // Gyro +/- 250 deg/s
  writeRegister(0x1C, 0x00); // Accelerometer +/- 2g

  delay(500);

  Serial.println("AX,AY,AZ,GX,GY,GZ");
}

void loop() {
  int16_t ax, ay, az, gx, gy, gz;

  if (readSixAxis(ax, ay, az, gx, gy, gz)) {
    Serial.print(ax);
    Serial.print(",");
    Serial.print(ay);
    Serial.print(",");
    Serial.print(az);
    Serial.print(",");
    Serial.print((int32_t)gx - GYRO_OFFSET_X);
    Serial.print(",");
    Serial.print((int32_t)gy - GYRO_OFFSET_Y);
    Serial.print(",");
    Serial.println((int32_t)gz - GYRO_OFFSET_Z);
  } else {
    Serial.println("READ_ERROR");
  }

  delay(1000);
}

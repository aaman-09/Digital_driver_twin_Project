import random


class IMUSensor:

    def __init__(self):
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0

    def read_data(self):

        self.yaw = random.uniform(-5, 5)
        self.pitch = random.uniform(-3, 3)
        self.roll = random.uniform(-3, 3)

        return {
            "yaw": round(self.yaw, 2),
            "pitch": round(self.pitch, 2),
            "roll": round(self.roll, 2)
        }


if __name__ == "__main__":

    imu = IMUSensor()

    data = imu.read_data()

    print("IMU Sensor Data:")
    print(data)
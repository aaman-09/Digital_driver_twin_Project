import random


class VehicleSensor:

    def __init__(self):
        self.speed = 0.0
        self.acceleration = 0.0
        self.braking = False
        self.steering_angle = 0.0

    def read_data(self):

        self.speed = random.uniform(20, 100)
        self.acceleration = random.uniform(-2.5, 2.5)
        self.braking = self.acceleration < -1.5
        self.steering_angle = random.uniform(-30, 30)

        return {
            "speed": round(self.speed, 2),
            "acceleration": round(self.acceleration, 2),
            "braking": self.braking,
            "steering_angle": round(self.steering_angle, 2)
        }


if __name__ == "__main__":

    vehicle = VehicleSensor()

    data = vehicle.read_data()

    print("Vehicle Sensor Data:")
    print(data)
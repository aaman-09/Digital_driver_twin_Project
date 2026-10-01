from src.sensors.imu_sensor import IMUSensor
from src.sensors.vehicle_sensor import VehicleSensor


class SensorFusion:

    def __init__(self):
        self.imu = IMUSensor()
        self.vehicle = VehicleSensor()

    def get_combined_data(self):

        imu_data = self.imu.read_data()
        vehicle_data = self.vehicle.read_data()

        return {
            "imu": imu_data,
            "vehicle": vehicle_data
        }


if __name__ == "__main__":

    fusion = SensorFusion()

    data = fusion.get_combined_data()

    print("Combined Sensor Data:")
    print(data)
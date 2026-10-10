
import csv
import time
import serial
from pathlib import Path
from datetime import datetime

PORT = "COM3"
BAUD_RATE = 115200

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "data" / "hardware"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "esp32_sensor_log.csv"


def main():
    print("Connecting to ESP32...")

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=2) as esp32:
            time.sleep(2)
            esp32.reset_input_buffer()

            print(f"Connected to {PORT}")
            print(f"CSV file: {LOG_FILE}")
            print("Recording sensor data. Press Ctrl+C to stop.\n")

            with LOG_FILE.open(
                "a", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)

                if file.tell() == 0:
                    writer.writerow([
                        "timestamp",
                        "ax_raw", "ay_raw", "az_raw",
                        "gx_corrected", "gy_corrected",
                        "gz_corrected"
                    ])

                while True:
                    line = esp32.readline().decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not line or line == "AX,AY,AZ,GX,GY,GZ":
                        continue

                    values = line.split(",")

                    if len(values) != 6:
                        continue

                    try:
                        ax, ay, az, gx, gy, gz = map(int, values)
                    except ValueError:
                        continue

                    timestamp = datetime.now().isoformat(
                        timespec="milliseconds"
                    )

                    writer.writerow([
                        timestamp, ax, ay, az, gx, gy, gz
                    ])
                    file.flush()

                    print(
                        f"AX={ax:6d} AY={ay:6d} AZ={az:6d} | "
                        f"GX={gx:6d} GY={gy:6d} GZ={gz:6d}"
                    )

    except serial.SerialException as error:
        print(f"Serial connection error: {error}")
        print("Check COM3 and close Arduino Serial Monitor.")

    except KeyboardInterrupt:
        print("\nRecording stopped. CSV data saved.")


if __name__ == "__main__":
    main()

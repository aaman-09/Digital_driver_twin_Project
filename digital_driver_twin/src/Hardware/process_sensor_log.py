
import csv
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "hardware" / "esp32_sensor_log.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "hardware" / "esp32_sensor_processed.csv"
)

ACCEL_SCALE = 16384.0
GYRO_SCALE = 131.0


def main():
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return

    processed_count = 0

    with INPUT_FILE.open("r", newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)

        with OUTPUT_FILE.open(
            "w", newline="", encoding="utf-8"
        ) as destination:
            columns = [
                "timestamp",
                "ax_g", "ay_g", "az_g",
                "gx_dps", "gy_dps", "gz_dps",
                "accel_magnitude_g",
                "pitch_deg", "roll_deg",
            ]

            writer = csv.DictWriter(
                destination, fieldnames=columns
            )
            writer.writeheader()

            for row in reader:
                try:
                    ax = int(row["ax_raw"]) / ACCEL_SCALE
                    ay = int(row["ay_raw"]) / ACCEL_SCALE
                    az = int(row["az_raw"]) / ACCEL_SCALE

                    gx = int(row["gx_corrected"]) / GYRO_SCALE
                    gy = int(row["gy_corrected"]) / GYRO_SCALE
                    gz = int(row["gz_corrected"]) / GYRO_SCALE

                    magnitude = math.sqrt(
                        ax * ax + ay * ay + az * az
                    )

                    pitch = math.degrees(
                        math.atan2(
                            ax, math.sqrt(ay * ay + az * az)
                        )
                    )

                    roll = math.degrees(math.atan2(ay, az))

                    writer.writerow({
                        "timestamp": row["timestamp"],
                        "ax_g": round(ax, 4),
                        "ay_g": round(ay, 4),
                        "az_g": round(az, 4),
                        "gx_dps": round(gx, 3),
                        "gy_dps": round(gy, 3),
                        "gz_dps": round(gz, 3),
                        "accel_magnitude_g": round(magnitude, 4),
                        "pitch_deg": round(pitch, 2),
                        "roll_deg": round(roll, 2),
                    })

                    processed_count += 1

                except (ValueError, KeyError, TypeError):
                    continue

    print(f"Processed rows: {processed_count}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

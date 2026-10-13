
from pathlib import Path
import pandas as pd
import numpy as np

# Project root: D:\Project\digital_driver_twin
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "hardware"
    / "esp32_combined_sensor_log.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "hardware"
    / "esp32_combined_sensor_processed.csv"
)

# MPU6050 configured ranges:
# Accelerometer = +/- 2g
# Gyroscope = +/- 250 degrees/second
ACCEL_SCALE = 16384.0
GYRO_SCALE = 131.0

def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input CSV not found:\n{INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "timestamp",
        "esp_ms",
        "ax_raw",
        "ay_raw",
        "az_raw",
        "gx_corrected",
        "gy_corrected",
        "gz_corrected",
        "ir_raw",
        "finger_status",
        "bpm",
        "avg_bpm",
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        print("ERROR: Missing columns:", missing)
        print("Available columns:", list(df.columns))
        return

    # Convert sensor columns to numeric values.
    numeric_columns = [
        "ax_raw", "ay_raw", "az_raw",
        "gx_corrected", "gy_corrected", "gz_corrected",
        "ir_raw", "bpm", "avg_bpm",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 1. Acceleration: raw counts -> g
    df["accel_x_g"] = df["ax_raw"] / ACCEL_SCALE
    df["accel_y_g"] = df["ay_raw"] / ACCEL_SCALE
    df["accel_z_g"] = df["az_raw"] / ACCEL_SCALE

    # Total acceleration magnitude.
    df["accel_magnitude_g"] = np.sqrt(
        df["accel_x_g"] ** 2
        + df["accel_y_g"] ** 2
        + df["accel_z_g"] ** 2
    )

    # 2. Gyroscope: corrected raw counts -> degrees/second
    df["gyro_x_dps"] = df["gx_corrected"] / GYRO_SCALE
    df["gyro_y_dps"] = df["gy_corrected"] / GYRO_SCALE
    df["gyro_z_dps"] = df["gz_corrected"] / GYRO_SCALE

    # 3. Accelerometer-based tilt estimates.
    # These are sensor tilt angles, NOT camera head-pose angles.
    ax = df["accel_x_g"]
    ay = df["accel_y_g"]
    az = df["accel_z_g"]

    df["tilt_pitch_deg"] = np.degrees(
        np.arctan2(-ax, np.sqrt(ay**2 + az**2))
    )

    df["tilt_roll_deg"] = np.degrees(
        np.arctan2(ay, az)
    )

    # 4. Heart-rate validity.
    # BPM=0 means no valid beat was reported in that row.
    df["bpm_valid"] = (
        (df["finger_status"] == "FINGER_OK")
        & df["bpm"].between(40, 200)
    )

    df["avg_bpm_valid"] = (
        (df["finger_status"] == "FINGER_OK")
        & df["avg_bpm"].between(40, 200)
    )

    # Preserve original readings and write a separate processed file.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nPROCESSING COMPLETED")
    print(f"Rows processed: {len(df)}")
    print(f"Output file:\n{OUTPUT_FILE}")

    print("\nProcessed sample:")
    display_columns = [
        "timestamp",
        "accel_magnitude_g",
        "gyro_x_dps",
        "gyro_y_dps",
        "gyro_z_dps",
        "ir_raw",
        "bpm",
        "bpm_valid",
    ]
    print(df[display_columns].head(10).to_string(index=False))


if __name__ == "__main__":
    main()


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

LOG_FILE = LOG_DIR / "esp32_combined_sensor_log.csv"
RISK_FILE = LOG_DIR / "current_risk.txt"

COLUMNS = [
    "timestamp", "esp_ms",
    "ax_raw", "ay_raw", "az_raw",
    "gx_corrected", "gy_corrected", "gz_corrected",
    "ir_raw", "finger_status", "bpm", "avg_bpm"
]


def read_risk_command():
    try:
        risk = RISK_FILE.read_text(encoding="utf-8").strip().upper()
        if risk in ("LOW", "MEDIUM", "HIGH", "OFF"):
            return risk
    except OSError:
        pass

    return None


def main():
    print("Connecting to ESP32...")

    last_risk = None
    last_risk_check = 0.0

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=0.2) as esp32:
            time.sleep(2)
            esp32.reset_input_buffer()

            print(f"Connected: {PORT} at {BAUD_RATE}")
            print(f"Saving sensor data to: {LOG_FILE}")
            print(f"Reading dashboard risk from: {RISK_FILE}")
            print("Press Ctrl+C to stop.\n")

            with LOG_FILE.open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(file, fieldnames=COLUMNS)
                writer.writeheader()
                file.flush()

                while True:
                    now = time.monotonic()

                    # Check dashboard's latest risk every 0.5 seconds.
                    if now - last_risk_check >= 0.5:
                        last_risk_check = now
                        risk = read_risk_command()

                        if risk is not None and risk != last_risk:
                            esp32.write(f"RISK:{risk}\n".encode("ascii"))
                            esp32.flush()
                            last_risk = risk
                            print(f"\nDashboard risk sent to ESP32: {risk}")

                    line = esp32.readline().decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not line or line.startswith("esp_ms,"):
                        continue

                    values = line.split(",")

                    if len(values) != 11:
                        if "ERROR" in line:
                            print(f"ESP32: {line}")
                        continue

                    try:
                        esp_ms = int(values[0])
                        ax, ay, az, gx, gy, gz = map(int, values[1:7])
                        ir = int(values[7])
                        status = values[8]
                        bpm = float(values[9])
                        avg_bpm = float(values[10])
                    except ValueError:
                        continue

                    row = {
                        "timestamp": datetime.now().isoformat(
                            timespec="milliseconds"
                        ),
                        "esp_ms": esp_ms,
                        "ax_raw": ax,
                        "ay_raw": ay,
                        "az_raw": az,
                        "gx_corrected": gx,
                        "gy_corrected": gy,
                        "gz_corrected": gz,
                        "ir_raw": ir,
                        "finger_status": status,
                        "bpm": bpm,
                        "avg_bpm": avg_bpm,
                    }

                    writer.writerow(row)
                    file.flush()

                    print(
                        f"IR={ir:7d} | {status:9s} | "
                        f"BPM={bpm:5.1f} | AVG={avg_bpm:5.1f} | "
                        f"ACC=({ax:6d},{ay:6d},{az:6d})"
                    )

    except serial.SerialException as error:
        print(f"Serial connection error: {error}")
        print("Close Arduino Serial Monitor and check COM3.")

    except KeyboardInterrupt:
        print("\nRecording stopped. CSV data saved.")


if __name__ == "__main__":
    main()

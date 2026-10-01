from flask import Flask, render_template, jsonify, Response
import csv
import os
import time

from src.analysis.driver_behavior import analyze_session
from src.sensors.sensor_fusion import SensorFusion
from src.analysis.risk_engine import RiskEngine


app = Flask(__name__)

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "driver_session.csv"
)

FRAME_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "latest_frame.jpg"
)


# Sensor Fusion
sensor_fusion = SensorFusion()
risk_engine = RiskEngine()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


def get_latest_driver_data():

    default_data = {
        "ear": 0.0,
        "perclos": 0.0,
        "mar": 0.0,
        "yawns": 0,
        "pitch": 0.0,
        "yaw": 0.0,
        "roll": 0.0,
        "drowsiness_score": 0.0,
        "risk_level": "LOW",
        "distraction_detected": False,
        "distraction_duration": 0.0
    }

    if not os.path.exists(CSV_FILE):
        return default_data

    try:

        with open(CSV_FILE, "r", newline="") as file:

            reader = csv.DictReader(file)
            rows = list(reader)

        if not rows:
            return default_data

        latest = rows[-1]

        return {
            "ear": float(latest["ear"]),
            "perclos": float(latest["perclos"]),
            "mar": float(latest["mar"]),
            "yawns": int(latest["yawns"]),
            "pitch": float(latest["pitch"]),
            "yaw": float(latest["yaw"]),
            "roll": float(latest["roll"]),
            "drowsiness_score": float(latest["drowsiness_score"]),
            "risk_level": latest["risk_level"],
            "distraction_detected": latest["distraction_detected"] == "True",
            "distraction_duration": float(latest["distraction_duration"])
        }

    except Exception as e:

        print("CSV ERROR:", e)
        return default_data


@app.route("/api/status")
def status():

    driver_data = get_latest_driver_data()

    sensor_data = sensor_fusion.get_combined_data()

    imu_data = sensor_data["imu"]
    vehicle_data = sensor_data["vehicle"]

    risk_data = risk_engine.calculate_risk(
        driver_data,
        imu_data,
        vehicle_data
    )

    return jsonify({

        **driver_data,
        
        "driver": driver_data,

        "imu": imu_data,

        "vehicle": vehicle_data,

        "overall_risk": risk_data

    })

@app.route("/api/behavior")
def behavior():

    result = analyze_session(CSV_FILE)

    if result is None:

        return jsonify({
            "error": "No session data available"
        })

    return jsonify(result)


def generate_frames():

    while True:

        if os.path.exists(FRAME_FILE):

            try:

                with open(FRAME_FILE, "rb") as image_file:

                    frame = image_file.read()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            except Exception:
                pass

        time.sleep(0.05)


@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )
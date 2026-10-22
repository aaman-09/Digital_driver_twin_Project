from flask import Flask, render_template, jsonify, Response, request
import csv
import os
import time
import joblib
import pandas as pd

from src.analysis.driver_behavior import analyze_session
from src.fusion.driver_profiles import (
    get_all_profiles,
    create_driver_profile
)


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

#H/w code added here
HARDWARE_CSV = os.path.join(
    BASE_DIR, "data", "hardware", "esp32_combined_sensor_log.csv"
)

# Experimental ML condition classifier
AI_MODEL_PATH = os.path.join(
    BASE_DIR, "models", "ml_condition_classifier.joblib"
)

_ai_bundle = None


def get_ai_prediction(driver_data):
    global _ai_bundle

    unavailable = {
        "available": False,
        "condition": "UNAVAILABLE",
        "confidence": None,
        "note": "Experimental AI prediction unavailable."
    }

    try:
        if not os.path.exists(AI_MODEL_PATH):
            return unavailable

        if _ai_bundle is None:
            _ai_bundle = joblib.load(AI_MODEL_PATH)

        features = _ai_bundle["features"]
        model = _ai_bundle["model"]

        values = {
            key: float(driver_data[key])
            for key in features
        }

        X = pd.DataFrame([values], columns=features)
        prediction = str(model.predict(X)[0])

        confidence = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X)[0]
            confidence = round(float(max(probabilities)), 3)

        return {
            "available": True,
            "condition": prediction,
            "confidence": confidence,
            "note": (
                "Experimental classification of simulated test conditions. "
                "Not medically validated; does not change safety risk."
            )
        }

    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        print("AI MODEL ERROR:", e)
        return unavailable


def get_latest_hardware_data():
    default = {
        "connected": False,
        "finger_status": "NO_DATA",
        "bpm": None,
        "avg_bpm": None,
        "accel_g": None,
        "gyro_x": None,
        "gyro_y": None,
        "gyro_z": None,
        "ir_raw": None
    }

    try:
        with open(HARDWARE_CSV, "r", newline="") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            return default

        row = rows[-1]

        ax = int(row["ax_raw"])
        ay = int(row["ay_raw"])
        az = int(row["az_raw"])

        finger_ok = row["finger_status"] == "FINGER_OK"
        bpm = float(row["bpm"])
        avg_bpm = float(row["avg_bpm"])

        return {
            "connected": True,
            "finger_status": row["finger_status"],
            "bpm": bpm if finger_ok and 40 <= bpm <= 200 else None,
            "avg_bpm": avg_bpm if finger_ok and 40 <= avg_bpm <= 200 else None,
            "accel_g": round(((ax**2 + ay**2 + az**2)**0.5) / 16384, 3),
            "gyro_x": round(int(row["gx_corrected"]) / 131, 2),
            "gyro_y": round(int(row["gy_corrected"]) / 131, 2),
            "gyro_z": round(int(row["gz_corrected"]) / 131, 2),
            "ir_raw": int(row["ir_raw"])
        }

    except (OSError, ValueError, KeyError):
        return default


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
    hardware_data = get_latest_hardware_data()
    ai_prediction = get_ai_prediction(driver_data)

    # Camera-based risk only.
    # This is NOT a validated combined driver-health risk score.
    camera_risk = {
        "risk_score": driver_data["drowsiness_score"],
        "risk_level": driver_data["risk_level"],
        "basis": "camera_drowsiness_only"
    }

    return jsonify({

        **driver_data,

        "driver": driver_data,

        # No real vehicle IMU/OBD sensor is connected yet.
        "imu": {
            "available": False,
            "message": "Dedicated vehicle IMU data unavailable"
        },

        "vehicle": {
            "available": False,
            "message": "Vehicle speed, braking and steering sensors not connected"
        },

        "overall_risk": camera_risk,

        "hardware": hardware_data,

        "ai_prediction": ai_prediction,

        "unified_driver_state": {
            **driver_data,
            "hardware_connected": hardware_data["connected"],
            "finger_status": hardware_data["finger_status"],
            "bpm": hardware_data["bpm"],
            "avg_bpm": hardware_data["avg_bpm"],
            "accel_g": hardware_data["accel_g"],
            "gyro_x": hardware_data["gyro_x"],
            "gyro_y": hardware_data["gyro_y"],
            "gyro_z": hardware_data["gyro_z"],
            "ir_raw": hardware_data["ir_raw"],
            "data_sources": {
                "camera": True,
                "hardware": hardware_data["connected"]
            }
}

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


@app.route("/api/profiles", methods=["GET"])
def list_driver_profiles():
    """Return all saved driver profiles."""
    try:
        return jsonify({
            "success": True,
            "profiles": get_all_profiles()
        })
    except (OSError, csv.Error) as e:
        print("DRIVER PROFILE ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Could not load driver profiles."
        }), 500


@app.route("/api/profiles", methods=["POST"])
def add_driver_profile():
    """Create a driver profile from dashboard input."""
    data = request.get_json(silent=True) or {}

    name = data.get("name", "")
    notes = data.get("notes", "")

    if not isinstance(name, str) or not isinstance(notes, str):
        return jsonify({
            "success": False,
            "message": "Name and notes must be text."
        }), 400

    success, message = create_driver_profile(name, notes)

    if not success:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    profiles = get_all_profiles()
    created_profile = next(
        (
            profile for profile in profiles
            if profile["name"].casefold() == name.strip().casefold()
        ),
        None
    )

    return jsonify({
        "success": True,
        "message": message,
        "profile": created_profile,
        "profiles": profiles
    }), 201


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )
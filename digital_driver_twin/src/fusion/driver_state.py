driver_state = {
    # Camera / vision data
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
    "distraction_duration": 0.0,

    # ESP32 / hardware data
    "hardware_connected": False,
    "finger_status": "NO_DATA",
    "bpm": None,
    "avg_bpm": None,
    "accel_g": None,
    "gyro_x": None,
    "gyro_y": None,
    "gyro_z": None,
    "ir_raw": None,

    # Integration metadata
    "data_sources": {
        "camera": False,
        "hardware": False
    }
}
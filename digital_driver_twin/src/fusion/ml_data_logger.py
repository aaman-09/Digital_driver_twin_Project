
import csv
import os
from datetime import datetime


class MLDataLogger:
    """Save camera features with an explicit test-condition label."""

    COLUMNS = [
        "timestamp",
        "session_id",
        "condition_label",
        "ear",
        "perclos",
        "mar",
        "yawns",
        "pitch",
        "yaw",
        "roll",
        "drowsiness_score",
        "risk_level",
        "distraction_detected",
        "distraction_duration",
    ]

    def __init__(self, file_path="data/processed/ml_driver_sessions.csv"):
        self.file_path = file_path
        self.session_id = None
        self.condition_label = None

        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        # Create a header only for a new/empty file.
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(self.COLUMNS)

    def start_session(self, condition_label):
        allowed = {
            "normal",
            "simulated_eye_closure",
            "simulated_distraction",
        }

        if condition_label not in allowed:
            raise ValueError(
                f"condition_label must be one of: {sorted(allowed)}"
            )

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.condition_label = condition_label
        return self.session_id

    def stop_session(self):
        self.session_id = None
        self.condition_label = None

    def log(
        self,
        ear,
        perclos,
        mar,
        yawns,
        pitch,
        yaw,
        roll,
        drowsiness_score,
        risk_level,
        distraction_detected,
        distraction_duration,
    ):
        # Do not collect rows until a session has been explicitly started.
        if self.session_id is None or self.condition_label is None:
            return

        row = [
            datetime.now().isoformat(timespec="seconds"),
            self.session_id,
            self.condition_label,
            round(float(ear), 4),
            round(float(perclos), 2),
            round(float(mar), 4),
            int(yawns),
            round(float(pitch), 2),
            round(float(yaw), 2),
            round(float(roll), 2),
            round(float(drowsiness_score), 2),
            str(risk_level),
            bool(distraction_detected),
            round(float(distraction_duration), 2),
        ]

        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

import csv
import os
from datetime import datetime


class DataLogger:

    def __init__(self, file_path):

        self.file_path = file_path

        # Create parent folder if it doesn't exist

        parent_folder = os.path.dirname(
            self.file_path
        )

        if parent_folder:
            os.makedirs(
                parent_folder,
                exist_ok=True
            )

        # Create CSV + header if it doesn't exist

        if not os.path.exists(self.file_path):

            with open(
                self.file_path,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
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
                    "distraction_duration"
                ])


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
        distraction_duration
    ):

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        with open(
            self.file_path,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                round(ear, 4),
                round(perclos, 2),
                round(mar, 4),
                yawns,
                round(pitch, 2),
                round(yaw, 2),
                round(roll, 2),
                round(drowsiness_score, 2),
                risk_level,
                distraction_detected,
                round(distraction_duration, 2)
            ])
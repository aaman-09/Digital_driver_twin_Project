import csv
import os
from datetime import datetime


def analyze_session(file_path):

    if not os.path.exists(file_path):
        print("CSV file not found!")
        return None

    with open(file_path, "r", newline="") as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        print("CSV file is empty!")
        return None

    # --------------------------------------------------
    # BASIC DATA
    # --------------------------------------------------

    timestamps = [
        datetime.fromisoformat(row["timestamp"])
        for row in rows
    ]

    yaws = [
        float(row["yaw"])
        for row in rows
    ]

    drowsiness_scores = [
        float(row["drowsiness_score"])
        for row in rows
    ]

    yawns = [
        int(row["yawns"])
        for row in rows
    ]

    # --------------------------------------------------
    # SESSION TIME
    # --------------------------------------------------

    session_duration = (
        timestamps[-1] - timestamps[0]
    ).total_seconds()

    # --------------------------------------------------
    # DISTRACTION ANALYSIS
    # --------------------------------------------------

    distraction_events = 0
    total_distraction_duration = 0.0

    previous_distraction = False

    for row in rows:

        current_distraction = (
            row["distraction_detected"] == "True"
        )

        # Count only False -> True transition
        if current_distraction and not previous_distraction:
            distraction_events += 1

        if current_distraction:
            total_distraction_duration += float(
                row["distraction_duration"]
            )

        previous_distraction = current_distraction

    # --------------------------------------------------
    # DRIVER BEHAVIOUR METRICS
    # --------------------------------------------------

    average_yaw = sum(yaws) / len(yaws)

    maximum_yaw = max(
        abs(yaw)
        for yaw in yaws
    )

    average_drowsiness = (
        sum(drowsiness_scores)
        / len(drowsiness_scores)
    )

    maximum_drowsiness = max(
        drowsiness_scores
    )

    total_yawns = max(yawns)

    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    result = {

        "session_duration": round(
            session_duration,
            2
        ),

        "distraction_events": distraction_events,

        "total_distraction_duration": round(
            total_distraction_duration,
            2
        ),

        "average_yaw": round(
            average_yaw,
            2
        ),

        "maximum_yaw": round(
            maximum_yaw,
            2
        ),

        "average_drowsiness": round(
            average_drowsiness,
            2
        ),

        "maximum_drowsiness": round(
            maximum_drowsiness,
            2
        ),

        "total_yawns": total_yawns
    }

    return result


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    BASE_DIR = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        )
    )

    CSV_FILE = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "driver_session.csv"
    )

    result = analyze_session(CSV_FILE)

    if result:

        print("\n===================================")
        print("     DRIVER BEHAVIOUR ANALYSIS")
        print("===================================")

        print(
            "Session Duration:",
            result["session_duration"],
            "seconds"
        )

        print(
            "Distraction Events:",
            result["distraction_events"]
        )

        print(
            "Total Distraction Duration:",
            result["total_distraction_duration"],
            "seconds"
        )

        print(
            "Average Yaw:",
            result["average_yaw"],
            "degrees"
        )

        print(
            "Maximum Yaw:",
            result["maximum_yaw"],
            "degrees"
        )

        print(
            "Average Drowsiness:",
            result["average_drowsiness"]
        )

        print(
            "Maximum Drowsiness:",
            result["maximum_drowsiness"]
        )

        print(
            "Total Yawns:",
            result["total_yawns"]
        )

        print("===================================\n")
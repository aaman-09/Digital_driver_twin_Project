import cv2
import mediapipe as mp
import numpy as np
import math
import time
import os

from src.fusion.driver_state import driver_state
from src.fusion.drowsiness_engine import DrowsinessEngine
from src.fusion.smoothing import ExponentialSmoother
from src.fusion.data_logger import DataLogger
from src.fusion.ml_data_logger import MLDataLogger


# ============================================================
# HELPER FUNCTION
# ============================================================

def distance(point1, point2):
    return math.sqrt(
        (point1.x - point2.x) ** 2 +
        (point1.y - point2.y) ** 2
    )


# ============================================================
# EAR CALCULATION
# ============================================================

def calculate_ear(landmarks, eye_indices):

    p1 = landmarks[eye_indices[0]]
    p2 = landmarks[eye_indices[1]]
    p3 = landmarks[eye_indices[2]]
    p4 = landmarks[eye_indices[3]]
    p5 = landmarks[eye_indices[4]]
    p6 = landmarks[eye_indices[5]]

    vertical_1 = distance(p2, p6)
    vertical_2 = distance(p3, p5)

    horizontal = distance(p1, p4)

    return (
        vertical_1 + vertical_2
    ) / (2.0 * horizontal)


# ============================================================
# MAR CALCULATION
# ============================================================

def calculate_mar(landmarks):

    left_corner = landmarks[61]

    right_corner = landmarks[291]

    upper_lip = landmarks[13]

    lower_lip = landmarks[14]


    horizontal = distance(
        left_corner,
        right_corner
    )


    vertical = distance(
        upper_lip,
        lower_lip
    )


    if horizontal == 0:

        return 0.0


    return vertical / horizontal


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

BaseOptions = mp.tasks.BaseOptions

FaceLandmarker = (
    mp.tasks.vision.FaceLandmarker
)

FaceLandmarkerOptions = (
    mp.tasks.vision.FaceLandmarkerOptions
)

RunningMode = (
    mp.tasks.vision.RunningMode
)


options = FaceLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=
        "models/mediapipe/face_landmarker.task"
    ),

    running_mode=RunningMode.IMAGE,

    num_faces=1
)


landmarker = (
    FaceLandmarker.create_from_options(
        options
    )
)


# ============================================================
# DROWSINESS ENGINE
# ============================================================

engine = DrowsinessEngine()
smoother = ExponentialSmoother(alpha=0.2)

# Existing logger — keep the original dataset unchanged
logger = DataLogger(
    "data/processed/driver_session.csv"
)

# Separate logger for explicitly labelled ML test sessions
ml_logger = MLDataLogger(
    "data/processed/ml_driver_sessions.csv"
)


# ============================================================
# CAMERA
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

FRAME_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "latest_frame.jpg"
)



camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Could not open webcam.")

    exit()


print("===================================")
print("DIGITAL DRIVER TWIN")
print("REAL-TIME DRIVER MONITOR")
print("===================================")
print("Press Q to quit.")


# ============================================================
# PARAMETERS
# ============================================================

EAR_THRESHOLD = 0.20

MAR_THRESHOLD = 0.60

YAWN_DURATION = 1.0

PERCLOS_WINDOW = 30.0


# ============================================================
# EYE LANDMARKS
# ============================================================

LEFT_EYE = [
    33,
    160,
    158,
    133,
    153,
    144
]


RIGHT_EYE = [
    362,
    385,
    387,
    263,
    373,
    380
]


# ============================================================
# HEAD POSE LANDMARKS
# ============================================================

NOSE = 1

CHIN = 152

LEFT_EYE_POSE = 33

RIGHT_EYE_POSE = 263

LEFT_MOUTH = 61

RIGHT_MOUTH = 291


# ============================================================
# TRACKING VARIABLES
# ============================================================

window_start = time.time()

previous_time = time.time()

last_log_time = time.time()

closed_time = 0.0

mouth_open_start = None

yawn_count = 0

closed_frames = 0

previous_pitch = 0.0
previous_yaw = 0.0
previous_roll = 0.0


# ============================================================
# DISTRACTION TRACKING
# ============================================================

distraction_start_time = None

distraction_detected = False

distraction_duration = 0.0


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    success, frame = camera.read()

    if not success:

        print("ERROR: Could not read frame.")

        break


    # --------------------------------------------------------
    # Mirror camera
    # --------------------------------------------------------

    frame = cv2.flip(frame, 1)


    # --------------------------------------------------------
    # Time
    # --------------------------------------------------------

    current_time = time.time()

    delta_time = (
        current_time - previous_time
    )

    previous_time = current_time


    # --------------------------------------------------------
    # Frame dimensions
    # --------------------------------------------------------

    height, width, _ = frame.shape


    # --------------------------------------------------------
    # Convert BGR → RGB
    # --------------------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame

    )


    # --------------------------------------------------------
    # Detect face
    # --------------------------------------------------------

    result = landmarker.detect(mp_image)


    if result.face_landmarks:

        face = result.face_landmarks[0]


        # ====================================================
        # 1. EAR
        # ====================================================

        left_ear = calculate_ear(
            face,
            LEFT_EYE
        )

        right_ear = calculate_ear(
            face,
            RIGHT_EYE
        )

        average_ear = (
            left_ear + right_ear
        ) / 2.0


        # ----------------------------------------------------
        # Eye closure
        # ----------------------------------------------------

        if average_ear < EAR_THRESHOLD:

            closed_frames += 1

            closed_time += delta_time

            eye_status = "CLOSED"

        else:

            closed_frames = 0

            eye_status = "OPEN"


        # ====================================================
        # 2. PERCLOS
        # ====================================================

        elapsed_time = (
            current_time - window_start
        )

        if elapsed_time > 0:

            perclos = (
                closed_time / elapsed_time
            ) * 100

        else:

            perclos = 0.0


        # ====================================================
        # 3. MAR / YAWN
        # ====================================================

        mar = calculate_mar(face)


        if mar > MAR_THRESHOLD:

            if mouth_open_start is None:

                mouth_open_start = current_time


            mouth_open_duration = (
                current_time -
                mouth_open_start
            )


        else:

            mouth_open_start = None

            mouth_open_duration = 0.0


        if (
            mouth_open_start is not None
            and mouth_open_duration
            >= YAWN_DURATION
        ):

            yawn_count += 1

            mouth_open_start = None


        # ====================================================
        # 4. HEAD POSE
        # ====================================================

        focal_length = width

        center = (
            width / 2,
            height / 2
        )


        camera_matrix = np.array([

            [focal_length, 0, center[0]],

            [0, focal_length, center[1]],

            [0, 0, 1]

        ], dtype=np.float64)


        dist_coeffs = np.zeros(
            (4, 1),
            dtype=np.float64
        )


        image_points = np.array([

            (
                face[NOSE].x * width,
                face[NOSE].y * height
            ),

            (
                face[CHIN].x * width,
                face[CHIN].y * height
            ),

            (
                face[LEFT_EYE_POSE].x * width,
                face[LEFT_EYE_POSE].y * height
            ),

            (
                face[RIGHT_EYE_POSE].x * width,
                face[RIGHT_EYE_POSE].y * height
            ),

            (
                face[LEFT_MOUTH].x * width,
                face[LEFT_MOUTH].y * height
            ),

            (
                face[RIGHT_MOUTH].x * width,
                face[RIGHT_MOUTH].y * height
            )

        ], dtype=np.float64)


        model_points = np.array([

            (0.0, 0.0, 0.0),

            (0.0, -330.0, -65.0),

            (-225.0, 170.0, -135.0),

            (225.0, 170.0, -135.0),

            (-150.0, -150.0, -125.0),

            (150.0, -150.0, -125.0)

        ], dtype=np.float64)


        success_pnp, rotation_vector, translation_vector = (
            cv2.solvePnP(

                model_points,

                image_points,

                camera_matrix,

                dist_coeffs,

                flags=cv2.SOLVEPNP_ITERATIVE

            )
        )


        if success_pnp:

            rotation_matrix, _ = cv2.Rodrigues(
                rotation_vector
            )


            angles, _, _, _, _, _ = (
                cv2.RQDecomp3x3(
                    rotation_matrix
                )
            )


            pitch = angles[0]
            yaw = angles[1]
            roll = angles[2]


            if pitch > 90:
                pitch -= 180

            elif pitch < -90:
                pitch += 180


            if yaw > 90:
                yaw -= 180

            elif yaw < -90:
                yaw += 180


            if roll > 90:
                roll -= 180

            elif roll < -90:
                roll += 180


            # Save latest valid head pose
            previous_pitch = pitch
            previous_yaw = yaw
            previous_roll = roll

        # ====================================================
        # 5. DROWSINESS ENGINE
        # ====================================================

        drowsiness_score = engine.calculate_score(

            perclos=perclos,

            yawn_count=yawn_count,

            pitch=pitch,

            yaw=yaw,

            roll=roll

        )

        drowsiness_score = smoother.update(
            drowsiness_score
        )


        drowsiness_level = (
            engine.get_drowsiness_level(
                drowsiness_score
            )
        )

        # ============================================================
        # DISTRACTION DETECTION
        # ============================================================

        YAW_LIMIT = 25.0
        PITCH_LIMIT = 20.0
        DISTRACTION_TIME = 2.0

        looking_away = (
            abs(yaw) > YAW_LIMIT
            or abs(pitch) > PITCH_LIMIT
        )

        if looking_away:

            if distraction_start_time is None:
                distraction_start_time = current_time

            distraction_duration = (
                current_time - distraction_start_time
            )

            if distraction_duration >= DISTRACTION_TIME:
                distraction_detected = True

        else:

            distraction_start_time = None
            distraction_duration = 0.0
            distraction_detected = False

        if current_time - last_log_time >= 1.0:
            driver_state["ear"] = average_ear
            driver_state["perclos"] = perclos
            driver_state["mar"] = mar
            driver_state["yawns"] = yawn_count
            driver_state["pitch"] = pitch
            driver_state["yaw"] = yaw
            driver_state["roll"] = roll
            driver_state["drowsiness_score"] = drowsiness_score
            driver_state["risk_level"] = drowsiness_level
            driver_state["distraction_detected"] = distraction_detected
            driver_state["distraction_duration"] = distraction_duration

            logger.log(

                ear=average_ear,

                perclos=perclos,

                mar=mar,

                yawns=yawn_count,

                pitch=pitch,

                yaw=yaw,

                roll=roll,

                drowsiness_score=drowsiness_score,

                risk_level=drowsiness_level,

                distraction_detected=distraction_detected,

                distraction_duration=distraction_duration,

            )

            # Save labelled ML data only during an active test session
            ml_logger.log(
                ear=average_ear,
                perclos=perclos,
                mar=mar,
                yawns=yawn_count,
                pitch=pitch,
                yaw=yaw,
                roll=roll,
                drowsiness_score=drowsiness_score,
                risk_level=drowsiness_level,
                distraction_detected=distraction_detected,
                distraction_duration=distraction_duration,
            )

            last_log_time = current_time


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.putText(

            frame,

            f"EAR: {average_ear:.3f}",

            (20, 35),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (0, 255, 0),

            2

        )


        cv2.putText(

            frame,

            f"EYES: {eye_status}",

            (20, 65),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (0, 255, 255),

            2

        )


        cv2.putText(

            frame,

            f"PERCLOS: {perclos:.1f}%",

            (20, 95),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 0),

            2

        )


        cv2.putText(

            frame,

            f"MAR: {mar:.3f}",

            (20, 125),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (0, 255, 0),

            2

        )


        cv2.putText(

            frame,

            f"YAWNS: {yawn_count}",

            (20, 155),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 0),

            2

        )


        cv2.putText(

            frame,

            f"PITCH: {pitch:.1f}",

            (20, 185),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 255),

            2

        )


        cv2.putText(

            frame,

            f"YAW: {yaw:.1f}",

            (20, 215),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 255),

            2

        )


        cv2.putText(

            frame,

            f"ROLL: {roll:.1f}",

            (20, 245),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 255),

            2

        )


        # ====================================================
        # DROWSINESS RESULT
        # ====================================================

        cv2.putText(

            frame,

            f"DROWSINESS: {drowsiness_score:.1f}%",

            (20, 295),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 255),

            2

        )


        cv2.putText(

            frame,

            f"RISK: {drowsiness_level}",

            (20, 335),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.9,

            (0, 0, 255),

            2

        )


    else:

        cv2.putText(

            frame,

            "NO FACE DETECTED",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 0, 255),

            2

        )


    # ========================================================
    # RESET PERCLOS WINDOW
    # ========================================================

    if (
        current_time - window_start
        >= PERCLOS_WINDOW
    ):

        window_start = current_time

        closed_time = 0.0

    # ========================================================
    # SAVE LATEST FRAME FOR WEB DASHBOARD
    # ========================================================

    TEMP_FRAME_FILE = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "temp_frame.jpg"
    )

    success = cv2.imwrite(
        TEMP_FRAME_FILE,
        frame
    )

    if success:
        for _ in range(10):
            try:
                os.replace(
                    TEMP_FRAME_FILE,
                    FRAME_FILE
                )
                break
            except PermissionError:
                time.sleep(0.01)


    # ========================================================
    # SHOW CAMERA
    # ========================================================

    cv2.imshow(

        "Digital Driver Twin - Driver Monitor",

        frame

    )


    # ========================================================
    # QUIT
    # ========================================================

    key = cv2.waitKey(1) & 0xFF

    if key == ord("1"):
        session_id = ml_logger.start_session("normal")
        print(f"\n[ML] Normal session started: {session_id}")

    elif key == ord("2"):
        session_id = ml_logger.start_session(
            "simulated_eye_closure"
        )
        print(f"\n[ML] Simulated eye-closure session started: {session_id}")

    elif key == ord("3"):
        session_id = ml_logger.start_session(
            "simulated_distraction"
        )
        print(f"\n[ML] Simulated distraction session started: {session_id}")

    elif key == ord("0"):
        ml_logger.stop_session()
        print("\n[ML] Session stopped. No further ML rows will be recorded.")

    elif key == ord("q"):
        ml_logger.stop_session()
        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()

landmarker.close()
import cv2
import mediapipe as mp
import math
import time


# ==================================================
# FUNCTION: Distance between two landmarks
# ==================================================

def distance(point1, point2):

    return math.sqrt(
        (point1.x - point2.x) ** 2 +
        (point1.y - point2.y) ** 2
    )


# ==================================================
# FUNCTION: Calculate EAR
# ==================================================

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

    ear = (
        vertical_1 + vertical_2
    ) / (2.0 * horizontal)

    return ear


# ==================================================
# MEDIAPIPE SETUP
# ==================================================

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


# ==================================================
# CAMERA
# ==================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Could not open webcam.")

    exit()


print("PERCLOS test started.")
print("Press Q to quit.")


# ==================================================
# PARAMETERS
# ==================================================

EAR_THRESHOLD = 0.20

WINDOW_DURATION = 30.0


# ==================================================
# EYE LANDMARKS
# ==================================================

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


# ==================================================
# TIME TRACKING
# ==================================================

window_start = time.time()

closed_time = 0.0

previous_time = time.time()


# ==================================================
# MAIN LOOP
# ==================================================

while True:

    success, frame = camera.read()

    if not success:

        print("ERROR: Could not read frame.")

        break


    # Mirror camera

    frame = cv2.flip(frame, 1)


    # Current time

    current_time = time.time()

    delta_time = (
        current_time - previous_time
    )

    previous_time = current_time


    # Convert BGR → RGB

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # Create MediaPipe image

    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame

    )


    # Detect face

    result = landmarker.detect(mp_image)


    eye_closed = False


    # ==================================================
    # FACE DETECTED
    # ==================================================

    if result.face_landmarks:

        face = result.face_landmarks[0]


        # Calculate EAR

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


        # Determine eye state

        if average_ear < EAR_THRESHOLD:

            eye_closed = True


        # Add closed duration

        if eye_closed:

            closed_time += delta_time


        # ==================================================
        # CALCULATE PERCLOS
        # ==================================================

        elapsed_time = (
            current_time - window_start
        )


        if elapsed_time > 0:

            perclos = (
                closed_time / elapsed_time
            ) * 100

        else:

            perclos = 0.0


        # ==================================================
        # DISPLAY EAR
        # ==================================================

        cv2.putText(

            frame,

            f"EAR: {average_ear:.3f}",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 0),

            2
        )


        # ==================================================
        # DISPLAY EYE STATE
        # ==================================================

        if eye_closed:

            status = "EYES CLOSED"

        else:

            status = "EYES OPEN"


        cv2.putText(

            frame,

            status,

            (20, 80),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 255),

            2
        )


        # ==================================================
        # DISPLAY PERCLOS
        # ==================================================

        cv2.putText(

            frame,

            f"PERCLOS: {perclos:.1f}%",

            (20, 120),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255, 255, 0),

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


    # ==================================================
    # RESET WINDOW
    # ==================================================

    if (
        current_time - window_start
        >= WINDOW_DURATION
    ):

        window_start = current_time

        closed_time = 0.0


    # ==================================================
    # SHOW CAMERA
    # ==================================================

    cv2.imshow(

        "Digital Driver Twin - PERCLOS",

        frame
    )


    # ==================================================
    # QUIT
    # ==================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==================================================
# CLEANUP
# ==================================================

camera.release()

cv2.destroyAllWindows()

landmarker.close()
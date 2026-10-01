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
# FUNCTION: Calculate Mouth Aspect Ratio (MAR)
# ==================================================

def calculate_mar(landmarks):

    # Mouth landmarks

    left = landmarks[61]
    right = landmarks[291]

    upper_1 = landmarks[13]
    lower_1 = landmarks[14]

    upper_2 = landmarks[82]
    lower_2 = landmarks[87]

    # Vertical distances

    vertical_1 = distance(
        upper_1,
        lower_1
    )

    vertical_2 = distance(
        upper_2,
        lower_2
    )

    # Horizontal distance

    horizontal = distance(
        left,
        right
    )

    # MAR

    mar = (
        vertical_1 + vertical_2
    ) / (2.0 * horizontal)

    return mar


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


print("Yawn detection started.")
print("Press Q to quit.")


# ==================================================
# PARAMETERS
# ==================================================

MAR_THRESHOLD = 0.60

YAWN_DURATION = 1.0

mouth_open_start = None

yawn_count = 0


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


    # Convert BGR → RGB

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # MediaPipe image

    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame
    )


    # Detect face

    result = landmarker.detect(mp_image)


    # ==================================================
    # FACE DETECTED
    # ==================================================

    if result.face_landmarks:

        face = result.face_landmarks[0]


        # Calculate MAR

        mar = calculate_mar(face)


        # ==================================================
        # MOUTH STATE
        # ==================================================

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


        # ==================================================
        # YAWN DETECTION
        # ==================================================

        if (
            mouth_open_start is not None
            and mouth_open_duration
            >= YAWN_DURATION
        ):

            yawn_count += 1

            # Reset so one yawn
            # doesn't count repeatedly

            mouth_open_start = None


        # ==================================================
        # DISPLAY MAR
        # ==================================================

        cv2.putText(

            frame,

            f"MAR: {mar:.3f}",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 0),

            2
        )


        # ==================================================
        # DISPLAY YAWN COUNT
        # ==================================================

        cv2.putText(

            frame,

            f"YAWNS: {yawn_count}",

            (20, 80),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (255, 255, 0),

            2
        )


        # ==================================================
        # DISPLAY MOUTH STATUS
        # ==================================================

        if mar > MAR_THRESHOLD:

            mouth_status = "MOUTH OPEN"

        else:

            mouth_status = "MOUTH CLOSED"


        cv2.putText(

            frame,

            mouth_status,

            (20, 120),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 255),

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
    # DISPLAY CAMERA
    # ==================================================

    cv2.imshow(

        "Digital Driver Twin - Yawn Test",

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
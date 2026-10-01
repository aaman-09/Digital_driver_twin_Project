import cv2
import mediapipe as mp
import math


# ==================================================
# FUNCTION: Calculate distance between two landmarks
# ==================================================

def distance(point1, point2):
    return math.sqrt(
        (point1.x - point2.x) ** 2 +
        (point1.y - point2.y) ** 2
    )


# ==================================================
# FUNCTION: Calculate Eye Aspect Ratio (EAR)
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

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)

    return ear


# ==================================================
# MEDIAPIPE SETUP
# ==================================================

BaseOptions = mp.tasks.BaseOptions

FaceLandmarker = mp.tasks.vision.FaceLandmarker

FaceLandmarkerOptions = (
    mp.tasks.vision.FaceLandmarkerOptions
)

RunningMode = mp.tasks.vision.RunningMode


options = FaceLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=
        "models/mediapipe/face_landmarker.task"
    ),

    running_mode=RunningMode.IMAGE,

    num_faces=1
)


landmarker = (
    FaceLandmarker.create_from_options(options)
)


# ==================================================
# WEBCAM SETUP
# ==================================================

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("ERROR: Could not open webcam.")

    exit()


print("EAR detection started.")
print("Press Q to quit.")


# ==================================================
# EYE CLOSURE PARAMETERS
# ==================================================

EAR_THRESHOLD = 0.20

CLOSED_FRAMES_THRESHOLD = 15

closed_frames = 0

blink_count = 0


# ==================================================
# EYE LANDMARK INDICES
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
# MAIN LOOP
# ==================================================

while True:

    success, frame = camera.read()


    if not success:

        print("ERROR: Could not read frame.")

        break


    # ----------------------------------------------
    # Flip camera horizontally
    # ----------------------------------------------

    frame = cv2.flip(frame, 1)


    # ----------------------------------------------
    # Convert BGR → RGB
    # ----------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # ----------------------------------------------
    # Create MediaPipe Image
    # ----------------------------------------------

    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame

    )


    # ----------------------------------------------
    # Detect face
    # ----------------------------------------------

    result = landmarker.detect(mp_image)


    # ==================================================
    # IF FACE DETECTED
    # ==================================================

    if result.face_landmarks:

        face = result.face_landmarks[0]


        # ----------------------------------------------
        # Calculate left eye EAR
        # ----------------------------------------------

        left_ear = calculate_ear(
            face,
            LEFT_EYE
        )


        # ----------------------------------------------
        # Calculate right eye EAR
        # ----------------------------------------------

        right_ear = calculate_ear(
            face,
            RIGHT_EYE
        )


        # ----------------------------------------------
        # Average EAR
        # ----------------------------------------------

        average_ear = (
            left_ear + right_ear
        ) / 2.0


        # ==================================================
        # EYE CLOSURE DETECTION
        # ==================================================

        if average_ear < EAR_THRESHOLD:

            closed_frames += 1


        else:

            # ------------------------------------------
            # Detect blink
            # ------------------------------------------

            if (
                1 <= closed_frames
                < CLOSED_FRAMES_THRESHOLD
            ):

                blink_count += 1


            # Reset closed frame counter

            closed_frames = 0


        # ==================================================
        # DETERMINE EYE STATUS
        # ==================================================

        if (
            closed_frames
            >= CLOSED_FRAMES_THRESHOLD
        ):

            eye_status = "EYES CLOSED"


        else:

            eye_status = "EYES OPEN"


        # ==================================================
        # DISPLAY EAR
        # ==================================================

        cv2.putText(

            frame,

            f"EAR: {average_ear:.3f}",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 255, 0),

            2

        )


        # ==================================================
        # DISPLAY EYE STATUS
        # ==================================================

        cv2.putText(

            frame,

            eye_status,

            (20, 80),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 255, 255),

            2

        )


        # ==================================================
        # DISPLAY BLINK COUNT
        # ==================================================

        cv2.putText(

            frame,

            f"BLINKS: {blink_count}",

            (20, 120),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (255, 255, 0),

            2

        )


        # ==================================================
        # DRAW EYE LANDMARK POINTS
        # ==================================================

        height, width, _ = frame.shape


        for index in LEFT_EYE + RIGHT_EYE:

            landmark = face[index]


            x = int(
                landmark.x * width
            )

            y = int(
                landmark.y * height
            )


            cv2.circle(

                frame,

                (x, y),

                3,

                (255, 0, 0),

                -1

            )


    # ==================================================
    # IF NO FACE DETECTED
    # ==================================================

    else:

        cv2.putText(

            frame,

            "NO FACE DETECTED",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 0, 255),

            2

        )


    # ==================================================
    # DISPLAY CAMERA
    # ==================================================

    cv2.imshow(

        "Digital Driver Twin - EAR Test",

        frame

    )


    # ==================================================
    # QUIT WITH Q
    # ==================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==================================================
# CLEANUP
# ==================================================

camera.release()

cv2.destroyAllWindows()

landmarker.close()
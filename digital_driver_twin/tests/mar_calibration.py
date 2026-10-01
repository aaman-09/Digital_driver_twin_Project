import cv2
import mediapipe as mp
import math


# ============================================================
# HELPER
# ============================================================

def distance(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


# ============================================================
# MEDIAPIPE
# ============================================================

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


landmarker = FaceLandmarker.create_from_options(
    options
)


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Could not open webcam.")

    exit()


print("========================================")
print("MAR CALIBRATION")
print("========================================")
print("Keep your mouth CLOSED.")
print("Then OPEN your mouth normally.")
print("Then simulate a YAWN.")
print("Press Q to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    success, frame = camera.read()

    if not success:

        break


    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape


    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb

    )


    result = landmarker.detect(mp_image)


    if result.face_landmarks:

        face = result.face_landmarks[0]


        # ----------------------------------------------------
        # Mouth landmarks
        #
        # 61  = left mouth corner
        # 291 = right mouth corner
        # 13  = upper inner lip
        # 14  = lower inner lip
        # ----------------------------------------------------

        left_corner = face[61]

        right_corner = face[291]

        upper_lip = face[13]

        lower_lip = face[14]


        horizontal = distance(
            left_corner,
            right_corner
        )


        vertical = distance(
            upper_lip,
            lower_lip
        )


        if horizontal > 0:

            mar = vertical / horizontal

        else:

            mar = 0.0


        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        cv2.putText(

            frame,

            f"MAR: {mar:.3f}",

            (20, 45),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.9,

            (0, 255, 0),

            2

        )


    else:

        cv2.putText(

            frame,

            "NO FACE DETECTED",

            (20, 45),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 0, 255),

            2

        )


    cv2.imshow(
        "MAR Calibration",
        frame
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


camera.release()

cv2.destroyAllWindows()

landmarker.close()
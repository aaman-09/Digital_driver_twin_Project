import cv2
import mediapipe as mp
import numpy as np


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


print("Head pose detection started.")
print("Press Q to quit.")


# ==================================================
# MEDIAPIPE LANDMARKS
# ==================================================

# Nose
NOSE = 1

# Chin
CHIN = 152

# Left eye corner
LEFT_EYE = 33

# Right eye corner
RIGHT_EYE = 263

# Left mouth corner
LEFT_MOUTH = 61

# Right mouth corner
RIGHT_MOUTH = 291


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


    # Get frame dimensions

    height, width, _ = frame.shape


    # ==================================================
    # CAMERA MATRIX
    # ==================================================

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


    # Assume no lens distortion

    dist_coeffs = np.zeros(
        (4, 1),
        dtype=np.float64
    )


    # ==================================================
    # CONVERT IMAGE
    # ==================================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame
    )


    # ==================================================
    # FACE DETECTION
    # ==================================================

    result = landmarker.detect(mp_image)


    if result.face_landmarks:

        face = result.face_landmarks[0]


        # ==================================================
        # 2D IMAGE POINTS
        # ==================================================

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
                face[LEFT_EYE].x * width,
                face[LEFT_EYE].y * height
            ),

            (
                face[RIGHT_EYE].x * width,
                face[RIGHT_EYE].y * height
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


        # ==================================================
        # 3D FACE MODEL POINTS
        # ==================================================

        model_points = np.array([

            (0.0, 0.0, 0.0),

            (0.0, -330.0, -65.0),

            (-225.0, 170.0, -135.0),

            (225.0, 170.0, -135.0),

            (-150.0, -150.0, -125.0),

            (150.0, -150.0, -125.0)

        ], dtype=np.float64)


        # ==================================================
        # SOLVE PNP
        # ==================================================

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

            # ==================================================
            # ROTATION MATRIX
            # ==================================================

            rotation_matrix, _ = cv2.Rodrigues(
                rotation_vector
            )


            # ==================================================
            # GET EULER ANGLES
            # ==================================================

            angles, _, _, _, _, _ = (
                cv2.RQDecomp3x3(
                    rotation_matrix
                )
            )


            pitch = angles[0]

            yaw = angles[1]

            roll = angles[2]


            # ==================================================
            # DISPLAY VALUES
            # ==================================================

            cv2.putText(

                frame,

                f"PITCH: {pitch:.1f}",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                f"YAW: {yaw:.1f}",

                (20, 80),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                f"ROLL: {roll:.1f}",

                (20, 120),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2

            )


            # ==================================================
            # DRAW LANDMARKS
            # ==================================================

            for point in image_points:

                x = int(point[0])

                y = int(point[1])

                cv2.circle(

                    frame,

                    (x, y),

                    5,

                    (255, 0, 0),

                    -1

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
    # SHOW CAMERA
    # ==================================================

    cv2.imshow(

        "Digital Driver Twin - Head Pose",

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
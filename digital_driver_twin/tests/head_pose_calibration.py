import cv2
import mediapipe as mp
import numpy as np


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
print("HEAD POSE CALIBRATION")
print("========================================")
print("Keep your face straight.")
print("Then move your head LEFT / RIGHT.")
print("Then UP / DOWN.")
print("Then TILT sideways.")
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
        # 2D facial points
        # ----------------------------------------------------

        image_points = np.array([

            (
                face[1].x * width,
                face[1].y * height
            ),

            (
                face[152].x * width,
                face[152].y * height
            ),

            (
                face[33].x * width,
                face[33].y * height
            ),

            (
                face[263].x * width,
                face[263].y * height
            ),

            (
                face[61].x * width,
                face[61].y * height
            ),

            (
                face[291].x * width,
                face[291].y * height
            )

        ], dtype=np.float64)


        # ----------------------------------------------------
        # Approximate 3D facial model
        # ----------------------------------------------------

        model_points = np.array([

            (0.0, 0.0, 0.0),

            (0.0, -330.0, -65.0),

            (-225.0, 170.0, -135.0),

            (225.0, 170.0, -135.0),

            (-150.0, -150.0, -125.0),

            (150.0, -150.0, -125.0)

        ], dtype=np.float64)


        # ----------------------------------------------------
        # Camera matrix
        # ----------------------------------------------------

        focal_length = width

        center = (
            width / 2,
            height / 2
        )


        camera_matrix = np.array([

            [
                focal_length,
                0,
                center[0]
            ],

            [
                0,
                focal_length,
                center[1]
            ],

            [
                0,
                0,
                1
            ]

        ], dtype=np.float64)


        dist_coeffs = np.zeros(
            (4, 1),
            dtype=np.float64
        )


        # ----------------------------------------------------
        # Solve PnP
        # ----------------------------------------------------

        success_pnp, rotation_vector, _ = cv2.solvePnP(

            model_points,

            image_points,

            camera_matrix,

            dist_coeffs,

            flags=cv2.SOLVEPNP_ITERATIVE

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


            # ------------------------------------------------
            # Normalize angles
            # ------------------------------------------------

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


            # ------------------------------------------------
            # Display
            # ------------------------------------------------

            cv2.putText(

                frame,

                f"PITCH: {pitch:.1f}",

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                f"YAW: {yaw:.1f}",

                (20, 75),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                f"ROLL: {roll:.1f}",

                (20, 110),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 255, 0),

                2

            )


    else:

        cv2.putText(

            frame,

            "NO FACE DETECTED",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0, 0, 255),

            2

        )


    cv2.imshow(
        "Head Pose Calibration",
        frame
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


camera.release()

cv2.destroyAllWindows()

landmarker.close()
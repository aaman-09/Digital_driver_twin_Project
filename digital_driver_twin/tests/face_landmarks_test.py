import cv2
import mediapipe as mp

# Load MediaPipe Face Landmarker
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="models/mediapipe/face_landmarker.task"
    ),
    running_mode=VisionRunningMode.IMAGE,
    num_faces=1
)

# Create the face landmarker
landmarker = FaceLandmarker.create_from_options(options)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("Face Landmarker started.")
print("Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read frame.")
        break

    # Convert BGR → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert OpenCV image to MediaPipe Image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Detect face landmarks
    result = landmarker.detect(mp_image)

    # Draw detected landmarks
    if result.face_landmarks:
        for face in result.face_landmarks:

            height, width, _ = frame.shape

            for landmark in face:
                x = int(landmark.x * width)
                y = int(landmark.y * height)

                cv2.circle(
                    frame,
                    (x, y),
                    1,
                    (0, 255, 0),
                    -1
                )

        cv2.putText(
            frame,
            "FACE DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

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

    cv2.imshow(
        "Digital Driver Twin - Face Landmarks",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
landmarker.close()
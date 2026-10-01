import cv2
import mediapipe as mp

print("OpenCV version:", cv2.__version__)
print("MediaPipe imported successfully!")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("Webcam opened successfully.")
print("Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read frame.")
        break

    cv2.imshow("Digital Driver Twin - Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
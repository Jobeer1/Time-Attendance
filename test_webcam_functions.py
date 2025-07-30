import cv2
import sys

def test_camera():
    print("[INFO] Starting camera test...")
    # Open the default camera (webcam)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Unable to access the camera. Please check if the camera is connected and not in use by another application.")
        sys.exit(1)

    print("[INFO] Camera accessed successfully. Press 'q' to quit.")

    # Load a pre-trained face detection model (Haar Cascade)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    if face_cascade.empty():
        print("[ERROR] Failed to load the face detection model. Ensure OpenCV is installed correctly.")
        sys.exit(1)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("[ERROR] Failed to capture frame from the camera. Exiting...")
            break

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Display the frame
        cv2.imshow('Camera Test - Press "q" to Quit', frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Camera test completed.")

if __name__ == "__main__":
    test_camera()

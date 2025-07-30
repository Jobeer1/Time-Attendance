import cv2
import sys
import requests

def test_url_camera(url):
    print(f"[INFO] Testing URL camera: {url}")

    # Check if the URL is reachable
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"[ERROR] Unable to reach the camera URL. HTTP Status Code: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to the camera URL: {e}")
        sys.exit(1)

    print("[INFO] Camera URL is reachable. Attempting to open the stream...")

    # Open the video stream from the URL
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("[ERROR] Unable to open the video stream. Please check the URL and camera settings.")
        sys.exit(1)

    print("[INFO] Video stream opened successfully. Press 'q' to quit.")

    # Load a pre-trained face detection model (Haar Cascade)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    if face_cascade.empty():
        print("[ERROR] Failed to load the face detection model. Ensure OpenCV is installed correctly.")
        sys.exit(1)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("[ERROR] Failed to capture frame from the video stream. Exiting...")
            break

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Display the frame
        cv2.imshow('URL Camera Test - Press "q" to Quit', frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video stream and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] URL camera test completed.")

if __name__ == "__main__":
    # Replace with the URL of your camera stream
    camera_url = "http://192.168.1.100/video"
    test_url_camera(camera_url)

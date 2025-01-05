import cv2
from fer import FER

def detect_faces_and_emotions():
    # Initialize FER emotion detector without MTCNN
    detector = FER(mtcnn=False)

    # Access the webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read a frame from the webcam.")
            break

        # Detect emotions using FER
        emotion, score = detector.top_emotion(frame)
        if emotion:
            print(f"Detected Emotion: {emotion} (Score: {score:.2f})")

        # Display the video feed
        cv2.imshow("Facial Emotion Detection", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces_and_emotions()

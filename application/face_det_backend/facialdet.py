import cv2
import numpy as np
import glob

# Load models
detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet.onnx",
    "",
    (320, 320)
)

recognizer = cv2.FaceRecognizerSF.create(
    "models/face_recognition_sface.onnx",
    ""
)

print("YuNet and SFace loaded!")


# Extract face embedding
def get_embedding(image):

    if image is None:
        return None

    height, width = image.shape[:2]
    detector.setInputSize((width, height))

    _, faces = detector.detect(image)

    if faces is None or len(faces) != 1:
        return None

    aligned_face = recognizer.alignCrop(image, faces[0])
    return recognizer.feature(aligned_face)


# Load all reference photos
known_embeddings = []

for path in glob.glob("images/*"):

    image = cv2.imread(path)
    embedding = get_embedding(image)

    if embedding is not None:
        known_embeddings.append(embedding)
        print("Loaded:", path)
    else:
        print("Skipped:", path)

if not known_embeddings:
    print("No usable reference photos!")
    exit()

known_embeddings = np.vstack(known_embeddings)

print("Reference embeddings:", known_embeddings.shape)


# Live webcam comparison
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Could not open webcam!")
    exit()

while True:

    success, frame = camera.read()

    if not success:
        break

    embedding = get_embedding(frame)

    if embedding is not None:

        scores = [
            recognizer.match(
                reference,
                embedding,
                cv2.FaceRecognizerSF_FR_COSINE
            )
            for reference in known_embeddings
        ]

        best_score = max(float(score) for score in scores)

        cv2.putText(
            frame,
            f"Best similarity: {best_score:.2f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    else:
        cv2.putText(
            frame,
            "No single face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow("Live Face Comparison", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()


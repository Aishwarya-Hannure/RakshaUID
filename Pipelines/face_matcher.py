import cv2
import numpy as np
import os

# -------------------------------------------------
# Load Haar Cascade
# -------------------------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# -------------------------------------------------
# Face Detection
# -------------------------------------------------
def detect_face(img):
    """Detects first face and returns resized grayscale face"""
    if img is None: return None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    if len(faces) == 0:
        return None

    x, y, w, h = faces[0]
    face = gray[y:y+h, x:x+w]
    return cv2.resize(face, (200, 200))

# -------------------------------------------------
# Face Comparison (Aadhaar vs Person)
# -------------------------------------------------
def verify_face(aadhaar_image_path, person_image_path):
    if not os.path.exists(aadhaar_image_path) or not os.path.exists(person_image_path):
        return {"status": "IMAGE_READ_FAILED", "match": False, "confidence": 0}

    img1 = cv2.imread(aadhaar_image_path)
    img2 = cv2.imread(person_image_path)

    if img1 is None or img2 is None:
        return {"status": "IMAGE_READ_FAILED", "match": False, "confidence": 0}

    face1 = detect_face(img1)
    face2 = detect_face(img2)

    if face1 is None:
        return {"status": "FACE_NOT_FOUND_IN_AADHAAR", "match": False, "confidence": 0}

    if face2 is None:
        return {"status": "FACE_NOT_FOUND_IN_PERSON_IMAGE", "match": False, "confidence": 0}

    # LBPH recognizer
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        recognizer.train([face1], np.array([0]))

        label, confidence = recognizer.predict(face2)

        # LBPH Confidence
        ui_score = max(0, min(100, 100 - confidence))
        is_match = confidence < 70 

        return {
            "status": "SUCCESS",
            "confidence": round(ui_score, 2), # Converted to % for UI
            "match": is_match
        }
    except AttributeError:
        return {"status": "ERROR_OPENCV_CONTRIB_MISSING", "match": False, "confidence": 0}
    except Exception as e:
        print(f"Face Error: {e}")
        return {"status": "ALGORITHM_ERROR", "match": False, "confidence": 0}
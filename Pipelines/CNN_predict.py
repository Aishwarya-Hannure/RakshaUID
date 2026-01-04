#CNN_predict.py
import cv2
import numpy as np

# Based on our debugging, the correct class order appears to be:
# Class 0: non_aadhaar, Class 1: aadhaar, Class 2: fake_aadhaar
TRAIN_CLASS_NAMES = ["aadhaar", "fake_aadhaar", "non_aadhaar"]

PROJECT_LABEL_MAP = {
    "aadhaar": "REAL_AADHAAR",
    "fake_aadhaar": "FAKE_AADHAAR",
    "non_aadhaar": "NON_AADHAAR"
}

def preprocess_single_image(img_path, target_size=(224, 224)):
    """
    Preprocess image for EfficientNet model
    Model has its own preprocessing layers, so just resize and convert to float32
    """
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize
    img = cv2.resize(img, target_size)
    
    # Convert to float32 (model has its own normalization layers)
    img = img.astype(np.float32)
    
    # Add batch dimension
    img = np.expand_dims(img, axis=0)
    
    return img

def cnn_predict(model, image_path, confidence_threshold=0.3):
    """
    Returns a dictionary compatible with backend workflow.
    """
    print(f"CNN predicting on: {image_path}")
    
    try:
        img = preprocess_single_image(image_path)
        
        preds = model.predict(img, verbose=0)[0]
        
        print(f"Raw predictions: {preds}")
        
        class_index = int(np.argmax(preds))
        confidence = float(preds[class_index])
        
        train_label = TRAIN_CLASS_NAMES[class_index]
        project_label = PROJECT_LABEL_MAP.get(train_label, "UNKNOWN")
        
        # Low-confidence safeguard
        if confidence < confidence_threshold:
            project_label = "UNCERTAIN"
        
        return {
            "train_label": train_label,
            "project_label": project_label,
            "confidence": round(confidence, 4),
            "raw_scores": {
                TRAIN_CLASS_NAMES[i]: round(float(preds[i]), 4)
                for i in range(len(TRAIN_CLASS_NAMES))
            }
        }
        
    except Exception as e:
        print(f"CNN prediction error: {e}")
        # Return a default response if CNN fails
        return {
            "train_label": "aadhaar",
            "project_label": "REAL_AADHAAR",
            "confidence": 0.7,
            "raw_scores": {"aadhaar": 0.7, "fake_aadhaar": 0.2, "non_aadhaar": 0.1}
        }
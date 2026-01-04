# FILE: Pipelines/preprocess.py
import cv2
import numpy as np
import imutils

def read_image(img_path):
    img = cv2.imread(img_path)
    if img is None: raise ValueError(f"Unable to read image: {img_path}")
    return img

def resize_image(img, size=(1024, 640)): # Adjusted for consistency
    return cv2.resize(img, size)

def noise_reduction(img):
    return cv2.GaussianBlur(img, (3, 3), 0)

def normalize_brightness(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

def deskew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0: return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle = -(90 + angle)
    else: angle = -angle
    return imutils.rotate_bound(img, angle)

def crop_background(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(th)
    if coords is None: return img
    x, y, w, h = cv2.boundingRect(coords)
    return img[y:y + h, x:x + w]

def preprocess_document(img_path):
    img = read_image(img_path)
    img = resize_image(img)
    #img = noise_reduction(img)
    img = normalize_brightness(img)
    # img = deskew(img)
    img = crop_background(img)
    
    # Fixed the return statement
    return {"processed_image": img}
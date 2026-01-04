#forensic_analyzer
import cv2
import numpy as np
from PIL import Image
import io

# -------------------------------------------------
# Sharpness (Laplacian Variance)
# -------------------------------------------------
def compute_sharpness(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# -------------------------------------------------
# Edge Density
# -------------------------------------------------
def compute_edge_density(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return float(np.mean(edges > 0))


# -------------------------------------------------
# Noise Level (simple std deviation)
# -------------------------------------------------
def compute_noise_level(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(np.std(gray))


# -------------------------------------------------
# Error Level Analysis (ELA)
# -------------------------------------------------
def compute_ela_score(img, quality=90):
    """
    Computes mean absolute difference after JPEG recompression
    """
    # Convert OpenCV image → PIL
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    # Save recompressed image to memory
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    recompressed = Image.open(buffer)

    # Convert back to OpenCV
    recompressed = cv2.cvtColor(
        np.array(recompressed), cv2.COLOR_RGB2BGR
    )

    # Compute absolute difference
    diff = cv2.absdiff(img, recompressed)

    return float(np.mean(diff))


# -------------------------------------------------
# MASTER FUNCTION
# -------------------------------------------------
def analyze_image_forensics(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return {
            "sharpness": 0.0,
            "edge_density": 0.0,
            "noise_level": 0.0,
            "ela_score": 0.0,
            "tampering_suspected": False
        }

    sharpness = compute_sharpness(img)
    edge_density = compute_edge_density(img)
    noise_level = compute_noise_level(img)
    ela_score = compute_ela_score(img)

    # -----------------------------
    # Light heuristic (NOT label)
    # -----------------------------
    tampering_suspected = (
        sharpness < 60 or
        ela_score > 25
    )
    tampering_reasons = []

    if sharpness < 60:
        tampering_reasons.append("Low sharpness")

    if ela_score > 0.25:
        tampering_reasons.append("High ELA")

    tampering_suspected = len(tampering_reasons) > 0

    return {
        "ela_score": round(ela_score, 4),
        "edge_density": round(edge_density, 4),
        "sharpness": round(sharpness, 2),
        "tampering_suspected": tampering_suspected,
        "tampering_reasons": tampering_reasons
    }

#qr_validator.py
import cv2
import numpy as np
import re
from pyzbar.pyzbar import decode as pyzbar_decode

# =====================================================
# 1. PARSER: PIPE FORMAT (GUI Style)
# =====================================================
def parse_pipe_format(text):
    """
    Parses: "123456789012|Name|Dob|Gender|..."
    """
    try:
        parts = [p.strip() for p in text.split('|')]
        if len(parts) >= 2:
            return {
                "aadhaar": parts[0] if len(parts[0]) == 12 and parts[0].isdigit() else None,
                "name": parts[1] if len(parts) > 1 else None,
                "dob": parts[2] if len(parts) > 2 else None,
                "gender": parts[3] if len(parts) > 3 else None
            }
    except:
        pass
    return None

# =====================================================
# 2. PARSER: XML FORMAT (Standard Aadhaar QR)
# =====================================================
def parse_xml_format(text):
    """
    Parses: <PrintLetterBarcodeData uid="1234..." name="Anamika..." .../>
    """
    data = {}
    try:
        # Extract UID
        m_uid = re.search(r'uid="(\d+)"', text)
        if m_uid: 
            data["aadhaar"] = m_uid.group(1)
        
        # Extract Name
        m_name = re.search(r'name="([^"]+)"', text)
        if m_name: 
            data["name"] = m_name.group(1)
            
        # Extract Gender
        m_gen = re.search(r'gender="([MF])"', text)
        if m_gen: 
            data["gender"] = "Male" if m_gen.group(1) == "M" else "Female"
            
        # Extract DOB or YOB
        m_dob = re.search(r'dob="([^"]+)"', text)
        if m_dob: 
            data["dob"] = m_dob.group(1)
        else:
            m_yob = re.search(r'yob="(\d+)"', text)
            if m_yob: 
                data["dob"] = m_yob.group(1)

        return data if data else None
    except:
        return None

# =====================================================
# 3. PARSER: SECURE QR (Pyaadhaar)
# =====================================================
def try_decode_secure_qr(decoded_text):
    try:
        from pyaadhaar.decode import AadhaarSecureQr
        decoded = AadhaarSecureQr(decoded_text).decoded_data()
        return {
            "name": decoded.get("name"),
            "dob": decoded.get("dob"),
            "gender": decoded.get("gender"),
            "aadhaar": decoded.get("uid") or decoded.get("aadhaar")
        }
    except:
        return None

# =====================================================
# 4. MAIN VALIDATOR
# =====================================================
def validate_qr(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return {"status": "NOT_DETECTED", "decoded_data": None}

    decoded_text = None
    
    # --- STRATEGY: pyzbar ---
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded_objects = pyzbar_decode(gray)
        if decoded_objects:
            decoded_text = decoded_objects[0].data.decode('utf-8')
    except Exception as e:
        print(f"DEBUG: pyzbar error: {e}")

    # --- FALLBACK: OpenCV ---
    if not decoded_text:
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        if data:
            decoded_text = data

    # --- PARSING ---
    if decoded_text:
        # 1. Try XML (Very Common)
        qr_data = parse_xml_format(decoded_text)
        
        # 2. Try Pipe Format
        if not qr_data:
            qr_data = parse_pipe_format(decoded_text)
        
        # 3. Try Secure Format
        if not qr_data:
            qr_data = try_decode_secure_qr(decoded_text)
            
        # 4. Fallback to Raw
        if not qr_data:
            qr_data = {"raw_text": decoded_text}

        return {
            "status": "DECODED",
            "decoded_data": qr_data
        }

    return {
        "status": "LIKELY_PRESENT_BUT_UNREADABLE",
        "decoded_data": None
    }
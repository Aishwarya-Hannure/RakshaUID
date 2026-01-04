import re

def normalize(text):
    """Removes spaces, special chars, and makes lowercase for fair comparison."""
    if not text:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def build_consistency(ocr_extracted, qr):
    print("\n" + "="*40)
    print("      STARTING CONSISTENCY CHECK      ")
    print("="*40)
    
    qr_status = qr.get("status", "UNKNOWN")
    qr_data = qr.get("decoded_data", {})
    
    if qr_status != "DECODED" or not qr_data:
        return {
            "matching_performed": False, "score": 0.5, "reason": "QR Code could not be read"
        }

    mismatches = []
    
    # 1. COMPARE AADHAAR NUMBER
    ocr_uid = ocr_extracted.get("aadhaar_number")
    qr_uid = qr_data.get("aadhaar") or qr_data.get("uid")

    if ocr_uid and qr_uid:
        if normalize(ocr_uid) != normalize(qr_uid):
            mismatches.append(f"Aadhaar Number mismatch ({ocr_uid} vs {qr_uid})")
    
    # 2. COMPARE NAME
    ocr_name = ocr_extracted.get("name")
    qr_name = qr_data.get("name")
    
    if ocr_name and qr_name:
        n_ocr = normalize(ocr_name)
        n_qr = normalize(qr_name)
        if n_ocr not in n_qr and n_qr not in n_ocr:
             mismatches.append(f"Name mismatch ({ocr_name} vs {qr_name})")

    # 3. COMPARE GENDER (IGNORED)
    ocr_gen = ocr_extracted.get("gender")
    qr_gen = qr_data.get("gender")
    
    if ocr_gen and qr_gen:
        if str(ocr_gen).lower()[0] != str(qr_gen).lower()[0]:
             print(f"WARNING: Gender mismatch detected ({ocr_gen} vs {qr_gen}) but IGNORED.")
             # We deliberately do NOT add this to 'mismatches' list.

    # FINAL VERDICT
    if mismatches:
        return {
            "matching_performed": True, "score": 0.0, "reason": "; ".join(mismatches)
        }

    return {
        "matching_performed": True, "score": 1.0, "reason": "OCR and QR data matched"
    }
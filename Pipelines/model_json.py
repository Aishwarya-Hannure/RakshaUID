# FILE: Pipelines/model_json.py
import pandas as pd
import numpy as np

def json_to_model_input(record):
    row = {}
    val = record.get("validation", {})
    cons = record.get("consistency", {})
    frn = record.get("image_forensics", {})
    ocr = record.get("ocr_extracted", {})

    # Validation
    row['aadhaar_valid'] = 1 if val.get("aadhaar_valid") else 0
    row['dob_valid'] = 1 if val.get("dob_valid") else 0
    row['name_valid'] = 1 if val.get("name_valid") else 0
    row['gender_valid'] = 1 if val.get("gender_valid") else 0
    row['qr_expected_but_failed'] = 1 if val.get("qr_expected_but_failed") else 0

    # Consistency
    row['qr_match'] = 1 if cons.get("matching_performed") else 0
    row['consistency_score'] = float(cons.get("score", 0.0))
    row['consistency_failed'] = 1 if row['consistency_score'] < 0.5 else 0

    # Forensics
    row['ela_score'] = float(frn.get("ela_score", 0.0))
    row['edge_density'] = float(frn.get("edge_density", 0.0))
    row['sharpness'] = float(frn.get("sharpness", 0.0))
    row['high_ela_flag'] = 1 if row['ela_score'] > 0.8 else 0 
    row['low_sharpness_flag'] = 1 if row['sharpness'] < 50 else 0

    # OCR
    present_fields = sum(1 for k in ["name", "dob", "gender", "aadhaar_number"] if ocr.get(k))
    row['ocr_field_count'] = present_fields
    row['missing_fields_ratio'] = (4 - present_fields) / 4.0
    row['ocr_failure_count'] = 4 - present_fields

    # QR
    qr_status = record.get("qr", {}).get("status", "NOT_DETECTED")
    row['qr_decoded'] = 1 if qr_status == "DECODED" else 0
    
    return row

def predict_fraud(model, record, threshold=0.5):
    features = json_to_model_input(record)
    df = pd.DataFrame([features])
    
    # SAFETY: Align columns to model
    if hasattr(model, "feature_names_in_"):
        for col in model.feature_names_in_:
            if col not in df.columns:
                df[col] = 0
        df = df[model.feature_names_in_]

    try:
        prob = model.predict_proba(df)[0][1]
        return {
            "prediction": "FAKE" if prob >= threshold else "REAL",
            "fraud_probability": round(float(prob), 4),
            "ml_model_status": "SUCCESS"
        }
    except Exception as e:
        return {
            "prediction": "REAL",
            "fraud_probability": 0.0,
            "ml_model_status": "FAILED",
            "error": str(e)
        }
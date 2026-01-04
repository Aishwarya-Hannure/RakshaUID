#rule_validator.py
import re
from datetime import datetime

def validate_aadhaar(aadhaar):
    if not aadhaar:
        return False
    return bool(re.fullmatch(r"\d{12}", aadhaar))

def validate_dob(dob):
    if not dob:
        return False

    try:
        datetime.strptime(dob, "%d/%m/%Y")
        return True
    except:
        return bool(re.fullmatch(r"(19\d{2}|20\d{2})", dob))

def validate_name(name):
    if not name:
        return False
    if re.search(r"\d", name):
        return False
    if len(name.split()) < 2:
        return False
    return True

def validate_gender(gender):
    return gender in ["Male", "Female"]

def rule_validation(fields, qr_status):
    validation = {}

    validation["aadhaar_valid"] = validate_aadhaar(fields.get("aadhaar_number"))
    validation["dob_valid"] = validate_dob(fields.get("dob"))
    validation["name_valid"] = validate_name(fields.get("name"))
    validation["gender_valid"] = validate_gender(fields.get("gender"))

    qr_expected_but_failed = (
        qr_status == "LIKELY_PRESENT_BUT_UNREADABLE"
    )

    validation["missing_fields"] = [
        k for k, v in fields.items()
        if v is None and k != "aadhaar_number"
    ]

    validation["overall_valid"] = (
        validation["aadhaar_valid"]
        and validation["dob_valid"]
        and validation["name_valid"]
        and validation["gender_valid"]
    )

    return {
        "aadhaar_valid": validation["aadhaar_valid"],
        "dob_valid": validation["dob_valid"],
        "name_valid": validation["name_valid"],
        "gender_valid": validation["gender_valid"],
        "missing_fields": validation["missing_fields"],
        "overall_valid": validation["overall_valid"],
        "qr_expected_but_failed": qr_expected_but_failed,
    }

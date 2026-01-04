def assess_fraud(validation, qr, consistency, image_forensics):
    """
    Combines signals to assess fraud risk.
    """
    reasons = []
    fraud_score = 0
    decision = "ACCEPTED"

    # 1. Validation Failures
    if not validation.get("aadhaar_valid", True):
        fraud_score += 20
        reasons.append("Invalid Aadhaar Format")

    if validation.get("qr_expected_but_failed", False):
        fraud_score += 20
        reasons.append("QR Code Unreadable")

    # 2. Consistency Check
    cons_score = consistency.get("score", 1.0)
    cons_reason = consistency.get("reason", "")
    
    if cons_score == 0.0:
        fraud_score += 100 
        reasons.append(f"DATA MISMATCH: {cons_reason}")
        decision = "FAKE"
    
    elif cons_score == 0.5:
        fraud_score += 30
        reasons.append(cons_reason)

    # 3. Forensics (LOWERED PENALTY)
    # Reduced from 30 to 15 so it doesn't trigger 'Suspicious' on its own
    if image_forensics.get("tampering_suspected", False):
        fraud_score += 15 
        reasons.append("Digital Tampering Detected")

    # 4. Final Scoring Logic
    if fraud_score >= 60:
        decision = "FAKE"
    elif fraud_score >= 25:
        decision = "SUSPICIOUS"

    # === SPECIAL RULE: BOTH MISMATCHES = SUSPICIOUS ===
    # If BOTH Aadhaar AND Name are wrong, set to SUSPICIOUS (override FAKE)
    if "Aadhaar Number mismatch" in cons_reason and "Name mismatch" in cons_reason:
        decision = "SUSPICIOUS"
        fraud_score = 45 # Set score to 'Suspicious' range
        reasons.append("Flagged as Suspicious due to double mismatch")

    return {
        "fraud_score": min(fraud_score, 100),
        "decision": decision,
        "reasons": reasons
    }
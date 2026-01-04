#final_decision.py
def make_final_decision(cnn_out, fraud_ml_out, fraud_rule_out=None):
    """
    Combines CNN + ML fraud model outputs into one decision.
    """

    cnn_label = cnn_out["project_label"]        # REAL_AADHAAR / FAKE_AADHAAR / NON_AADHAAR
    ml_label = fraud_ml_out["prediction"]       # REAL / FAKE
    ml_prob  = fraud_ml_out["fraud_probability"]

    # Optional rule-based decision (from fraud_assessment)
    rule_decision = None
    if fraud_rule_out:
        rule_decision = fraud_rule_out.get("decision")

    # ---------------------------
    # HARD REJECTION
    # ---------------------------
    if cnn_label == "NON_AADHAAR":
        return {
            "final_decision": "REJECTED",
            "reason": "Document is not Aadhaar",
            "confidence": cnn_out["confidence"]
        }

    # ---------------------------
    # CONFIRMED FRAUD
    # ---------------------------
    if cnn_label == "FAKE_AADHAAR" and ml_label == "FAKE":
        return {
            "final_decision": "FRAUD",
            "reason": "Visual forgery + data inconsistency",
            "fraud_probability": ml_prob
        }

    # ---------------------------
    # SUSPICIOUS CASES
    # ---------------------------
    if (
        (cnn_label == "FAKE_AADHAAR" and ml_label == "REAL") or
        (cnn_label == "REAL_AADHAAR" and ml_label == "FAKE") or
        (rule_decision == "SUSPICIOUS")
    ):
        return {
            "final_decision": "SUSPICIOUS",
            "reason": "Conflicting fraud signals",
            "fraud_probability": ml_prob
        }

    # ---------------------------
    # CLEAN CASE
    # ---------------------------
    return {
        "final_decision": "ACCEPTED",
        "reason": "No fraud indicators detected",
        "fraud_probability": ml_prob
    }

# backend/services/fraud_classifier.py

from collections import defaultdict


# -------------------------------
# CONFIG (Easy tuning 🔥)
# -------------------------------
FRAUD_TYPES = [
    "Fake Reward Scam",
    "Refund Scam",
    "OTP Theft",
    "KYC Scam",
    "QR Scam",
    "Impersonation Scam"
]


# -------------------------------
# MAIN CLASSIFIER
# -------------------------------
def classify_fraud(all_signals, detected_action=None, user_intent=None):
    fraud_scores = defaultdict(float)

    if not all_signals:
        return _empty_result()

    # -------------------------------
    # 1. SIGNAL-BASED SCORING
    # -------------------------------
    for signal in all_signals:
        reason = (signal.get("reason") or "").lower()
        signal_type = (signal.get("type") or "").lower()
        weight = float(signal.get("score", 1))  # dynamic weighting

        # -------------------------
        # KEYWORD / BAIT
        # -------------------------
        if signal_type in ["keyword", "bait", "greed"]:
            if any(k in reason for k in ["reward", "cashback", "win", "prize"]):
                fraud_scores["Fake Reward Scam"] += 2 * weight

            if "refund" in reason:
                fraud_scores["Refund Scam"] += 2 * weight

        # -------------------------
        # OTP / AUTH ATTACKS
        # -------------------------
        if signal_type in ["scam_sentence", "otp"]:
            if "otp" in reason:
                fraud_scores["OTP Theft"] += 3 * weight

        # -------------------------
        # KYC / ACCOUNT THREATS
        # -------------------------
        if signal_type in ["urgency", "pressure", "fear"]:
            fraud_scores["KYC Scam"] += 1 * weight

        if "kyc" in reason:
            fraud_scores["KYC Scam"] += 2 * weight

        # -------------------------
        # IMPERSONATION
        # -------------------------
        if signal_type == "name_mismatch" or "mismatch" in reason:
            fraud_scores["Impersonation Scam"] += 3 * weight

        # -------------------------
        # FALLBACK TEXT SIGNALS
        # -------------------------
        if "otp" in reason:
            fraud_scores["OTP Theft"] += 1.5 * weight

        if "refund" in reason:
            fraud_scores["Refund Scam"] += 1.5 * weight

    # -------------------------------
    # 2. CONTEXT-AWARE LOGIC (VERY IMPORTANT 🔥)
    # -------------------------------
    if user_intent and detected_action:
        user_intent = user_intent.lower()
        detected_action = detected_action.lower()

        # Classic QR Scam pattern
        if user_intent == "receive" and detected_action == "pay":
            fraud_scores["QR Scam"] += 4

        # Reverse trick (less common but possible)
        if user_intent == "pay" and detected_action == "request":
            fraud_scores["QR Scam"] += 2

    # -------------------------------
    # 3. NORMALIZE + PICK BEST
    # -------------------------------
    if not fraud_scores:
        return _empty_result()

    fraud_type = max(fraud_scores, key=fraud_scores.get)
    max_score = fraud_scores[fraud_type]

    total_score = sum(fraud_scores.values())

    # -------------------------------
    # 4. CONFIDENCE CALCULATION
    # -------------------------------
    confidence = max_score / total_score if total_score > 0 else 0

    # Boost if dominant
    if max_score > (0.6 * total_score):
        confidence += 0.05

    confidence = round(min(confidence, 0.95), 2)

    # -------------------------------
    # 5. RETURN STRUCTURED OUTPUT
    # -------------------------------
    return {
        "fraud_type": fraud_type,
        "confidence": confidence,
        "score_breakdown": dict(fraud_scores)
    }


# -------------------------------
# HELPER
# -------------------------------
def _empty_result():
    return {
        "fraud_type": "No clear fraud detected",
        "confidence": 0.0,
        "score_breakdown": {}
    }
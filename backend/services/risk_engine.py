# backend/services/risk_engine.py

def get_risk_level(score):
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    elif score >= 20:
        return "LOW"
    else:
        return "SAFE"


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def calculate_risk(intent, action, keyword_count, suspicious_upi_count):
    signals = []

    # -------------------------------
    # 1. KEYWORD SIGNAL 🔥
    # -------------------------------
    if keyword_count >= 5:
        signals.append(_signal(
            "keyword_high",
            3,
            0.9,
            f"{keyword_count} strong scam keywords detected"
        ))

    elif keyword_count >= 3:
        signals.append(_signal(
            "keyword_medium",
            2,
            0.75,
            f"{keyword_count} suspicious keywords detected"
        ))

    elif keyword_count > 0:
        signals.append(_signal(
            "keyword_low",
            1,
            0.6,
            f"{keyword_count} keyword(s) detected"
        ))

    # -------------------------------
    # 2. INTENT MISMATCH 🚨
    # -------------------------------
    if intent == "receive" and action == "PAY":
        signals.append(_signal(
            "intent_mismatch",
            3,
            0.9,
            "User intended to receive but it's a payment request"
        ))

    # -------------------------------
    # 3. UNKNOWN ACTION
    # -------------------------------
    if action == "UNKNOWN":
        signals.append(_signal(
            "unknown_action",
            1,
            0.6,
            "Transaction type unclear"
        ))

    # -------------------------------
    # 4. SUSPICIOUS UPI 🔥
    # -------------------------------
    if suspicious_upi_count > 0:
        signals.append(_signal(
            "suspicious_upi",
            3,
            0.85,
            f"{suspicious_upi_count} suspicious UPI ID(s) detected"
        ))

    # -------------------------------
    # FINAL SCORING
    # -------------------------------
    total_score = sum(s["score"] for s in signals)

    # Scale to 100
    risk_score = min(total_score * 15, 100)

    # -------------------------------
    # CONFIDENCE
    # -------------------------------
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(min(confidence, 0.95), 2)

    # -------------------------------
    # LEVEL
    # -------------------------------
    risk_level = get_risk_level(risk_score)

    # -------------------------------
    # TOP FACTOR
    # -------------------------------
    top_factor = max(signals, key=lambda x: x["score"])["type"] if signals else None

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "signals": signals,
        "top_risk_factor": top_factor,
        "reasons": [s["reason"] for s in signals]
    }


# -------------------------------
# HELPER
# -------------------------------
def _signal(signal_type, score, confidence, reason):
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }
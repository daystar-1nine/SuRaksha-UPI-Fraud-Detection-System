# backend/services/risk_aggregator.py

def compute_weighted_risk(data):
    """
    data = {
        "intent_mismatch": int (0/1),
        "keyword_score": int (0–10),
        "upi_pattern_score": int (0–10),
        "behavior_score": int (0–10),
        "name_mismatch_score": int (0–10),
        "tampering": bool,
        "metadata": bool
    }
    """

    # -------------------------
    # WEIGHTS (TUNED 🔥)
    # -------------------------
    WEIGHTS = {
        "intent_mismatch": 0.30,
        "keyword_score": 0.15,
        "upi_pattern_score": 0.12,
        "behavior_score": 0.12,
        "name_mismatch_score": 0.18,
        "tampering": 0.08,
        "metadata": 0.05
    }

    # -------------------------
    # NORMALIZATION HELPERS
    # -------------------------
    def normalize_score(value, max_val=10):
        try:
            return min(float(value) / max_val, 1.0)
        except:
            return 0.0

    def normalize_bool(value):
        return 1.0 if value else 0.0

    # -------------------------
    # CALCULATION
    # -------------------------
    weighted_sum = 0
    contributions = {}

    for key, weight in WEIGHTS.items():
        value = data.get(key, 0)

        # Normalize input
        if isinstance(value, bool):
            norm_val = normalize_bool(value)
        elif key.endswith("_score"):
            norm_val = normalize_score(value)
        else:
            norm_val = normalize_score(value, max_val=1)

        contribution = round(norm_val * weight, 4)
        contributions[key] = contribution

        weighted_sum += contribution

    # -------------------------
    # FINAL SCORE (0–100)
    # -------------------------
    risk_score = int(weighted_sum * 100)

    # -------------------------
    # RISK LEVELS
    # -------------------------
    if risk_score <= 20:
        level = "SAFE"
    elif risk_score <= 40:
        level = "LOW"
    elif risk_score <= 60:
        level = "MEDIUM"
    elif risk_score <= 80:
        level = "HIGH"
    else:
        level = "CRITICAL"

    # -------------------------
    # CONFIDENCE 🔥
    # -------------------------
    active_signals = [v for v in contributions.values() if v > 0]
    confidence = min(len(active_signals) / len(WEIGHTS), 1.0)
    confidence = round(confidence, 2)

    # -------------------------
    # TOP FACTOR
    # -------------------------
    top_factor = max(contributions, key=contributions.get) if contributions else None

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "contributions": contributions,
        "top_risk_factor": top_factor
    }
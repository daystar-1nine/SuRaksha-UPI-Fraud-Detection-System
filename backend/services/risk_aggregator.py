from utils.constants import WEIGHTS

def compute_weighted_risk(data):
    """
    Aggregates threat signal scores, applies normalizations, and checks critical gate overrides.
    
    Arguments:
        data: Dict containing sub-scores from the OCR, image tampering, metadata, VPA patterns, 
              name mismatches, and user intent alignment checks.
              Format: {
                  "intent_mismatch": int (0/1),
                  "keyword_score": int (0–10),
                  "upi_pattern_score": int (0–10),
                  "behavior_score": int (0–10),
                  "name_mismatch_score": int (0–10),
                  "tampering": float (0.0-1.0 ELA score),
                  "metadata": float (0.0-1.0 EXIF score)
              }
              
    Returns:
        Dict: Contains final risk score (0-100), risk level label (SAFE, LOW, MEDIUM, HIGH, CRITICAL),
              aggregated module contributions, confidence rating (0.0-1.0), and the top risk factor.
    """

    # ----------------------------------------------------------------------
    # NORMALIZATION HELPERS
    # ----------------------------------------------------------------------
    def normalize_score(value, max_val=10):
        """Scales numeric integer threat scores (0-10) to a uniform 0.0-1.0 range."""
        try:
            return min(float(value) / max_val, 1.0)
        except:
            return 0.0

    def normalize_bool(value):
        """Converts logical flags to float representations (1.0 or 0.0)."""
        return 1.0 if value else 0.0

    # ----------------------------------------------------------------------
    # WEIGHTED SCORING CALCULATION
    # ----------------------------------------------------------------------
    weighted_sum = 0
    contributions = {}

    for key, weight in WEIGHTS.items():
        value = data.get(key, 0)

        # Apply appropriate normalization based on key naming convention/data type
        if isinstance(value, bool):
            norm_val = normalize_bool(value)
        elif key.endswith("_score"):
            norm_val = normalize_score(value)
        else:
            norm_val = normalize_score(value, max_val=1)

        contribution = round(norm_val * weight, 4)
        contributions[key] = contribution

        weighted_sum += contribution

    # Convert normalized weighted sum (0.0 - 1.0) to a standard 0-100 scale
    risk_score = int(weighted_sum * 100)

    # ----------------------------------------------------------------------
    # CRITICAL GATE OVERRIDES 🔥
    # ----------------------------------------------------------------------
    # Heuristics can sometimes be watered down by clean transaction parameters.
    # Overrides ensure that high visual anomalies (like ELA splicing) force a critical block 
    # regardless of keyword or VPA compliance.
    override_triggered = False
    override_factor = None

    tampering_val = data.get("tampering", 0.0)
    metadata_val = data.get("metadata", 0.0)

    # If ELA image tampering is >= 75%, override and force risk to 99 (CRITICAL)
    if tampering_val >= 0.75:
        risk_score = 99
        override_triggered = True
        override_factor = "tampering"
    # If EXIF editing software metadata matches >= 45%, override and force risk to 95 (CRITICAL)
    elif metadata_val >= 0.45:
        risk_score = 95
        override_triggered = True
        override_factor = "metadata"

    # ----------------------------------------------------------------------
    # RISK LEVEL CLASSIFICATION
    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    # DYNAMIC CONFIDENCE SCORING
    # ----------------------------------------------------------------------
    # Calculates confidence as the ratio of active threat modules to total modules.
    active_signals = [v for v in contributions.values() if v > 0]
    confidence = min(len(active_signals) / len(WEIGHTS), 1.0)
    confidence = round(confidence, 2)

    # ----------------------------------------------------------------------
    # TOP RISK FACTOR DETERMINATION
    # ----------------------------------------------------------------------
    if override_triggered:
        top_factor = override_factor
    else:
        top_factor = max(contributions, key=contributions.get) if contributions else None

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "contributions": contributions,
        "top_risk_factor": top_factor
    }
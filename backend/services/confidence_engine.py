# backend/services/confidence_engine.py

def compute_confidence(all_signals):
    if not all_signals:
        return 0.0

    total_weighted_conf = 0.0
    total_weight = 0.0

    strong_signal_count = 0
    weak_signal_penalty = 0.0

    for signal in all_signals:
        conf = float(signal.get("confidence", 0))
        score = float(signal.get("score", 1))

        # -------------------------------
        # 1. FILTER VERY WEAK SIGNALS
        # -------------------------------
        if conf < 0.4:
            weak_signal_penalty += 0.02
            continue

        # -------------------------------
        # 2. COUNT STRONG SIGNALS
        # -------------------------------
        if conf >= 0.75:
            strong_signal_count += 1

        # -------------------------------
        # 3. WEIGHTED CONFIDENCE
        # -------------------------------
        total_weighted_conf += conf * score
        total_weight += score

    if total_weight == 0:
        return 0.0

    base_conf = total_weighted_conf / total_weight

    # -------------------------------
    # 4. BOOST (multiple strong signals)
    # -------------------------------
    if strong_signal_count >= 3:
        base_conf += 0.08
    elif strong_signal_count == 2:
        base_conf += 0.04

    # -------------------------------
    # 5. DIMINISHING RETURNS
    # (prevent overconfidence explosion)
    # -------------------------------
    if base_conf > 0.9:
        base_conf = 0.9 + (base_conf - 0.9) * 0.5

    # -------------------------------
    # 6. APPLY PENALTY (noise reduction)
    # -------------------------------
    base_conf -= weak_signal_penalty

    # -------------------------------
    # 7. NORMALIZE
    # -------------------------------
    final_conf = max(0.0, min(base_conf, 0.98))

    return round(final_conf, 2)
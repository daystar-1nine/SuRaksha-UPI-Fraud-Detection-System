# backend/services/confidence_engine.py
"""Confidence aggregation engine for analyzing threat scores and signals."""

from typing import Any, Dict, List

def compute_confidence(all_signals: List[Dict[str, Any]]) -> float:
    """Computes a unified confidence score from a list of security threat signals.

    Filters weak signals, boosting confidence when multiple strong signals are
    present, and normalizes the score to prevent exponential explosion.

    Args:
        all_signals: List of dictionary records, each containing 'confidence'
                     and 'score' properties representing individual signal metrics.

    Returns:
        float: Rounded consolidated confidence score between 0.0 and 0.98.
    """
    if not all_signals:
        return 0.0

    total_weighted_conf: float = 0.0
    total_weight: float = 0.0

    strong_signal_count: int = 0
    weak_signal_penalty: float = 0.0

    for signal in all_signals:
        conf: float = float(signal.get("confidence", 0.0))
        score: float = float(signal.get("score", 1.0))

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

    if total_weight == 0.0:
        return 0.0

    base_conf: float = total_weighted_conf / total_weight

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
    final_conf: float = max(0.0, min(base_conf, 0.98))

    return round(final_conf, 2)
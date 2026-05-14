# backend/services/upi_pattern_intelligence.py

import re
import math
from collections import Counter


# -------------------------------
# CONFIG
# -------------------------------
KNOWN_HANDLES = [
    "ybl", "ibl", "okaxis", "okhdfcbank", "okicici",
    "oksbi", "paytm", "apl", "upi"
]

# 🌍 MULTILINGUAL SCAM TERMS
SCAM_TERMS = [
    # English
    "reward", "cash", "offer", "bonus", "gift", "win", "free",

    # Hindi / Marathi
    "इनाम", "पुरस्कार", "कैशबैक", "ऑफर", "जीतें", "फ्री",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার", "জিতুন"
]


# -------------------------------
# HELPERS
# -------------------------------
def make_signal(type_, score, confidence, reason):
    return {
        "type": type_,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def shannon_entropy(text):
    """Detect randomness (VERY IMPORTANT 🔥)"""
    if not text:
        return 0
    prob = [n_x / len(text) for x, n_x in Counter(text).items()]
    return -sum(p * math.log2(p) for p in prob)


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def analyze_upi_patterns(upi_ids):
    signals = []

    for upi in upi_ids:
        upi_lower = upi.lower()

        if "@" not in upi_lower:
            continue

        name, handle = upi_lower.split("@", 1)

        # -------------------------
        # 1. NUMERIC HEAVY 🔢
        # -------------------------
        if len(name) > 0:
            digit_ratio = sum(c.isdigit() for c in name) / len(name)

            if digit_ratio > 0.5:
                signals.append(make_signal(
                    "numeric_heavy",
                    2,
                    0.7,
                    f"UPI '{upi}' has too many numbers"
                ))

        # -------------------------
        # 2. RANDOMNESS (ENTROPY) 🔥
        # -------------------------
        entropy = shannon_entropy(name)

        if entropy > 3.5:
            signals.append(make_signal(
                "high_entropy",
                3,
                0.85,
                f"UPI '{upi}' looks randomly generated"
            ))

        # -------------------------
        # 3. VERY LONG ID
        # -------------------------
        if len(name) > 20:
            signals.append(make_signal(
                "long_id",
                2,
                0.8,
                f"UPI '{upi}' is unusually long"
            ))

        # -------------------------
        # 4. REPEATED CHARACTERS 🔁
        # -------------------------
        if re.search(r"(.)\1{3,}", name):
            signals.append(make_signal(
                "repetition_pattern",
                2,
                0.75,
                f"UPI '{upi}' contains repeated characters"
            ))

        # -------------------------
        # 5. SCAM KEYWORDS 🌍
        # -------------------------
        for term in SCAM_TERMS:
            if term in upi_lower:
                signals.append(make_signal(
                    "scam_term",
                    3,
                    0.9,
                    f"UPI '{upi}' contains suspicious term '{term}'"
                ))

        # -------------------------
        # 6. UNKNOWN HANDLE 🔥
        # -------------------------
        if handle not in KNOWN_HANDLES:
            signals.append(make_signal(
                "unknown_handle",
                2,
                0.8,
                f"UPI '{upi}' uses unknown handle '{handle}'"
            ))

    # -------------------------------
    # FINAL SCORE
    # -------------------------------
    total_score = sum(s["score"] for s in signals)
    risk_score = min(total_score, 10)

    if risk_score >= 7:
        level = "HIGH"
    elif risk_score >= 4:
        level = "MEDIUM"
    else:
        level = "LOW"

    # -------------------------------
    # CONFIDENCE (WEIGHTED)
    # -------------------------------
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(confidence, 2)

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }
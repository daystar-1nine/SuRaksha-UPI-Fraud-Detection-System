# backend/services/fraud_intelligence.py

import re
from collections import defaultdict

# -------------------------------
# CONFIG
# -------------------------------
SUSPICIOUS_KEYWORDS = [
    # English
    "reward", "cashback", "offer", "urgent",
    "refund", "gift", "bonus", "free",

    # Hindi / Marathi
    "इनाम", "कैशबैक", "ऑफर", "फ्री",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার"
]

SUSPICIOUS_PATTERNS = [
    "paytm", "wallet", "cash", "quickpay"
]

REPEAT_PATTERN = re.compile(r"(.)\1{3,}")


# -------------------------------
# SIGNAL HELPERS
# -------------------------------
def _signal(signal_type, score, confidence, reason):
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def _normalize(text):
    return (text or "").lower().strip()


def _deduplicate(signals):
    seen = set()
    unique = []

    for s in signals:
        key = (s["type"], s["reason"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# -------------------------------
# 1. KEYWORD SIGNAL
# -------------------------------
def keyword_signal(text):
    text = _normalize(text)
    signals = []

    for word in SUSPICIOUS_KEYWORDS:
        if word in text:
            signals.append(
                _signal("keyword", 2, 0.75, f"Suspicious keyword: {word}")
            )

    return signals


# -------------------------------
# 2. UPI PATTERN SIGNAL
# -------------------------------
def upi_pattern_signal(upi_ids):
    signals = []

    for upi in upi_ids:
        lower = _normalize(upi)

        name = lower.split("@")[0] if "@" in lower else lower

        # Pattern match
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in lower:
                signals.append(
                    _signal("upi_pattern", 3, 0.8, f"Suspicious pattern: {pattern}")
                )

        # Too many digits
        if len(name) > 0:
            digit_ratio = sum(c.isdigit() for c in name) / len(name)
            if digit_ratio > 0.5:
                signals.append(
                    _signal("upi_numeric", 2, 0.7, "Too many numbers in UPI ID")
                )

        # Long/random
        if len(name) > 25:
            signals.append(
                _signal("upi_length", 2, 0.6, "Unusually long UPI ID")
            )

        # Repeated characters
        if REPEAT_PATTERN.search(name):
            signals.append(
                _signal("upi_repeat", 2, 0.7, "Repeated character pattern")
            )

    return signals


# -------------------------------
# 3. INTENT MISMATCH (CRITICAL 🔥)
# -------------------------------
def intent_mismatch_signal(intent, action):
    signals = []

    intent = _normalize(intent)
    action = _normalize(action)

    if intent == "receive" and action == "pay":
        signals.append(
            _signal(
                "intent_mismatch",
                4,
                0.9,
                "User wants to receive but payment is requested"
            )
        )

    if intent == "pay" and action == "request":
        signals.append(
            _signal(
                "reverse_mismatch",
                2,
                0.7,
                "Unexpected payment request flow"
            )
        )

    return signals


# -------------------------------
# 4. AGGREGATOR (SMART 🔥)
# -------------------------------
def aggregate_signals(signals):
    signals = _deduplicate(signals)

    total_score = 0
    weighted_conf = 0
    total_weight = 0

    for s in signals:
        score = s["score"]
        conf = s["confidence"]

        total_score += score
        weighted_conf += score * conf
        total_weight += score

    # Risk score normalization
    risk_score = min(total_score, 10)

    # Better confidence
    confidence = (weighted_conf / total_weight) if total_weight else 0

    # Boost if many strong signals
    if len(signals) >= 4:
        confidence += 0.05

    confidence = round(min(confidence, 0.95), 2)

    # Risk level
    if risk_score >= 7:
        level = "HIGH"
    elif risk_score >= 4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }


# -------------------------------
# MAIN ENGINE
# -------------------------------
def analyze_fraud_intelligence(text, upi_ids, intent, action):
    signals = []

    signals.extend(keyword_signal(text))
    signals.extend(upi_pattern_signal(upi_ids))
    signals.extend(intent_mismatch_signal(intent, action))

    return aggregate_signals(signals)
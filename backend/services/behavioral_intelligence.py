# backend/services/behavioral_intelligence.py

import re
from collections import Counter


# -------------------------------
# CONFIG (Easy to tune later)
# -------------------------------
WEIGHTS = {
    "bait_amount": 2,
    "reward_bait": 2,
    "urgency": 2,
    "fear": 2,
    "greed": 2,
    "high_pressure": 3,
    "repetition": 2,
    "density": 2
}


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def analyze_behavior(text: str):
    text = (text or "").lower().strip()
    words = text.split()
    signals = []

    if not text:
        return _empty_response()

    # -------------------------------
    # 1. BAIT / MONEY DETECTION 💰
    # -------------------------------
    bait_regex = re.compile(
        r"(₹\s?\d+|\b\d{2,6}\s?(rs|inr)?\b|\b(win|get|earn)\s?\d+\b|\b\d+\s?cashback\b)"
    )

    if bait_regex.search(text):
        signals.append(_signal("bait_amount", "Suspicious money/bait amount detected"))

    if any(k in text for k in ["cashback", "reward", "bonus", "prize"]):
        signals.append(_signal("reward_bait", "Reward-based bait detected"))

    # -------------------------------
    # 2. URGENCY ⏰
    # -------------------------------
    urgency_words = [
        "urgent", "act now", "limited time", "last chance",
        "verify now", "immediately", "hurry", "today only"
    ]

    urgency_hits = _count_matches(text, urgency_words)

    for word in urgency_words:
        if word in text:
            signals.append(_signal("urgency", f"Urgency detected: {word}"))

    # -------------------------------
    # 3. PSYCHOLOGY 🧠
    # -------------------------------
    fear_words = ["blocked", "suspended", "deactivated", "expired", "restricted"]
    greed_words = ["reward", "cashback", "bonus", "gift", "offer", "prize"]

    for word in fear_words:
        if word in text:
            signals.append(_signal("fear", f"Fear trigger: {word}"))

    for word in greed_words:
        if word in text:
            signals.append(_signal("greed", f"Greed trigger: {word}"))

    # -------------------------------
    # 4. ADVANCED SIGNALS 🔥
    # -------------------------------
    if urgency_hits >= 2:
        signals.append(_signal("high_pressure", "Multiple urgency signals"))

    if urgency_hits >= 3:
        signals.append(_signal("repetition", "Repeated urgency pressure"))

    # Keyword density
    if words:
        density = urgency_hits / len(words)
        if density > 0.2:
            signals.append(_signal("density", "High urgency density"))

    # -------------------------------
    # 5. REMOVE DUPLICATES
    # -------------------------------
    signals = _deduplicate(signals)

    # -------------------------------
    # 6. FINAL SCORING
    # -------------------------------
    total_score = sum(WEIGHTS[s["type"]] for s in signals)
    risk_score = min(total_score, 10)

    risk_level = _get_risk_level(risk_score)
    confidence = _calculate_confidence(signals)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }


# -------------------------------
# HELPERS
# -------------------------------
def _signal(signal_type, reason):
    return {
        "type": signal_type,
        "score": WEIGHTS[signal_type],
        "confidence": 0.8,
        "reason": reason
    }


def _count_matches(text, keywords):
    return sum(1 for word in keywords if word in text)


def _deduplicate(signals):
    seen = set()
    unique = []

    for s in signals:
        key = (s["type"], s["reason"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


def _get_risk_level(score):
    if score >= 7:
        return "HIGH"
    elif score >= 4:
        return "MEDIUM"
    return "LOW"


def _calculate_confidence(signals):
    if not signals:
        return 0

    # Better confidence logic
    base = sum(s["confidence"] for s in signals) / len(signals)

    # Boost if multiple strong signals
    if len(signals) >= 4:
        base += 0.1

    return round(min(base, 0.95), 2)


def _empty_response():
    return {
        "risk_score": 0,
        "risk_level": "LOW",
        "confidence": 0,
        "signals": [],
        "reasons": []
    }
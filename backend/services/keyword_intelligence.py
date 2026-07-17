# backend/services/keyword_intelligence.py

import re
import unicodedata
from collections import defaultdict

from utils.fraud_patterns import (
    SUSPICIOUS_KEYWORDS,
    URGENCY_PHRASES,
    SCAM_SENTENCES
)

# -------------------------------
# CONFIG
# -------------------------------
EMOTIONAL_WORDS = [
    "urgent", "blocked", "suspended",
    "verify", "immediately"
]

REPEAT_PATTERN = re.compile(r"(.)\1{3,}")


from utils.text_utils import normalize_text
from utils.signal_utils import empty_response

def make_signal(type_, score, confidence, reason):
    return {
        "type": type_,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }

def deduplicate_signals(signals):
    seen = set()
    unique = []
    for sig in signals:
        key = (sig["type"], sig["reason"])
        if key not in seen:
            seen.add(key)
            unique.append(sig)
    return unique


def match_terms(text, terms):
    """Word-boundary + safe regex match"""
    matches = []
    for term in terms:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, text):
            matches.append(term)
    return matches





# -------------------------------
# MAIN ENGINE
# -------------------------------
def analyze_text_patterns(text):
    text = normalize_text(text)
    words = text.split()
    signals = []

    if not text:
        return empty_response("keyword_intelligence")

    # -------------------------------
    # 1. KEYWORD DETECTION
    # -------------------------------
    keyword_matches = match_terms(text, SUSPICIOUS_KEYWORDS)

    for kw in keyword_matches:
        signals.append(make_signal(
            "keyword", 1.5, 0.7, f"Suspicious keyword: {kw}"
        ))

    # -------------------------------
    # 2. URGENCY DETECTION
    # -------------------------------
    urgency_matches = match_terms(text, URGENCY_PHRASES)

    for phrase in urgency_matches:
        signals.append(make_signal(
            "urgency", 2, 0.8, f"Urgency phrase: {phrase}"
        ))

    # -------------------------------
    # 3. SCAM SENTENCE DETECTION
    # -------------------------------
    scam_matches = match_terms(text, SCAM_SENTENCES)

    for sentence in scam_matches:
        signals.append(make_signal(
            "scam_sentence", 3, 0.9, f"Scam phrase: {sentence}"
        ))

    # -------------------------------
    # 4. KEYWORD DENSITY
    # -------------------------------
    if words:
        density = len(keyword_matches) / len(words)
        if density > 0.2:
            signals.append(make_signal(
                "keyword_density", 2, 0.75, "High keyword density"
            ))

    # -------------------------------
    # 5. REPETITION
    # -------------------------------
    if len(keyword_matches) >= 3:
        signals.append(make_signal(
            "repetition", 2, 0.8, "Repeated suspicious terms"
        ))

    # -------------------------------
    # 6. EMOTIONAL TRIGGERS
    # -------------------------------
    emotional_matches = match_terms(text, EMOTIONAL_WORDS)

    for word in emotional_matches:
        signals.append(make_signal(
            "emotion", 1, 0.7, f"Emotional trigger: {word}"
        ))

    # -------------------------------
    # 7. PRESSURE LOGIC
    # -------------------------------
    if len(urgency_matches) >= 2:
        signals.append(make_signal(
            "pressure", 2.5, 0.85, "High urgency pressure"
        ))

    # -------------------------------
    # 8. SPAM / PATTERN NOISE
    # -------------------------------
    if REPEAT_PATTERN.search(text):
        signals.append(make_signal(
            "spam_pattern", 1.5, 0.7, "Repeated character pattern"
        ))

    # -------------------------------
    # 9. CLEAN SIGNALS
    # -------------------------------
    signals = deduplicate_signals(signals)

    # -------------------------------
    # 10. FINAL SCORING
    # -------------------------------
    total_score = sum(s["score"] for s in signals)
    risk_score = min(total_score, 10)

    # Better confidence (weighted)
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0

    # Boost if strong signals
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


# backend/services/scam_detector.py

import unicodedata
from difflib import SequenceMatcher

from utils.keyword_db import SCAM_KEYWORDS


# -------------------------------
# HELPERS
# -------------------------------
def normalize(text):
    if not text:
        return ""
    return unicodedata.normalize("NFKC", text).lower().strip()


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def is_fuzzy_match(keyword, text_words, threshold=0.85):
    keyword_words = keyword.split()
    n = len(keyword_words)

    if n == 0 or len(text_words) < n:
        return False

    for i in range(len(text_words) - n + 1):
        window_phrase = " ".join(text_words[i:i+n])
        if similarity(keyword, window_phrase) >= threshold:
            return True

    return False


def make_signal(keyword, warning):
    return {
        "type": "scam_keyword",
        "score": 1,
        "confidence": 0.7,
        "reason": warning,
        "keyword": keyword
    }


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def detect_scam_keywords(text):
    text = normalize(text)
    words = text.split()

    detected_keywords = set()
    warnings = []
    signals = []

    # -------------------------------
    # DETECTION LOGIC 🔥
    # -------------------------------
    for keyword, warning in SCAM_KEYWORDS.items():
        keyword_norm = normalize(keyword)

        # 1. Exact match
        if keyword_norm in text:
            detected_keywords.add(keyword)
            warnings.append(warning)
            signals.append(make_signal(keyword, warning))
            continue

        # 2. Fuzzy match (handles OCR/typos)
        if is_fuzzy_match(keyword_norm, words):
            detected_keywords.add(keyword)
            warnings.append(warning + " (fuzzy match)")
            signals.append(make_signal(keyword, warning))
            continue

    # -------------------------------
    # FINAL SCORING
    # -------------------------------
    total_score = len(signals)
    risk_score = min(total_score * 2, 10)

    if risk_score >= 7:
        level = "HIGH"
    elif risk_score >= 4:
        level = "MEDIUM"
    elif risk_score > 0:
        level = "LOW"
    else:
        level = "SAFE"

    # -------------------------------
    # CONFIDENCE
    # -------------------------------
    confidence = round(min(0.5 + (len(signals) * 0.1), 0.9), 2)

    # -------------------------------
    # FINAL RESPONSE
    # -------------------------------
    return {
        "keywords": list(detected_keywords),
        "warnings": list(dict.fromkeys(warnings)),  # deduplicate
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals
    }
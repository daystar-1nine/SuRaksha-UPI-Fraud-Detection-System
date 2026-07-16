# backend/services/scam_detector.py

"""
SuRaksha Scam Keyword Detection Service

This module scans OCR text for high-risk phrases (e.g., "refund coupon", "lottery winner").
It utilizes two levels of verification:
1. Exact keyword containment check (fast path).
2. Fuzzy matching (sliding-window comparison using Gestalt Pattern Matching) to catch typos,
   scammer attempts to bypass keyword blocks, and Tesseract character recognition glitches.
Unicode normalization is applied to mitigate homoglyph (lookalike character) evasion tricks.
"""

import unicodedata
from difflib import SequenceMatcher
from utils.keyword_db import SCAM_KEYWORDS


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------
from utils.text_utils import normalize_text

def similarity(a, b):
    """Calculates the similarity ratio (0.0 to 1.0) between two strings using Ratcliff-Obershelp."""
    return SequenceMatcher(None, a, b).ratio()


def is_fuzzy_match(keyword, text_words, threshold=0.85):
    """
    Runs a sliding window over text words to see if any phrase matches the keyword.
    
    Why: Since keywords can consist of multiple words (e.g., "customer support"),
    we chunk the OCR word list into sliding windows of length N (where N is the number
    of words in the target keyword) and run fuzzy similarity checks. A threshold
    of 0.85 balances catching OCR spelling errors with preventing false positives.
    """
    keyword_words = keyword.split()
    n = len(keyword_words)

    # If the text is shorter than the search keyword, it's mathematically impossible to match
    if n == 0 or len(text_words) < n:
        return False

    # Slide the window word by word and compare phrase similarity
    for i in range(len(text_words) - n + 1):
        window_phrase = " ".join(text_words[i:i+n])
        if similarity(keyword, window_phrase) >= threshold:
            return True

    return False


def make_signal(keyword, warning):
    """Factory helper to structure threat signal dictionaries."""
    return {
        "type": "scam_keyword",
        "score": 1,
        "confidence": 0.7,
        "reason": warning,
        "keyword": keyword
    }


# ----------------------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------------------
def detect_scam_keywords(text):
    """
    Scans the provided text for items in the scam dictionary.
    
    Args:
        text (str): OCR normalized transaction screenshot text.
        
    Returns:
        Dict: Match details, aggregate risk scores, and warning signals.
    """
    text = normalize_text(text)
    words = text.split()

    detected_keywords = set()
    warnings = []
    signals = []

    # ----------------------------------------------------------------------
    # DETECTION LOGIC
    # ----------------------------------------------------------------------
    for keyword, warning in SCAM_KEYWORDS.items():
        keyword_norm = normalize_text(keyword)

        # 1. Exact match (highly performant check)
        if keyword_norm in text:
            detected_keywords.add(keyword)
            warnings.append(warning)
            signals.append(make_signal(keyword, warning))
            continue

        # 2. Fuzzy match (handles OCR errors/scammer spelling alterations)
        if is_fuzzy_match(keyword_norm, words):
            detected_keywords.add(keyword)
            warnings.append(warning + " (fuzzy match)")
            signals.append(make_signal(keyword, warning))
            continue

    # ----------------------------------------------------------------------
    # FINAL SCORING
    # ----------------------------------------------------------------------
    # Scale risk score based on the number of distinct warning keywords matched
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

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    # Higher density of distinct matched flags yields higher system confidence.
    confidence = round(min(0.5 + (len(signals) * 0.1), 0.9), 2)

    # ----------------------------------------------------------------------
    # FINAL RESPONSE
    # ----------------------------------------------------------------------
    return {
        "keywords": list(detected_keywords),
        "warnings": list(dict.fromkeys(warnings)),  # deduplicate warning strings
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals
    }
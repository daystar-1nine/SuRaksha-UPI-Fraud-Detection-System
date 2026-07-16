# backend/services/intent_detector.py

import re

# -------------------------------
# CONFIG
# -------------------------------
PAY_KEYWORDS = [
    "pay", "payment", "sent", "debit", "debited",
    "upi payment", "send money", "transfer", "paid"
]

COLLECT_KEYWORDS = [
    "collect", "receive", "request money",
    "incoming", "collect request", "money request"
]

# 🌍 Multilingual (basic support)
PAY_KEYWORDS_MULTI = [
    "भुगतान", "पैसे भेजें",  # Hindi
    "পেমেন্ট", "টাকা পাঠান"  # Bengali
]

COLLECT_KEYWORDS_MULTI = [
    "पैसे प्राप्त", "राशि प्राप्त",  # Hindi
    "টাকা গ্রহণ", "পাওয়া গেছে"       # Bengali
]


from utils.text_utils import normalize_text

# -------------------------------
# MATCH HELPER
# -------------------------------
def match_keywords(text, keywords):
    matches = []
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            matches.append(kw)
    return matches


# -------------------------------
# MAIN DETECTOR
# -------------------------------
def detect_action(text):
    text = normalize_text(text)

    if not text:
        return {
            "action": "UNKNOWN",
            "confidence": 0.0,
            "matches": []
        }

    pay_matches = []
    collect_matches = []

    # -------------------------------
    # 1. English Detection
    # -------------------------------
    pay_matches += match_keywords(text, PAY_KEYWORDS)
    collect_matches += match_keywords(text, COLLECT_KEYWORDS)

    # -------------------------------
    # 2. Multilingual Detection
    # -------------------------------
    pay_matches += match_keywords(text, PAY_KEYWORDS_MULTI)
    collect_matches += match_keywords(text, COLLECT_KEYWORDS_MULTI)

    # -------------------------------
    # 3. Scoring
    # -------------------------------
    pay_score = len(pay_matches)
    collect_score = len(collect_matches)

    # -------------------------------
    # 4. Decision Logic
    # -------------------------------
    if pay_score == 0 and collect_score == 0:
        return {
            "action": "UNKNOWN",
            "confidence": 0.0,
            "matches": []
        }

    if pay_score > collect_score:
        confidence = min(0.9, 0.5 + (pay_score * 0.1))
        return {
            "action": "PAY",
            "confidence": round(confidence, 2),
            "matches": list(set(pay_matches))
        }

    if collect_score > pay_score:
        confidence = min(0.9, 0.5 + (collect_score * 0.1))
        return {
            "action": "COLLECT",
            "confidence": round(confidence, 2),
            "matches": list(set(collect_matches))
        }

    # -------------------------------
    # 5. Tie case (ambiguous)
    # -------------------------------
    return {
        "action": "AMBIGUOUS",
        "confidence": 0.5,
        "matches": list(set(pay_matches + collect_matches))
    }
# backend/services/name_matcher.py

import re
from difflib import SequenceMatcher

# -------------------------------
# CONFIG
# -------------------------------
COMMON_NOISE_WORDS = [
    "upi", "bank", "payment", "paid", "received",
    "account", "transfer", "transaction"
]


# -------------------------------
# HELPERS
# -------------------------------
def normalize(text):
    return (text or "").lower().strip()


def clean_text(text):
    text = normalize(text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def tokenize(text):
    words = clean_text(text).split()
    return [w for w in words if w not in COMMON_NOISE_WORDS]


def extract_name_from_upi(upi_id):
    if not upi_id:
        return ""

    name = upi_id.split("@")[0]
    name = re.sub(r'[\d._-]', ' ', name)
    return clean_text(name)


def fuzzy_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def token_similarity(tokens1, tokens2):
    set1 = set(tokens1)
    set2 = set(tokens2)

    if not set1 or not set2:
        return 0

    return len(set1 & set2) / len(set1 | set2)


def combined_similarity(name1, name2):
    tokens1 = tokenize(name1)
    tokens2 = tokenize(name2)

    token_score = token_similarity(tokens1, tokens2)
    fuzzy_score = fuzzy_similarity(" ".join(tokens1), " ".join(tokens2))

    return max(token_score, fuzzy_score)


def extract_possible_names(text):
    text = normalize(text)

    lines = text.split("\n")
    candidates = []

    for line in lines:
        if any(k in line for k in ["name", "from", "to", "beneficiary"]):
            candidates.append(line)

    # fallback: use full text
    if not candidates:
        candidates.append(text)

    return candidates


def make_signal(score, confidence, reason):
    return {
        "type": "name_mismatch",
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def deduplicate(signals):
    seen = set()
    unique = []

    for s in signals:
        key = s["reason"]
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def detect_name_mismatch(upi_ids, detected_text):
    signals = []

    if not upi_ids or not detected_text:
        return _empty_response()

    possible_names = extract_possible_names(detected_text)

    for upi in upi_ids:
        upi_name = extract_name_from_upi(upi)

        if not upi_name:
            continue

        best_similarity = 0

        for name in possible_names:
            sim = combined_similarity(upi_name, name)
            best_similarity = max(best_similarity, sim)

        # -------------------------------
        # DECISION LOGIC (SMART 🔥)
        # -------------------------------
        if best_similarity < 0.25:
            signals.append(make_signal(
                3,
                0.9,
                f"UPI '{upi}' strongly mismatches detected name"
            ))

        elif best_similarity < 0.5:
            signals.append(make_signal(
                2,
                0.75,
                f"UPI '{upi}' partially mismatches detected name"
            ))

    # -------------------------------
    # CLEAN SIGNALS
    # -------------------------------
    signals = deduplicate(signals)

    # -------------------------------
    # FINAL SCORING
    # -------------------------------
    total_score = sum(s["score"] for s in signals)
    risk_score = min(total_score, 10)

    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
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
# EMPTY
# -------------------------------
def _empty_response():
    return {
        "risk_score": 0,
        "risk_level": "LOW",
        "confidence": 0.0,
        "signals": [],
        "reasons": []
    }
# backend/services/name_matcher.py

"""
SuRaksha Name Mismatch Verification Service

This service detects merchant spoofing scams (e.g., a sticker displaying a store name
like "Sharma Kirana Store" but actually registering a personal VPA like "hackers_node@ybl").
It extracts name candidates from the screenshot OCR, parses name tokens from the VPA,
and computes a similarity score using tokenized Jaccard indices and fuzzy SequenceMatcher comparisons.
"""

import re
from difflib import SequenceMatcher

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
# Words commonly seen in transaction logs that skew name comparison metrics
COMMON_NOISE_WORDS = [
    "upi", "bank", "payment", "paid", "received",
    "account", "transfer", "transaction"
]


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------
def normalize(text):
    """Lowers and strips text values to standardize string matching."""
    return (text or "").lower().strip()


def clean_text(text):
    """Removes all non-alphabetic characters and normalizes spaces."""
    text = normalize(text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def tokenize(text):
    """Splits string into lowercase alphanumeric tokens, filtering out noise words."""
    words = clean_text(text).split()
    return [w for w in words if w not in COMMON_NOISE_WORDS]


def extract_name_from_upi(upi_id):
    """
    Parses a VPA address to extract potential name tokens.
    
    Why: VPA addresses split the local part before the "@" symbol. By removing numbers,
    dots, dashes, and underscores, we isolate the phonetic name components.
    """
    if not upi_id:
        return ""

    name = upi_id.split("@")[0]
    name = re.sub(r'[\d._-]', ' ', name)
    return clean_text(name)


def fuzzy_similarity(a, b):
    """Calculates Gestalt Pattern Matching ratio (0.0 - 1.0) between strings."""
    return SequenceMatcher(None, a, b).ratio()


def token_similarity(tokens1, tokens2):
    """
    Computes a Jaccard Similarity index (intersection over union) of token sets.
    
    Why: Token set overlap is order-independent, which is critical since names can be
    re-ordered (e.g., "Sharma Suraj" vs "Suraj Sharma").
    """
    set1 = set(tokens1)
    set2 = set(tokens2)

    if not set1 or not set2:
        return 0

    return len(set1 & set2) / len(set1 | set2)


def combined_similarity(name1, name2):
    """
    Aggregates token and string fuzzy metrics into a single matching score.
    
    Why: Combining token set overlap (order-invariant) with fuzzy SequenceMatcher (edit-distance)
    provides high accuracy for varying names. A substring containment check is used
    as a fast shortcut (e.g., "sharmakirana" inside "sharma kirana store") to reduce false alerts.
    """
    tokens1 = tokenize(name1)
    tokens2 = tokenize(name2)

    if not tokens1 or not tokens2:
        return 0.0

    str1 = "".join(tokens1)
    str2 = "".join(tokens2)

    # Substring containment check prevents false positives on compressed user names
    if str1 in str2 or str2 in str1:
        return 1.0

    token_score = token_similarity(tokens1, tokens2)
    fuzzy_score = fuzzy_similarity(" ".join(tokens1), " ".join(tokens2))

    # Return the maximum score of Jaccard vs edit-distance to avoid penalizing word re-ordering
    return max(token_score, fuzzy_score)


def extract_possible_names(text):
    """
    Scans screenshot OCR lines for patterns indicating sender or payee names.
    Filters lines containing label terms. Falls back to comparing the entire text.
    """
    text = normalize(text)

    lines = text.split("\n")
    candidates = []

    for line in lines:
        if any(k in line for k in ["name", "from", "to", "beneficiary"]):
            candidates.append(line)

    # Fallback to the entire block of text if no specific name label matches
    if not candidates:
        candidates.append(text)

    return candidates


def make_signal(score, confidence, reason):
    """Factory helper to structure threat signal dictionaries."""
    return {
        "type": "name_mismatch",
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def deduplicate(signals):
    """Filters duplicate signals by description reasons to avoid inflating warnings."""
    seen = set()
    unique = []

    for s in signals:
        key = s["reason"]
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# ----------------------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------------------
def detect_name_mismatch(upi_ids, detected_text):
    """
    Cross-references VPA targets with invoice/recipient names on the screenshot.
    
    Args:
        upi_ids (List[str]): List of UPI VPAs parsed from the screenshot.
        detected_text (str): Complete OCR text from the screenshot.
        
    Returns:
        Dict: Final name matching risk score, confidence rating, and details.
    """
    signals = []

    if not upi_ids or not detected_text:
        return _empty_response()

    possible_names = extract_possible_names(detected_text)

    for upi in upi_ids:
        upi_name = extract_name_from_upi(upi)

        if not upi_name:
            continue

        best_similarity = 0

        # Compare the VPA name tokens against each extracted name candidate line
        for name in possible_names:
            sim = combined_similarity(upi_name, name)
            best_similarity = max(best_similarity, sim)

        # ----------------------------------------------------------------------
        # DECISION LOGIC (SMART 🔥)
        # ----------------------------------------------------------------------
        # Heuristics: similarity < 25% represents strong mismatch (high scam risk)
        # Heuristics: similarity < 50% represents partial mismatch (medium scam risk)
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

    # Deduplicate warning triggers
    signals = deduplicate(signals)

    # ----------------------------------------------------------------------
    # FINAL SCORING
    # ----------------------------------------------------------------------
    total_score = sum(s["score"] for s in signals)
    risk_score = min(total_score, 10)

    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(min(confidence, 0.95), 2)

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


# ----------------------------------------------------------------------
# EMPTY RESPONSE DEFAULT
# ----------------------------------------------------------------------
def _empty_response():
    return {
        "risk_score": 0,
        "risk_level": "LOW",
        "confidence": 0.0,
        "signals": [],
        "reasons": []
    }
# backend/services/explanation_engine.py

import re
import unicodedata

# -------------------------------
# CONFIG
# -------------------------------
UPI_HANDLES = {
    "ybl", "ibl", "okaxis", "okhdfcbank", "okicici",
    "oksbi", "paytm", "apl", "upi"
}

# 🌍 MULTILINGUAL SCAM TERMS
SUSPICIOUS_TERMS = [
    # English
    "reward", "gift", "refund", "offer", "help", "cashback", "win", "free",

    # Hindi / Marathi
    "इनाम", "पुरस्कार", "कैशबैक", "ऑफर", "जीतें", "फ्री",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার", "জিতুন"
]

# -------------------------------
# PRECOMPILED REGEX
# -------------------------------
STANDARD_PATTERN = re.compile(r"\b[a-z0-9._-]{2,}@[a-z]{2,}\b")
SPACED_PATTERN = re.compile(r"\b([a-z0-9._-]{2,})\s*@\s*([a-z]{2,})\b")
REPEAT_PATTERN = re.compile(r"(.)\1{3,}")


# -------------------------------
# NORMALIZATION
# -------------------------------
def normalize_text(text: str):
    return unicodedata.normalize("NFKC", (text or "")).lower().strip()


# -------------------------------
# EXTRACT UPI IDS
# -------------------------------
def extract_upi_ids(text: str):
    text = normalize_text(text)
    results = set()

    # 1. Standard pattern
    results.update(STANDARD_PATTERN.findall(text))

    # 2. Fix spaced '@'
    for name, handle in SPACED_PATTERN.findall(text):
        results.add(f"{name}@{handle}")

    # 3. OCR fix: missing '@'
    for handle in UPI_HANDLES:
        pattern = re.compile(rf"\b([a-z0-9._-]{{3,}}){handle}\b")
        for match in pattern.findall(text):
            results.add(f"{match}@{handle}")

    # 4. Validate + clean
    return list({
        upi.strip()
        for upi in results
        if _is_valid_upi(upi)
    })


# -------------------------------
# VALIDATION (STRICT)
# -------------------------------
def _is_valid_upi(upi: str):
    if "@" not in upi:
        return False

    parts = upi.split("@", 1)
    if len(parts) != 2:
        return False

    name, handle = parts

    # realistic constraints
    if not (3 <= len(name) <= 50):
        return False

    if not re.match(r"^[a-z0-9._-]+$", name):
        return False

    return True


# -------------------------------
# DETECT SUSPICIOUS UPI IDs
# -------------------------------
def detect_suspicious_upi(upi_ids):
    suspicious = []
    reasons = {}

    for upi in upi_ids:
        lower_upi = normalize_text(upi)
        name, handle = lower_upi.split("@", 1)

        flags = []

        # -------------------------------
        # 1. Keyword-based suspicion (MULTILINGUAL)
        # -------------------------------
        for term in SUSPICIOUS_TERMS:
            if term in lower_upi:
                flags.append(f"Suspicious term: {term}")

        # -------------------------------
        # 2. Too many digits
        # -------------------------------
        digit_ratio = sum(c.isdigit() for c in name) / len(name)
        if digit_ratio > 0.5:
            flags.append("Too many numbers")

        # -------------------------------
        # 3. Random / long IDs
        # -------------------------------
        if len(name) > 25:
            flags.append("Unusually long ID")

        # -------------------------------
        # 4. Repeated characters
        # -------------------------------
        if REPEAT_PATTERN.search(name):
            flags.append("Repeated characters")

        # -------------------------------
        # 5. Unknown UPI handle (STRONG SIGNAL 🔥)
        # -------------------------------
        if handle not in UPI_HANDLES:
            flags.append("Unknown UPI handle")

        # -------------------------------
        # FINAL
        # -------------------------------
        if flags:
            suspicious.append(upi)
            reasons[upi] = flags

    return {
        "suspicious_upis": list(set(suspicious)),
        "reasons": reasons
    }


# -------------------------------
# 🔥 NEW: MULTILINGUAL TEXT SCAN
# (for messages, OCR text, etc.)
# -------------------------------
def detect_multilingual_scam(text: str):
    text = normalize_text(text)

    detected = []

    for term in SUSPICIOUS_TERMS:
        if term in text:
            detected.append(term)

    return {
        "detected_terms": list(set(detected)),
        "is_suspicious": len(detected) > 0
    }
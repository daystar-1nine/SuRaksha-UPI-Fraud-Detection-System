# backend/services/qr_risk_analyzer.py

import re
import unicodedata

# -------------------------------
# CONFIG (MULTILINGUAL 🔥)
# -------------------------------
SUSPICIOUS_TERMS = [
    # English
    "reward", "gift", "refund", "offer",
    "support", "help", "cashback", "win", "free",

    # Hindi / Marathi (Devanagari)
    "इनाम", "पुरस्कार", "कैशबैक", "ऑफर",
    "जीतें", "फ्री", "मदत",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার",
    "জিতুন", "ফ্রি"
]

HIGH_RISK_HANDLES = ["ybl", "paytm", "ibl"]


# -------------------------------
# HELPERS
# -------------------------------
def normalize(text):
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text)).lower().strip()


def make_signal(signal_type, score, confidence, reason):
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def is_valid_upi(upi):
    return bool(re.match(r"^[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}$", upi or ""))


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def analyze_qr_risk(parsed_data):
    signals = []

    # -------------------------------
    # SAFE EXTRACTION
    # -------------------------------
    upi_id = normalize((parsed_data.get("pa") or [""])[0])
    payee_name = normalize((parsed_data.get("pn") or [""])[0])
    note = normalize((parsed_data.get("tn") or [""])[0])
    amount = (parsed_data.get("am") or [""])[0]

    combined_text = f"{upi_id} {payee_name} {note}"

    # -------------------------------
    # 1. MULTILINGUAL SUSPICIOUS TERMS 🔥
    # -------------------------------
    for term in SUSPICIOUS_TERMS:
        if term in combined_text:
            signals.append(make_signal(
                "suspicious_term",
                2,
                0.8,
                f"Suspicious term detected: {term}"
            ))

    # -------------------------------
    # 2. INVALID UPI
    # -------------------------------
    if upi_id and not is_valid_upi(upi_id):
        signals.append(make_signal(
            "invalid_upi",
            3,
            0.9,
            "Invalid UPI ID format"
        ))

    # -------------------------------
    # 3. MISSING PAYEE NAME
    # -------------------------------
    if not payee_name:
        signals.append(make_signal(
            "missing_name",
            2,
            0.75,
            "QR has no payee name"
        ))

    # -------------------------------
    # 4. AMOUNT ANALYSIS 💰
    # -------------------------------
    try:
        amt = float(amount) if amount else 0

        if amt > 50000:
            signals.append(make_signal(
                "very_high_amount",
                3,
                0.9,
                "Very high transaction amount"
            ))

        elif amt > 10000:
            signals.append(make_signal(
                "high_amount",
                2,
                0.75,
                "High transaction amount"
            ))

    except Exception:
        if amount:
            signals.append(make_signal(
                "invalid_amount",
                1,
                0.6,
                "Invalid amount format"
            ))

    # -------------------------------
    # 5. RISKY UPI HANDLE
    # -------------------------------
    if "@" in upi_id:
        handle = upi_id.split("@")[1]

        if handle in HIGH_RISK_HANDLES:
            signals.append(make_signal(
                "risky_handle",
                1,
                0.6,
                f"UPI handle often used in scams: {handle}"
            ))

    # -------------------------------
    # 6. GENERIC / FAKE NAME
    # -------------------------------
    if payee_name in ["support", "help", "customer care"]:
        signals.append(make_signal(
            "generic_name",
            2,
            0.8,
            "Generic payee name (possible scam)"
        ))

    # -------------------------------
    # FINAL SCORING
    # -------------------------------
    total_score = sum(s["score"] for s in signals)

    # Scale to 100
    risk_score = min(int(total_score * 10), 100)

    # Risk level
    if risk_score >= 75:
        level = "CRITICAL"
    elif risk_score >= 50:
        level = "HIGH"
    elif risk_score >= 30:
        level = "MEDIUM"
    elif risk_score >= 10:
        level = "LOW"
    else:
        level = "SAFE"

    # -------------------------------
    # CONFIDENCE
    # -------------------------------
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(min(confidence, 0.95), 2)

    # -------------------------------
    # FINAL RESPONSE
    # -------------------------------
    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "suspicious": len(signals) > 0,
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }
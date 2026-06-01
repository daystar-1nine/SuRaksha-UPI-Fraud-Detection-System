# backend/services/qr_risk_analyzer.py

import re
import unicodedata


# ────────────────────────────────────────
# SUSPICIOUS TERMS (MULTILINGUAL 🔥)
# ────────────────────────────────────────
SUSPICIOUS_TERMS = [
    # English — reward/scam patterns
    "reward", "gift", "refund", "offer", "support", "help",
    "cashback", "win", "free", "prize", "bonus", "lucky",
    "claim", "verify", "kyc", "otp", "wallet", "block",
    "urgent", "expire", "suspended", "activate", "limited",

    # Hindi / Marathi (Devanagari)
    "इनाम", "पुरस्कार", "कैशबैक", "ऑफर",
    "जीतें", "फ्री", "मदत", "रिफंड", "इनाम",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার", "জিতুন", "ফ্রি",

    # Tamil
    "பரிசு", "திரும்ப",

    # Telugu
    "బహుమతి", "రీఫండ్",
]

# ────────────────────────────────────────
# HIGH-RISK UPI HANDLES
# Extended to 25+ known scam VPA suffixes
# ────────────────────────────────────────
HIGH_RISK_HANDLES = {
    # Commonly spoofed / misused
    "ybl", "paytm", "ibl", "axl", "axisbank",
    # Fake bank handles
    "sbi", "icici", "hdfc", "pnb", "boi",
    # Phishing patterns
    "support", "helpdesk", "care", "refund", "reward",
    "kyc", "verify", "wallet", "block", "claim",
    # Generic free handles used in scams
    "upi", "pay", "cash", "money", "send",
}

# ────────────────────────────────────────
# TYPOSQUAT PATTERNS (spoof detection)
# ────────────────────────────────────────
SPOOFED_BRANDS = {
    "paytm":  ["paytml", "paytmm", "paymt", "patym", "paiytm"],
    "gpay":   ["gppay", "goglepay", "goooglepay", "gpayy"],
    "phonepe":["phonpee", "phonppe", "phonnpe", "fonpe"],
    "bhim":   ["bhiim", "bhhim", "biim"],
    "npci":   ["npcii", "npcci"],
    "sbi":    ["sbii", "sbii", "statebank"],
}


# ────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────
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
    """Validate UPI ID format: user@bank"""
    return bool(re.match(r"^[a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20}$", upi or ""))


def detect_typosquat(upi_id):
    """Check if UPI ID contains a misspelled brand name"""
    local = upi_id.split("@")[0] if "@" in upi_id else upi_id
    for brand, variants in SPOOFED_BRANDS.items():
        if brand in local:
            return None  # Genuine brand name — not a spoof
        for variant in variants:
            if variant in local:
                return brand
    return None


# ────────────────────────────────────────
# MAIN FUNCTION
# ────────────────────────────────────────
def analyze_qr_risk(parsed_data):
    signals = []

    # ── Safe extraction ──
    upi_id     = normalize((parsed_data.get("pa") or [""])[0])
    payee_name = normalize((parsed_data.get("pn") or [""])[0])
    note       = normalize((parsed_data.get("tn") or [""])[0])
    amount     = (parsed_data.get("am") or [""])[0]
    combined   = f"{upi_id} {payee_name} {note}"

    # ────────────────────────────────────────
    # 0. DATABASE BLACKLIST CHECK 🔥 (FIRST)
    # ────────────────────────────────────────
    from services.history_store import get_upi_count

    complaint_count = get_upi_count(upi_id) if upi_id else 0
    if complaint_count > 0:
        signals.append(make_signal(
            "database_blacklist",
            10,
            0.99,
            f"UPI address reported {complaint_count} time(s) in SuRaksha fraud database"
        ))
        return {
            "risk_score": 100,
            "risk_level": "CRITICAL",
            "confidence": 0.99,
            "suspicious": True,
            "fraud_type": "Known Fraudster",
            "detected_action": "Immediate Block — Multiple reports exist",
            "signals": signals,
            "reasons": [s["reason"] for s in signals]
        }

    # ────────────────────────────────────────
    # 1. MULTILINGUAL SUSPICIOUS TERMS
    # ────────────────────────────────────────
    matched_terms = []
    for term in SUSPICIOUS_TERMS:
        if term in combined:
            matched_terms.append(term)

    if matched_terms:
        score = min(len(matched_terms) * 1.5, 5)
        signals.append(make_signal(
            "suspicious_terms",
            score,
            0.82,
            f"Suspicious terms in QR: {', '.join(matched_terms[:4])}"
        ))

    # ────────────────────────────────────────
    # 2. INVALID UPI FORMAT
    # ────────────────────────────────────────
    if upi_id and not is_valid_upi(upi_id):
        signals.append(make_signal(
            "invalid_upi_format",
            3,
            0.92,
            f"Invalid UPI ID format: '{upi_id}'"
        ))

    # ────────────────────────────────────────
    # 3. MISSING PAYEE NAME
    # ────────────────────────────────────────
    if not payee_name:
        signals.append(make_signal(
            "missing_payee_name",
            2,
            0.75,
            "QR code has no payee name — anonymous transaction"
        ))

    # ────────────────────────────────────────
    # 4. AMOUNT ANALYSIS 💰
    # ────────────────────────────────────────
    try:
        amt = float(amount) if amount else 0

        if amt > 100000:
            signals.append(make_signal(
                "extreme_amount",
                4,
                0.93,
                f"Extremely high amount ₹{amt:,.0f} — verify manually"
            ))
        elif amt > 50000:
            signals.append(make_signal(
                "very_high_amount",
                3,
                0.88,
                f"Very high transaction amount ₹{amt:,.0f}"
            ))
        elif amt > 10000:
            signals.append(make_signal(
                "high_amount",
                1.5,
                0.72,
                f"High transaction amount ₹{amt:,.0f}"
            ))
        elif 0 < amt < 1:
            # Re: "₹1 test payment" scam pattern
            signals.append(make_signal(
                "micro_amount",
                2,
                0.78,
                f"Micro amount ₹{amt} — often used in 'collect request' scam to verify account"
            ))

    except Exception:
        if amount:
            signals.append(make_signal(
                "invalid_amount",
                1,
                0.6,
                f"Amount field has invalid format: '{amount}'"
            ))

    # ────────────────────────────────────────
    # 5. RISKY UPI HANDLE
    # ────────────────────────────────────────
    if "@" in upi_id:
        handle = upi_id.split("@")[1]

        if handle in HIGH_RISK_HANDLES:
            signals.append(make_signal(
                "risky_handle",
                2,
                0.72,
                f"UPI handle '@{handle}' frequently appears in fraud cases"
            ))

    # ────────────────────────────────────────
    # 6. TYPOSQUAT / BRAND SPOOFING 🔥NEW
    # ────────────────────────────────────────
    spoofed_brand = detect_typosquat(upi_id)
    if spoofed_brand:
        signals.append(make_signal(
            "typosquat_brand",
            4,
            0.91,
            f"UPI ID appears to impersonate '{spoofed_brand}' with slight spelling variation"
        ))

    # ────────────────────────────────────────
    # 7. GENERIC / SUPPORT-SOUNDING NAME
    # ────────────────────────────────────────
    GENERIC_NAMES = {
        "support", "help", "customer care", "customer service",
        "helpdesk", "care center", "refund team", "kyc team",
        "bank support", "wallet support"
    }
    if payee_name in GENERIC_NAMES:
        signals.append(make_signal(
            "generic_payee_name",
            2.5,
            0.85,
            f"Payee name '{payee_name}' is a known scammer pattern"
        ))

    # ────────────────────────────────────────
    # 8. NOTE / PURPOSE ANALYSIS 🔥NEW
    # ────────────────────────────────────────
    SCAM_NOTE_PATTERNS = [
        "kyc update", "account verification", "otp", "pin",
        "bank blocked", "account blocked", "urgent payment",
        "claim reward", "claim prize", "verify account"
    ]
    for pattern in SCAM_NOTE_PATTERNS:
        if pattern in note:
            signals.append(make_signal(
                "scam_note_pattern",
                3,
                0.87,
                f"Transaction note contains scam phrase: '{pattern}'"
            ))
            break

    # ────────────────────────────────────────
    # FINAL SCORING
    # ────────────────────────────────────────
    total_score = sum(s["score"] for s in signals)
    risk_score = min(int(total_score * 8), 100)  # Scale: 8x (more sensitive)

    if risk_score >= 75:
        level = "CRITICAL"
    elif risk_score >= 50:
        level = "HIGH"
    elif risk_score >= 25:
        level = "MEDIUM"
    elif risk_score >= 10:
        level = "LOW"
    else:
        level = "SAFE"

    # Confidence (weighted)
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)
    confidence = round((weighted_conf / total_weight), 2) if total_weight else 0.0
    confidence = min(confidence, 0.97)

    # Fraud type classification
    fraud_type = "Unknown"
    if any(s["type"] == "typosquat_brand" for s in signals):
        fraud_type = "Brand Spoofing"
    elif any(s["type"] == "scam_note_pattern" for s in signals):
        fraud_type = "Social Engineering"
    elif any(s["type"] == "suspicious_terms" for s in signals):
        fraud_type = "Cashback/Reward Scam"
    elif any(s["type"] in ("risky_handle", "generic_payee_name") for s in signals):
        fraud_type = "Fake Merchant"
    elif level == "SAFE":
        fraud_type = "No Fraud Detected"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "suspicious": len(signals) > 0,
        "fraud_type": fraud_type,
        "detected_action": (
            "Do NOT proceed — high fraud risk" if risk_score >= 50
            else ("Verify carefully before paying" if risk_score >= 25
                  else "Looks safe — proceed with caution")
        ),
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }
# backend/services/qr_risk_analyzer.py

"""
SuRaksha QR Code Threat Analysis Service

This service evaluates scanned QR code payloads (typically decoded from upi:// pay URLs)
for a variety of fraud signals:
1. Malicious Web Redirects (blocking non-upi:// schemes that redirect to phishing sites)
2. Database Blacklist checks (direct lookup of reported scammer VPAs)
3. Cryptographic Signature Integrity (detecting physical sticker tampering via SHA-256 signature mismatch)
4. Typo-squatting / Brand Spoofing (detecting VPAs mimicking SBI, Paytm, PhonePe, etc.)
5. Multilingual Keyword Scans (flagging reward/scam terms in English, Hindi, Bengali, Tamil, Telugu)
6. Transaction Amount and Note anomalies (micro-payments, extreme payouts, scam purposes)
"""

import re
import unicodedata
import hashlib
import math
import time
from services.ml_classifier import predict_scam_probabilities
from utils.constants import TRUSTED_MERCHANTS


# ────────────────────────────────────────────────────────────────────────
# SUSPICIOUS TERMS (MULTILINGUAL 🔥)
# ────────────────────────────────────────────────────────────────────────
# Scammers target victims in their native language to increase trust.
# This list matches scam keywords across multiple major Indian languages.
SUSPICIOUS_TERMS = [
    # English — reward/scam patterns
    "reward", "gift", "refund", "offer", "support", "help",
    "cashback", "win", "free", "prize", "bonus", "lucky",
    "claim", "verify", "kyc", "otp", "wallet", "block",
    "urgent", "expire", "suspended", "activate", "limited",

    # Hindi / Marathi (Devanagari script)
    "इनाम", "पुरस्कार", "कैशबैक", "ऑफर",
    "जीतें", "फ्री", "मदत", "रिफंड", "इनाम",

    # Bengali
    "পুরস্কার", "ক্যাশব্যাক", "অফার", "জিতুন", "ফ্রি",

    # Tamil
    "பரிசு", "திரும்ப",

    # Telugu
    "బహుమతి", "రీఫండ్",
]

# ────────────────────────────────────────────────────────────────────────
# HIGH-RISK UPI HANDLES
# ────────────────────────────────────────────────────────────────────────
# Handles (PSP extensions) and words commonly abused in phishing VPAs
# to masquerade as official support desks or bank gateways.
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

# ────────────────────────────────────────────────────────────────────────
# TYPOSQUAT PATTERNS (spoof detection)
# ────────────────────────────────────────────────────────────────────────
# Maps popular payment brands to common misspellings used by scammers
# to trick users into believing they are transferring to a trusted brand.
SPOOFED_BRANDS = {
    "paytm":  ["paytml", "paytmm", "paymt", "patym", "paiytm"],
    "gpay":   ["gppay", "goglepay", "goooglepay", "gpayy"],
    "phonepe":["phonpee", "phonppe", "phonnpe", "fonpe"],
    "bhim":   ["bhiim", "bhhim", "biim"],
    "npci":   ["npcii", "npcci"],
    "sbi":    ["sbii", "sbii", "statebank"],
}


# ────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────
def normalize(text):
    """
    Cleans and standardizes input string to prevent evasion.
    Uses Unicode NFKC normalization to resolve homoglyphs/lookalike characters.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text)).lower().strip()


def make_signal(signal_type, score, confidence, reason):
    """Factory helper to structure threat signal dictionaries."""
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def is_valid_upi(upi):
    """
    Validates general UPI VPA format using strict regular expression constraints.
    Format: [username]@[psp]
    """
    return bool(re.match(r"^[a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20}$", upi or ""))


def detect_typosquat(upi_id):
    """
    Checks if a local VPA prefix contains a typosquatted variant of a top brand.
    
    If the brand is paytm (e.g. local name contains 'paytm'), it is fine.
    If it contains a misspelling like 'paytml', it triggers a typosquat alert.
    """
    local = upi_id.split("@")[0] if "@" in upi_id else upi_id
    for brand, variants in SPOOFED_BRANDS.items():
        if brand in local:
            return None  # Matches the exact brand keyword (genuine name context)
        for variant in variants:
            if variant in local:
                return brand
    return None


def to_paise(val):
    """
    Converts numeric/string amount to integer paise to eliminate floating-point representation errors.
    Returns integer paise >= 0, or None if invalid/negative/non-numeric.
    """
    if val is None or val == "":
        return None
    try:
        val_float = float(val)
        if math.isnan(val_float) or math.isinf(val_float) or val_float < 0:
            return None
        # Use round to safely convert 10000.00 -> 1000000 paise
        return int(round(val_float * 100))
    except (ValueError, TypeError):
        return None


def compute_canonical_signature(vpa: str, name: str, mam_str: str, am_str: str, cu: str, qr_id: str, ts: str, exp: str, secret: str) -> str:
    """
    Computes cryptographic SHA-256 hash covering all critical QR transaction parameters.
    """
    canonical = (
        f"{vpa.strip().lower()}|"
        f"{name.strip().lower()}|"
        f"{mam_str.strip()}|"
        f"{am_str.strip()}|"
        f"{cu.strip().upper()}|"
        f"{qr_id.strip()}|"
        f"{ts.strip()}|"
        f"{exp.strip()}|"
        f"{secret.strip()}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ────────────────────────────────────────────────────────────────────────
def analyze_qr_risk(parsed_data, raw_text="", requested_amount=None):
    """
    Main evaluation pipeline checking UPI parameters, signatures, and string features.
    
    Args:
        parsed_data (Dict): Decoded query arguments from the UPI URI string.
        raw_text (str): Raw scanned QR payload text (e.g. "upi://pay?pa=...").
        requested_amount (float|str|int, optional): Payer's proposed payment amount to validate against limits.
        
    Returns:
        Dict: Final QR risk determination payload.
    """
    signals = []

    # Safe extraction of UPI URL query parameters:
    # pa: Payee Address (VPA), pn: Payee Name, tn: Transaction Note, am: Fixed Amount, mam: Maximum Amount Limit
    upi_id     = normalize((parsed_data.get("pa") or [""])[0])
    payee_name = normalize((parsed_data.get("pn") or [""])[0])
    note       = normalize((parsed_data.get("tn") or [""])[0])
    amount_raw = (parsed_data.get("am") or [""])[0].strip()
    mam_raw    = (parsed_data.get("mam") or parsed_data.get("max_amount") or [""])[0].strip()
    currency   = (parsed_data.get("cu") or ["INR"])[0].strip().upper() or "INR"
    qr_id      = (parsed_data.get("qr_id") or parsed_data.get("id") or [""])[0].strip()
    ts_raw     = (parsed_data.get("ts") or [""])[0].strip()
    exp_raw    = (parsed_data.get("exp") or [""])[0].strip()
    signature  = (parsed_data.get("sign") or [""])[0].strip()

    combined   = f"{upi_id} {payee_name} {note}"

    # Integer paise conversions for precision monetary safety
    am_paise  = to_paise(amount_raw)
    mam_paise = to_paise(mam_raw)
    req_paise = to_paise(requested_amount) if requested_amount is not None else None

    # Determine QR Mode: Maximum Limit QR vs Fixed Amount QR vs Open QR
    if mam_paise is not None and mam_paise > 0:
        qr_mode = "max_limit"
        max_amount_val = mam_paise / 100.0
        fixed_amount_val = None
    elif am_paise is not None and am_paise > 0:
        qr_mode = "fixed_amount"
        max_amount_val = am_paise / 100.0
        fixed_amount_val = am_paise / 100.0
    else:
        qr_mode = "open"
        max_amount_val = None
        fixed_amount_val = None

    # ────────────────────────────────────────────────────────────────────────
    # -1. NON-UPI SCHEME / PHISHING REDIRECT CHECK 🔥
    # ────────────────────────────────────────────────────────────────────────
    if raw_text and "://" in raw_text and not raw_text.lower().startswith("upi://"):
        signals.append(make_signal(
            "malicious_web_redirect",
            10,
            0.99,
            "QR code contains a non-UPI URL scheme (potential phishing web redirect)"
        ))
        return {
            "risk_score": 100,
            "risk_level": "CRITICAL",
            "confidence": 0.99,
            "suspicious": True,
            "fraud_type": "Phishing Redirect",
            "detected_action": "Immediate Block — Malicious web redirect detected",
            "signals": signals,
            "reasons": [s["reason"] for s in signals],
            "constraints": {
                "qr_mode": "invalid",
                "is_signed": False,
                "signature_valid": False
            }
        }

    # 0. DIRECTORY REGISTRY CHECK 🔥
    # ────────────────────────────────────────────────────────────────────────
    from services.history_store import lookup_upi_in_directory
    
    dir_info = lookup_upi_in_directory(upi_id) if upi_id else None
    if dir_info:
        if dir_info["category"] == "unsafe":
            main_reason = f"Blacklisted {dir_info['subtype'].upper()} VPA ({dir_info['name']}): {dir_info['description']}"
            signals.append(make_signal(
                "directory_blacklist",
                10,
                0.99,
                main_reason
            ))
            reasons_list = [main_reason]
            if dir_info.get("complaints"):
                for c in dir_info["complaints"]:
                    reasons_list.append(f"Cyber Complaint: {c}")

            return {
                "risk_score": 100,
                "risk_level": "CRITICAL",
                "confidence": 0.99,
                "suspicious": True,
                "fraud_type": f"Criminal / {dir_info['subtype'].capitalize()}",
                "detected_action": "Immediate Block — Listed in National Cyber Fraud Registry",
                "signals": signals,
                "reasons": reasons_list,
                "constraints": {
                    "qr_mode": qr_mode,
                    "max_amount": max_amount_val,
                    "fixed_amount": fixed_amount_val,
                    "is_signed": bool(signature),
                    "signature_valid": False
                }
            }
        elif dir_info["category"] == "medium":
            main_reason = f"Suspect {dir_info['subtype'].upper()} VPA ({dir_info['name']}): {dir_info['description']}"
            signals.append(make_signal(
                "directory_medium_risk",
                4.0,
                0.85,
                main_reason
            ))
            reasons_list = [main_reason]
            if dir_info.get("complaints"):
                for c in dir_info["complaints"]:
                    reasons_list.append(f"Caution Flag: {c}")

            return {
                "risk_score": 35,
                "risk_level": "MEDIUM",
                "confidence": 0.85,
                "suspicious": True,
                "fraud_type": f"Suspect / {dir_info['subtype'].capitalize()}",
                "detected_action": "Verify carefully before paying — Unverified profile",
                "signals": signals,
                "reasons": reasons_list,
                "constraints": {
                    "qr_mode": qr_mode,
                    "max_amount": max_amount_val,
                    "fixed_amount": fixed_amount_val,
                    "is_signed": bool(signature),
                    "signature_valid": False
                }
            }
        elif dir_info["category"] == "safe":
            signals.append(make_signal(
                "directory_whitelist",
                0.0,
                1.0,
                f"Verified Safe {dir_info['subtype'].capitalize()} VPA: {dir_info['name']} ({dir_info['description']})"
            ))

    # ────────────────────────────────────────────────────────────────────────
    # 0. DATABASE BLACKLIST CHECK 🔥
    # ────────────────────────────────────────────────────────────────────────
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
            "reasons": [s["reason"] for s in signals],
            "constraints": {
                "qr_mode": qr_mode,
                "max_amount": max_amount_val,
                "fixed_amount": fixed_amount_val,
                "is_signed": bool(signature),
                "signature_valid": False
            }
        }

    # ────────────────────────────────────────────────────────────────────────
    # 0.5. EXPIRY CHECK ⏳
    # ────────────────────────────────────────────────────────────────────────
    is_expired = False
    if exp_raw:
        try:
            exp_time = float(exp_raw)
            if exp_time > 0 and time.time() > exp_time:
                is_expired = True
                signals.append(make_signal(
                    "expired_qr_code",
                    10.0,
                    0.99,
                    f"QR code has expired (Expiry: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp_time))})"
                ))
        except (ValueError, TypeError):
            pass

    # ────────────────────────────────────────────────────────────────────────
    # 0.6. CRYPTOGRAPHIC SIGNATURE CHECK 🔒
    # ────────────────────────────────────────────────────────────────────────
    is_signed = bool(signature)
    signature_valid = False
    
    # Determine merchant secret
    merchant_secret = None
    if upi_id in TRUSTED_MERCHANTS:
        merchant_secret = TRUSTED_MERCHANTS[upi_id]["secret"]
    elif signature:
        merchant_secret = "SuRakshaShield2026"

    if merchant_secret:
        # 1. Try canonical signature covering all constraint fields
        expected_sign_canonical = compute_canonical_signature(
            vpa=upi_id,
            name=payee_name or "recipient",
            mam_str=mam_raw,
            am_str=amount_raw,
            cu=currency,
            qr_id=qr_id,
            ts=ts_raw,
            exp=exp_raw,
            secret=merchant_secret
        )

        # 2. Try legacy fallback signature for backward compatibility
        expected_sign_legacy = hashlib.sha256(f"{payee_name.strip()}{upi_id.strip()}{merchant_secret}".encode("utf-8")).hexdigest()

        if signature and (signature == expected_sign_canonical or signature == expected_sign_legacy):
            signature_valid = True
        elif signature:
            # Signature present but mismatch -> Payload (VPA, name, or maximum limit) was altered!
            signature_valid = False
            signals.append(make_signal(
                "tampered_qr_signature",
                9.8,
                0.99,
                "Cryptographic signature verification failed: Maximum payment limit or merchant identity has been modified / tampered!"
            ))
        elif upi_id in TRUSTED_MERCHANTS and not signature:
            # Trusted merchant ID found, but scanned QR lacks a signature parameter
            signature_valid = False
            signals.append(make_signal(
                "unsigned_trusted_merchant",
                9.5,
                0.98,
                f"Physical sticker tampering detected: '{payee_name}' is a registered store but lacks a valid SuRaksha Cryptographic signature"
            ))

    # ────────────────────────────────────────────────────────────────────────
    # 0.7. PAYMENT AMOUNT VALIDATION (SECURITY ENFORCEMENT) 💰
    # ────────────────────────────────────────────────────────────────────────
    payment_validation = None
    if requested_amount is not None:
        if req_paise is None or req_paise <= 0:
            signals.append(make_signal(
                "invalid_payment_amount",
                10.0,
                0.99,
                f"Invalid payment amount: '{requested_amount}'. Payment amount must be greater than ₹0."
            ))
            payment_validation = {
                "requested_amount": requested_amount,
                "allowed": False,
                "reason": "Payment amount must be greater than ₹0."
            }
        elif qr_mode == "max_limit" and mam_paise is not None:
            if req_paise > mam_paise:
                signals.append(make_signal(
                    "amount_exceeds_max_limit",
                    10.0,
                    0.99,
                    f"Payment amount ₹{req_paise/100:,.2f} exceeds maximum allowed limit of ₹{mam_paise/100:,.2f}."
                ))
                payment_validation = {
                    "requested_amount": req_paise / 100.0,
                    "max_limit": mam_paise / 100.0,
                    "allowed": False,
                    "reason": f"Payment amount ₹{req_paise/100:,.2f} exceeds maximum allowed limit of ₹{mam_paise/100:,.2f}."
                }
            else:
                # Allowed: 0 < req_paise <= mam_paise
                payment_validation = {
                    "requested_amount": req_paise / 100.0,
                    "max_limit": mam_paise / 100.0,
                    "allowed": True,
                    "reason": f"Payment of ₹{req_paise/100:,.2f} is within maximum limit of ₹{mam_paise/100:,.2f}."
                }
        elif qr_mode == "fixed_amount" and am_paise is not None:
            if req_paise != am_paise:
                signals.append(make_signal(
                    "amount_mismatch_fixed_qr",
                    10.0,
                    0.99,
                    f"Payment amount ₹{req_paise/100:,.2f} does not match fixed QR amount of ₹{am_paise/100:,.2f}."
                ))
                payment_validation = {
                    "requested_amount": req_paise / 100.0,
                    "fixed_amount": am_paise / 100.0,
                    "allowed": False,
                    "reason": f"Payment amount must match fixed amount of ₹{am_paise/100:,.2f}."
                }
            else:
                payment_validation = {
                    "requested_amount": req_paise / 100.0,
                    "fixed_amount": am_paise / 100.0,
                    "allowed": True,
                    "reason": f"Payment matches fixed QR amount of ₹{am_paise/100:,.2f}."
                }
        else:
            # Open QR
            payment_validation = {
                "requested_amount": req_paise / 100.0,
                "allowed": True,
                "reason": f"Payment of ₹{req_paise/100:,.2f} is valid."
            }

    # If valid signature is active and no other critical failures
    if signature_valid and not is_expired and (payment_validation is None or payment_validation.get("allowed", True)):
        signals.append(make_signal(
            "verified_merchant_shield",
            0.0,
            1.0,
            f"Verified Merchant Shield active: Identity and integrity confirmed ({'Max Limit ₹' + str(max_amount_val) if qr_mode == 'max_limit' else 'Fixed ₹' + str(fixed_amount_val) if qr_mode == 'fixed_amount' else 'Open QR'})"
        ))
        return {
            "risk_score": 0,
            "risk_level": "SAFE",
            "confidence": 1.0,
            "suspicious": False,
            "fraud_type": "Verified Merchant Shield",
            "detected_action": "SuRaksha Cryptographic Signature Validated",
            "signals": signals,
            "reasons": [s["reason"] for s in signals],
            "constraints": {
                "qr_mode": qr_mode,
                "max_amount": max_amount_val,
                "max_amount_paise": mam_paise or am_paise,
                "fixed_amount": fixed_amount_val,
                "fixed_amount_paise": am_paise if qr_mode == "fixed_amount" else None,
                "currency": currency,
                "qr_id": qr_id,
                "timestamp": ts_raw,
                "expiry": exp_raw,
                "is_expired": is_expired,
                "is_signed": is_signed,
                "signature_valid": signature_valid,
                "payment_validation": payment_validation
            }
        }

    # ────────────────────────────────────────────────────────────────────────
    # 1. MULTILINGUAL SUSPICIOUS TERMS
    # ────────────────────────────────────────────────────────────────────────
    # Scan VPA details, display name, and note fields for regional refund/lottery patterns.
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

    # ────────────────────────────────────────────────────────────────────────
    # 2. INVALID UPI FORMAT
    # ────────────────────────────────────────────────────────────────────────
    if upi_id and not is_valid_upi(upi_id):
        signals.append(make_signal(
            "invalid_upi_format",
            3,
            0.92,
            f"Invalid UPI ID format: '{upi_id}'"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 3. MISSING PAYEE NAME
    # ────────────────────────────────────────────────────────────────────────
    # Standard payments should specify a clear recipient display name.
    # Missing payee name suggests a custom-generated anonymous payment hook.
    if not payee_name:
        signals.append(make_signal(
            "missing_payee_name",
            2,
            0.75,
            "QR code has no payee name — anonymous transaction"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 4. AMOUNT ANALYSIS 💰
    # ────────────────────────────────────────────────────────────────────────
    # Evaluate risks based on target payment magnitude.
    try:
        amt = float(amount_raw or mam_raw or 0)

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
            # "₹1 Verification Test" Scam:
            # Scammers send collect requests of ₹0.50 to victims, telling them it is a "test payment"
            # to verify their account. Once the victim approves, the scammer initiates a large debit.
            signals.append(make_signal(
                "micro_amount",
                2,
                0.78,
                f"Micro amount ₹{amt} — often used in 'collect request' scam to verify account"
            ))

    except Exception:
        if amount_raw or mam_raw:
            signals.append(make_signal(
                "invalid_amount",
                1,
                0.6,
                f"Amount field has invalid format: '{amount_raw or mam_raw}'"
            ))

    # ────────────────────────────────────────────────────────────────────────
    # 5. RISKY UPI HANDLE
    # ────────────────────────────────────────────────────────────────────────
    # Certain handles are commonly chosen by fraud developers because they offer easy onboarding.
    if "@" in upi_id:
        handle = upi_id.split("@")[1]

        if handle in HIGH_RISK_HANDLES:
            signals.append(make_signal(
                "risky_handle",
                2,
                0.72,
                f"UPI handle '@{handle}' frequently appears in fraud cases"
            ))

    # ────────────────────────────────────────────────────────────────────────
    # 6. TYPOSQUAT / BRAND SPOOFING
    # ────────────────────────────────────────────────────────────────────────
    # Flag spoofed accounts mimicking brands like GPay or Paytm.
    spoofed_brand = detect_typosquat(upi_id)
    if spoofed_brand:
        signals.append(make_signal(
            "typosquat_brand",
            4,
            0.91,
            f"UPI ID appears to impersonate '{spoofed_brand}' with slight spelling variation"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 7. GENERIC / SUPPORT-SOUNDING NAME
    # ────────────────────────────────────────────────────────────────────────
    # Scammers label their accounts "Paytm Support" or "SBI Refund Team" to look official.
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

    # ────────────────────────────────────────────────────────────────────────
    # 8. NOTE / PURPOSE ANALYSIS
    # ────────────────────────────────────────────────────────────────────────
    # Check transaction notes for terms that claim blockages or prompt PIN entries.
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

    # ────────────────────────────────────────────────────────────────────────
    # FINAL SCORING
    # ────────────────────────────────────────────────────────────────────────
    total_score = sum(s["score"] for s in signals)
    # Multiply score to map to risk percentage (more responsive than visual tamper aggregation)
    risk_score = min(int(total_score * 8), 100)

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

    # Compute weighted average confidence factor
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)
    confidence = round((weighted_conf / total_weight), 2) if total_weight else 0.0
    confidence = min(confidence, 0.97)

    # Classify category taxonomic type based on primary warning trigger
    fraud_type = "Unknown"
    detected_action = (
        "Do NOT proceed — high fraud risk" if risk_score >= 50
        else ("Verify carefully before paying" if risk_score >= 25
              else "Looks safe — proceed with caution")
    )

    if any(s["type"] == "tampered_qr_signature" for s in signals):
        fraud_type = "Cryptographic Tampering Detected"
        detected_action = "INVALID — QR DATA TAMPERED"
        risk_score = 100
        level = "CRITICAL"
        confidence = 0.99
    elif any(s["type"] == "expired_qr_code" for s in signals):
        fraud_type = "Expired QR Code"
        detected_action = "QR EXPIRED — Payment Blocked"
        risk_score = 100
        level = "CRITICAL"
        confidence = 0.99
    elif any(s["type"] == "typosquat_brand" for s in signals):
        fraud_type = "Brand Spoofing"
    elif any(s["type"] == "scam_note_pattern" for s in signals):
        fraud_type = "Social Engineering"
    elif any(s["type"] == "suspicious_terms" for s in signals):
        fraud_type = "Cashback/Reward Scam"
    elif any(s["type"] in ("risky_handle", "generic_payee_name") for s in signals):
        fraud_type = "Fake Merchant"
    elif level == "SAFE":
        fraud_type = "No Fraud Detected"

    # Query the ML probability model with all parsed text strings for added signal verification
    ml_probs = predict_scam_probabilities(combined)
    top_ml_category = max(ml_probs, key=ml_probs.get) if ml_probs else "unknown"

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
        "ml_analysis": {
            "probabilities": ml_probs,
            "top_category": top_ml_category
        },
        "signals": signals,
        "reasons": [s["reason"] for s in signals],
        "constraints": {
            "qr_mode": qr_mode,
            "max_amount": max_amount_val,
            "max_amount_paise": mam_paise or am_paise,
            "fixed_amount": fixed_amount_val,
            "fixed_amount_paise": am_paise if qr_mode == "fixed_amount" else None,
            "currency": currency,
            "qr_id": qr_id,
            "timestamp": ts_raw,
            "expiry": exp_raw,
            "is_expired": is_expired,
            "is_signed": is_signed,
            "signature_valid": signature_valid,
            "payment_validation": payment_validation
        }
    }
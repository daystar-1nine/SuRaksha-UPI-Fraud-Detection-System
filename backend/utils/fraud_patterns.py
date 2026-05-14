# backend/utils/fraud_patterns.py

# -------------------------------
# 🎯 MASTER FRAUD PATTERN DATABASE
# -------------------------------

FRAUD_PATTERNS = [
    # -------------------------
    # 💰 REWARD / GREED BAIT
    # -------------------------
    {
        "pattern": ["reward", "cashback", "bonus", "gift", "offer", "free", "win"],
        "category": "greed",
        "score": 2,
        "confidence": 0.7
    },

    # Hindi / Marathi
    {
        "pattern": ["इनाम", "पुरस्कार", "कैशबैक", "ऑफर", "जीतें", "फ्री"],
        "category": "greed",
        "score": 2,
        "confidence": 0.75
    },

    # Bengali
    {
        "pattern": ["পুরস্কার", "ক্যাশব্যাক", "অফার", "জিতুন"],
        "category": "greed",
        "score": 2,
        "confidence": 0.75
    },

    # Tamil
    {
        "pattern": ["பரிசு", "கேஷ்பேக்", "சலுகை"],
        "category": "greed",
        "score": 2,
        "confidence": 0.75
    },

    # -------------------------
    # ⏰ URGENCY / PRESSURE
    # -------------------------
    {
        "pattern": [
            "urgent", "act now", "limited time",
            "verify immediately", "hurry", "today only"
        ],
        "category": "urgency",
        "score": 2,
        "confidence": 0.8
    },

    # Hindi
    {
        "pattern": ["तुरंत", "अभी करें", "जल्दी करें"],
        "category": "urgency",
        "score": 2,
        "confidence": 0.8
    },

    # -------------------------
    # ⚠️ FEAR / THREAT
    # -------------------------
    {
        "pattern": [
            "account blocked", "suspended",
            "deactivated", "restricted", "expired"
        ],
        "category": "fear",
        "score": 3,
        "confidence": 0.85
    },

    # Hindi
    {
        "pattern": ["खाता बंद", "सस्पेंड", "ब्लॉक"],
        "category": "fear",
        "score": 3,
        "confidence": 0.85
    },

    # -------------------------
    # 🔐 OTP / KYC FRAUD
    # -------------------------
    {
        "pattern": [
            "share otp", "send otp", "otp required",
            "complete kyc", "update kyc"
        ],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9
    },

    # Hindi
    {
        "pattern": ["otp साझा करें", "kyc अपडेट करें"],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9
    },

    # Marathi
    {
        "pattern": ["otp शेअर करा"],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9
    },

    # Tamil
    {
        "pattern": ["otp பகிரவும்"],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9
    }
]


# -------------------------------
# 🔍 QUICK ACCESS LISTS (BACKWARD COMPATIBILITY)
# -------------------------------

# Flattened lists for old modules (optional)
SUSPICIOUS_KEYWORDS = [
    word
    for group in FRAUD_PATTERNS
    for word in group["pattern"]
]

URGENCY_PHRASES = [
    word
    for group in FRAUD_PATTERNS
    if group["category"] == "urgency"
    for word in group["pattern"]
]

SCAM_SENTENCES = [
    word
    for group in FRAUD_PATTERNS
    if group["category"] in ["otp_fraud", "fear"]
    for word in group["pattern"]
]
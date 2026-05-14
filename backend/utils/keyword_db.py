# backend/utils/keyword_db.py

# -------------------------------
# 🎯 SMART KEYWORD DATABASE
# -------------------------------

KEYWORD_DB = [
    # -------------------------
    # 🔐 OTP FRAUD
    # -------------------------
    {
        "keywords": ["otp", "share otp", "send otp"],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9,
        "message": "Banks never ask for OTPs."
    },

    {
        "keywords": ["otp साझा करें", "otp शेअर करा", "otp பகிரவும்"],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.9,
        "message": "OTP sharing is unsafe."
    },

    # -------------------------
    # ⏰ URGENCY / PRESSURE
    # -------------------------
    {
        "keywords": ["urgent", "act now", "immediately", "hurry"],
        "category": "urgency",
        "score": 2,
        "confidence": 0.8,
        "message": "Scammers use urgency to create panic."
    },

    {
        "keywords": ["तुरंत", "अभी करें", "जल्दी करें"],
        "category": "urgency",
        "score": 2,
        "confidence": 0.8,
        "message": "Urgency detected."
    },

    # -------------------------
    # 💰 REWARD / GREED
    # -------------------------
    {
        "keywords": ["reward", "cashback", "offer", "bonus", "gift", "free"],
        "category": "greed",
        "score": 2,
        "confidence": 0.75,
        "message": "Unexpected rewards may be scams."
    },

    {
        "keywords": ["इनाम", "पुरस्कार", "कैशबैक", "ऑफर", "ফ্রি", "পুরস্কার"],
        "category": "greed",
        "score": 2,
        "confidence": 0.75,
        "message": "Reward-based bait detected."
    },

    # -------------------------
    # ⚠️ ACCOUNT THREAT
    # -------------------------
    {
        "keywords": ["blocked", "suspended", "restricted", "deactivated"],
        "category": "fear",
        "score": 3,
        "confidence": 0.85,
        "message": "Fake account threat warning."
    },

    {
        "keywords": ["खाता बंद", "ब्लॉक", "সাসপেন্ড"],
        "category": "fear",
        "score": 3,
        "confidence": 0.85,
        "message": "Account threat detected."
    },

    # -------------------------
    # 🧾 KYC FRAUD
    # -------------------------
    {
        "keywords": ["kyc", "update kyc", "complete kyc"],
        "category": "kyc_fraud",
        "score": 3,
        "confidence": 0.85,
        "message": "KYC scams are common."
    },

    # -------------------------
    # 🔗 PHISHING LINKS
    # -------------------------
    {
        "keywords": ["click link", "verify link", "login here"],
        "category": "phishing",
        "score": 3,
        "confidence": 0.85,
        "message": "Avoid clicking unknown links."
    }
]


# -------------------------------
# 🔍 BACKWARD COMPATIBILITY
# -------------------------------

SCAM_KEYWORDS = {
    kw: entry["message"]
    for entry in KEYWORD_DB
    for kw in entry["keywords"]
}
# backend/utils/fraud_patterns.py

FRAUD_PATTERNS = [
    # -------------------------
    # 💰 REWARD / GREED BAIT / LOTTERY
    # -------------------------
    {
        "pattern": [
            "reward", "cashback", "bonus", "gift", "offer", "free", "win",
            "lottery", "lucky draw", "winner", "kbc", "jeep winner", "mahindra winner", "crorepat"
        ],
        "category": "greed",
        "score": 3,
        "confidence": 0.8
    },
    {
        "pattern": ["इनाम", "पुरस्कार", "कैशबैक", "ऑफर", "जीतें", "फ्री", "लॉटरी", "विजेता"],
        "category": "greed",
        "score": 3,
        "confidence": 0.8
    },
    
    # -------------------------
    # ⏰ URGENCY / PRESSURE
    # -------------------------
    {
        "pattern": [
            "urgent", "act now", "limited time", "within 24 hours", "tonight",
            "verify immediately", "hurry", "today only", "immediately"
        ],
        "category": "urgency",
        "score": 3,
        "confidence": 0.85
    },
    {
        "pattern": ["तुरंत", "अभी करें", "जल्दी करें", "आज रात"],
        "category": "urgency",
        "score": 3,
        "confidence": 0.85
    },

    # -------------------------
    # ⚠️ FEAR / BANK / KYC THREAT
    # -------------------------
    {
        "pattern": [
            "account blocked", "suspended", "deactivated", "restricted", "expired",
            "pan card", "kyc", "aadhar", "penalty", "permanent suspension",
            "bank account will be blocked", "update your details"
        ],
        "category": "fear_kyc",
        "score": 5,
        "confidence": 0.95
    },
    {
        "pattern": ["खाता बंद", "सस्पेंड", "ब्लॉक", "पैन कार्ड", "आधार", "केवाईसी"],
        "category": "fear_kyc",
        "score": 5,
        "confidence": 0.95
    },

    # -------------------------
    # ⚡ ELECTRICITY SCAM
    # -------------------------
    {
        "pattern": [
            "electricity", "power disconnect", "update bill", "electricity officer",
            "power will be disconnected", "unpaid bill", "disconnection"
        ],
        "category": "electricity_scam",
        "score": 4,
        "confidence": 0.9
    },
    {
        "pattern": ["बिजली", "कटेगी", "बिल अपडेट", "बिजली अधिकारी"],
        "category": "electricity_scam",
        "score": 4,
        "confidence": 0.9
    },

    # -------------------------
    # 💼 JOB / TASK SCAM
    # -------------------------
    {
        "pattern": [
            "part time", "work from home", "wfh", "daily income", "youtube like", 
            "telegram hr", "salary daily", "data entry job", "easy money"
        ],
        "category": "job_scam",
        "score": 4,
        "confidence": 0.85
    },
    
    # -------------------------
    # 📦 CUSTOMS / PARCEL SCAM
    # -------------------------
    {
        "pattern": [
            "customs fee", "parcel detained", "clearance fee", "fedex", "dhl",
            "package suspended", "pay delivery fee"
        ],
        "category": "parcel_scam",
        "score": 4,
        "confidence": 0.9
    },

    # -------------------------
    # 💸 LOAN SCAM
    # -------------------------
    {
        "pattern": [
            "pre-approved", "personal loan", "zero interest", "processing fee", 
            "cibil score", "instant approval", "loan amount"
        ],
        "category": "loan_scam",
        "score": 3,
        "confidence": 0.8
    },

    # -------------------------
    # 🔗 PHISHING LINKS / APPS
    # -------------------------
    {
        "pattern": [
            "click the link", "click below", "official portal", "verify link", 
            "download apk", "install app", "login here", "claim now", "bit.ly", "tinyurl"
        ],
        "category": "phishing",
        "score": 4,
        "confidence": 0.9
    },
    
    # -------------------------
    # 🔐 OTP FRAUD
    # -------------------------
    {
        "pattern": [
            "share otp", "send otp", "otp required", "do not share"
        ],
        "category": "otp_fraud",
        "score": 4,
        "confidence": 0.95
    }
]

# Flattened lists for backward compatibility
SUSPICIOUS_KEYWORDS = [
    word
    for group in FRAUD_PATTERNS
    if group["category"] not in ["urgency", "phishing"]
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
    if group["category"] in ["otp_fraud", "fear_kyc", "electricity_scam", "parcel_scam", "phishing"]
    for word in group["pattern"]
]

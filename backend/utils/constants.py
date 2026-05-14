# backend/utils/constants.py

# -------------------------------
# 🎯 GLOBAL SYSTEM CONFIG
# -------------------------------

APP_NAME = "SuRaksha Fraud Detection"
VERSION = "1.0"


# -------------------------------
# 📊 RISK SCORE THRESHOLDS
# -------------------------------
RISK_THRESHOLDS = {
    "SAFE": 0,
    "LOW": 20,
    "MEDIUM": 40,
    "HIGH": 60,
    "CRITICAL": 80
}


# -------------------------------
# ⚖️ WEIGHT CONFIG (MASTER ENGINE)
# -------------------------------
WEIGHTS = {
    "intent_mismatch": 40,
    "keyword_score": 20,
    "upi_pattern_score": 15,
    "behavior_score": 15,
    "name_mismatch_score": 25,
    "tampering": 15,
    "metadata": 10
}


# -------------------------------
# 🚨 ALERT MESSAGES
# -------------------------------
ALERTS = {
    "SAFE": "🟢 Safe",
    "LOW": "🟢 Low Risk",
    "MEDIUM": "🟡 Warning",
    "HIGH": "🟠 Danger",
    "CRITICAL": "🔴 FRAUD ALERT"
}


# -------------------------------
# 💳 PAYMENT DECISION RULE
# -------------------------------
SAFE_PAYMENT_THRESHOLD = 60  # risk_score >= 60 → unsafe


# -------------------------------
# 📁 FILE / IMAGE LIMITS
# -------------------------------
MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]

MAX_TEXT_LENGTH = 5000  # prevent abuse


# -------------------------------
# 🔍 OCR SETTINGS
# -------------------------------
OCR_LANGUAGES = "eng+hin+ben"
OCR_CONFIG = "--oem 3 --psm 6"


# -------------------------------
# 🔐 SECURITY LIMITS
# -------------------------------
MAX_UPI_PER_REQUEST = 10
MAX_REQUESTS_PER_MIN = 30


# -------------------------------
# 🧠 SIGNAL SCORING LIMITS
# -------------------------------
MAX_SIGNAL_SCORE = 10
MAX_CONFIDENCE = 0.95


# -------------------------------
# 🧾 QR ANALYSIS LIMITS
# -------------------------------
MAX_QR_TEXT_LENGTH = 2000


# -------------------------------
# 🔁 DUPLICATE DETECTION
# -------------------------------
ENABLE_IMAGE_HASH_CHECK = True


# -------------------------------
# ⚙️ DEBUG MODE
# -------------------------------
DEBUG = True
LOG_LEVEL = "INFO"
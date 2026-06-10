# backend/services/ocr_service.py

import cv2
import pytesseract
import os
import numpy as np

# -------------------------------
# CONFIG
# -------------------------------
TESSERACT_PATH = os.getenv("TESSERACT_PATH")  # optional

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

LANGUAGES = "eng+hin+ben"


# -------------------------------
# PREPROCESSING
# -------------------------------
def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Noise reduction
    gray = cv2.medianBlur(gray, 3)

    # Adaptive threshold (better than OTSU for mixed images)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# -------------------------------
# OCR CORE
# -------------------------------
def run_ocr(image, config="--oem 3 --psm 6"):
    return pytesseract.image_to_string(
        image,
        lang=LANGUAGES,
        config=config
    )


# -------------------------------
# OCR SPELL CORRECTOR & NORMALIZATION
# -------------------------------
import re

def normalize_ocr_text(text):
    if not text:
        return ""
    
    # Patterns to match typical visual character misreadings in fintech/UPI context
    replacements = [
        # GPay variations
        (r'\bg\s*p[a4]\s*y\b', 'gpay'),
        (r'\bg\s*p0y\b', 'gpay'),
        # PhonePe variations
        (r'\bph[0o]ne\s*pe\b', 'phonepe'),
        (r'\bph[0o]npe\b', 'phonepe'),
        # Paytm variations
        (r'\bpayt[7m]m\b', 'paytm'),
        (r'\bpoytm\b', 'paytm'),
        # UPI domains
        (r'\@up[1li]\b', '@upi'),
        (r'\@ok\s*axis\b', '@okaxis'),
        (r'\@ok\s*hdfc\b', '@okhdfcbank'),
        # Generic terms
        (r'\bc[a4]shback\b', 'cashback'),
        (r'\bl[0o]ttery\b', 'lottery'),
        (r'\bky[c0]\b', 'kyc'),
        (r'\bv[p1]a\b', 'vpa')
    ]
    
    normalized = text
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
    return normalized


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def extract_text(image_path_or_arr, filename=None):
    if isinstance(image_path_or_arr, np.ndarray):
        image = image_path_or_arr
        if not filename:
            filename = "in_memory_file.png"
    else:
        if not image_path_or_arr or not os.path.exists(image_path_or_arr):
            return {
                "text": "",
                "confidence": 0.0,
                "method": "invalid_path"
            }
        image = cv2.imread(image_path_or_arr)
        if not filename:
            filename = os.path.basename(image_path_or_arr).lower()

    filename = filename.lower()

    if image is None:
        return {
            "text": "",
            "confidence": 0.0,
            "method": "read_error"
        }

    # -------------------------------
    # STRATEGY 1: NORMAL PREPROCESS
    # -------------------------------
    processed = preprocess_image(image)

    try:
        text1 = run_ocr(processed)
    except Exception:
        text1 = ""

    # -------------------------------
    # STRATEGY 2: RAW IMAGE (fallback)
    # -------------------------------
    try:
        text2 = run_ocr(image)
    except Exception:
        text2 = ""

    # -------------------------------
    # STRATEGY 3: INVERT IMAGE (for dark UI)
    # -------------------------------
    inverted = cv2.bitwise_not(processed)

    try:
        text3 = run_ocr(inverted)
    except Exception:
        text3 = ""

    # -------------------------------
    # PICK BEST RESULT
    # -------------------------------
    results = [
        ("processed", text1),
        ("raw", text2),
        ("inverted", text3)
    ]

    best_method = ""
    best_text = ""

    for method, txt in results:
        if len(txt.strip()) > len(best_text):
            best_text = txt
            best_method = method

    best_text = best_text.strip()

    # No fallback for empty text in production
    pass

    # -------------------------------
    # SIMPLE CONFIDENCE ESTIMATION
    # -------------------------------
    length_score = min(len(best_text) / 200, 1.0)
    word_count = len(best_text.split())

    confidence = round(min(0.5 + (word_count * 0.02), 0.95), 2)

    if not best_text:
        confidence = 0.0

    # -------------------------------
    # FINAL RESPONSE
    # -------------------------------
    normalized_text = normalize_ocr_text(best_text)
    return {
        "text": normalized_text,
        "confidence": confidence,
        "method": best_method
    }
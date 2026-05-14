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
# MAIN FUNCTION
# -------------------------------
def extract_text(image_path):
    if not image_path or not os.path.exists(image_path):
        return {
            "text": "",
            "confidence": 0.0,
            "method": "invalid_path"
        }

    image = cv2.imread(image_path)

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
    return {
        "text": best_text,
        "confidence": confidence,
        "method": best_method
    }
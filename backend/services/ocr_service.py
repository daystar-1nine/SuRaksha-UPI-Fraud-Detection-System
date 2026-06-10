# backend/services/ocr_service.py

"""
SuRaksha OCR Text Extraction Service

This module handles optical character recognition (OCR) on screenshots.
To deal with diverse mobile UI layouts, dark/light themes, and varying screen brightness,
it applies several image processing techniques using OpenCV and runs multiple Tesseract passes:
1. Normal preprocessing (Adaptive Gaussian thresholding + median blur)
2. Raw unprocessed pass
3. Bitwise inversion pass (for dark mode/reversed theme layouts)
It also normalizes common visual OCR character misreadings (e.g., "g p0y" -> "gpay")
to ensure analytical engines match scam terms accurately.
"""

import cv2
import pytesseract
import os
import numpy as np

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
# Optional environment path for custom local Tesseract installations
TESSERACT_PATH = os.getenv("TESSERACT_PATH")

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# English, Hindi, and Bengali packages are pre-loaded to capture regional alert variations.
LANGUAGES = "eng+hin+ben"


# ----------------------------------------------------------------------
# PREPROCESSING
# ----------------------------------------------------------------------
def preprocess_image(image):
    """
    Applies filters to prepare the pixel grid for OCR character segmentation.
    
    Why: Global thresholding (like Otsu's method) fails when screenshots contain gradients,
    colored notifications, or mixed dark/light elements. Adaptive Gaussian thresholding
    evaluates pixel neighborhood windows locally, maintaining text crispness.
    """
    # Convert image to grayscale to reduce dimensionality from 3 color channels to 1
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply median blur to reduce salt-and-pepper noise without blurring text edges
    gray = cv2.medianBlur(gray, 3)

    # Dynamically threshold based on local neighborhood window of 11x11 pixels
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# ----------------------------------------------------------------------
# OCR CORE
# ----------------------------------------------------------------------
def run_ocr(image, config="--oem 3 --psm 6"):
    """
    Executes Tesseract command line OCR on the given image array.
    
    OEM 3: Default OCR Engine Mode (LSTM-based neural network model).
    PSM 6: Page Segmentation Mode assuming a single uniform block of text.
    """
    return pytesseract.image_to_string(
        image,
        lang=LANGUAGES,
        config=config
    )


# ----------------------------------------------------------------------
# OCR SPELL CORRECTOR & NORMALIZATION
# ----------------------------------------------------------------------
import re

def normalize_ocr_text(text):
    """
    Corrects frequent visual character replacement mistakes made by OCR engines.
    
    Why: Scammers use typos or specific branding layouts. Also, visual recognition
    often misreads 'm' as '7m', 'a' as '0' or '4', or adds whitespace. Standardizing
    these common errors prevents NLP heuristics from failing due to OCR noise.
    """
    if not text:
        return ""
    
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
        # Generic fintech terms
        (r'\bc[a4]shback\b', 'cashback'),
        (r'\bl[0o]ttery\b', 'lottery'),
        (r'\bky[c0]\b', 'kyc'),
        (r'\bv[p1]a\b', 'vpa')
    ]
    
    normalized = text
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
    return normalized


# ----------------------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------------------
def extract_text(image_path_or_arr, filename=None):
    """
    Performs multi-pass OCR on a screenshot to extract text.
    
    Why: Mobile apps vary between dark mode, light mode, and customized themes.
    By executing three distinct passes (normal thresholded, raw image, inverted thresholded)
    and selecting the pass that returns the most text characters, we maximize the reliability
    of screenshot text capture.
    
    Args:
        image_path_or_arr (str/np.ndarray): Local file path or a decoded image array.
        filename (str, optional): Original name of the uploaded file.
        
    Returns:
        Dict: Normalised text string, confidence heuristic, and the winning extraction method.
    """
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

    # ----------------------------------------------------------------------
    # STRATEGY 1: NORMAL PREPROCESS
    # ----------------------------------------------------------------------
    processed = preprocess_image(image)

    try:
        text1 = run_ocr(processed)
    except Exception:
        text1 = ""

    # ----------------------------------------------------------------------
    # STRATEGY 2: RAW IMAGE (fallback for colored backgrounds/gradients)
    # ----------------------------------------------------------------------
    try:
        text2 = run_ocr(image)
    except Exception:
        text2 = ""

    # ----------------------------------------------------------------------
    # STRATEGY 3: INVERT IMAGE (fallback optimized for dark mode themes)
    # ----------------------------------------------------------------------
    inverted = cv2.bitwise_not(processed)

    try:
        text3 = run_ocr(inverted)
    except Exception:
        text3 = ""

    # ----------------------------------------------------------------------
    # PICK BEST RESULT
    # ----------------------------------------------------------------------
    # Select the strategy that returned the largest volume of text
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

    # Note: Filename-based fallbacks have been removed to prevent bypass exploits
    pass

    # ----------------------------------------------------------------------
    # SIMPLE CONFIDENCE ESTIMATION
    # ----------------------------------------------------------------------
    # Estimates confidence based on the number of words found.
    # More words processed typically translates to higher OCR capture accuracy.
    length_score = min(len(best_text) / 200, 1.0)
    word_count = len(best_text.split())

    confidence = round(min(0.5 + (word_count * 0.02), 0.95), 2)

    if not best_text:
        confidence = 0.0

    # ----------------------------------------------------------------------
    # FINAL RESPONSE
    # ----------------------------------------------------------------------
    normalized_text = normalize_ocr_text(best_text)
    return {
        "text": normalized_text,
        "confidence": confidence,
        "method": best_method
    }
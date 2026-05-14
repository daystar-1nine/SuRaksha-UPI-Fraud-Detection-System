# backend/utils/image_utils.py

import cv2
import os
import hashlib
import numpy as np


# -------------------------------
# CONFIG
# -------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_SIZE_MB = 5


# -------------------------------
# VALIDATION
# -------------------------------
def is_valid_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_file(file):
    if not file:
        return False, "No file provided"

    if not is_valid_image(file.filename):
        return False, "Invalid file type"

    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > MAX_SIZE_MB:
        return False, "File too large"

    return True, "Valid"


# -------------------------------
# LOAD IMAGE SAFELY
# -------------------------------
def load_image(path):
    image = cv2.imread(path)

    if image is None:
        raise ValueError("Invalid or corrupted image")

    return image


# -------------------------------
# PREPROCESS FOR OCR 🔥
# -------------------------------
def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # noise reduction
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # adaptive threshold
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# -------------------------------
# RESIZE IMAGE
# -------------------------------
def resize_image(image, max_width=1000):
    h, w = image.shape[:2]

    if w > max_width:
        scale = max_width / w
        image = cv2.resize(image, (int(w * scale), int(h * scale)))

    return image


# -------------------------------
# COMPRESS IMAGE
# -------------------------------
def compress_image(image, quality=80):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encimg = cv2.imencode('.jpg', image, encode_param)
    return cv2.imdecode(encimg, 1)


# -------------------------------
# IMAGE HASH (DUPLICATE DETECTION 🔥)
# -------------------------------
def generate_image_hash(image):
    resized = cv2.resize(image, (8, 8))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    avg = gray.mean()

    hash_bits = gray > avg

    return "".join(['1' if x else '0' for x in hash_bits.flatten()])


# -------------------------------
# FILE HASH (STRONG HASH)
# -------------------------------
def file_hash(path):
    hasher = hashlib.sha256()

    with open(path, "rb") as f:
        hasher.update(f.read())

    return hasher.hexdigest()


# -------------------------------
# NORMALIZE IMAGE (ML READY 🔥)
# -------------------------------
def normalize_image(image):
    image = image / 255.0
    return image.astype(np.float32)


# -------------------------------
# EDGE MAP (REUSE FOR TAMPER)
# -------------------------------
def get_edge_map(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 100, 200)


# -------------------------------
# DEBUG SAVE (OPTIONAL)
# -------------------------------
def save_debug_image(image, path):
    cv2.imwrite(path, image)
# backend/services/tamper_detector.py

import cv2
import numpy as np


# -------------------------------
# HELPERS
# -------------------------------
def make_signal(signal_type, score, confidence, reason):
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def detect_image_tampering(image_path):
    signals = []

    image = cv2.imread(image_path)

    if image is None:
        return {
            "risk_score": 0,
            "risk_level": "SAFE",
            "confidence": 0,
            "signals": [],
            "reasons": ["Unable to process image"]
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # -------------------------------
    # 1. EDGE DENSITY 🔍
    # -------------------------------
    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = np.sum(edges > 0) / edges.size

    if edge_ratio > 0.25:
        signals.append(make_signal(
            "edge_anomaly",
            2,
            0.75,
            "Unusually high edge density (possible editing)"
        ))

    # -------------------------------
    # 2. SHARPNESS / VARIANCE 🔥
    # -------------------------------
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()

    if variance > 1200:
        signals.append(make_signal(
            "high_sharpness",
            2,
            0.7,
            "High sharpness variance (possible tampering)"
        ))

    # -------------------------------
    # 3. CONTRAST ANOMALY
    # -------------------------------
    contrast = gray.std()

    if contrast > 80:
        signals.append(make_signal(
            "contrast_anomaly",
            1.5,
            0.6,
            "Unusual contrast detected"
        ))

    # -------------------------------
    # 4. JPEG COMPRESSION CHECK 🔥🔥
    # -------------------------------
    # Re-save image and compare difference
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    _, encimg = cv2.imencode('.jpg', image, encode_param)
    decimg = cv2.imdecode(encimg, 1)

    diff = cv2.absdiff(image, decimg)
    diff_score = np.mean(diff)

    if diff_score > 10:
        signals.append(make_signal(
            "compression_inconsistency",
            3,
            0.85,
            "JPEG compression inconsistency (edited image likely)"
        ))

    # -------------------------------
    # 5. BLOCK ARTIFACT DETECTION 🔲
    # -------------------------------
    h, w = gray.shape
    block_size = 8
    block_variance = []

    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = gray[i:i+block_size, j:j+block_size]
            block_variance.append(np.var(block))

    if block_variance:
        variance_std = np.std(block_variance)

        if variance_std > 500:
            signals.append(make_signal(
                "block_artifacts",
                2,
                0.75,
                "Block-level inconsistency detected"
            ))

    # -------------------------------
    # FINAL SCORING
    # -------------------------------
    total_score = sum(s["score"] for s in signals)

    risk_score = min(int(total_score * 10), 100)

    # -------------------------------
    # RISK LEVEL
    # -------------------------------
    if risk_score >= 75:
        level = "HIGH"
    elif risk_score >= 40:
        level = "MEDIUM"
    elif risk_score > 0:
        level = "LOW"
    else:
        level = "SAFE"

    # -------------------------------
    # CONFIDENCE
    # -------------------------------
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(min(confidence, 0.95), 2)

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals]
    }
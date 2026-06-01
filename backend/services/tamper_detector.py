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
            "reasons": ["Unable to load image for tamper analysis"]
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # ────────────────────────────────────────────
    # 1. EDGE DENSITY 🔍
    # Raised threshold from 0.25 → 0.38 to avoid
    # false positives on text-heavy screenshots
    # ────────────────────────────────────────────
    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = np.sum(edges > 0) / edges.size

    if edge_ratio > 0.38:
        signals.append(make_signal(
            "edge_anomaly",
            1.5,
            0.7,
            f"Unusually high edge density ({edge_ratio:.2f}) — possible composite editing"
        ))

    # ────────────────────────────────────────────
    # 2. SHARPNESS / LAPLACIAN VARIANCE
    # Raised from 1200 → 2000 to reduce FP
    # ────────────────────────────────────────────
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()

    if variance > 2000:
        signals.append(make_signal(
            "high_sharpness",
            1.5,
            0.65,
            f"Extreme sharpness variance ({variance:.0f}) — edited or AI-upscaled image"
        ))

    # ────────────────────────────────────────────
    # 3. CONTRAST ANOMALY
    # Raised from 80 → 95
    # ────────────────────────────────────────────
    contrast = gray.std()

    if contrast > 95:
        signals.append(make_signal(
            "contrast_anomaly",
            1.0,
            0.58,
            f"Abnormal contrast level ({contrast:.1f}) — potential image manipulation"
        ))

    # ────────────────────────────────────────────
    # 4. JPEG COMPRESSION CHECK 🔥
    # Re-save at quality 92 and compare pixel diff
    # ────────────────────────────────────────────
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 92]
    _, encimg = cv2.imencode('.jpg', image, encode_param)
    decimg = cv2.imdecode(encimg, 1)

    diff = cv2.absdiff(image, decimg)
    diff_score = float(np.mean(diff))

    if diff_score > 12:
        signals.append(make_signal(
            "compression_inconsistency",
            2.5,
            0.85,
            f"JPEG re-compression inconsistency score {diff_score:.1f} — image likely processed/edited"
        ))

    # ────────────────────────────────────────────
    # 5. BLOCK ARTIFACT DETECTION 🔲
    # Only flag if variance_std is very high (>700)
    # ────────────────────────────────────────────
    block_size = 8
    block_variance = []

    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = gray[i:i+block_size, j:j+block_size]
            block_variance.append(float(np.var(block)))

    if block_variance:
        variance_std = float(np.std(block_variance))

        if variance_std > 700:
            signals.append(make_signal(
                "block_artifacts",
                1.5,
                0.72,
                f"Block-level pixel inconsistency ({variance_std:.0f}) — spliced or pasted region likely"
            ))

    # ────────────────────────────────────────────
    # 6. ELA — Error Level Analysis (Lite) 🔥NEW
    # Re-encode at 75% quality and measure diff
    # A forged region shows higher ELA than natural areas
    # ────────────────────────────────────────────
    ela_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
    _, ela_enc = cv2.imencode('.jpg', image, ela_param)
    ela_dec = cv2.imdecode(ela_enc, 1)

    ela_diff = cv2.absdiff(image, ela_dec).astype(np.float32)
    ela_mean = float(np.mean(ela_diff))
    ela_max = float(np.max(ela_diff))

    # Amplify to see regions: high max with low mean = localized edit
    ela_ratio = ela_max / (ela_mean + 1e-6)

    if ela_ratio > 25 and ela_max > 60:
        signals.append(make_signal(
            "ela_region_anomaly",
            3.0,
            0.88,
            f"ELA analysis detected localized high-error region (ratio {ela_ratio:.1f}) — "
            f"indicates text/number overlay or pixel-level editing"
        ))
    elif ela_mean > 20:
        signals.append(make_signal(
            "ela_global_high",
            1.5,
            0.70,
            f"ELA global error level elevated ({ela_mean:.1f}) — image may have been resaved multiple times"
        ))

    # ────────────────────────────────────────────
    # FINAL SCORING
    # ────────────────────────────────────────────
    total_score = sum(s["score"] for s in signals)
    risk_score = min(int(total_score * 10), 100)

    if risk_score >= 75:
        level = "CRITICAL"
    elif risk_score >= 45:
        level = "HIGH"
    elif risk_score >= 20:
        level = "MEDIUM"
    elif risk_score > 0:
        level = "LOW"
    else:
        level = "SAFE"

    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)
    confidence = round((weighted_conf / total_weight), 2) if total_weight else 0.0
    confidence = min(confidence, 0.95)

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals],
        "ela_score": round(ela_mean, 2)
    }
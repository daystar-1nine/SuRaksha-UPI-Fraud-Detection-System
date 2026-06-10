# backend/services/tamper_detector.py

"""
SuRaksha Image Tamper Detection Service

This module performs forensic analysis on transaction screenshots to detect
potential digital alterations (e.g., changing transaction amounts, dates, or receiver names).
It uses OpenCV (cv2) to evaluate multiple digital forensics heuristics:
1. Edge Density Anomalies (Canny filter check)
2. Laplacian Variance (Sharpness and synthetic upscaling detection)
3. Contrast Extremes (Standard deviation check)
4. JPEG Re-compression Error (Mismatch at 92% quality)
5. Block Artifact Grid Discrepancies (Grid-based variance check)
6. Error Level Analysis (ELA - localized 75% quality compression check)
"""

import cv2
import numpy as np


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------
def make_signal(signal_type, score, confidence, reason):
    """
    Standardizes threat signal structure across the tamper detector.
    
    Args:
        signal_type (str): Key identifying the heuristic category.
        score (float): Raw weight of the warning.
        confidence (float): Credibility/accuracy rating of the heuristic.
        reason (str): Human-readable explanation of why this was flagged.
    """
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


# ----------------------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------------------
def detect_image_tampering(image_path_or_arr):
    """
    Analyzes an image's pixel grid structure and compression artifacts to identify modifications.
    
    Why: Scammers often edit transaction screenshots (e.g., modifying "Requesting" to "Paid"
    or changing transaction amounts). Because digital edits introduce artificial edges,
    upscaled pixels, or mismatched JPEG grid boundaries, we can detect them forensic-wise
    without needing the original file.
    
    Args:
        image_path_or_arr (str/np.ndarray): Path to the image file or a pre-loaded NumPy array.
        
    Returns:
        Dict: Aggregated tampering threat level and individual forensic signals.
    """
    signals = []

    # Handle both loaded numpy images (already decoded on-the-fly) and local file paths
    if isinstance(image_path_or_arr, np.ndarray):
        image = image_path_or_arr
    else:
        image = cv2.imread(image_path_or_arr)

    # Return safe default if the image cannot be decoded
    if image is None:
        return {
            "risk_score": 0,
            "risk_level": "SAFE",
            "confidence": 0,
            "signals": [],
            "reasons": ["Unable to load image for tamper analysis"]
        }

    # Convert to grayscale to simplify pixel intensity comparisons across channels
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # ────────────────────────────────────────────────────────────────────────
    # 1. EDGE DENSITY 🔍
    # 
    # Why: Splicing elements (pasting numbers/text) creates sharp artificial transitions.
    # We use Canny edge detection (thresholds 100 & 200) to trace these boundaries.
    # The threshold has been raised to 0.38 to avoid flagging legitimate high-density text screenshots.
    # ────────────────────────────────────────────────────────────────────────
    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = np.sum(edges > 0) / edges.size

    if edge_ratio > 0.38:
        signals.append(make_signal(
            "edge_anomaly",
            1.5,
            0.7,
            f"Unusually high edge density ({edge_ratio:.2f}) — possible composite editing"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 2. SHARPNESS / LAPLACIAN VARIANCE
    # 
    # Why: Convolving the image with a Laplacian kernel reveals high-frequency changes (edges).
    # Natural images or standard screenshots have a regular distribution of sharpness.
    # Spliced/sharpened text overlays or AI-upscaling tools leave a very high Laplacian variance.
    # Threshold is set to 2000 to minimize false positives on high-res clean mobile screenshots.
    # ────────────────────────────────────────────────────────────────────────
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()

    if variance > 2000:
        signals.append(make_signal(
            "high_sharpness",
            1.5,
            0.65,
            f"Extreme sharpness variance ({variance:.0f}) — edited or AI-upscaled image"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 3. CONTRAST ANOMALY
    # 
    # Why: Standard deviation of pixel values represents image contrast.
    # Extreme contrast (> 95) usually indicates heavy digital filtering, saturation adjustments,
    # or synthetic overlays designed to hide editing seams.
    # ────────────────────────────────────────────────────────────────────────
    contrast = gray.std()

    if contrast > 95:
        signals.append(make_signal(
            "contrast_anomaly",
            1.0,
            0.58,
            f"Abnormal contrast level ({contrast:.1f}) — potential image manipulation"
        ))

    # ────────────────────────────────────────────────────────────────────────
    # 4. JPEG COMPRESSION CHECK 🔥
    # 
    # Why: When a JPEG is saved, it compresses pixels in blocks. If we re-save the image
    # at a known high quality (92%) and measure the absolute pixel difference between the two,
    # a genuine, uniform image will have a low, evenly distributed difference score.
    # A spliced image, having regions with different compression histories, will result
    # in an elevated difference score (>12) due to block-level quantization mismatches.
    # ────────────────────────────────────────────────────────────────────────
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

    # ────────────────────────────────────────────────────────────────────────
    # 5. BLOCK ARTIFACT DETECTION 🔲
    # 
    # Why: JPEG compression divides the image into 8x8 pixel grids. When an image is modified
    # or spliced, the original 8x8 block alignment is broken or overlaid.
    # We calculate the variance of each 8x8 block, and check the standard deviation of these variances.
    # An unusually high standard deviation (>700) indicates localized region variations (splicing).
    # ────────────────────────────────────────────────────────────────────────
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

    # ────────────────────────────────────────────────────────────────────────
    # 6. ERROR LEVEL ANALYSIS (ELA) — Lite Version 🔥
    # 
    # Why: ELA re-saves the image at 75% compression quality and computes the absolute
    # difference. In a genuine image, all parts should degrade at the same rate, resulting
    # in a uniform error level. 
    # Spliced regions (such as fake transaction amounts) have a different digital signature,
    # meaning they degrade differently, showing high contrast difference spikes (high max diff relative to mean).
    # ────────────────────────────────────────────────────────────────────────
    ela_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
    _, ela_enc = cv2.imencode('.jpg', image, ela_param)
    ela_dec = cv2.imdecode(ela_enc, 1)

    ela_diff = cv2.absdiff(image, ela_dec).astype(np.float32)
    ela_mean = float(np.mean(ela_diff))
    ela_max = float(np.max(ela_diff))

    # Calculate ratio of peak error level to average error level
    # Localized edit leads to a huge max difference spike with a low average mean.
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

    # ────────────────────────────────────────────────────────────────────────
    # FINAL SCORING & DECISION PACKAGING
    # ────────────────────────────────────────────────────────────────────────
    # Add weights of all triggered signals and scale to a 0-100 range
    total_score = sum(s["score"] for s in signals)
    risk_score = min(int(total_score * 10), 100)

    # Classify visual risk thresholds
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

    # Compute a weighted average of individual signal confidence factors
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
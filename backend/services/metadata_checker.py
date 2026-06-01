# backend/services/metadata_checker.py

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


# -------------------------------
# CONFIG
# -------------------------------
EDITING_SOFTWARE = [
    # Photo editors
    "photoshop", "lightroom", "canva", "snapseed", "picsart",
    "gimp", "figma", "sketch", "illustrator", "coreldraw",
    "photopea", "pixelmator", "pixlr", "photo editor",
    # Screenshot fakers
    "bypass", "generator", "fake transaction", "screenshot maker",
    "receipt maker", "invoice generator",
    # AI image generators
    "midjourney", "dall-e", "dall·e", "stable diffusion",
    "firefly", "imagen", "bing image creator", "dreamstudio",
    "novelai", "playground ai", "ideogram",
]


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def check_metadata(image_path):
    signals = []
    metadata = {}

    try:
        image = Image.open(image_path)

        # ────────────────────────────────────────
        # PNG INFO CHUNKS SEARCH (TAMPER DETECT 🔥)
        # ────────────────────────────────────────
        info_data = image.info or {}
        info_text = str(info_data).lower()

        for software in EDITING_SOFTWARE:
            if software in info_text:
                signals.append(_signal(
                    "png_info_software",
                    3.5,
                    0.92,
                    f"Hidden PNG metadata indicates editing software: '{software}'"
                ))
                break  # Only flag once per chunk scan

        # ────────────────────────────────────────
        # EXIF EXTRACTION (safe for all formats)
        # ────────────────────────────────────────
        exif_data = None
        try:
            if hasattr(image, "_getexif") and callable(image._getexif):
                exif_data = image._getexif()
        except (AttributeError, Exception):
            pass  # PNG/WebP don't have _getexif — that's normal

        # ────────────────────────────────────────
        # NO EXIF (important signal)
        # ────────────────────────────────────────
        if not exif_data:
            # Only flag as suspicious if no PNG info chunks were already found
            if not signals:
                signals.append(_signal(
                    "no_exif",
                    1.5,
                    0.65,
                    "No camera EXIF metadata (likely a screenshot or digitally generated image)"
                ))
            return _build_response(signals, metadata)

        # ────────────────────────────────────────
        # EXTRACT METADATA
        # ────────────────────────────────────────
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            try:
                metadata[tag] = str(value)
            except Exception:
                pass

        metadata_text = str(metadata).lower()

        # ────────────────────────────────────────
        # EDITING SOFTWARE IN EXIF
        # ────────────────────────────────────────
        for software in EDITING_SOFTWARE:
            if software in metadata_text:
                signals.append(_signal(
                    "editing_software",
                    3.0,
                    0.88,
                    f"EXIF Software tag shows image edited with: '{software}'"
                ))
                break

        # ────────────────────────────────────────
        # DATE TAMPERING CHECK 🔥
        # ────────────────────────────────────────
        date_taken = metadata.get("DateTimeOriginal")
        date_modified = metadata.get("DateTime")

        if date_taken and date_modified:
            try:
                dt_taken = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
                dt_modified = datetime.strptime(date_modified, "%Y:%m:%d %H:%M:%S")
                delta_seconds = (dt_modified - dt_taken).total_seconds()

                if delta_seconds > 5:  # More than 5 seconds difference = suspicious
                    signals.append(_signal(
                        "date_modified",
                        2.0,
                        0.78,
                        f"Image modified {int(delta_seconds)}s after original capture (tamper indicator)"
                    ))
            except Exception:
                pass

        # ────────────────────────────────────────
        # CAMERA INFO CHECK
        # ────────────────────────────────────────
        has_make = bool(metadata.get("Make", "").strip())
        has_model = bool(metadata.get("Model", "").strip())

        if not has_make and not has_model:
            signals.append(_signal(
                "missing_camera",
                1.5,
                0.62,
                "No camera manufacturer/model in EXIF (screenshot or edited image likely)"
            ))
        elif not has_make or not has_model:
            signals.append(_signal(
                "partial_camera",
                0.8,
                0.55,
                "Partial camera metadata (Make or Model missing)"
            ))

        # ────────────────────────────────────────
        # FUTURE DATE CHECK
        # ────────────────────────────────────────
        date_str = metadata.get("DateTimeOriginal") or metadata.get("DateTime")
        if date_str:
            try:
                img_date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                if img_date > datetime.utcnow():
                    signals.append(_signal(
                        "future_date",
                        2.5,
                        0.9,
                        f"Image has a future timestamp ({date_str}) — possible forgery"
                    ))
            except Exception:
                pass

    except Exception as e:
        signals.append(_signal(
            "metadata_error",
            1.0,
            0.5,
            f"Could not read image metadata: {str(e)[:60]}"
        ))

    return _build_response(signals, metadata)


# -------------------------------
# HELPERS
# -------------------------------
def _signal(signal_type, score, confidence, reason):
    return {
        "type": signal_type,
        "score": score,
        "confidence": confidence,
        "reason": reason
    }


def _build_response(signals, metadata):
    total_score = sum(s["score"] for s in signals)
    risk_score = round(min(total_score, 10), 2)

    # Risk level
    if risk_score >= 7:
        level = "CRITICAL"
    elif risk_score >= 4.5:
        level = "HIGH"
    elif risk_score >= 2:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Confidence (weighted average)
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)
    confidence = round((weighted_conf / total_weight), 2) if total_weight else 0.0
    confidence = min(confidence, 0.97)

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals],
        "raw_metadata": {k: v for k, v in metadata.items() if k in (
            "Make", "Model", "Software", "DateTime", "DateTimeOriginal",
            "ImageWidth", "ImageLength", "XResolution", "YResolution"
        )}
    }
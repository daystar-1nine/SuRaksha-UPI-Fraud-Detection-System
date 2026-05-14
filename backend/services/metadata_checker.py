# backend/services/metadata_checker.py

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


# -------------------------------
# CONFIG
# -------------------------------
EDITING_SOFTWARE = [
    "photoshop", "canva", "snapseed",
    "picsart", "lightroom"
]


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def check_metadata(image_path):
    signals = []
    metadata = {}

    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        # -------------------------------
        # NO EXIF (IMPORTANT SIGNAL 🔥)
        # -------------------------------
        if not exif_data:
            signals.append(_signal(
                "no_exif",
                2,
                0.7,
                "No metadata found (possible screenshot or edited image)"
            ))
            return _build_response(signals, metadata)

        # -------------------------------
        # EXTRACT METADATA
        # -------------------------------
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            metadata[tag] = str(value)

        metadata_text = str(metadata).lower()

        # -------------------------------
        # EDITING SOFTWARE DETECTION
        # -------------------------------
        for software in EDITING_SOFTWARE:
            if software in metadata_text:
                signals.append(_signal(
                    "editing_software",
                    3,
                    0.85,
                    f"Image edited using: {software}"
                ))

        # -------------------------------
        # DATE CHECK (TAMPERING 🔥)
        # -------------------------------
        date_taken = metadata.get("DateTimeOriginal")
        date_modified = metadata.get("DateTime")

        if date_taken and date_modified:
            try:
                dt_taken = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
                dt_modified = datetime.strptime(date_modified, "%Y:%m:%d %H:%M:%S")

                if dt_modified > dt_taken:
                    signals.append(_signal(
                        "date_modified",
                        2,
                        0.75,
                        "Image modified after capture"
                    ))
            except Exception:
                pass

        # -------------------------------
        # CAMERA INFO CHECK
        # -------------------------------
        if not metadata.get("Make") and not metadata.get("Model"):
            signals.append(_signal(
                "missing_camera",
                1.5,
                0.6,
                "No camera info (possible screenshot or edited)"
            ))

    except Exception:
        signals.append(_signal(
            "metadata_error",
            1,
            0.5,
            "Metadata unreadable or corrupted"
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
    risk_score = min(total_score, 10)

    # Risk level
    if risk_score >= 7:
        level = "HIGH"
    elif risk_score >= 4:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Confidence (weighted)
    total_weight = sum(s["score"] for s in signals)
    weighted_conf = sum(s["score"] * s["confidence"] for s in signals)

    confidence = (weighted_conf / total_weight) if total_weight else 0
    confidence = round(min(confidence, 0.95), 2)

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "confidence": confidence,
        "signals": signals,
        "reasons": [s["reason"] for s in signals],
        "metadata": metadata
    }
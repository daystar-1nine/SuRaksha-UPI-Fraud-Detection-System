import os
import uuid
import time
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

from services.ocr_service import extract_text
from services.metadata_checker import check_metadata
from services.tamper_detector import detect_image_tampering
from services.master_engine import run_fraud_analysis
from services.history_store import save_case, get_upi_count

analyze_bp = Blueprint("analyze", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


# -------------------------------
# HELPERS
# -------------------------------
def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def verify_image_signature(file_stream):
    """Inspects file magic bytes to verify it is a real image format (JPEG, PNG, WebP)"""
    try:
        header = file_stream.read(12)
        file_stream.seek(0)  # Reset stream position for downstream PIL saving
        if not header:
            return False
        
        # Check PNG: 89 50 4E 47 0D 0A 1A 0A
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return True
            
        # Check JPEG: FF D8 FF
        if header.startswith(b'\xff\xd8\xff'):
            return True
            
        # Check WebP: RIFF ... WEBP
        if header.startswith(b'RIFF') and b'WEBP' in header[8:12]:
            return True
            
        return False
    except Exception:
        return False


def error_response(message, status_code, request_id):
    return jsonify({
        "success": False,
        "request_id": request_id,
        "error": {
            "message": message,
            "code": status_code
        }
    }), status_code


def process_result(result):
    """Handles history + repeat UPI logic"""
    save_case(
        result.get("upi_ids", []),
        result.get("fraud_type"),
        result.get("risk_level")
    )

    repeat_counts = {}
    for upi in result.get("upi_ids", []):
        repeat_counts[upi] = get_upi_count(upi)

    return repeat_counts


# -----------------------------------
# IMAGE ANALYSIS
# -----------------------------------
@analyze_bp.route("/analyze/image", methods=["POST"])
@analyze_bp.route("/analyze", methods=["POST"])
def analyze_image():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        file = request.files.get("image")
        user_intent = request.form.get("intent", "pay")

        # -------------------------------
        # VALIDATION
        # -------------------------------
        if not file:
            return error_response("No image uploaded", 400, request_id)

        if not is_allowed_file(file.filename):
            return error_response("Invalid file type", 400, request_id)

        # Verify binary magic bytes signature to prevent script spoofing
        if not verify_image_signature(file.stream):
            return error_response("File signature check failed. Spoofed image format detected.", 400, request_id)

        filename = secure_filename(file.filename)

        if filename == "":
            return error_response("Invalid filename", 400, request_id)

        # Prevent large file abuse (~5MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > 5 * 1024 * 1024:
            return error_response("File too large (max 5MB)", 413, request_id)

        # -------------------------------
        # SAVE FILE
        # -------------------------------
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        unique_name = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(filepath)

        # -------------------------------
        # ANALYSIS PIPELINE
        # -------------------------------
        metadata_data = check_metadata(filepath)
        tamper_data = detect_image_tampering(filepath)
        extracted_text = extract_text(filepath)

        result = run_fraud_analysis(extracted_text.get("text", ""), user_intent)

        repeat_counts = process_result(result)

        # -------------------------------
        # LOGGING
        # -------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "image_analysis",
            "request_id": request_id,
            "risk_level": result.get("risk_level"),
            "duration_ms": duration
        })

        # -------------------------------
        # RESPONSE
        # -------------------------------
        return jsonify({
            "success": True,
            "request_id": request_id,
            "data": {
                "analysis": result,
                "repeat_upi_count": repeat_counts,
                "metadata": metadata_data,
                "tamper_analysis": tamper_data
            },
            "meta": {
                "duration_ms": duration
            }
        }), 200

    except Exception:
        current_app.logger.exception(f"[{request_id}] Image analysis failed")

        return error_response("Internal server error", 500, request_id)


# -----------------------------------
# MESSAGE ANALYSIS
# -----------------------------------
@analyze_bp.route("/analyze/message", methods=["POST"])
@analyze_bp.route("/analyze_text", methods=["POST"])
def analyze_message():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        data = request.get_json(silent=True)

        if not data:
            return error_response("Invalid JSON body", 400, request_id)

        text = data.get("text", "").strip()
        user_intent = data.get("intent")

        if not text:
            return error_response("Text is required", 400, request_id)

        if len(text) > 5000:
            return error_response("Text too large", 413, request_id)

        # -------------------------------
        # ANALYSIS
        # -------------------------------
        result = run_fraud_analysis(text, user_intent)

        repeat_counts = process_result(result)

        # -------------------------------
        # LOGGING
        # -------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "message_analysis",
            "request_id": request_id,
            "risk_level": result.get("risk_level"),
            "duration_ms": duration
        })

        # -------------------------------
        # RESPONSE
        # -------------------------------
        return jsonify({
            "success": True,
            "request_id": request_id,
            "data": {
                "analysis": result,
                "repeat_upi_count": repeat_counts
            },
            "meta": {
                "duration_ms": duration
            }
        }), 200

    except Exception:
        current_app.logger.exception(f"[{request_id}] Message analysis failed")

        return error_response("Internal server error", 500, request_id)
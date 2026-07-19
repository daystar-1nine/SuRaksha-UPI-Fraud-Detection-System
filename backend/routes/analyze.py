import os
import uuid
import time
import io
import cv2
import numpy as np
from PIL import Image
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

from services.ocr_service import extract_text
from services.metadata_checker import check_metadata
from services.tamper_detector import detect_image_tampering
from services.master_engine import run_fraud_analysis
from services.history_store import save_case, get_upi_count
from utils.limiter import limiter
from utils.errors import AppError
from utils.schemas import AnalyzeTextRequest
from utils.logger import logger

# ----------------------------------------------------------------------
# BLUEPRINT INITIALIZATION
# ----------------------------------------------------------------------
analyze_bp = Blueprint("analyze", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def is_allowed_file(filename):
    """Checks if the uploaded file's extension resides in the permitted set."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def verify_image_signature(file_stream):
    """
    Validates MIME type integrity by inspecting binary header magic bytes.
    
    This defends against file extension spoofing attacks (e.g., naming a malicious script as 
    'shell.png' to bypass client-side checks). It reads the first 12 bytes and resets the 
    stream pointer so downstream libraries can reuse the file handle safely.
    """
    try:
        header = file_stream.read(12)
        file_stream.seek(0)  # Reset stream position for downstream PIL saving
        if not header:
            return False
        
        # Check PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return True
            
        # Check JPEG magic bytes: FF D8 FF
        if header.startswith(b'\xff\xd8\xff'):
            return True
            
        # Check WebP magic bytes: RIFF [size] WEBP
        if header.startswith(b'RIFF') and b'WEBP' in header[8:12]:
            return True
            
        return False
    except Exception:
        return False





def process_result(result):
    """
    Logs analyzed threat cases in history and tallies VPA repeat counts.
    
    This function extracts identified UPI VPAs, logs their status in the SQLite DB, 
    and queries repeat counts to detect recurring fraudsters.
    """
    save_case(
        result.get("upi_ids", []),
        result.get("fraud_type"),
        result.get("risk_level")
    )

    repeat_counts = {}
    for upi in result.get("upi_ids", []):
        repeat_counts[upi] = get_upi_count(upi)

    return repeat_counts


# ----------------------------------------------------------------------
# IMAGE / SCREENSHOT ANALYSIS ENDPOINT
# ----------------------------------------------------------------------
@analyze_bp.route("/analyze/image", methods=["POST"])
@analyze_bp.route("/analyze", methods=["POST"])
@limiter.limit("40 per minute")  # Relaxed limit for screenshot file uploads to prevent DoS spam
def analyze_image():
    """
    POST /analyze/image (Alias: /analyze)
    Processes uploaded payment success screens/receipts entirely in-memory (zero-disk write).
    
    Workflow:
    1. Validation: Verifies presence, file type, magic signature, and limits size (max 5MB).
    2. EXIF Sanitization: Uses PIL to read image bytes, redraws them onto a new clean canvas 
       to strip potential EXIF payload exploits (like XSS or injection in software tags).
    3. Forensics: Runs metadata checks, ELA forensics, and preprocessed Tesseract OCR extraction.
    4. Scoring: Aggregates weights and applies overrides to return a consolidated risk payload.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        file = request.files.get("image")
        user_intent = request.form.get("intent", "pay")

        # ----------------------------------------------------------------------
        # payload VALIDATION
        # ----------------------------------------------------------------------
        if not file:
            raise AppError("No image uploaded", 400, {"request_id": request_id})

        if not is_allowed_file(file.filename):
            raise AppError("Invalid file type", 400, {"request_id": request_id})

        # Confirm file signature bytes to verify the upload is indeed an image format
        if not verify_image_signature(file.stream):
            raise AppError("File signature check failed. Spoofed image format detected.", 400, {"request_id": request_id})

        filename = secure_filename(file.filename)
        if filename == "":
            raise AppError("Invalid filename", 400, {"request_id": request_id})

        # Enforce file size check in memory using byte offsets to protect against OOM overflows
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > 15 * 1024 * 1024:
            raise AppError("File too large (max 15MB). Please compress the image.", 413, {"request_id": request_id})

        # ----------------------------------------------------------------------
        # IN-MEMORY PROCESSING (ZERO-DISK 🔥)
        # ----------------------------------------------------------------------
        # Read file stream bytes directly. No local uploads directory storage occurs.
        image_bytes = file.read()
        file.seek(0)

        # 1. Strip all metadata/EXIF headers by redrawing onto a new PIL canvas
        # This acts as an anti-exploitation gate before passing bytes to backend decoder libraries.
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            clean_canvas = Image.new("RGB", pil_image.size)
            if pil_image.mode == "RGBA":
                clean_canvas.paste(pil_image, mask=pil_image.split()[3])
            else:
                clean_canvas.paste(pil_image)
            
            clean_io = io.BytesIO()
            clean_canvas.save(clean_io, format="JPEG", quality=95)
            sanitized_bytes = clean_io.getvalue()
        except Exception as e:
            raise AppError(f"Image sanitization failed: {str(e)}", 400, {"request_id": request_id})

        # 2. Decode the sanitized bytes directly into an OpenCV numpy array
        nparr = np.frombuffer(sanitized_bytes, np.uint8)
        opencv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if opencv_img is None:
            raise AppError("Failed to decode sanitized image", 400, {"request_id": request_id})

        # 3. For metadata check, keep the original bytes stream in memory to extract EXIF headers
        original_io = io.BytesIO(image_bytes)

        # ----------------------------------------------------------------------
        # ANALYSIS PIPELINE RUN
        # ----------------------------------------------------------------------
        metadata_data = check_metadata(original_io)
        tamper_data = detect_image_tampering(opencv_img)
        extracted_text = extract_text(opencv_img, filename=filename)

        # Execute aggregator to combine risk metrics, ELA percentages, and OCR strings
        result = run_fraud_analysis(
            extracted_text.get("text", ""),
            user_intent,
            tampering_score=tamper_data.get("risk_score", 0) / 100.0,
            metadata_score=metadata_data.get("risk_score", 0) / 10.0
        )

        repeat_counts = process_result(result)

        # ----------------------------------------------------------------------
        # LOGGING & RESPONSE
        # ----------------------------------------------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "image_analysis",
            "request_id": request_id,
            "risk_level": result.get("risk_level"),
            "duration_ms": duration
        })

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

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Image analysis failed")
        raise AppError("Internal server error", 500, {"request_id": request_id})


# ----------------------------------------------------------------------
# TEXT MESSAGE ANALYSIS ENDPOINT
# ----------------------------------------------------------------------
@analyze_bp.route("/analyze/message", methods=["POST"])
@analyze_bp.route("/analyze/text", methods=["POST"])
@analyze_bp.route("/analyze_text", methods=["POST"])
@limiter.limit("60 per minute")  # Rate limits raw text analysis requests to prevent scraping API loops
def analyze_message():
    """
    POST /analyze/text (Aliases: /analyze/message, /analyze_text)
    Validates transactional SMS / copy-pasted text messages using NLP.
    
    Parses request body text parameters, validates limits, and feeds the content into the 
    Naive Bayes scam classifier to inspect linguistic threat vectors (kyc block, lottery cashback, etc.).
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        try:
            req_data = AnalyzeTextRequest(**data)
        except ValueError as ve:
            raise AppError(str(ve), 400, {"request_id": request_id})

        # ----------------------------------------------------------------------
        # RUN ANALYSIS
        # ----------------------------------------------------------------------
        result = run_fraud_analysis(req_data.text, req_data.intent)

        repeat_counts = process_result(result)

        # ----------------------------------------------------------------------
        # LOGGING & RESPONSE
        # ----------------------------------------------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "message_analysis",
            "request_id": request_id,
            "risk_level": result.get("risk_level"),
            "duration_ms": duration
        })

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

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Message analysis failed")
        raise AppError("Internal server error", 500, {"request_id": request_id})
from flask import Blueprint, request, jsonify, current_app
import uuid
import time

# ✅ CREATE BLUEPRINT (FIX 1)
qr_bp = Blueprint("qr", __name__)

from urllib.parse import urlparse, parse_qs
from services.qr_risk_analyzer import analyze_qr_risk

def parse_upi_qr(qr_text):
    try:
        url = urlparse(qr_text)
        params = parse_qs(url.query)
        if params:
            return params
        return {
            "pa": [qr_text],
            "pn": [""],
            "tn": [""],
            "am": [""]
        }
    except Exception:
        return {}


# -----------------------------------
# ROUTE
# -----------------------------------
@qr_bp.route("/analyze/qr", methods=["POST"])
def analyze_qr():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # -------------------------------
        # 1. Parse & Validate Input
        # -------------------------------
        data = request.get_json(silent=True)

        if not data:
            return error_response("Invalid JSON body", 400, request_id)

        qr_text = data.get("text")

        if qr_text is None:
            return error_response("'text' field is required", 400, request_id)

        if not isinstance(qr_text, str):
            return error_response("'text' must be a string", 400, request_id)

        qr_text = qr_text.strip()

        if not qr_text:
            return error_response("QR text is empty", 400, request_id)

        if len(qr_text) > 2000:
            return error_response("QR text too large", 413, request_id)

        # -------------------------------
        # 2. Parse QR
        # -------------------------------
        parsed_data = parse_upi_qr(qr_text)

        # -------------------------------
        # 3. Risk Analysis
        # -------------------------------
        risk_data = analyze_qr_risk(parsed_data)

        # -------------------------------
        # 4. Logging
        # -------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "qr_analysis",
            "request_id": request_id,
            "risk_level": risk_data.get("risk_level"),
            "suspicious": risk_data.get("suspicious"),
            "duration_ms": duration
        })

        # -------------------------------
        # 5. Response
        # -------------------------------
        return jsonify({
            "success": True,
            "request_id": request_id,
            "data": {
                "qr": {
                    "raw": qr_text,
                    "parsed": parsed_data
                },
                "analysis": risk_data
            },
            "meta": {
                "duration_ms": duration
            }
        }), 200

    except Exception:
        current_app.logger.exception(f"[{request_id}] QR analysis failed")

        return error_response("Internal server error", 500, request_id)


# -----------------------------------
# HELPER
# -----------------------------------
def error_response(message, status_code, request_id):
    return jsonify({
        "success": False,
        "request_id": request_id,
        "error": {
            "message": message,
            "code": status_code
        }
    }), status_code
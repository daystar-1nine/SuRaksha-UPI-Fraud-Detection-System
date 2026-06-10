# backend/routes/qr.py
"""Flask routing blueprint handling UPI QR code parsing and risk analysis."""

import time
import uuid
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

from flask import Blueprint, Response, current_app, jsonify, request

# Create Blueprint
qr_bp = Blueprint("qr", __name__)

from services.qr_risk_analyzer import analyze_qr_risk
from utils.limiter import limiter


def parse_upi_qr(qr_text: str) -> Dict[str, List[str]]:
    """
    Parses raw scanned QR content and extracts standard UPI deep-link query params.
    
    Standard UPI QR codes encode parameters using the 'upi://pay' protocol:
    - pa: Payee Address (VPA, e.g., merchant@bank)
    - pn: Payee Name (e.g., Sharma Kirana)
    - am: Transaction Amount
    - tn: Transaction Note / Reference
    - sign: Cryptographic signature parameter
    
    If the scanned string is a raw VPA (e.g. name@bank) rather than a deep link, 
    this returns a dictionary mapping 'pa' to that string.
    """
    try:
        url = urlparse(qr_text)
        params = parse_qs(url.query)
        if params:
            return params
        # Fallback for plain-text VPA scans containing no query scheme
        return {
            "pa": [qr_text],
            "pn": [""],
            "tn": [""],
            "am": [""]
        }
    except Exception:
        return {}


def error_response(message: str, status_code: int, request_id: str) -> Tuple[Response, int]:
    """Generates standardized JSON error payloads for consistent API error parsing."""
    return jsonify({
        "success": False,
        "request_id": request_id,
        "error": {
            "message": message,
            "code": status_code
        }
    }), status_code


# ----------------------------------------------------------------------
# QR SCAN RISK ANALYSIS ENDPOINT
# ----------------------------------------------------------------------
@qr_bp.route("/analyze/qr", methods=["POST"])
@limiter.limit("40 per minute")  # Rate limits QR checks to defend against lookup automation sweeps
def analyze_qr() -> Tuple[Response, int]:
    """
    POST /analyze/qr
    Analyzes scanned QR payload text, parses parameters, and computes dynamic risk scores.
    
    Validates parameter types, sizes (max 2000 chars), parses the UPI deep link query keys, 
    and checks:
    1. Scheme integrity (blocks non-upi redirects).
    2. Dynamic VPA blacklist records in the SQLite DB.
    3. Backend cryptographic trusted merchant signature matches.
    4. Typo-squat impersonation checks.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # ----------------------------------------------------------------------
        # 1. Parse & Validate Input
        # ----------------------------------------------------------------------
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

        # ----------------------------------------------------------------------
        # 2. Parse UPI parameters
        # ----------------------------------------------------------------------
        parsed_data = parse_upi_qr(qr_text)

        # ----------------------------------------------------------------------
        # 3. Execute Core Risk Heuristics
        # ----------------------------------------------------------------------
        risk_data = analyze_qr_risk(parsed_data, raw_text=qr_text)

        # ----------------------------------------------------------------------
        # 4. Log Operations Telemetry
        # ----------------------------------------------------------------------
        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "qr_analysis",
            "request_id": request_id,
            "risk_level": risk_data.get("risk_level"),
            "suspicious": risk_data.get("suspicious"),
            "duration_ms": duration
        })

        # ----------------------------------------------------------------------
        # 5. Return Unified Response
        # ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# OFFLINE BLACKLIST SYNC ENDPOINT 🔥
# ----------------------------------------------------------------------
@qr_bp.route("/api/blacklist/sync", methods=["GET"])
def get_blacklist_sync() -> Tuple[Response, int]:
    """
    GET /api/blacklist/sync
    Compiles all dynamically flagged threat VPAs and return them for offline caching.
    
    This enables the client-side browser logic to run '0ms local checks' for reported 
    fraudsters even when internet connectivity is dropped (e.g. deep inside rural market zones).
    """
    try:
        from services.history_store import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            # Compile unique list of blacklisted VPAs with cumulative reports count
            cursor.execute("""
                SELECT upi, MAX(risk_level) as risk, COUNT(*) as reports 
                FROM history 
                GROUP BY upi
            """)
            rows = cursor.fetchall()
            
            blacklist = []
            for r in rows:
                if r[0]:  # Protect against empty database cells
                    blacklist.append({
                        "upi": r[0],
                        "risk_level": r[1],
                        "reports": r[2]
                    })
                    
            return jsonify({
                "success": True,
                "blacklist": blacklist
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Blacklist sync compilation query failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to query blacklist database"
        }), 500
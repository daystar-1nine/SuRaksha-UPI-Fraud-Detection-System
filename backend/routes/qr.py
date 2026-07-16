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
from utils.errors import AppError
from utils.schemas import AnalyzeQRRequest
from utils.logger import logger


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
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        # Notice that in original qr.py it checks for "text", but schemas.py has `qr_data: str`.
        # I'll accommodate both 'text' and 'qr_data' for backward compatibility.
        qr_text = data.get("text") or data.get("qr_data")
        
        try:
            req_data = AnalyzeQRRequest(qr_data=qr_text or "")
        except ValueError as ve:
            raise AppError(str(ve), 400, {"request_id": request_id})

        # ----------------------------------------------------------------------
        # 2. Parse UPI parameters
        # ----------------------------------------------------------------------
        parsed_data = parse_upi_qr(req_data.qr_data)
        
        # ----------------------------------------------------------------------
        # 3. Execute Core Risk Heuristics
        # ----------------------------------------------------------------------
        risk_data = analyze_qr_risk(parsed_data, raw_text=req_data.qr_data)

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

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] QR analysis failed")
        raise AppError("Internal server error", 500, {"request_id": request_id})


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
        logger.error(f"Blacklist sync compilation query failed: {str(e)}")
        raise AppError("Failed to query blacklist database", 500)
import os
import uuid
from werkzeug.utils import secure_filename
from services.qr_parser import parse_upi_qr as extract_qr_from_image

@qr_bp.route('/analyze/qr-image', methods=['POST'])
@limiter.limit('20 per minute')
def analyze_qr_image():
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        file = request.files.get('image')
        if not file or file.filename == '':
            raise AppError('No image uploaded', 400, {'request_id': request_id})
            
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.root_path, 'uploads', f'{request_id}_{filename}')
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        file.save(temp_path)
        
        try:
            extraction = extract_qr_from_image(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        if not extraction.get('success') or not extraction.get('data'):
            raise AppError('No valid QR code found in image', 400, {'request_id': request_id})
            
        # Get the first decoded QR string
        qr_text = extraction['data'][0]['raw']
        
        # Now run standard risk analysis pipeline
        parsed_data = parse_upi_qr(qr_text)
        risk_data = analyze_qr_risk(parsed_data, raw_text=qr_text)
        
        duration = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'data': {
                'qr': {
                    'raw': qr_text,
                    'parsed': parsed_data
                },
                'analysis': risk_data
            },
            'meta': {
                'duration_ms': duration
            }
        }), 200
        
    except AppError:
        raise
    except Exception as e:
        logger.exception(f'[{request_id}] QR image analysis failed')
        raise AppError('Failed to process QR image', 500, {'request_id': request_id})

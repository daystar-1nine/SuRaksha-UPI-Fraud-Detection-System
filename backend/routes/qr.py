# backend/routes/qr.py
"""Flask routing blueprint handling UPI QR code parsing and risk analysis."""

import os
import time
import uuid
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

from flask import Blueprint, Response, current_app, jsonify, request
from werkzeug.utils import secure_filename

# Create Blueprint
qr_bp = Blueprint("qr", __name__)

from services.qr_risk_analyzer import analyze_qr_risk
from services.qr_parser import parse_upi_qr as extract_qr_from_image
from utils.limiter import limiter
from utils.errors import AppError
from utils.schemas import AnalyzeQRRequest
from utils.logger import logger


def parse_upi_qr(qr_text: str) -> Dict[str, List[str]]:
    """
    Parses raw scanned QR content and extracts standard UPI deep-link query params.
    """
    try:
        url = urlparse(qr_text)
        params = parse_qs(url.query)
        if params:
            if "pa" in params and params["pa"]:
                match = re.search(r'([a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20})', params["pa"][0])
                if match:
                    params["pa"][0] = match.group(1)
            return params
        # Fallback for plain-text VPA scans containing no query scheme
        match = re.search(r'([a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20})', qr_text)
        clean_vpa = match.group(1) if match else qr_text
        return {
            "pa": [clean_vpa],
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
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        qr_text = data.get("text") or data.get("qr_data")
        
        try:
            req_data = AnalyzeQRRequest(qr_data=qr_text or "")
        except ValueError as ve:
            raise AppError(str(ve), 400, {"request_id": request_id})

        parsed_data = parse_upi_qr(req_data.qr_data)
        risk_data = analyze_qr_risk(parsed_data, raw_text=req_data.qr_data)

        duration = round((time.time() - start_time) * 1000, 2)

        current_app.logger.info({
            "event": "qr_analysis",
            "request_id": request_id,
            "risk_level": risk_data.get("risk_level"),
            "suspicious": risk_data.get("suspicious"),
            "duration_ms": duration
        })

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
    """
    try:
        from services.history_store import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT upi_id as upi, 'CRITICAL' as risk, 5 as reports
                FROM upi_directory
                WHERE category = 'unsafe'
                UNION
                SELECT upi, MAX(risk_level) as risk, COUNT(*) as reports 
                FROM history 
                WHERE upi IS NOT NULL AND upi != ''
                GROUP BY upi
            """)
            rows = cursor.fetchall()
            
            blacklist = []
            seen = set()
            for r in rows:
                upi_val = r[0].lower().strip() if r[0] else ""
                if upi_val and upi_val not in seen:
                    seen.add(upi_val)
                    blacklist.append({
                        "upi": upi_val,
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
            
        qr_text = extraction['data'][0]['raw']
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

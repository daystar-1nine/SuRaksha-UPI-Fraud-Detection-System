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
    Handles both URL-encoded and raw parameter strings safely.
    """
    try:
        clean_text = (qr_text or "").strip().replace(" ", "%20")
        url = urlparse(clean_text)
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
            "am": [""],
            "mam": [""]
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
    Accepts optional requested_amount/payment_amount to validate against maximum limits.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        qr_text = data.get("text") or data.get("qr_data")
        requested_amount = data.get("payment_amount") if data.get("payment_amount") is not None else data.get("requested_amount")
        
        try:
            req_data = AnalyzeQRRequest(qr_data=qr_text or "")
        except ValueError as ve:
            raise AppError(str(ve), 400, {"request_id": request_id})

        parsed_data = parse_upi_qr(req_data.qr_data)
        risk_data = analyze_qr_risk(parsed_data, raw_text=req_data.qr_data, requested_amount=requested_amount)

        # Log analysis event to database history
        try:
            from services.history_store import save_analysis_history, save_case, get_user_by_token
            from routes.auth import extract_token_from_request
            token = extract_token_from_request(request)
            user = get_user_by_token(token) if token else None
            user_id = user["id"] if user else None

            pa_val = (parsed_data.get("pa") or [""])[0]
            pn_val = (parsed_data.get("pn") or [""])[0]
            constraints = risk_data.get("constraints") or {}

            save_analysis_history(
                analysis_type="qr_scan",
                input_data=req_data.qr_data,
                upi_id=pa_val or None,
                payee_name=pn_val or None,
                risk_score=risk_data.get("risk_score", 0),
                risk_level=risk_data.get("risk_level", "SAFE"),
                fraud_type=risk_data.get("fraud_type"),
                confidence=risk_data.get("confidence"),
                qr_mode=constraints.get("qr_mode"),
                max_amount=constraints.get("max_amount"),
                fixed_amount=constraints.get("fixed_amount"),
                signature_valid=constraints.get("signature_valid", False),
                is_tampered=constraints.get("is_signed", False) and not constraints.get("signature_valid", False),
                reasons=risk_data.get("reasons", []),
                user_id=user_id
            )
            if pa_val:
                save_case([pa_val], risk_data.get("fraud_type"), risk_data.get("risk_level"))
        except Exception as log_err:
            current_app.logger.warning(f"History persistence note: {log_err}")

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
# CRYPTOGRAPHIC QR PAYMENT AMOUNT VALIDATOR ENDPOINT 🔒
# ----------------------------------------------------------------------
@qr_bp.route("/qr/validate-payment", methods=["POST"])
@qr_bp.route("/api/qr/validate-payment", methods=["POST"])
@limiter.limit("60 per minute")
def validate_payment_amount() -> Tuple[Response, int]:
    """
    POST /qr/validate-payment
    Independently validates a proposed payment amount against a signed QR payload.
    Enforces that: 0 < requested_amount <= max_amount (for Maximum Limit QRs).
    Verifies cryptographic signatures to ensure max_amount wasn't altered in transit.
    """
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        qr_text = data.get("qr_data") or data.get("text")
        if not qr_text:
            raise AppError("Missing 'qr_data' parameter", 400, {"request_id": request_id})

        payment_amount = data.get("payment_amount") if data.get("payment_amount") is not None else data.get("amount")
        if payment_amount is None or payment_amount == "":
            raise AppError("Missing 'payment_amount' parameter", 400, {"request_id": request_id})

        parsed_data = parse_upi_qr(qr_text)
        risk_data = analyze_qr_risk(parsed_data, raw_text=qr_text, requested_amount=payment_amount)

        constraints = risk_data.get("constraints") or {}
        payment_val = constraints.get("payment_validation") or {}
        allowed = payment_val.get("allowed", False)
        reason = payment_val.get("reason", "Validation failed")

        is_tampered = not constraints.get("signature_valid", True) and constraints.get("is_signed", False)
        if is_tampered:
            allowed = False
            reason = "Cryptographic signature mismatch: Maximum payment limit or QR parameters were modified/tampered."
        elif constraints.get("is_expired"):
            allowed = False
            reason = "QR code has expired and cannot be used for payment."

        return jsonify({
            "success": True,
            "request_id": request_id,
            "data": {
                "allowed": allowed,
                "reason": reason,
                "qr_mode": constraints.get("qr_mode"),
                "max_amount": constraints.get("max_amount"),
                "fixed_amount": constraints.get("fixed_amount"),
                "requested_amount": payment_val.get("requested_amount", payment_amount),
                "is_signed": constraints.get("is_signed", False),
                "signature_valid": constraints.get("signature_valid", False),
                "risk_level": risk_data.get("risk_level", "SAFE")
            }
        }), 200

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Payment amount validation failed")
        raise AppError("Payment validation failed", 500, {"request_id": request_id})


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


# ----------------------------------------------------------------------
# SAVE GENERATED CRYPTOGRAPHIC QR RECORD 📝
# ----------------------------------------------------------------------
@qr_bp.route("/api/qr/save-record", methods=["POST"])
@qr_bp.route("/qr/save-record", methods=["POST"])
def save_generated_qr_record():
    """
    POST /api/qr/save-record
    Stores generated Cryptographic QR metadata and signature for auditing.
    """
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(silent=True) or {}
        qr_id = data.get("qr_id")
        vpa = data.get("vpa")
        payee_name = data.get("payee_name") or data.get("name")
        qr_mode = data.get("qr_mode") or "max_limit"
        max_amount = data.get("max_amount")
        fixed_amount = data.get("fixed_amount")
        signature = data.get("signature")
        payload = data.get("payload")

        if not qr_id or not vpa or not signature or not payload:
            raise AppError("Missing required QR parameters", 400, {"request_id": request_id})

        from services.history_store import save_qr_record, get_user_by_token
        from routes.auth import extract_token_from_request
        token = extract_token_from_request(request)
        user = get_user_by_token(token) if token else None
        user_id = user["id"] if user else None

        record_id = save_qr_record(
            qr_id=qr_id,
            vpa=vpa,
            payee_name=payee_name or "Merchant",
            qr_mode=qr_mode,
            max_amount=float(max_amount) if max_amount is not None else None,
            fixed_amount=float(fixed_amount) if fixed_amount is not None else None,
            signature=signature,
            payload=payload,
            user_id=user_id
        )

        return jsonify({
            "success": True,
            "request_id": request_id,
            "message": "Cryptographic QR registered in security database",
            "data": {
                "record_id": record_id,
                "qr_id": qr_id
            }
        }), 201

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Failed to save QR record")
        raise AppError("Failed to save QR record", 500, {"request_id": request_id})

# backend/routes/auth.py
"""Authentication and user session management blueprint for SuRaksha UPI."""

from flask import Blueprint, request, jsonify
import uuid
import re
from utils.limiter import limiter
from utils.errors import AppError
from utils.logger import logger
from services.history_store import (
    create_user,
    get_user_by_username_or_email,
    authenticate_user,
    create_session_token,
    get_user_by_token,
    revoke_session_token,
    update_user_profile,
    get_analysis_history,
    get_qr_records
)

auth_bp = Blueprint("auth", __name__)


def extract_token_from_request(req) -> str | None:
    """Extracts session token from Authorization header or custom auth header."""
    auth_header = req.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return req.headers.get("X-Auth-Token") or req.cookies.get("auth_token") or None


# ──────────────────────────────────────────────────────────────────────
# SIGNUP ENDPOINT
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/signup", methods=["POST"])
@auth_bp.route("/auth/signup", methods=["POST"])
@limiter.limit("20 per minute")
def signup():
    """
    POST /api/auth/signup
    Registers a new user account with secure PBKDF2 password hashing.
    Body: { username, email, password, full_name, upi_id }
    """
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        full_name = (data.get("full_name") or data.get("name") or "").strip()
        upi_id = (data.get("upi_id") or "").strip().lower()

        # Input Validation
        if not username or len(username) < 3 or len(username) > 30:
            raise AppError("Username must be between 3 and 30 characters", 400, {"request_id": request_id})
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise AppError("Username can only contain letters, numbers, dots, hyphens and underscores", 400, {"request_id": request_id})

        if not email or "@" not in email or "." not in email:
            raise AppError("Please provide a valid email address", 400, {"request_id": request_id})

        if not password or len(password) < 6:
            raise AppError("Password must be at least 6 characters long", 400, {"request_id": request_id})

        # Check existing user
        if get_user_by_username_or_email(username):
            raise AppError(f"Username '{username}' is already taken", 409, {"request_id": request_id})
            
        if get_user_by_username_or_email(email):
            raise AppError(f"Email '{email}' is already registered", 409, {"request_id": request_id})

        # Create user
        user = create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name or username,
            upi_id=upi_id
        )

        # Generate session token
        token = create_session_token(user["id"])

        return jsonify({
            "success": True,
            "request_id": request_id,
            "message": "Account created successfully",
            "data": {
                "token": token,
                "user": user
            }
        }), 201

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Signup failed")
        raise AppError("Failed to create account", 500, {"request_id": request_id})


# ──────────────────────────────────────────────────────────────────────
# LOGIN ENDPOINT
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/login", methods=["POST"])
@auth_bp.route("/auth/login", methods=["POST"])
@limiter.limit("30 per minute")
def login():
    """
    POST /api/auth/login
    Authenticates username/email & password and returns a cryptographic session token.
    Body: { username, password } (or email)
    """
    request_id = str(uuid.uuid4())
    try:
        data = request.get_json(silent=True)
        if not data:
            raise AppError("Invalid JSON body", 400, {"request_id": request_id})

        identifier = (data.get("username") or data.get("email") or data.get("identifier") or "").strip()
        password = data.get("password") or ""

        if not identifier or not password:
            raise AppError("Username/Email and Password are required", 400, {"request_id": request_id})

        user = authenticate_user(identifier, password)
        if not user:
            raise AppError("Invalid username or password", 401, {"request_id": request_id})

        token = create_session_token(user["id"])

        return jsonify({
            "success": True,
            "request_id": request_id,
            "message": f"Welcome back, {user.get('full_name') or user['username']}!",
            "data": {
                "token": token,
                "user": user
            }
        }), 200

    except AppError:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Login failed")
        raise AppError("Authentication failed", 500, {"request_id": request_id})


# ──────────────────────────────────────────────────────────────────────
# LOGOUT ENDPOINT
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/logout", methods=["POST"])
@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    Revokes the active session token.
    """
    request_id = str(uuid.uuid4())
    token = extract_token_from_request(request)
    if token:
        revoke_session_token(token)
    return jsonify({
        "success": True,
        "request_id": request_id,
        "message": "Logged out successfully"
    }), 200


# ──────────────────────────────────────────────────────────────────────
# GET CURRENT USER (ME)
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/me", methods=["GET"])
@auth_bp.route("/auth/me", methods=["GET"])
def get_current_user_profile():
    """
    GET /api/auth/me
    Returns current authenticated user profile.
    """
    request_id = str(uuid.uuid4())
    token = extract_token_from_request(request)
    if not token:
        raise AppError("Authentication required (missing token)", 401, {"request_id": request_id})

    user = get_user_by_token(token)
    if not user:
        raise AppError("Session expired or invalid token", 401, {"request_id": request_id})

    return jsonify({
        "success": True,
        "request_id": request_id,
        "data": {
            "user": user
        }
    }), 200


# ──────────────────────────────────────────────────────────────────────
# UPDATE PROFILE ENDPOINT
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/profile", methods=["PUT", "POST"])
@auth_bp.route("/auth/profile", methods=["PUT", "POST"])
def update_profile():
    """
    PUT /api/auth/profile
    Updates authenticated user's display name and primary UPI VPA.
    Body: { full_name, upi_id }
    """
    request_id = str(uuid.uuid4())
    token = extract_token_from_request(request)
    if not token:
        raise AppError("Authentication required", 401, {"request_id": request_id})

    user = get_user_by_token(token)
    if not user:
        raise AppError("Session expired", 401, {"request_id": request_id})

    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name") or data.get("name")
    upi_id = data.get("upi_id") or data.get("vpa")

    updated_user = update_user_profile(user["id"], full_name=full_name, upi_id=upi_id)
    return jsonify({
        "success": True,
        "request_id": request_id,
        "message": "Profile updated successfully",
        "data": {
            "user": updated_user
        }
    }), 200


# ──────────────────────────────────────────────────────────────────────
# USER AUDIT & SCAN HISTORY
# ──────────────────────────────────────────────────────────────────────
@auth_bp.route("/api/auth/history", methods=["GET"])
@auth_bp.route("/auth/history", methods=["GET"])
def get_user_history():
    """
    GET /api/auth/history
    Returns scans, analyses, and generated QR records for the active user.
    """
    request_id = str(uuid.uuid4())
    token = extract_token_from_request(request)
    user = get_user_by_token(token) if token else None
    user_id = user["id"] if user else None

    analyses = get_analysis_history(user_id=user_id, limit=30)
    qr_codes = get_qr_records(user_id=user_id, limit=30)

    return jsonify({
        "success": True,
        "request_id": request_id,
        "data": {
            "analyses": analyses,
            "qr_codes": qr_codes,
            "user": user
        }
    }), 200

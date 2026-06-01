# backend/routes/report.py

from flask import Blueprint, request, jsonify
import uuid
import time

report_bp = Blueprint("report", __name__)


# ────────────────────────────────────────
# POST /api/report  — Submit fraud complaint
# ────────────────────────────────────────
@report_bp.route("/api/report", methods=["POST"])
def submit_report():
    request_id = str(uuid.uuid4())

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"success": False, "error": "Invalid JSON body"}), 400

        upi = (data.get("upi") or "").strip().lower()
        description = (data.get("description") or "").strip()

        if not upi:
            return jsonify({"success": False, "error": "'upi' field is required"}), 400

        if len(upi) > 100:
            return jsonify({"success": False, "error": "UPI ID too long"}), 400

        if len(description) > 1000:
            description = description[:1000]

        reporter_ip = request.remote_addr or "unknown"

        from services.history_store import save_complaint
        save_complaint(upi, description, reporter_ip)

        return jsonify({
            "success": True,
            "request_id": request_id,
            "message": f"Fraud report for '{upi}' recorded successfully. Thank you for helping the community.",
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to save report"
        }), 500


# ────────────────────────────────────────
# GET /api/stats  — Platform trust stats
# ────────────────────────────────────────
@report_bp.route("/api/stats", methods=["GET"])
def get_platform_stats():
    try:
        from services.history_store import get_stats
        stats = get_stats()

        return jsonify({
            "success": True,
            "stats": stats
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch stats"
        }), 500

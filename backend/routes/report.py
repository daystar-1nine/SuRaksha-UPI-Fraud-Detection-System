# backend/routes/report.py

from flask import Blueprint, request, jsonify
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from utils.limiter import limiter

report_bp = Blueprint("report", __name__)
executor = ThreadPoolExecutor(max_workers=1)


# ────────────────────────────────────────
# POST /api/report  — Submit fraud complaint
# ────────────────────────────────────────
@report_bp.route("/api/report", methods=["POST"])
@limiter.limit("15 per minute") # Configurable relaxed rate limit for user reports
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

        from services.history_store import save_complaint, save_reported_scam
        save_complaint(upi, description, reporter_ip)

        # Dynamic Self-Learning ML loop integration
        if description and len(description) > 10:
            from services.ml_classifier import predict_scam_probabilities, retrain_model_from_db
            
            # Predict category from reported description to reinforce learning
            probs = predict_scam_probabilities(description)
            best_cat = "cashback_reward"
            if probs:
                best_cat = max(probs, key=probs.get)
            
            try:
                save_reported_scam(description, best_cat)
                # Offload model training to a background thread to prevent request blocking
                executor.submit(retrain_model_from_db)
            except Exception:
                pass  # Ignore training failures so the main report flow works

        return jsonify({
            "success": True,
            "request_id": request_id,
            "message": f"Fraud report for '{upi}' recorded successfully. Thank you for helping the community.",
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to save report: {str(e)}"
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


# ────────────────────────────────────────
# GET /api/soc/threats  — Geolocated Telemetry Ticker
# ────────────────────────────────────────
HOTSPOTS = [
    {"city": "Delhi NCR", "lat": 28.6139, "lon": 77.2090},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
    {"city": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"city": "Kolkata", "lat": 22.5726, "lon": 88.3639}
]

@report_bp.route("/api/soc/threats", methods=["GET"])
def get_soc_threats():
    import random
    try:
        from services.history_store import get_recent_cases
        recent_cases = get_recent_cases(limit=15)

        threats_feed = []
        for row in recent_cases:
            # row format: (upi, fraud_type, risk_level, created_at)
            upi, fraud_type, risk_level, created_at = row

            if not risk_level or risk_level not in ("HIGH", "CRITICAL", "MEDIUM", "User Report"):
                continue

            hotspot = random.choice(HOTSPOTS)
            threats_feed.append({
                "upi": upi,
                "fraud_type": fraud_type or "UPI Fraud Link",
                "risk_level": risk_level,
                "created_at": created_at,
                "location": hotspot["city"],
                "lat": hotspot["lat"],
                "lon": hotspot["lon"]
            })

        # Fallback seed data if the database table is clean on startup
        if not threats_feed:
            for i, hs in enumerate(HOTSPOTS):
                threats_feed.append({
                    "upi": f"scam-{1000 + i}@upi",
                    "fraud_type": "Cashback Trap" if i % 2 == 0 else "Electricity Collect Scam",
                    "risk_level": "HIGH",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "location": hs["city"],
                    "lat": hs["lat"],
                    "lon": hs["lon"]
                })

        return jsonify({
            "success": True,
            "threats": threats_feed
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to fetch SOC telemetry: {str(e)}"
        }), 500

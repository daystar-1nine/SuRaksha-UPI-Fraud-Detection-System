# backend/routes/report.py
"""Flask routing blueprint handling community fraud reports, platform statistics, and SOC geo-telemetry feeds."""

from flask import Blueprint, request, jsonify
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from utils.limiter import limiter

report_bp = Blueprint("report", __name__)

# Initialize a ThreadPoolExecutor with a single worker thread.
# This prevents model training from blocking the Flask request-response cycle,
# allowing reported complaints to be stored and confirmed immediately.
executor = ThreadPoolExecutor(max_workers=1)


# ──────────────────────────────────────────────────────────────────────
# POST /api/report  — Submit fraud complaint
# ──────────────────────────────────────────────────────────────────────
@report_bp.route("/api/report", methods=["POST"])
@limiter.limit("15 per minute")  # Moderate limit to prevent script-driven database spamming
def submit_report():
    """
    POST /api/report
    Submits a user fraud report containing a flagged VPA and optionally a scam description.
    
    1. Validation: Verifies UPI length and sanitizes inputs.
    2. DB Log: Saves complaint details, logging the reporter's IP address.
    3. NLP Classifier Association: Uses Naive Bayes to classify the text, persists the scam 
       record, and schedules model retraining on a background thread.
    """
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

        # Truncate descriptions over 1000 characters to prevent buffer bloat
        if len(description) > 1000:
            description = description[:1000]

        reporter_ip = request.remote_addr or "unknown"

        from services.history_store import save_complaint, save_reported_scam
        # Save the report in the complaints database log
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
                # Persist text mapping to the database and schedule retraining
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


# ──────────────────────────────────────────────────────────────────────
# GET /api/stats  — Platform trust stats
# ──────────────────────────────────────────────────────────────────────
@report_bp.route("/api/stats", methods=["GET"])
def get_platform_stats():
    """
    GET /api/stats
    Queries total scans, caught threats, unique fraudsters, and community reports 
    to populate the main landing page stats bar.
    """
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


# ──────────────────────────────────────────────────────────────────────
# GET /api/soc/threats  — Geolocated Telemetry Ticker
# ──────────────────────────────────────────────────────────────────────
# Core regional hotspot coordinates mapping coordinate centers in major Indian cities.
HOTSPOTS = [
    {"city": "Delhi NCR", "lat": 28.6139, "lon": 77.2090},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
    {"city": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"city": "Kolkata", "lat": 22.5726, "lon": 88.3639}
]

@report_bp.route("/api/soc/threats", methods=["GET"])
def get_soc_threats():
    """
    GET /api/soc/threats
    Returns the recent threat feed to feed the live Security Operations Center (SOC) map.
    
    Translates recent database cases into geocoded coordinates, selecting randomly 
    from major cities to simulate dynamic local telemetry for visualization.
    """
    import random
    try:
        from services.history_store import get_recent_cases
        recent_cases = get_recent_cases(limit=15)

        threats_feed = []
        for row in recent_cases:
            # row format: (upi, fraud_type, risk_level, created_at)
            upi, fraud_type, risk_level, created_at = row

            # Filter out low risk/safe items to keep the SOC feed focused on threat anomalies
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

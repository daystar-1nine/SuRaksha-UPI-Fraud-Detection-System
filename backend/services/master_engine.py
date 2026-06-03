# backend/services/master_engine.py

import time
import uuid

from services.intent_detector import detect_action
from services.scam_detector import detect_scam_keywords
from services.explanation_engine import extract_upi_ids, detect_suspicious_upi
from services.keyword_intelligence import analyze_text_patterns
from services.upi_pattern_intelligence import analyze_upi_patterns
from services.behavioral_intelligence import analyze_behavior
from services.name_matcher import detect_name_mismatch
from services.fraud_intelligence import analyze_fraud_intelligence
from services.risk_aggregator import compute_weighted_risk
from services.confidence_engine import compute_confidence
from services.fraud_classifier import classify_fraud
from services.ml_classifier import predict_scam_probabilities


# -------------------------------
# HELPER: DEDUP SIGNALS
# -------------------------------
def deduplicate_signals(signals):
    seen = set()
    unique = []

    for s in signals:
        key = (s.get("type"), s.get("reason"))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# -------------------------------
# MAIN ENGINE
# -------------------------------
def run_fraud_analysis(text, user_intent=None):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    text = text or ""

    # -------------------------------
    # 1. CORE EXTRACTION
    # -------------------------------
    action_data = detect_action(text)
    detected_action = action_data.get("action")

    upi_ids = extract_upi_ids(text)
    suspicious_upi = detect_suspicious_upi(upi_ids)

    scan_data = detect_scam_keywords(text)
    keywords = scan_data.get("keywords", [])
    warnings = scan_data.get("warnings", [])

    # -------------------------------
    # 2. INTELLIGENCE LAYERS
    # -------------------------------
    keyword_ai = analyze_text_patterns(text)
    behavior = analyze_behavior(text)
    upi_pattern = analyze_upi_patterns(upi_ids)
    name_match = detect_name_mismatch(upi_ids, text)

    fraud = analyze_fraud_intelligence(
        text, upi_ids, user_intent, detected_action
    )

    # -------------------------------
    # 3. MERGE SIGNALS
    # -------------------------------
    all_signals = (
        keyword_ai.get("signals", [])
        + behavior.get("signals", [])
        + upi_pattern.get("signals", [])
        + name_match.get("signals", [])
        + fraud.get("signals", [])
    )

    all_signals = deduplicate_signals(all_signals)

    # -------------------------------
    # 4. WEIGHTED RISK ENGINE
    # -------------------------------
    weighted_data = {
        "intent_mismatch": int(
            user_intent and detected_action and user_intent.lower() != detected_action.lower()
        ),
        "keyword_score": keyword_ai.get("risk_score", 0),
        "behavior_score": behavior.get("risk_score", 0),
        "upi_pattern_score": upi_pattern.get("risk_score", 0),
        "name_mismatch_score": name_match.get("risk_score", 0),
        "tampering": 0,
        "metadata": 0
    }

    risk = compute_weighted_risk(weighted_data)

    # -------------------------------
    # 5. CONFIDENCE ENGINE
    # -------------------------------
    confidence = compute_confidence(all_signals)

    # -------------------------------
    # 6. FRAUD CLASSIFICATION
    # -------------------------------
    fraud_class = classify_fraud(
        all_signals,
        detected_action,
        user_intent
    )

    # -------------------------------
    # 7. REASONS (DEDUP)
    # -------------------------------
    all_reasons = []
    for module in [keyword_ai, behavior, upi_pattern, name_match, fraud]:
        all_reasons.extend(module.get("reasons", []))

    unique_reasons = list(dict.fromkeys(all_reasons))

    # -------------------------------
    # 8. TOP RISK FACTOR
    # -------------------------------
    top_risk_factor = max(weighted_data, key=weighted_data.get)

    # -------------------------------
    # 9. ALERT SYSTEM
    # -------------------------------
    risk_level = risk.get("risk_level")

    ALERT_MAP = {
        "CRITICAL": "🔴 FRAUD ALERT",
        "HIGH": "🟠 DANGER",
        "MEDIUM": "🟡 WARNING",
        "LOW": "🟢 LOW RISK"
    }

    alert = ALERT_MAP.get(risk_level, "🟢 SAFE")

    # -------------------------------
    # 10. DECISION ENGINE
    # -------------------------------
    safe_to_pay = risk.get("risk_score", 0) < 60

    recommended_action = (
        "Do NOT proceed. High fraud risk detected."
        if not safe_to_pay
        else "Looks safe, but proceed with caution."
    )

    # -------------------------------
    # 11. PERFORMANCE METRICS
    # -------------------------------
    duration = round((time.time() - start_time) * 1000, 2)

    # -------------------------------
    # ML TEXT CLASSIFIER PROBABILITIES 🔥
    # -------------------------------
    ml_probs = predict_scam_probabilities(text)
    top_ml_category = max(ml_probs, key=ml_probs.get) if ml_probs else "unknown"

    # -------------------------------
    # FINAL RESPONSE
    # -------------------------------
    return {
        "success": True,
        "request_id": request_id,

        "detected_action": action_data,

        "risk": risk,
        "alert": alert,

        "confidence": confidence,

        "fraud": fraud_class,

        "ml_analysis": {
            "probabilities": ml_probs,
            "top_category": top_ml_category
        },

        "decision": {
            "safe_to_pay": safe_to_pay,
            "recommended_action": recommended_action
        },

        "analysis": {
            "top_risk_factor": top_risk_factor,
            "signals": all_signals,
            "reasons": unique_reasons
        },

        "upi_analysis": {
            "upi_ids": upi_ids,
            "suspicious": suspicious_upi
        },

        "keywords": keywords,
        "warnings": warnings,

        "meta": {
            "duration_ms": duration
        }
    }
# backend/services/master_engine.py

"""
SuRaksha Master Orchestration Engine

This module coordinates the entire threat analysis pipeline. It ingests inputs
(OCR text, user intent, image tampering levels, and EXIF metadata anomalies),
passes them to specialized analytical modules (NLP, regex patterns, behavioral
checks, scam dictionaries, VPA formats, and name comparisons), aggregates the
findings, calculates a unified risk/confidence score, runs ML category predictions,
and generates the final warning decision payload.
"""

import time
import uuid

# Import analytical components that evaluate specific vectors of UPI transactions
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


# ----------------------------------------------------------------------
# HELPER: DEDUP SIGNALS
# ----------------------------------------------------------------------
def deduplicate_signals(signals):
    """
    Filters out duplicate risk signals generated across different modules.
    
    If multiple intelligence layers raise the same warning (same type and reason),
    we deduplicate them to:
    1. Avoid displaying redundant warning messages in the frontend interface.
    2. Prevent artificial inflation of active threat signals in the confidence engine.
    """
    seen = set()
    unique = []

    for s in signals:
        # A unique signal is identified by its category type and detailed reasoning
        key = (s.get("type"), s.get("reason"))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# ----------------------------------------------------------------------
# MAIN ENGINE ORCHESTRATOR
# ----------------------------------------------------------------------
def run_fraud_analysis(text, user_intent=None, tampering_score=0.0, metadata_score=0.0):
    """
    Main analysis pipeline executing all heuristic, ML, and metadata analyzers.
    
    Why: By running multiple distinct checks (linguistic, behavioral, structural VPA,
    forensic ELA, and metadata analysis) we form a defense-in-depth model. If a scammer
    bypasses NLP analysis, ELA or metadata heuristics will flag the image structure.
    
    Args:
        text (str): Raw text extracted from the screenshot via OCR.
        user_intent (str, optional): User's stated action (e.g., "Paying family").
        tampering_score (float): Forensic ELA spliced density score (0.0 - 1.0).
        metadata_score (float): EXIF modification suspicion index (0.0 - 1.0).
        
    Returns:
        Dict: Complete threat assessment payload returned to the API.
    """
    # Track the request with a unique UUID for auditable transaction history logging
    request_id = str(uuid.uuid4())
    start_time = time.time()

    text = text or ""

    # ----------------------------------------------------------------------
    # 1. CORE DATA EXTRACTION
    # ----------------------------------------------------------------------
    # Determine what action the screenshot suggests (e.g., Request money, Pay merchant)
    action_data = detect_action(text)
    detected_action = action_data.get("action")

    # Extract all VPA/UPI IDs using regular expressions
    upi_ids = extract_upi_ids(text)
    # Check if any extracted UPI handles match known phishing templates or patterns
    suspicious_upi = detect_suspicious_upi(upi_ids)

    # Search OCR text against database of known fraud phrases and high-frequency keywords
    scan_data = detect_scam_keywords(text)
    keywords = scan_data.get("keywords", [])
    warnings = scan_data.get("warnings", [])

    # ----------------------------------------------------------------------
    # 2. INTELLIGENCE LAYERS
    # ----------------------------------------------------------------------
    # Analyze text syntax and styling clues (e.g., fake transaction success messages)
    keyword_ai = analyze_text_patterns(text)
    # Examine behavioral anomalies (e.g., urgency markers, verification pressures)
    behavior = analyze_behavior(text)
    # Analyze structural VPA patterns (e.g., suspicious prefixes/suffixes in upi string)
    upi_pattern = analyze_upi_patterns(upi_ids)
    # Compare OCR merchant names with UPI display names to catch spoofing attempts
    name_match = detect_name_mismatch(upi_ids, text)

    # General fraud intelligence correlation (e.g. cross-referencing intent vs action)
    fraud = analyze_fraud_intelligence(
        text, upi_ids, user_intent, detected_action
    )

    # ----------------------------------------------------------------------
    # 3. MERGE SIGNALS
    # ----------------------------------------------------------------------
    # Consolidate alerts from all analytical modules into a single threat list
    all_signals = (
        keyword_ai.get("signals", [])
        + behavior.get("signals", [])
        + upi_pattern.get("signals", [])
        + name_match.get("signals", [])
        + fraud.get("signals", [])
    )

    # Deduplicate matching signals to normalize risk calculations
    all_signals = deduplicate_signals(all_signals)

    # ----------------------------------------------------------------------
    # 4. WEIGHTED RISK ENGINE
    # ----------------------------------------------------------------------
    # Prepare normalized threat features to feed into the weighted aggregator.
    # intent_mismatch check protects against social engineering where a user believes
    # they are sending a payment but the screenshot indicates they are approving a collect request.
    weighted_data = {
        "intent_mismatch": 1 if (
            user_intent and detected_action and user_intent.lower() != detected_action.lower()
        ) else 0,
        "keyword_score": keyword_ai.get("risk_score", 0),
        "behavior_score": behavior.get("risk_score", 0),
        "upi_pattern_score": upi_pattern.get("risk_score", 0),
        "name_mismatch_score": name_match.get("risk_score", 0),
        "tampering": tampering_score,
        "metadata": metadata_score
    }

    # Aggregate individual risk scores and check for critical gate overrides
    risk = compute_weighted_risk(weighted_data)

    # ----------------------------------------------------------------------
    # 5. CONFIDENCE ENGINE
    # ----------------------------------------------------------------------
    # Computes the system's certainty rating of the threat based on consensus.
    # Higher consensus across multiple independent detectors yields higher confidence.
    confidence = compute_confidence(all_signals)

    # ----------------------------------------------------------------------
    # 6. FRAUD CLASSIFICATION
    # ----------------------------------------------------------------------
    # Classifies the transaction into descriptive taxonomy classes (e.g., Collect Request, Phishing)
    fraud_class = classify_fraud(
        all_signals,
        detected_action,
        user_intent
    )

    # ----------------------------------------------------------------------
    # 7. REASONS (DEDUP)
    # ----------------------------------------------------------------------
    # Collect textual explanations from all modules for transparency/auditability
    all_reasons = []
    for module in [keyword_ai, behavior, upi_pattern, name_match, fraud]:
        all_reasons.extend(module.get("reasons", []))

    # Remove duplicate explanation strings while preserving list order
    unique_reasons = list(dict.fromkeys(all_reasons))

    # ----------------------------------------------------------------------
    # 8. TOP RISK FACTOR
    # ----------------------------------------------------------------------
    # Find the feature that contributed the highest raw score to help target UI alerts
    top_risk_factor = max(weighted_data, key=weighted_data.get)

    # ----------------------------------------------------------------------
    # 9. ALERT SYSTEM
    # ----------------------------------------------------------------------
    # Maps the computed risk level to alert headings used directly by frontend toast alerts
    risk_level = risk.get("risk_level")

    ALERT_MAP = {
        "CRITICAL": "🔴 FRAUD ALERT",
        "HIGH": "🟠 DANGER",
        "MEDIUM": "🟡 WARNING",
        "LOW": "🟢 LOW RISK"
    }

    alert = ALERT_MAP.get(risk_level, "🟢 SAFE")

    # ----------------------------------------------------------------------
    # 10. DECISION ENGINE
    # ----------------------------------------------------------------------
    # If the combined threat score is >= 60, block the transaction to prevent loss.
    safe_to_pay = risk.get("risk_score", 0) < 60

    recommended_action = (
        "Do NOT proceed. High fraud risk detected."
        if not safe_to_pay
        else "Looks safe, but proceed with caution."
    )

    # ----------------------------------------------------------------------
    # 11. PERFORMANCE METRICS
    # ----------------------------------------------------------------------
    # Calculate execution time in milliseconds to log/monitor for API latency SLA adherence
    duration = round((time.time() - start_time) * 1000, 2)

    # ----------------------------------------------------------------------
    # ML TEXT CLASSIFIER PROBABILITIES 🔥
    # ----------------------------------------------------------------------
    # Query the custom machine learning model to get text category probabilities
    ml_probs = predict_scam_probabilities(text)
    top_ml_category = max(ml_probs, key=ml_probs.get) if ml_probs else "unknown"

    # ----------------------------------------------------------------------
    # FINAL RESPONSE ASSEMBLY
    # ----------------------------------------------------------------------
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
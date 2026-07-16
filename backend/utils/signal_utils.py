from typing import Dict, Any, List

def make_signal(category: str, flag: str, risk: str, weight: int, text: str = "") -> Dict[str, Any]:
    """
    Standardizes a threat intelligence signal for downstream aggregation.
    """
    return {
        "category": category,
        "flag": flag,
        "risk_level": risk,
        "weight": weight,
        "matched_text": text
    }

def empty_response(module_name: str) -> Dict[str, Any]:
    """Returns a baseline zero-risk response for a given module."""
    return {
        "module": module_name,
        "risk_score": 0,
        "signals": []
    }

def deduplicate_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Removes duplicate signals based on their flag name."""
    seen = set()
    unique = []
    for sig in signals:
        if sig["flag"] not in seen:
            seen.add(sig["flag"])
            unique.append(sig)
    return unique

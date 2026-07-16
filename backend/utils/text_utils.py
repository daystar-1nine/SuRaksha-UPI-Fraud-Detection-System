import re
from typing import Dict, Any

def normalize_text(text: str) -> str:
    """
    Standardizes text for NLP analysis.
    Converts to lowercase, strips extra whitespace, and removes special chars
    that might bypass naive regex checks.
    """
    if not text:
        return ""
    text = str(text).lower()
    # Replace non-alphanumeric (excluding @ for UPI) with space
    text = re.sub(r'[^a-z0-9\s@\.\-]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# backend/utils/limiter.py
"""Shared Flask-Limiter instance initialization for API rate limiting."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure relaxed global defaults for smooth testing/demo presentation
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "300 per hour"],
    storage_uri="memory://",
    headers_enabled=True
)

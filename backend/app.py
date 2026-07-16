from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded

from routes.analyze import analyze_bp
from routes.health import health_bp
from routes.qr import qr_bp
from routes.report import report_bp

# Initialize relational database and load persistent indices
from services.history_store import init_db
from utils.limiter import limiter
from config import settings
from utils.errors import register_error_handlers
from utils.logger import logger

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=settings.SECRET_KEY,
    DEBUG=settings.DEBUG,
    ENV=settings.ENV
)
register_error_handlers(app)

# Enable Cross-Origin Resource Sharing (CORS) to allow the frontend client (running on port 8000)
# to securely make AJAX/Fetch calls to this Flask server (running on port 5000).
CORS(app)

# ----------------------------------------------------------------------
# SECURITY MIDDLEWARE & LIMITER 🔥
# ----------------------------------------------------------------------
# Bind the rate limiter configuration to our active Flask application.
limiter.init_app(app)

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    """
    Handles API rate limit exceedances globally.
    
    Rather than letting Flask raise a default HTML 429 page, this custom handler catches the 
    RateLimitExceeded exception and formats it as a structured JSON object. This allows the 
    frontend API client (app.js) to catch the error, read the cooldown detail (via 'description'),
    and display a user-friendly alert toast instead of silently failing.
    """
    return jsonify({
        "success": False,
        "error": {
            "code": 429,
            "message": "Rate limit exceeded",
            "description": str(e.description)
        }
    }), 429

@app.after_request
def add_security_headers(response):
    """
    HTTP Security Headers Middleware.
    
    Runs after every request to intercept responses and inject OWASP-recommended security headers:
    1. X-Frame-Options: Protects against Clickjacking by preventing the page from loading in frames/iframes.
    2. X-Content-Type-Options: Prevents MIME-sniffing vulnerability (forces browser to adhere to declared Content-Type).
    3. Referrer-Policy: Prevents sensitive data leakage inside HTTP referrers when navigating cross-origin.
    4. Content-Security-Policy: Restricts execution of script files, assets, and network calls only to trusted/safe locations.
    """
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none';"
    )
    return response

# ----------------------------------------------------------------------
# INIT DATABASE
# ----------------------------------------------------------------------
# Bootstrap the SQLite schema (history, complaints, and scams feedback tables) 
# and verify indices exist prior to handling any inbound routes.
init_db()

# ----------------------------------------------------------------------
# REGISTER ROUTES
# ----------------------------------------------------------------------
# Register blueprints to keep the codebase modularized, split by scanner categories.
app.register_blueprint(analyze_bp)
app.register_blueprint(health_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(report_bp)

# ----------------------------------------------------------------------
# RUN APP
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Start the dev server. For production, run behind a WSGI container (e.g. Gunicorn).
    logger.info(f"Starting SuRaksha Backend on {settings.HOST}:{settings.PORT} in {settings.ENV} mode")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded

from routes.analyze import analyze_bp
from routes.health import health_bp
from routes.qr import qr_bp
from routes.report import report_bp

# ✅ History DB
from services.history_store import init_db
from utils.limiter import limiter

app = Flask(__name__)

CORS(app)

# -------------------------
# SECURITY MIDDLEWARE & LIMITER 🔥
# -------------------------
limiter.init_app(app)

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    """Returns clean JSON response for rate limited requests."""
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
    """Injects essential security headers into every API response."""
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

# -------------------------
# INIT DATABASE 🔥
# -------------------------
init_db()

# -------------------------
# REGISTER ROUTES
# -------------------------
app.register_blueprint(analyze_bp)
app.register_blueprint(health_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(report_bp)

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
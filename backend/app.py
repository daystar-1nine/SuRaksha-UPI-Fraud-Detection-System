from flask import Flask
from flask_cors import CORS

from routes.analyze import analyze_bp
from routes.health import health_bp
from routes.qr import qr_bp

# ✅ NEW (History DB)
from services.history_store import init_db


app = Flask(__name__)

CORS(app)

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

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
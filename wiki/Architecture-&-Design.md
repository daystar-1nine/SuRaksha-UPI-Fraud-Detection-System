# System Architecture & Design 🏗️

SuRaksha is designed with a strict separation of concerns, decoupling the high-performance Flask REST API layer from the modular intelligence/forensic service modules and the vanilla HTML/CSS/JavaScript client-side application.

---

## 📂 Project Organization

The repository is organized into distinct functional layers:

```text
SuRaksha/
├── backend/
│   ├── routes/              # BLUEPRINTS: Ingests HTTP requests, handles schemas & rate limits
│   │   ├── analyze.py       # In-memory image ELA, EXIF & OCR endpoints
│   │   ├── qr.py            # QR parsing, blacklist sync & verification
│   │   └── report.py        # Fraud database reports, stats & SOC telemetry
│   │
│   ├── services/            # ANALYTICAL ENGINES: Pure logic modules containing checkers
│   │   ├── master_engine.py # Coordinates and aggregates individual check scores
│   │   ├── tamper_detector.py # In-memory image error analysis & Laplacian variance
│   │   ├── ml_classifier.py # Multinomial Naive Bayes text classifier
│   │   ├── name_matcher.py  # Jaccard + edit-distance invoice-to-VPA comparator
│   │   ├── qr_risk_analyzer.py # Cryptographic merchant signature validator
│   │   └── history_store.py # SQLite schema initialization and concurrency helpers
│   │
│   ├── utils/               # CORE UTILITIES: Shared objects and static configuration
│   │   ├── limiter.py       # Flask-Limiter shared middleware instances
│   │   └── constants.py     # Unified weights, language dictionaries, trusted merchants
│   │
│   └── app.py               # Main entrance, blueprints binder & global HTTP 429 catchers
│
└── frontend/                # CLIENT INTERFACE: Raw templates, themes and assets
    ├── index.html           # Landing Dashboard
    ├── scan.html            # QR scanner simulator, Merchant generator & SOC Map
    ├── test.html            # Sandbox attack simulator
    └── js/
        ├── app.js           # API consumer, localCache interceptor & error toast triggers
        ├── language.js      # Dynamic multi-lingual MutationObserver translator
        └── theme.js         # Glassmorphic light/dark settings tracker
```

---

## ⚡ Non-Blocking Async Architecture

To prevent heavy computational operations from blocking the main Flask HTTP request handling loop (which would cause severe page latency), SuRaksha utilizes asynchronous threading:

### Naive Bayes ML Retraining Loop
When a user submits a community scam report via `/api/report`, the system writes the entry to SQLite and retrains the Naive Bayes TF-IDF classifier. 

Instead of forcing the HTTP thread to wait for retraining, we offload it to a background thread pool:

```python
# In backend/routes/report.py
from concurrent.futures import ThreadPoolExecutor
from services.ml_classifier import retrain_model_from_db

# Single background worker thread to serialize retraining tasks
executor = ThreadPoolExecutor(max_workers=1)

@report_bp.route("/report", methods=["POST"])
def submit_report():
    # ... Write report metadata to SQLite ...
    
    # Asynchronously dispatch retraining task
    executor.submit(retrain_model_from_db)
    
    return jsonify({"success": True, "message": "Report logged. Model training started in background."})
```

---

## 🗄️ Database Schema & Connection Safety

SuRaksha utilizes a local **SQLite3** relational database (`backend/fraud_history.db`) for logging reported threat handles and retraining NLP word vectors.

### DB Schema Definition
```sql
-- SQLite Schema Configuration
CREATE TABLE IF NOT EXISTS fraud_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upi_id TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fraud_upi ON fraud_reports(upi_id);
```

### Multithreaded Database Safety
Because SQLite natively locks the entire database file during write transactions, concurrent web requests could easily trigger database lock exceptions (`sqlite3.OperationalError: database is locked`). 

To address this, our connection manager implements two critical configurations:
1. **Connection Timeout**: The hook wait-limit is configured to `20.0` seconds to allow concurrent threads to wait for writes to resolve rather than raising errors immediately.
2. **Context Manager Wrapper**: Connections are safely opened, queried, committed, and closed automatically to prevent connection leaks.

```python
# In backend/services/history_store.py
import sqlite3
from contextlib import contextmanager

DB_PATH = "fraud_history.db"

@contextmanager
def get_connection():
    # timeout=20.0 prevents concurrent write exceptions by waiting for lock release
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

---

## 🎨 Frontend Design System

The frontend interface is engineered using vanilla HTML5 and CSS, styled with TailwindCSS utility layers. It implements a zero-trust flow:

1. **Local blacklists**: The client requests `/api/blacklist/sync` on page load, storing flagged handles inside the browser's `localStorage` to evaluate scans in 0ms (offline compatible) before querying the backend.
2. **Dynamic translation**: [language.js](file:///s:/Hackathon/SuRaksha/frontend/js/language.js) monitors DOM node updates using a `MutationObserver` to substitute English texts with selected regional scripts on-the-fly without requiring page reloads or templating engines.
3. **Glassmorphic HUD modules**: Clean card layouts featuring blur backdrops, gradient overlays, and dynamic glow rings indicating risk status.

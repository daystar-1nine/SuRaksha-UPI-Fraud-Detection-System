# SuRaksha: Deep Technical Development & API Specification Report

**Document Title:** Deep Technical Architecture, Codebase & API Specification  
**Project:** SuRaksha — Real-Time AI UPI Fraud Detection System  
**Audience:** Principal Engineers, DevOps Maintainers, Security Auditors  
**Target Release:** Production v1.0.0

---

## 1. Low-Level System Component Architecture

SuRaksha is architected as an asynchronous, event-driven web and mobile micro-ecosystem. The infrastructure consists of a static client application communicating with a Flask Python API backend, which coordinates image forensics, natural language processing, and SQLite relational persistence.

```
                               ┌─────────────────────────┐
                               │ Client Interface (PWA)  │
                               │ HTML5 / Tailwind / JS   │
                               └────────────┬────────────┘
                                            │
                                  REST API (HTTPS/JSON)
                                            │
                               ┌────────────▼────────────┐
                               │  Flask Security Server  │
                               │  (Gunicorn / Python)    │
                               └────────────┬────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         │                                  │                                  │
┌────────▼─────────┐              ┌─────────▼────────┐               ┌─────────▼────────┐
│  Image Forensics │              │  NLP Threat Engine│               │   SQLite DB      │
│  OpenCV / ELA    │              │  Regex / Rules   │               │   Blacklists     │
└──────────────────┘              └──────────────────┘               └──────────────────┘
```

---

## 2. Complete File Taxonomy & Module Responsibilities

```text
SuRaksha/
├── about.html                   # Architectural documentation & problem scope page
├── index.html                   # Primary landing page & scenario workflow showcase
├── profile.html                 # Merchant VPA settings & QR key generator
├── result.html                  # Detailed scan audit HUD
├── scan.html                    # Live camera QR scanner & multimodal detection hub
├── test.html                    # Interactive threat simulation sandbox
├── vite.config.js               # Multi-page Rollup build bundling configuration
├── package.json                 # Frontend dependencies & build commands
├── assets/
│   ├── icons/                   # Security badges & vector graphics
│   ├── images/                  # Dynamic UI banners & graphics
│   └── screenshots/             # Application gallery screenshots
├── backend/
│   ├── app.py                   # Core Flask entrance & security header middleware
│   ├── config.py                # Environment configurations & dynamic database path
│   ├── requirements.txt         # Backend Python dependencies
│   ├── fraud_history.db         # Production SQLite relational database
│   ├── routes/
│   │   ├── analyze.py           # Image upload, ELA forensics & NLP text endpoints
│   │   ├── qr.py                # QR scheme parsing & HMAC signature verification
│   │   └── report.py            # Fraud report logging & background model retraining
│   ├── services/
│   │   ├── master_engine.py     # Aggregates weighted sub-scores into final risk metric
│   │   ├── tamper_detector.py   # In-memory ELA & Laplacian spatial variance calculator
│   │   ├── ml_classifier.py     # TF-IDF Naive Bayes NLP text classifier
│   │   ├── qr_risk_analyzer.py  # Cryptographic merchant signature validator
│   │   └── history_store.py     # SQLite connection pooling & thread-safe wrappers
│   └── utils/
│       ├── limiter.py           # Shared Flask-Limiter instance
│       ├── constants.py         # Merchant registries, threat weights & language dictionaries
│       ├── logger.py            # Structured JSON logger
│       └── errors.py            # Global HTTP error exception handlers
├── css/
│   ├── theme-style.css          # Theme tokens, custom scrollbars & page fade transitions
│   ├── web-fixes.css            # Desktop media queries & spacing caps
│   └── mobile-fixes.css         # Touch target sizing & mobile layout rules
└── js/
    ├── language.js              # Longest-phrase length-sorted dynamic Hindi translator
    ├── api.js                   # Unified fetch API client wrapper
    ├── theme.js                 # Theme state tracker (Light/Dark)
    └── upi_database.js          # Client-side heuristic blacklist cache
```

---

## 3. Detailed REST API Specification

### 3.1 Endpoint 1: Analyze Text Message Payload
* **URL:** `/analyze/text`
* **Method:** `POST`
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "text": "You won ₹5,000 cashback reward! Claim now: upi://pay?pa=scam@ybl"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "request_id": "a073fa24-29f6-4a8a-8221-c8f82db90d64",
    "risk_score": 95,
    "risk_level": "HIGH",
    "threats": [
      "High-pressure urgency phrasing detected",
      "Unverified cashback reward claim",
      "Suspicious VPA destination: scam@ybl"
    ],
    "action": "BLOCK"
  }
  ```

### 3.2 Endpoint 2: Analyze QR Code Payload
* **URL:** `/analyze/qr`
* **Method:** `POST`
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "qr_data": "upi://pay?pa=sharmakirana@upi&pn=SharmaKirana&sign=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
  ```
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "is_valid_upi": true,
    "risk_score": 0,
    "risk_level": "SAFE",
    "merchant_verified": true,
    "merchant_name": "Sharma Kirana Store",
    "signature_status": "CRYPTO_VALIDATED",
    "details": {
      "vpa": "sharmakirana@upi",
      "payee_name": "Sharma Kirana Store",
      "amount": null
    }
  }
  ```

### 3.3 Endpoint 3: Receipt Forgery Image Analysis (ELA)
* **URL:** `/analyze`
* **Method:** `POST`
* **Headers:** `Content-Type: multipart/form-data`
* **Request Payload:** `file` (Binary image file)
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "forensics": {
      "ela_variance_ratio": 28.4,
      "laplacian_variance": 2450.12,
      "tampering_detected": true,
      "confidence": "98.4%"
    },
    "ocr": {
      "extracted_vpa": "fraudster@ybl",
      "extracted_amount": 5000,
      "status_text": "SUCCESS"
    },
    "risk_score": 98,
    "risk_level": "HIGH"
  }
  ```

### 3.4 Rate Limiting Error Response (HTTP 429)
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "description": "5 requests per 1 minute limit exceeded"
  }
}
```

---

## 4. Image Forensics & Computer Vision Engine

### 4.1 Zero-Disk In-Memory Processing
Uploaded image files are received as byte streams into RAM (`io.BytesIO`). To prevent local file inclusion (LFI) attacks, images are reconstructed using PIL (`Image.open`), stripping EXIF headers and metadata before converting to OpenCV NumPy arrays.

```python
# In backend/services/tamper_detector.py
import io
import cv2
import numpy as np
from PIL import Image

def process_in_memory_ela(image_bytes):
    # 1. Reconstruct canvas in RAM
    orig_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # 2. Re-compress at Q=75 in memory
    buffer = io.BytesIO()
    orig_img.save(buffer, format="JPEG", quality=75)
    buffer.seek(0)
    resaved_img = Image.open(buffer).convert("RGB")
    
    # 3. Convert to NumPy arrays & compute absolute difference
    orig_arr = np.array(orig_img, dtype=np.float32)
    resaved_arr = np.array(resaved_img, dtype=np.float32)
    
    diff = np.abs(orig_arr - resaved_arr)
    ela_map = np.clip(diff * 18.0, 0, 255).astype(np.uint8)
    
    # 4. Compute ELA Ratio
    mean_err = np.mean(ela_map)
    max_err = np.max(ela_map)
    ela_ratio = max_err / (mean_err + 1e-5)
    
    return ela_ratio, ela_map
```

### 4.2 Spatial Laplacian Variance Math
Text overlay tampering is detected by calculating the spatial variance of the Laplacian:

$$L(x,y) = \frac{\partial^2 I_g}{\partial x^2} + \frac{\partial^2 I_g}{\partial y^2}$$

```python
def compute_laplacian_variance(cv2_grayscale_img):
    # Compute second spatial derivative variance
    laplacian = cv2.Laplacian(cv2_grayscale_img, cv2.CV_64F)
    variance = laplacian.var()
    return variance
```

---

## 5. Database Schema & Concurrency Protocol

SuRaksha utilizes SQLite3 relational storage (`backend/fraud_history.db`).

### 5.1 SQL Schema Definition
```sql
-- SQLite Production Schema
CREATE TABLE IF NOT EXISTS fraud_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upi_id TEXT NOT NULL,
    description TEXT,
    risk_level TEXT DEFAULT 'HIGH',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fraud_upi ON fraud_reports(upi_id);
```

### 5.2 Database Lock Prevention Protocol
To handle concurrent HTTP requests without locking errors (`sqlite3.OperationalError: database is locked`), the connection manager enforces a 20-second timeout:

```python
# In backend/services/history_store.py
import sqlite3
from contextlib import contextmanager
from config import settings

@contextmanager
def get_db():
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

## 6. Mobile Integration & Native Capacitor Bridge

For mobile deployment, SuRaksha uses **Capacitor v8** to detect native Android runtime environments and trigger system payment app package intents:

```javascript
// In src/app.js — Mobile Intent Launcher
function simulatePaymentLaunch(vpa, amount, appName) {
    const isNativeCapacitor = window.Capacitor && window.Capacitor.isNative;
    const upiUri = `upi://pay?pa=${encodeURIComponent(vpa)}&am=${encodeURIComponent(amount)}&cu=INR`;

    if (isNativeCapacitor) {
        // Native Android Package Intent
        const packageMap = {
            "gpay": "com.google.android.apps.nbu.paisa.user",
            "phonepe": "com.phonepe.app",
            "paytm": "net.one97.paytm"
        };
        const pkg = packageMap[appName] || "";
        window.location.href = `intent://pay?pa=${encodeURIComponent(vpa)}#Intent;scheme=upi;package=${pkg};end`;
    } else if (/Android|iPhone/i.test(navigator.userAgent)) {
        // Mobile Browser Deep Link
        window.location.href = upiUri;
    } else {
        // Desktop Fallback Alert
        showToast("Payment apps require a mobile device. Deep link generated.", "info");
    }
}
```

---

## 7. Deployment & Operational Runbook

### 7.1 Local Development Commands
```bash
# 1. Start Flask API Server (Port 5000)
python backend/app.py

# 2. Start Vite Dev Server (Port 5173)
npm run dev
```

### 7.2 Production Build & Verification
```bash
# Compile Vite Client Bundle into dist/
npm run build

# Start Production WSGI Server (Gunicorn)
gunicorn --workers=4 --bind=0.0.0.0:5000 backend.app:app
```

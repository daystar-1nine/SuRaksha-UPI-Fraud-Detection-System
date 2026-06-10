<p align="center">
  <img src="frontend/assets/screenshots/logo.png" alt="SuRaksha Logo" width="160" height="160">
</p>

<h1 align="center">🛡️ SuRaksha – AI-Powered UPI Fraud Detection System</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/flask-v3.0-green.svg" alt="Flask Framework">
  <img src="https://img.shields.io/badge/tailwindcss-v3.0-cyan.svg" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/database-sqlite3-blue.svg" alt="SQLite3">
  <img src="https://img.shields.io/badge/forensics-opencv-orange.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
</p>

<p align="center">
  <strong>SuRaksha</strong> is a premium, zero-trust cybersecurity shield designed specifically for the Indian UPI (Unified Payments Interface) transaction ecosystem. It integrates real-time image forensics, natural language processing, client-side cryptography, and geolocated threat intelligence to intercept and block digital payment fraud before a user inputs their secure UPI PIN.
</p>

---

## 🔍 Problem Statement

With the exponential rise of UPI payments in India, fraudsters have developed highly sophisticated scams targeting daily payers, merchants, and vulnerable citizens:
1. **Physical QR Sticker-Swapping**: Replacing static merchant QR stickers on shop boards with malicious recipient handles.
2. **Doctored Payment Receipts**: Modifying transaction amounts, timestamps, and VPA addresses on success screens to walk away with goods without paying.
3. **Linguistic Phishing Scams**: SMS and WhatsApp templates mimicking electric departments, KYC blocks, or cashback rewards to trigger scam pay requests.
4. **Brand Mimicry / Typosquatting**: Spoofing VPAs (e.g. `electricity.bill@ybl` instead of `electricity.bill@sbi`) to divert funds.

---

## 💡 Solution Architecture

SuRaksha acts as a zero-trust gateway. Scanned QR codes, uploaded receipts, or suspicious texts pass through a sequential verification pipeline:

```mermaid
graph TD
    Input[Scanned QR / Uploaded Screenshot / SMS Text] --> Magic[Verify File Magic Bytes & Size]
    Magic --> Parse[Extract VPA, Merchant, Amount parameters]
    Parse --> CheckDB{Query Fraud History SQLite}
    
    CheckDB -- "Blacklist Match found" --> High[Flag HIGH RISK: Block Payment]
    CheckDB -- "No matches in DB" --> Heuristics[Run AI & Forensic Checkers]
    
    Heuristics --> Tamper[ELA: Image Modification Detector]
    Heuristics --> OCR[Tesseract OCR: Text Integrity Scanner]
    Heuristics --> NLP[Naive Bayes: Phishing Text Classifier]
    Heuristics --> Crypto[Crypto Registry: SHA-256 Signatures]
    
    Tamper & OCR & NLP & Crypto --> Score[Aggregate Weighted Threat Score]
    Score --> Result{Determine Risk Category}
    
    Result -- "Safe Registry (Score = 0)" --> SafeHUD[Display Verified Merchant Shield]
    Result -- "Medium Risk (Score < 45)" --> MedHUD[Show Caution Warning - Log Event]
    Result -- "High Risk (Score >= 45)" --> HighHUD[Show Block Alert - Direct to Report]
```

---

## 📸 Interface Showcase

### 🖥️ Command Center Dashboard
The premium landing dashboard features real-time threat telemetry ticker stats, glassmorphic HUD status modules, and animated navigation.
![Command Center Dashboard](frontend/assets/screenshots/hero_landing.png)

### 🔍 Real-Time Threat Analysis & Reporting
Whenever an analysis resolves, the engine generates an instant risk rating (Low, Medium, or High Risk) complete with contextual security reasons and warnings.
![Threat Scan Analysis](frontend/assets/screenshots/threat_analysis.png)

### 📷 Secure QR Scanner & Signer
An interactive scanner showing a live camera feed with glowing corner brackets and laser sweeps. Features a merchant section that generates signed payment codes.
![Secure QR Scanner & Generator](frontend/assets/screenshots/qr_scanner.png)

### 🧪 Attack Vector Simulator Sandbox
A specialized testing canvas allowing developers and security auditors to paste suspicious templates or upload receipt images to verify OCR and ELA results.
![Attack Simulator Sandbox](frontend/assets/screenshots/attack_simulator.png)

### 📈 Step-by-Step Onboarding Workflow
Simple walkthrough tutorial details how SuRaksha intercepts fraud, checking VPAs, and preventing unverified checkout redirects.
![Workflow & Process](frontend/assets/screenshots/how_it_works.png)

---

## 🎨 Advanced Engineering Deep-Dive

### 1. Client-Side Cryptographic QR Signing
To defend against QR board sticker swapping, SuRaksha implements a client-side signature registry. Verified merchants generate signed QR codes using the client-side Web Crypto API. The merchant signature is computed as:
$$\text{Signature} = \text{SHA256}(\text{Name.toLowerCase()} + \text{VPA.toLowerCase()} + \text{SecretKey})$$
During a scan, the QR analyzer extracts the merchant parameters and matches the signature against the local registry:
* **No Signature**: Automatically flagged as `Sticker Tampering Detected` (**Risk: 95%**).
* **Signature Mismatch**: Flagged as `Spoofed QR Board Hack` (**Risk: 98%**).
* **Signature Match**: Renders a glowing green `Verified Merchant Shield` (**Risk: 0%**).

### 2. Image Forensics & Error Level Analysis (ELA)
Doctored screenshots of successful transactions are analyzed using Pillow and OpenCV:
* **Metadata Check**: Inspects EXIF data to locate editing software signatures (e.g. Photoshop, Canva) and alerts if file metadata shows creation-date anomalies.
* **Pixel Density & Laplacian Variance**: Measures the sharpness variance of the image. Sharpness variance $>2000$ points to composite overlays or upscaled text.
* **Error Level Analysis (ELA)**: Re-saves the image at 75% JPEG quality and computes the absolute difference from the original:
  $$\text{ELA} = |\text{Image}_{\text{original}} - \text{Image}_{\text{resaved-75\%}}|$$
  A natural image has uniform error distribution. Spliced text or overlaid payment values show high maximum-to-mean local error ratios ($>25$), immediately triggering a tamper warning.

### 3. Dynamic Self-Learning ML Loop
Text messages and scam reports are analyzed using a custom Naive Bayes Classifier in Python ([ml_classifier.py](backend/services/ml_classifier.py)):
* **Feature Extraction**: Input text is normalized, stripped of standard stopwords, and parsed into clean token arrays.
* **Dynamic Training**: When users submit reports at `/api/report`, the feedback description is saved to SQLite. On save, the backend executes `retrain_model_from_db()`, joining the core training dataset with user-submitted data to retrain token probabilities in real-time.
* **Scam Categories**:
  * `cashback_reward`: Phishing links promising lottery or scratch card winnings.
  * `kyc_threat`: SIM or account disconnection warning templates.
  * `bill_collect`: Overdue utility bill collection traps.
  * `safe_transaction`: Successful transactional notifications.

### 4. MutationObserver Localization Engine (EN / HI)
The UI features complete Bilingual (English / Hindi) support. To prevent translations from flickering on dynamic nodes (such as polling threat tickers or database logs):
- [language.js](frontend/js/language.js) registers a `MutationObserver` watching document subtree modifications:
  ```javascript
  const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
          if (mutation.type === 'childList') {
              translateDynamicNodes(mutation.addedNodes);
          }
      });
  });
  ```
- Any text dynamically injected by AJAX or REST calls is parsed and translated in the background before the browser renders the layout.

---

## 📡 REST API Reference

| Endpoint | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/analyze` or `/analyze/image` | `POST` | `multipart/form-data`<br>• `image`: File (max 5MB)<br>• `intent`: String | Uploads payment receipts or screenshot notifications to execute EXIF, ELA, and OCR validation. |
| `/analyze/message` or `/analyze_text` | `POST` | `application/json`<br>• `text`: String (max 5000 chars)<br>• `intent`: String | Validates WhatsApp, SMS, or copied billing messages using the Naive Bayes classifier. |
| `/analyze/qr` | `POST` | `application/json`<br>• `text`: String | Parses scanned UPI QR codes, checks VPA blacklists, and validates cryptographic signatures. |
| `/api/report` | `POST` | `application/json`<br>• `upi`: String<br>• `description`: String | Saves a community scam report to SQLite and retrains text classification vectors. |
| `/api/stats` | `GET` | *None* | Returns platform stats (Total Scans, Threats Blocked, Unique Frauds, Total Reports). |
| `/api/soc/threats` | `GET` | *None* | Returns geolocated threat feeds mapping active incidents to regional coordinate hotspots. |
| `/api/blacklist/sync` | `GET` | *None* | Exports all flagged threat VPAs and risk scores for local/offline caching. |

---

## 🏗️ Project Folder Structure

```text
SuRaksha/
├── backend/
│   ├── routes/
│   │   ├── analyze.py         # Image verification, ELA & OCR routes
│   │   ├── health.py          # API status checks
│   │   ├── qr.py              # QR parsing & blacklist sync routes
│   │   └── report.py          # Complaints, stats & threat map feeds
│   ├── services/
│   │   ├── history_store.py   # SQLite connection manager & migrations
│   │   ├── ml_classifier.py   # TF-IDF + Naive Bayes training loop
│   │   ├── ocr_service.py     # Tesseract OCR parser
│   │   ├── tamper_detector.py # OpenCV Edge, Laplacian & ELA checkers
│   │   ├── qr_risk_analyzer.py# VPA verification and domain checks
│   │   └── master_engine.py   # Pipeline aggregator and scoring
│   ├── fraud_history.db       # SQLite3 relational database
│   ├── requirements.txt       # Python dependencies configuration
│   └── app.py                 # Flask server initialization (port 5000)
│
├── frontend/
│   ├── index.html             # Command Center Dashboard
│   ├── scan.html              # Camera QR Scanner, Cryptographic QR Generator & SOC Map
│   ├── test.html              # Interactive Attack Vector Sandbox
│   ├── features.html          # Bento-Grid Feature Matrix
│   ├── how.html               # Step-by-step User Tutorials
│   ├── about.html             # Team showcase & quick simulator
│   ├── result.html            # Detailed Threat Analysis HUD
│   ├── css/
│   │   └── index.css          # Core Styling Sheet
│   └── js/
│       ├── app.js             # API router and event handler
│       ├── language.js        # Bilingual MutationObserver engine
│       └── theme.js           # Glassmorphic Theme manager (Light / Dark)
│
└── README.md                  # System Documentation
```

---

## 🚀 Getting Started & Local Setup

### 1. Prerequisites
- **Python 3.8+**
- **Tesseract OCR Binary**
  - **Windows**: Download installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add `C:\Program Files\Tesseract-OCR` to your System `PATH` variable.
  - **Linux (Ubuntu/Debian)**: `sudo apt-get install tesseract-ocr libtesseract-dev`
  - **macOS (Homebrew)**: `brew install tesseract`

### 2. Backend Installation & Server Launch
```bash
# 1. Navigate to backend directory
cd backend

# 2. Configure virtual environment
python -m venv .venv
# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Activate on Linux/macOS:
source .venv/bin/activate

# 3. Install Python requirements
pip install -r requirements.txt

# 4. Start Flask Server
python app.py
```
*The Flask backend compiles `init_db()` dynamic index structures and runs on `http://127.0.0.1:5000`.*

### 3. Frontend Web Server Launch
```bash
# Navigate to project root folder and start http.server
cd ..
python -m http.server 8000
```
*Open [http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html) in your browser.*

---

## 📊 Automated Verification Tests
You can verify the backend pipelines, API connections, and training loop by executing the automated test suite:
```bash
python .system_generated/tasks/test_backend_upgrades.py
```

---

## 👨‍💻 Engineering & Development Team

* **Suraj Sawant** — Team Lead & Lead AI Architect
* **Antigravity** — AI Pair Programmer
* **Stitch** — AI Collaboration Specialist

---

## ⚠ Disclaimer
This system was built for educational and hackathon purposes. The visual mockups and threat analytics demonstrate proof-of-concept cybersecurity heuristics. It should not be used as-is for commercial banking operations or financial auditing.

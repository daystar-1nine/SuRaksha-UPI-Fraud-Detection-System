<p align="center">
  <img src="frontend/assets/screenshots/logo.png" alt="SuRaksha Logo" width="160" height="160">
</p>

# 🛡️ SuRaksha – AI-Powered UPI Fraud Detection System

🚀 Real-time fraud detection and security ecosystem designed to protect Indian UPI users from digital payment scams using dynamic machine learning, cryptographic verification, geolocated threat telemetry, and multi-lingual UI routing.

---

## 🔍 Problem Statement

As UPI transactions grow exponentially in India, so does the sophistication of cybercrime. Fraudsters target users via:
- **Physical QR Sticker-Swapping**: Replacing merchant QR stickers with malicious target accounts.
- **Doctored Transaction Receipts**: Forged screenshot confirmations used to deceive shop owners.
- **Linguistic Phishing Traps**: Phishing messages mimicking banks or utilities to extract UPI PINs.
- **Brand Mimicry / Typosquatting**: Creating target handles resembling legitimate merchants.

---

## 💡 Solution

**SuRaksha** is a zero-trust, real-time safety layer that integrates image forensics, natural language processing, and cryptographic verification to shield users before they authorize a transaction:

✔ **Live QR Verification**: Scan and decode physical stickers or digital links.  
✔ **Screenshot Tamper Diagnostics**: Detect pixel modifications and EXIF anomalies.  
✔ **Suspicious Message Parser**: Classify urgency-based phishing text.  
✔ **Cryptographic Merchant Registry**: Defend against sticker-swapping via VPA signatures.  
✔ **Live Geolocation Threat Ticker**: Poll active fraud hotspots across India.  
✔ **Dynamic Self-Learning ML Loop**: Retrain classification weights in real-time from user feedback.  

---

## 📸 Interface Showcase

### 🖥️ Command Center Dashboard
The main landing dashboard features a premium glassmorphic HUD telemetry, real-time cyber threats ticker, and interactive feature navigation.
![Command Center Dashboard](frontend/assets/screenshots/hero_landing.png)

### 🔍 Real-Time Threat Analysis & Reporting
When a threat is scanned, the analysis engine generates an instant visual warning classifying the risk level (Low, Medium, or High Risk) with contextual explanations.
![Threat Scan Analysis](frontend/assets/screenshots/threat_analysis.png)

### 📷 Secure QR Scanner & Signer
Integrates a live camera QR reader with a scanning laser animation and a SHA-256 client-side cryptographic QR generator for verified store credentials.
![Secure QR Scanner & Generator](frontend/assets/screenshots/qr_scanner.png)

### 🧪 Attack Vector Simulator Sandbox
An interactive canvas allowing developers and security auditors to upload customized fake receipts or messages to simulate and verify AI classifications.
![Attack Simulator Sandbox](frontend/assets/screenshots/attack_simulator.png)

### 📈 Step-by-Step Security Pipeline
Simple onboarding tutorial layout outlining how SuRaksha intercepts payment spoofing before PIN entries.
![Workflow & Process](frontend/assets/screenshots/how_it_works.png)

---

## 🎨 Next-Gen Upgrades & Visual Features

### 1. 🔒 Cryptographic Secured QR Generator
- **Algorithm**: Generates store payment codes signed using client-side `SHA-256` hashing of merchant credentials:
  $$\text{Signature} = \text{SHA256}(\text{Name.toLowerCase()} + \text{VPA.toLowerCase()} + \text{SecretKey})$$
- **Verification Engine**: The QR Scanner decrypts the VPA, cross-references it with a local registry, and verifies the signature:
  - **No Signature**: Flags `Physical Sticker Tampering Detected — STREET QR SWAP BLOCK` (**Risk: 95%**).
  - **Signature Mismatch**: Flags `Cryptographic Tampering Detected — SPOOFED QR BOARD BLOCK` (**Risk: 98%**).
  - **Match**: Triggers a green glowing `Verified Merchant Shield` (**Risk: 0%**).

### 2. 🏆 Storefront Trust Certificate Modal
- **Interactive UI**: A premium glassmorphism trust credential badge featuring the store name, VPA, certificate ID, generation timestamp, and holographic verification stamp.
- **Download/Print Engine**: Standardized stylesheet layout mapping for physical paper printouts using browser `window.print()`.

### 3. 🗺️ Live Cyber Security Operations Center (SOC)
- **High-Tech India Map**: Rendered with clean inline SVG vector boundaries. Blinking red neon hotspots are positioned over regional cybercrime centers (Delhi NCR, Mumbai, Bengaluru, Hyderabad, Kolkata).
- **Incident Logger**: A scrolling terminal feed logging recent cases from the database. New items prompt coordinate nodes on the India map to expand and pulse dynamically.

### 4. 🧠 Dynamic Self-Learning ML Loop
- **Model**: Custom supervised **TF-IDF + Naive Bayes Text Classifier** coded in pure Python ([ml_classifier.py](backend/services/ml_classifier.py)).
- **Self-Learning Loop**: When users report scams at `/api/report`, descriptions are saved to SQLite and automatically trigger `retrain_model_from_db()`, reinforcing the Naive Bayes weights on the fly.
- **Scam Categorization**: Classifies text patterns into 4 classes:
  - `cashback_reward` (Lottery / Scratch card cashback lures)
  - `kyc_threat` (Account block / PAN card suspension scares)
  - `bill_collect` (Power / Gas disconnection bill traps)
  - `safe_transaction` (Successful banking transaction receipts)

### 5. 🌐 Multi-Language i18n Localization Engine (EN / HI)
- **DOM Translation Engine**: Built in [language.js](frontend/js/language.js), recursively translates leaf text elements and inputs to Hindi, using local memory caching to toggle back to English instantly.
- **Dynamic Watcher**: Uses a `MutationObserver` to automatically translate asynchronously generated content (logs, database listings, sandbox alerts).
- **Micro-Animations**: Features a smooth 360-degree globe rotation spin transition on button click.
- **Persistence**: Remembers preferences across routing using `localStorage`.

---

## 🏗️ Tech Stack

### 💻 Frontend
- HTML5 (Semantic Structure)
- TailwindCSS (Styling, Dark Mode, Animations)
- Javascript (ES6 DOM Logic, Web Crypto API)
- HTML5-Qrcode Library (Camera Scanner)

### 🧠 Backend
- Python 3 (Flask API Server)
- OpenCV / Pillow (Image processing & analysis)
- SQLite3 (Transaction logging, complaints, training repository)
- Pytesseract (OCR text extraction)

---

## 📂 Project Structure

```text
SuRaksha/
├── backend/
│   ├── routes/
│   │   ├── analyze.py         # Image signature checks & OCR pipeline
│   │   ├── health.py          # API status checks
│   │   ├── qr.py              # QR decoding route
│   │   └── report.py          # Complaints & geolocated telemetry feeds
│   ├── services/
│   │   ├── history_store.py   # SQLite tables, indexing & dynamic migration
│   │   ├── ml_classifier.py   # TF-IDF + Naive Bayes training engine
│   │   ├── ocr_service.py     # Tesseract OCR & spelling normalizer
│   │   ├── risk_aggregator.py # Weighted threat calculation
│   │   └── master_engine.py   # Aggregated analytics dispatcher
│   └── app.py                 # Flask server initialization & DB setup
│
├── frontend/
│   ├── index.html             # Hero landing & visual comparisons
│   ├── scan.html              # Core scanning dashboard, generator, and SOC map
│   ├── about.html             # Team profiles and quick AI simulator
│   ├── features.html          # Bento-grid feature highlights
│   ├── how.html               # Multi-step safety tutorials
│   ├── test.html              # Attack vector testing canvas
│   ├── css/                   # Global CSS rules
│   └── js/
│       ├── app.js             # API request routing, ELA, and map triggers
│       ├── language.js        # Dynamic translation dictionary & observer
│       └── theme.js           # Theme state manager
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- Tesseract OCR (added to System PATH)

### 2. Backend Setup
```bash
# Navigate to backend folder
cd backend

# Install dependencies (virtual environment recommended)
pip install -r requirements.txt

# Start Flask Server
python app.py
```
*The Flask server launches at `http://127.0.0.1:5000` and automatically runs `init_db()` to configure database indexes.*

### 3. Frontend Setup
```bash
# Run a local web server from the project root
python -m http.server 8000
```
*Open [http://localhost:8000/index.html](http://localhost:8000/index.html) in your browser.*

---

## 📊 Verification & Tests

A validation test suite is available under the scratch space. To execute tests for the telemetry endpoints, reports, and ML training loops:
```bash
python .system_generated/tasks/test_backend_upgrades.py
```

---

## 👨‍💻 Development Team

* **Suraj Sawant** — Team Lead & Lead AI Architect
* **Antigravity** — AI Pair Programmer
* **Stitch** — AI Collaboration Specialist

---

## ⚠ Disclaimer

This project was built for educational and hackathon purposes. It is a simulated application demonstrating modern cybersecurity concepts and should not be used as-is for commercial financial transactions.

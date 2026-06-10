# Welcome to the SuRaksha Wiki 🛡️

**SuRaksha** (meaning *Security* or *Protection* in Sanskrit) is a zero-trust cybersecurity shield designed specifically for the Indian Unified Payments Interface (UPI) transaction ecosystem. 

It acts as an intercepting gateway between transaction inputs (QR scans, invoice screenshots, SMS texts) and the user entering their secure UPI PIN, protecting daily payers and merchants from sophisticated visual and cryptographic payment fraud.

---

## ⚡ Quick Start / TL;DR

Get the SuRaksha system running locally in 3 simple steps:

### 1. Start the Flask Backend API
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
*Backend runs on `http://127.0.0.1:5000`.*

### 2. Start the Frontend Web Server
In a new terminal window at the project root:
```bash
python -m http.server 8000
```
*Open your browser and navigate to `http://localhost:8000/frontend/index.html`.*

### 3. Run the Security Tests
Ensure rate limiters, HTTP security headers, and in-memory canvas sanitizers are functioning:
```bash
python verify_security.py
```

---

## 🔍 The UPI Threat Landscape

SuRaksha actively intercepts four main classes of payment vector attacks:

| Attack Vector | Scam Technique | SuRaksha Defense Layer |
| :--- | :--- | :--- |
| **Physical Sticker Swap** | Replacing merchant QR stickers on shop counters with attacker-controlled handles. | **Cryptographic QR Signing** (validates WebCrypto signatures against a private backend registry). |
| **Doctored Success Screen** | Editing transaction success screenshots (timestamp/amount) to walk away with goods. | **Error Level Analysis (ELA)** & **Laplacian Variance** (detects visual text overlay alterations). |
| **Linguistic Phishing** | SMS/WhatsApp messages warning about KYC blocks, bills, or claiming cashbacks. | **Multilingual Naive Bayes NLP** (extracts threat intent across 5 major Indian languages). |
| **VPA Typosquatting** | Registering similar-looking handles (e.g. `electricity.bill@ybl` instead of `sbi`). | **Fuzzy Word Sequence Matcher** (checks similarity ratios against registered domains). |

---

## 🏗️ Core Defense Modules

SuRaksha is designed with a **defense-in-depth** model. If an attacker evades one checker, secondary checks in the pipeline flag the transaction:

```
                  ┌──────────────────────────────┐
                  │ Scanned QR / Screenshot / SMS│
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                     [ localCache interceptor ] ──────► Matches Local Blacklist? ──► [ BLOCK ]
                                 │ (No)
                                 ▼
                    [ In-Memory EXIF Scanner ] ──────► Contains Photo Editor EXIF? ─► [ OVERRIDE BLOCK ]
                                 │ (Pass)
                                 ▼
                   [ Error Level Analysis (ELA) ] ───► Localized Noise High? ────► [ OVERRIDE BLOCK ]
                                 │ (Pass)
                                 ▼
                    [ Dual-Layer Text Checkers ]
                  ┌──────────────┴───────────────┐
                  ▼                              ▼
          [ Naive Bayes NLP ]          [ Fuzzy Name Matcher ]
      Categorizes text intent &     Checks VPA handle alignment
      flags multilingual threats       against display names
                  │                              │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                     [ Unified Risk Aggregator ] ─────► Weighted Score >= 60% ─────► [ BLOCK ]
```

---

## 📖 Wiki Navigation

Use the links below to explore the detailed technical configurations, algorithms, and modules:

* 🏗️ **[[Architecture & Design]]**: System routes, directories, SQLite schemas, and async processing threads.
* 📷 **[[Image Forensics & Receipt Verification]]**: In-memory OpenCV operations, EXIF stripping, and Error Level Analysis math.
* 🧠 **[[Natural Language Processing & Phishing Detection]]**: TF-IDF NLP model details, multi-lingual keyword maps, and fuzzy matches.
* 🔑 **[[QR Code Signing & Registry]]**: Secure client-side WebCrypto signing and secure backend signature verification.
* 📡 **[[API Documentation]]**: Full REST API reference, request/response models, and global JSON rate limit formats.
* 🛠️ **[[Setup & Auditing]]**: Prerequisites, Tesseract OCR setup guide, PyCharm run configurations, and test suite execution.
* 🎬 **[[User Walkthrough & Demo Flow]]**: Visual simulation scripts and step-by-step user interaction scenarios.

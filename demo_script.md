# 🛡️ SuRaksha Hackathon Demo Script & Testing Guide

Welcome to the **SuRaksha UPI Fraud Detection System** interactive demonstration guide! This script is designed to help hackathon judges and developers quickly experience the full threat intelligence capabilities of our system.

---

## 🚀 1. Setup & Quick Start

If you haven't already started the servers, run these command blocks in your terminal:

### Start the Flask Backend
```powershell
backend\venv\Scripts\python.exe backend\app.py
```
*App launches on: `http://127.0.0.1:5000`*

### Start the Frontend Web Server
```powershell
backend\venv\Scripts\python.exe -m http.server 8000 --directory frontend
```
*Site launches on: [http://127.0.0.1:8000](http://127.0.0.1:8000)*

---

## 🎯 2. Interactive Demo Scenarios

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser and proceed with the following test scenarios:

### 📱 Scenario A: UPI QR Scan Analysis
This module detects forged QR codes, intent mismatches, and high-risk handles.

1. **Test Safe Transaction**:
   - Select **Send Money (Pay)**.
   - Click **Upload QR from Gallery** and select any standard, safe UPI QR image.
   - **Expected Outcome**: Flat **Safe Transaction (LOW RISK)** popup.

2. **Test Malicious Scammer QR (Deep Link)**:
   - Select **Send Money (Pay)**.
   - Click **Upload QR from Gallery** or input a raw UPI link string containing high-risk parameters, for example:
     `upi://pay?pa=scammer@ybl&pn=Reward%20Office&am=50000&tn=cashback`
   - **Expected Outcome**: **🚨 High Risk Detected (CRITICAL/HIGH)**, risk score ≥ 75%, sirens play, and clear list of reasons (Suspicious term "cashback", Risky handle "@ybl", Generic name).

---

### 🖼️ Scenario B: Payment Screenshot & Tamper AI Detection
This module combines CV2 Image Tampering metrics (Laplacian variance, compression artifacts, block consistency) with OCR Text analysis.

> [!TIP]
> **Resilience Fallback Active**: If you don't have the external `tesseract` binary installed on your local OS, we have built a **Smart Filename Fallback** system. Simply name your image file with a keyword to simulate full OCR text parsing:

1. **Test AI Fraud Screen Fallback (Lottery Scam)**:
   - Save any random image as `reward_proof.png`.
   - Drag & drop or upload it under **Analyze Payment Screenshot** and click **Analyze Screenshot**.
   - **Expected Outcome**: The system automatically triggers the lottery/reward threat engine, alerting you to the fake reward cash transaction with high confidence.

2. **Test Account Block Scams**:
   - Save any random image as `support_verification.png`.
   - Upload it and click **Analyze Screenshot**.
   - **Expected Outcome**: Triggers the social engineering alarm for bank account blocks and phishing help desk handles.

---

### 💬 Scenario C: SMS & WhatsApp Message Intelligence
This module analyzes plain-text behavioral patterns, scam structures, and multilingual keywords in real-time.

Copy and paste the following sample messages into the **Message Scanner** input box:

1. **Lottery/Reward Scam (Hindi/Marathi/English Mix)**:
   > *"Congratulations! You have won an official Paytm cashback reward of Rs 25000. Click here to claim your इनाम: upi://pay?pa=win_paytm@ybl"*
   - **Expected Outcome**: **CRITICAL** risk levels flagging the mismatched payment intent and devious cashback keywords.

2. **Helpline Phishing**:
   > *"Your SBI bank account is suspended due to missing KYC. Contact customer care support division immediately at SBI Helpline upi://pay?pa=sbi_helpdesk@ibl"*
   - **Expected Outcome**: **HIGH** risk flagging fake helpline payee name, suspicious handle, and panic-inducing behavioral phrases.

---

## 🧠 3. Core Tech Stack Powering SuRaksha
* **Master Risk Engine**: Aggregates signals from Keyword Intelligence, Behavioral Intelligence, and Metadata checks.
* **Tamper AI**: OpenCV Edge Analysis, JPEG Compression inconsistencies, and Laplacian Variance calculators.
* **Multilingual NLP**: Built-in support for Hindi, Bengali, and English scam patterns.

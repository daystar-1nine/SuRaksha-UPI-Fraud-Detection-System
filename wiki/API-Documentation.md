# REST API Documentation 📡

The SuRaksha Flask server provides a set of JSON REST API endpoints to process transaction checks, manage the merchant registry, log threat reports, and sync local blacklists.

---

## 🚦 Global Rate Limiting & Intercepts

To prevent automated spam and denial-of-service attempts, SuRaksha implements IP-based rate limiting via `Flask-Limiter`. 

When a rate limit is exceeded:
- The API returns an **HTTP 429 Too Many Requests** status code.
- The response body is formatted as a structured JSON object.
- Response headers include rate limit metadata:
  - `X-RateLimit-Limit`: Maximum requests allowed in the window.
  - `X-RateLimit-Remaining`: Remaining requests allowed in the current window.
  - `X-RateLimit-Reset`: Unix timestamp when the limit resets.

### JSON Error Format (HTTP 429)
```json
{
  "success": false,
  "error": {
    "code": 429,
    "name": "Too Many Requests",
    "description": "Limit exceeded: 15 per minute"
  }
}
```

---

## 📡 Endpoint Directory

| Endpoint | Method | Rate Limit | Description |
| :--- | :--- | :--- | :--- |
| `/analyze/image` | `POST` | 40 / min | Analyzes invoice and payment receipt screenshots (in-memory ELA + OCR). |
| `/analyze/text` | `POST` | 60 / min | Analyzes message texts using the Naive Bayes NLP threat engine. |
| `/analyze/qr` | `POST` | 40 / min | Validates QR codes, checks VPAs, and verifies cryptographic signatures. |
| `/api/report` | `POST` | 15 / min | Registers a community fraud report and triggers model retraining. |
| `/api/stats` | `GET` | Unlimited | Retrieves platform statistics (threats blocked, reports logged). |
| `/api/soc/threats` | `GET` | Unlimited | Fetches threat telemetry coordinates for the Security Operations map. |
| `/api/blacklist/sync` | `GET` | Unlimited | Exports the compiled fraud VPA registry to synchronize local caches. |

---

## 📝 Detailed Endpoint References

### 1. Image Threat Scanner
Analyze uploaded screenshot image streams for visual tampering and check transaction details.

- **URL**: `/analyze/image`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Payload**:
  - `image`: File (Binary image stream, max 5MB)
  - `intent`: String (`"pay"` or `"receive"`)
- **Success Response (HTTP 200)**:
```json
{
  "success": true,
  "request_id": "4b6b7a2d-1a89-4d92-bf39-38b8d4e9d0a1",
  "detected_action": {
    "action": "PAY",
    "confidence": 0.95
  },
  "risk": {
    "risk_score": 15.0,
    "risk_level": "LOW"
  },
  "tamper_analysis": {
    "ela_score": 0.12,
    "laplacian_variance": 845.2,
    "risk_level": "SAFE"
  },
  "decision": {
    "safe_to_pay": true,
    "recommended_action": "Looks safe, but proceed with caution."
  }
}
```

---

### 2. NLP Message Threat Scanner
Analyze SMS, WhatsApp texts, or clipboard templates for phishing indicators.

- **URL**: `/analyze/text`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "text": "Your electricity bill is unpaid. Connection will be cut tonight. Pay immediately at upi://pay?pa=electricity@ybl",
  "intent": "pay"
}
```
- **Success Response (HTTP 200)**:
```json
{
  "success": true,
  "risk": {
    "risk_score": 85.0,
    "risk_level": "HIGH"
  },
  "ml_analysis": {
    "top_category": "phishing_urgency",
    "probabilities": {
      "phishing_urgency": 0.82,
      "cashback_scam": 0.11,
      "legitimate": 0.07
    }
  },
  "analysis": {
    "top_risk_factor": "behavior_score",
    "reasons": [
      "Urgency marker detected: cut connection warning",
      "UPI ID mismatch for unregistered VPA domain"
    ]
  }
}
```

---

### 3. QR Code Verifier
Analyze parsed QR string payloads, check blacklists, and verify merchant signatures.

- **URL**: `/analyze/qr`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "text": "upi://pay?pa=starcafe@upi&pn=Star%20Cafe&sign=900c7e2c9efcc9497e29a9b70559eb4a362f68db757e2bbd8e0ca2c8c4a16147"
}
```
- **Success Response (HTTP 200)**:
```json
{
  "success": true,
  "vpa": "starcafe@upi",
  "payee_name": "Star Cafe",
  "signature_status": "VALID",
  "is_blacklisted": false,
  "risk": {
    "risk_score": 0.0,
    "risk_level": "SAFE",
    "reason": "Cryptographically verified merchant certificate"
  }
}
```

---

### 4. Community Fraud Registry
Submit a VPA fraud report to SQLite and queue background classifier retraining.

- **URL**: `/api/report`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "upi": "scammer@ybl",
  "description": "WhatsApp KYC block link scam"
}
```
- **Success Response (HTTP 200)**:
```json
{
  "success": true,
  "message": "Report successfully logged. Model training initiated."
}
```

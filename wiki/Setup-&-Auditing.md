# Setup & Auditing Guide 🛠️

Follow this guide to configure Python environments, install system-level OCR binaries, launch the application locally, and run the security test suite.

---

## 📋 Prerequisites

To support image text extraction (OCR), you must install **Tesseract OCR** on your system:

### 1. Install Tesseract OCR

* **Windows**:
  1. Download the installer from the [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Run the installer and complete the setup. By default, it installs to `C:\Program Files\Tesseract-OCR`.
  3. Add the installation path (`C:\Program Files\Tesseract-OCR`) to your system **Path** Environment Variable:
     - Search for "Edit the system environment variables" in Windows Search.
     - Click **Environment Variables**, select **Path** under System Variables, click **Edit**, and add the path.
* **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt-get update
  sudo apt-get install tesseract-ocr libtesseract-dev
  ```
* **macOS**:
  ```bash
  brew install tesseract
  ```

---

## 🚀 Local Installation & Run

### 1. Configure and Run the Flask Backend
```bash
# Navigate to the backend folder
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Unix / macOS:
source venv/bin/activate

# Install required Python dependencies
pip install -r requirements.txt

# Start the Flask API server
python app.py
```
*The Flask server compiles dynamic index structures and starts on `http://127.0.0.1:5000`.*

### 2. Run the Frontend Interface
Since the frontend consumes the backend REST endpoints directly using AJAX requests, you can serve the frontend files using a local Python web server:
```bash
# Navigate back to the project root directory
cd ..

# Start a simple HTTP server on port 8000
python -m http.server 8000
```
*Open your browser and navigate to `http://localhost:8000/frontend/index.html`.*

---

## 💻 PyCharm Integration & Workspace

SuRaksha includes pre-configured settings to make it compatible with PyCharm out-of-the-box:

- **Shared Run Configurations**: Pre-loaded run configurations are saved in the `.idea/runConfigurations/` directory. You can run the Flask server or the security verification script directly from PyCharm's Run dropdown.
- **Index Exclusions**: Heavy directories such as virtual environments (`venv/`, `.venv/`) and upload folders are excluded from indexing to optimize search and IDE performance.

---

## 🧪 Security Auditing Suite

SuRaksha includes an automated security audit script (`verify_security.py`) to verify API integrity and defense controls.

To run the audit:
```bash
python verify_security.py
```

### What the Audit Verifies:
1. **Flask Bootstrap**: Verifies that the Flask backend binds to port 5000 and responds successfully.
2. **HTTP Security Headers**: Checks that headers like `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Content-Security-Policy` are active and match secure defaults.
3. **Flask-Limiter Integration**: Validates that rate-limiting headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`) are present in responses.
4. **In-Memory File Processing**: Verifies that image uploads processed by `/analyze/image` are kept in memory and that zero temporary files are written to the server's disk.
5. **Rate-Limiter Interceptions**: Simulates a rapid-fire attack (20 requests in 5 seconds) to confirm that the server intercepts spam and responds with **HTTP 429 Too Many Requests**.

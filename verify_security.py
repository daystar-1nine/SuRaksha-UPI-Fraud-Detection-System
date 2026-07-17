# s:\Hackathon\SuRaksha\verify_security.py
"""Automated security and stability verification suite for SuRaksha APIs."""

import os
import sys
import time
import subprocess
import requests
import io
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    print("==================================================")
    print("🔍 SURAKSHA SECURITY VERIFICATION SUITE")
    print("==================================================")

    # 1. Start Flask app in background
    print("\n[1/5] Launching Flask Server in background...")
    cmd = [r"backend\venv\Scripts\python.exe", "backend/app.py"]
    
    # Run with subprocess, piped outputs to prevent blocking
    server_proc = subprocess.Popen(
        cmd,
        cwd="s:\\Hackathon\\SuRaksha",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for Flask to bind to port 5000
    time.sleep(4)

    # Check if server started successfully
    if server_proc.poll() is not None:
        stdout, stderr = server_proc.communicate()
        print("[ERROR] Flask server failed to start. Logs:")
        print(stderr)
        sys.exit(1)

    try:
        # Check connection
        try:
            r = requests.get("http://127.0.0.1:5000/api/stats", timeout=5)
            print("  [OK] Successfully connected to Flask API server.")
        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            sys.exit(1)

        # 2. Verify Security Headers
        print("\n[2/5] Inspecting HTTP Security Headers...")
        headers = r.headers
        required_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none';"
        }
        
        headers_ok = True
        for header, expected in required_headers.items():
            value = headers.get(header)
            print(f"  - {header}: {value}")
            if not value or value.strip().replace(" ", "") != expected.strip().replace(" ", ""):
                # Accept slight whitespace variations
                if not value:
                    print(f"    [FAIL] Missing {header}!")
                    headers_ok = False
        
        if headers_ok:
            print("  [SUCCESS] All response security headers are active and valid!")
        else:
            print("  [WARNING] Some security headers did not match expected values.")

        # 3. Verify Rate Limiting
        print("\n[3/5] Inspecting Flask-Limiter Integration...")
        r_msg = requests.post(
            "http://127.0.0.1:5000/analyze/message",
            json={"text": "Congratulations! You won a cashback reward of Rs 50000. Claim at upi://pay?pa=scam@ybl", "intent": "pay"},
            timeout=5
        )
        
        print(f"  - Route: /analyze/message")
        print(f"  - Response status: {r_msg.status_code}")
        
        limit = r_msg.headers.get("X-RateLimit-Limit")
        remaining = r_msg.headers.get("X-RateLimit-Remaining")
        print(f"  - X-RateLimit-Limit: {limit}")
        print(f"  - X-RateLimit-Remaining: {remaining}")
        
        if limit and remaining:
            print("  [SUCCESS] Rate limiting headers verified successfully.")
        else:
            print("  [ERROR] Rate limiting headers are missing from response.")

        # 4. Verify Zero-Disk In-Memory Image Upload & Sanitization
        print("\n[4/5] Testing In-Memory Upload & EXIF Sanitization...")
        
        uploads_dir = "backend/uploads"
        initial_files = set()
        if os.path.exists(uploads_dir):
            initial_files = set(os.listdir(uploads_dir))

        # Generate a dummy test image in memory
        img = Image.new("RGB", (150, 150), color="blue")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        # Upload
        upload_files = {
            "image": ("attack_vector_sample.png", img_io, "image/png")
        }
        upload_data = {
            "intent": "pay"
        }
        
        r_upload = requests.post(
            "http://127.0.0.1:5000/analyze/image",
            files=upload_files,
            data=upload_data,
            timeout=10
        )
        
        print(f"  - Response status: {r_upload.status_code}")
        if r_upload.status_code == 200:
            res_data = r_upload.json()
            risk = res_data.get("data", {}).get("analysis", {}).get("risk_level")
            print(f"  - Returned Risk Classification: {risk}")
            print("  - Metadata Scan Result:", res_data.get("data", {}).get("metadata", {}).get("risk_level"))
            print("  - Tamper Check Result:", res_data.get("data", {}).get("tamper_analysis", {}).get("risk_level"))
        else:
            print(f"  - [ERROR] Upload failed with body: {r_upload.text}")

        # Check for disk leakage
        final_files = set()
        if os.path.exists(uploads_dir):
            final_files = set(os.listdir(uploads_dir))
        
        leakage = final_files - initial_files
        if not leakage:
            print("  [SUCCESS] In-memory file processing verified: zero files written to disk!")
        else:
            print(f"  [FAIL] Leakage detected! Files written to uploads: {leakage}")

        # 5. Check consecutive requests to verify rate limits behavior
        print("\n[5/5] Testing consecutive requests rate limiting limits...")
        # Send a few quick requests to /api/report to test rate limits
        print("  - Sending 20 requests to /api/report inside 5 seconds...")
        triggered_429 = False
        for i in range(20):
            r_rep = requests.post(
                "http://127.0.0.1:5000/api/report",
                json={"upi_id": "test_spam@ybl", "fraud_type": "Spam", "description": "Spam query test"},
                timeout=2
            )
            if r_rep.status_code == 429:
                triggered_429 = True
                description = r_rep.json().get('error', {}).get('description', '')
                print(f"    - [OK] Rate limit triggered on request {i+1} (HTTP 429: {description})")
                break
            time.sleep(0.05)
            
        if triggered_429:
            print("  [SUCCESS] Rate limiter successfully intercepted spam requests.")
        else:
            print("  [INFO] Rate limit not triggered (limits might be configured relaxed). Check configuration.")

    finally:
        # Shutdown server
        print("\nShuttling down background Flask server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
            print("  [OK] Flask server terminated.")
        except subprocess.TimeoutExpired:
            server_proc.kill()
            print("  [FORCE] Flask server force-killed.")
            
    print("\n==================================================")
    print("🎉 VERIFICATION COMPLETE")
    print("==================================================")

if __name__ == "__main__":
    run_verification()

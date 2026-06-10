# User Walkthrough & Demo Flow 🎬

This guide provides step-by-step scenarios to demonstrate the capabilities of the SuRaksha UPI Fraud Detection platform.

---

## 🎬 Scenario 1: Scanning a Merchant QR Code

This scenario demonstrates how the system protects users against static QR sticker-swapping.

### Step 1: Scan an Unverified/Tampered QR Code
1. Open the **Secure QR Scanner** page (`scan.html`).
2. Generate a standard UPI payment QR code containing:
   `upi://pay?pa=malicious_attacker@upi&pn=Fake%20Store`
3. Point your camera at the QR code (or upload it in the scanner interface).
4. **Expected Result**: 
   - The scanner flags a **CRITICAL RISK (95%)** alert.
   - The warning specifies: `Physical sticker swap detected (Missing cryptographic signature)`.
   - The payment route is blocked to prevent funds diversion.

### Step 2: Scan a Cryptographically Signed QR Code
1. Scroll down to the **Cryptographic Secure QR Generator** section on the scan page.
2. Select a pre-registered merchant (e.g. *Star Cafe* or *Sharma Kirana Store*) and input a test amount.
3. Click **Generate Cryptographically Secure QR**.
4. Scan the resulting QR code.
5. **Expected Result**:
   - The interface glows green and displays the **Verified Merchant Shield**.
   - The risk rating is shown as **SAFE (0% Risk)**.
   - The system confirms: `Cryptographically verified merchant signature`.

---

## 🎬 Scenario 2: Verifying a Doctored Payment Receipt

This scenario demonstrates how to audit transaction screenshots for visual manipulation.

1. Navigate to the **Attack Vector Simulator Sandbox** (`test.html`).
2. Select the **Image / Screenshot Upload** tab.
3. Upload a modified receipt screenshot (e.g., one where the transaction amount text was overlayed or altered).
4. Click **Analyze Screenshot**.
5. **Expected Result**:
   - The system analyzes the image in-memory.
   - The **Error Level Analysis (ELA) Viewer** displays a visual heatmap. Modified text blocks highlight as bright pixel clusters due to compression mismatch.
   - The **Laplacian Variance** checker flags if edge gradients exceed the sharpness limit ($>2000$), warning of text overlay.
   - The risk aggregator sets the risk rating to **CRITICAL** and advises blocking.

---

## 🎬 Scenario 3: Checking a Suspicious Message

This scenario demonstrates NLP phishing detection.

1. Navigate to the **Scan Message** chassis simulator on the scanner page (`scan.html`).
2. Click on the **Cashback Scam** chip or paste a custom threat text:
   `"Congratulations! You won a cash reward of Rs 25,000 from GPay. Claim now at: upi://pay?pa=claim@ybl"`
3. Click the **Send** button.
4. **Expected Result**:
   - The message is analyzed by the Naive Bayes engine.
   - The simulation screen displays a threat warning.
   - The NLP classification resolves to `cashback_scam` with high probability.
   - Specific triggers identify the use of urgent language and reward claims.

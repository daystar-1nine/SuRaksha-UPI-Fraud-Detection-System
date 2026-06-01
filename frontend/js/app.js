// -----------------------------
// 🌍 GLOBAL STATE
// -----------------------------
const API_BASE = "http://127.0.0.1:5000";

let AppState = {
    intent: "pay",
    scanner: null,
    scanning: false,
    lastScannedUpi: ""   // Tracks UPI for Report Fraud flow
};

let localBlacklist = [];


// -----------------------------
// 🧠 UTILITIES
// -----------------------------
const $ = (id) => document.getElementById(id);

function safeText(el, value) {
    if (el) el.innerText = value;
}

function toggle(el, show) {
    if (!el) return;
    el.classList.toggle("hidden", !show);
}


// -----------------------------
// 🎯 INTENT HANDLER
// -----------------------------
function selectIntent(intent) {

    AppState.intent = intent;

    document.getElementById("qrSection")
    ?.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    const UI = {
        qrTitle: $("qrTitle"),
        qrSubtitle: $("qrSubtitle"),
        uploadQRSection: $("uploadQRSection"),
        scanText: $("scanText"),
        scanStatus: $("scanStatus"),
        payCard: $("payCard"),
        receiveCard: $("receiveCard"),
        payTick: $("payTick"),
        receiveTick: $("receiveTick"),
        reader: $("reader"),
        qr: $("receiveQR")
    };

    // Reset UI
    [UI.payTick, UI.receiveTick].forEach(el => el?.classList.add("hidden"));
    [UI.payCard, UI.receiveCard].forEach(el => el?.classList.remove("border-primary", "border-2"));

    toggle(UI.reader, false);
    toggle($("scannerWrapper"), false);
    toggle(UI.qr, false);

    if (intent === "pay") {

        safeText(UI.qrTitle, "Scan QR Code");
        safeText(UI.qrSubtitle, "Scan live QR or upload from gallery");
        toggle(UI.uploadQRSection, true);
        toggle(UI.scanText, true);

        safeText(UI.scanText, "Align QR code within the frame");
        UI.scanStatus.style.display = "block";

        UI.payTick?.classList.remove("hidden");
        UI.payCard?.classList.add("border-primary", "border-2");

        toggle(UI.reader, true);
        toggle($("scannerWrapper"), true);

        startScanner();

    } else {

        safeText(UI.qrTitle, "Receive Money");
        safeText(UI.qrSubtitle, "Show this QR to the sender to receive money safely");
        toggle(UI.uploadQRSection, false);
        toggle(UI.scanText, false); // Hide duplicate/out-of-place scan description

        UI.scanStatus.style.display = "none";

        UI.receiveTick?.classList.remove("hidden");
        UI.receiveCard?.classList.add("border-primary", "border-2");

        toggle(UI.qr, true);

        stopScanner();
    }
}


// -----------------------------
// 📡 API LAYER (CLEAN 🔥)
// -----------------------------
async function apiRequest(endpoint, body, isForm = false) {

    try {
        const options = {
            method: "POST",
            headers: isForm ? {} : { "Content-Type": "application/json" },
            body: isForm ? body : JSON.stringify(body)
        };

        const res = await fetch(`${API_BASE}${endpoint}`, options);

        if (!res.ok) {
            throw new Error(`HTTP Error: ${res.status}`);
        }

        const data = await res.json();

        if (data.success === false) {
            throw new Error(data.error || "API Error");
        }

        return data;

    } catch (err) {
        showToast("⚠ Backend connection failed", "error");
        console.error("API ERROR:", err);
        throw err;
    }
}


// -----------------------------
// 🔔 TOAST NOTIFICATIONS
// -----------------------------
function showToast(message, type = "info", duration = 3500) {
    const existing = document.getElementById("suraksha-toast");
    if (existing) existing.remove();

    const colors = {
        success: "bg-green-500/90 text-white",
        error:   "bg-red-500/90 text-white",
        warning: "bg-yellow-500/90 text-black",
        info:    "bg-blue-500/90 text-white"
    };

    const icons = {
        success: "check_circle",
        error:   "error",
        warning: "warning",
        info:    "info"
    };

    const toast = document.createElement("div");
    toast.id = "suraksha-toast";
    toast.className = `fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999] px-5 py-3 rounded-2xl
        backdrop-blur-xl shadow-2xl flex items-center gap-3 text-sm font-semibold
        transition-all duration-300 opacity-0 translate-y-4 ${ colors[type] || colors.info }`;
    toast.style.minWidth = "260px";
    toast.style.maxWidth = "90vw";
    toast.innerHTML = `
        <span class="material-symbols-outlined text-[20px]">${ icons[type] || "info" }</span>
        <span>${message}</span>`;

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateX(-50%) translateY(0)";
    });

    // Animate out and remove
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(-50%) translateY(16px)";
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

// -----------------------------
// 🖼 IMAGE ANALYSIS
// -----------------------------
async function analyzeImage() {

    const fileInput = $("imageInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Upload image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", file); // Use key "image" to match what the backend expects!
    formData.append("intent", AppState.intent); // Add active intent!

    toggle($("loader"), true);

    try {

        const data = await apiRequest("/analyze", formData, true);

        showScreenshotResultPopup(data);

    } catch (err) {

        alert("Backend error");
        console.error(err);

    } finally {
        toggle($("loader"), false);
    }
}


// -----------------------------
// 📷 SCANNER
// -----------------------------
async function startScanner() {

    if (AppState.scanning) {
        await stopScanner();
    }

    AppState.scanner = new Html5Qrcode("reader");
    AppState.scanning = true;
    try {
        await AppState.scanner.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: 250 },
            async (text) => {
                stopScanner();
                await sendQR(text);
            }
        );
    } catch (err) {
        console.error("Scanner error:", err);
    }
}

function stopScanner() {

    if (!AppState.scanner) return;

    AppState.scanner.stop()
        .then(() => {
            AppState.scanner.clear();
            AppState.scanner = null;
            AppState.scanning = false;
        })
        .catch(() => {});
}


// -----------------------------
// 🧠 UPI ADDRESS PARSER HELPER
// -----------------------------
function extractUpiAddress(text) {
    if (!text) return "";
    const lower = text.toLowerCase();
    if (lower.startsWith("upi://")) {
        try {
            const match = text.match(/[?&]pa=([^&]+)/i);
            if (match) return decodeURIComponent(match[1]).toLowerCase().trim();
        } catch (e) {
            console.error("URI parse error:", e);
        }
    }
    if (text.includes("@")) {
        return text.toLowerCase().trim();
    }
    return "";
}


// -----------------------------
// 📦 QR SEND
// -----------------------------
async function sendQR(text) {

    toggle($("loader"), true);

    // 0ms LOCAL CACHE PRECHECK INTERCEPTOR 🔥
    if (AppState.intent === "pay") {
        const scannedUpi = extractUpiAddress(text);
        if (scannedUpi) {
            AppState.lastScannedUpi = scannedUpi;  // Track for report fraud
            const matched = localBlacklist.find(item => item.upi.toLowerCase() === scannedUpi);
            if (matched) {
                console.log("0ms Local Intercept Match Found for UPI:", scannedUpi);
                toggle($("loader"), false);

                const mockApiResponse = {
                    success: true,
                    data: {
                        qr: {
                            parsed: {
                                pa: [matched.upi],
                                pn: ["Reported Fraud Profile"],
                                am: [""],
                                tn: ["Local Database Blocked"]
                            }
                        },
                        analysis: {
                            risk_score: Math.max(matched.reports * 10, 80),
                            risk_level: matched.risk_level || "CRITICAL",
                            fraud_type: "Local Blacklist Match",
                            detected_action: "Immediate Block. Severe reports exist locally.",
                            confidence: 0.99,
                            reasons: [
                                `UPI address match found in locally synchronized blacklist database.`,
                                `Reported threat intensity: ${matched.risk_level}.`,
                                `Total complaints logged locally: ${matched.reports}.`
                            ]
                        }
                    }
                };

                showResultPopup(mockApiResponse);
                return;
            }
        }

        // OFFLINE MODE COMPATIBILITY CHECK 🔥
        if (!navigator.onLine) {
            toggle($("loader"), false);
            showToast("⚠ Offline: No local threat found. Verify manually!", "warning", 5000);
            return;
        }
    }

    try {
        const data = await apiRequest("/analyze/qr", {
            text,
            intent: AppState.intent
        });

        // Store UPI for report fraud feature
        const extractedUpi = extractUpiAddress(text);
        if (extractedUpi) AppState.lastScannedUpi = extractedUpi;

        if (AppState.intent === "receive") {
            toggle($("loader"), false);
            $("resultPopup")?.classList.add("hidden");
            showToast("✅ This QR is safe for receiving money", "success");
            return;
        }

        showResultPopup(data);

    } catch {
        showToast("QR scan failed ❌", "error");
    } finally {
        toggle($("loader"), false);
    }
}
// -----------------------------
// 💬 MESSAGE ANALYSIS
// -----------------------------
async function analyzeMessage() {

    const text = $("messageInput").value;

    if (!text.trim()) {
        showToast("Please enter a message first", "warning");
        return;
    }

    toggle($("loader"), true);

    try {
        const data = await apiRequest("/analyze_text", { text });
        showResultPopup(data);
    } catch (err) {
        showToast("Error analyzing message", "error");
        console.error(err);
    } finally {
        toggle($("loader"), false);
    }
}


// -----------------------------
// 🔤 MANUAL UPI ID CHECK
// -----------------------------
async function checkUpiManual() {
    const input = $("manualUpiInput");
    if (!input) return;

    const upiText = input.value.trim();

    if (!upiText) {
        showToast("Enter a UPI ID first (e.g. name@bank)", "warning");
        return;
    }

    // Basic format check before sending
    const upiPattern = /^[a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20}$/;
    if (!upiPattern.test(upiText)) {
        showToast("Invalid UPI format. Use format: name@bank", "error");
        return;
    }

    AppState.lastScannedUpi = upiText.toLowerCase();

    // Build a synthetic UPI QR string
    const syntheticQR = `upi://pay?pa=${encodeURIComponent(upiText)}&pn=&am=&tn=&cu=INR`;
    await sendQR(syntheticQR);
}


// -----------------------------
// 🚨 REPORT FRAUD MODAL
// -----------------------------
function showReportModal(upiId) {
    const existing = document.getElementById("reportFraudModal");
    if (existing) existing.remove();

    const modal = document.createElement("div");
    modal.id = "reportFraudModal";
    modal.className = "fixed inset-0 bg-black/70 backdrop-blur-sm z-[9998] flex items-center justify-center p-4";
    modal.innerHTML = `
        <div class="bg-[#111827] border border-red-500/30 rounded-2xl p-6 w-full max-w-sm shadow-2xl shadow-red-500/10 animate-fadeIn">
            <div class="flex items-center gap-3 mb-4">
                <span class="material-symbols-outlined text-red-400 text-3xl">flag</span>
                <div>
                    <h3 class="text-white font-bold text-lg">Report Fraud</h3>
                    <p class="text-gray-400 text-xs">Help protect the community</p>
                </div>
            </div>
            <div class="bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 mb-4">
                <span class="text-red-300 text-xs font-mono">${upiId || "unknown"}</span>
            </div>
            <textarea id="reportDescription"
                class="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white text-sm placeholder:text-gray-500 resize-none focus:outline-none focus:border-red-400/50 transition"
                rows="3"
                placeholder="Describe the fraud (optional): e.g. 'Fake cashback QR sent via WhatsApp'"
                maxlength="500"></textarea>
            <div class="flex gap-2 mt-3">
                <button onclick="submitFraudReport('${upiId}')"
                    class="flex-1 bg-red-500 hover:bg-red-600 active:scale-95 text-white py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined text-[16px]">flag</span>
                    Submit Report
                </button>
                <button onclick="document.getElementById('reportFraudModal').remove()"
                    class="px-4 bg-white/5 hover:bg-white/10 text-white/70 py-2.5 rounded-xl text-sm transition-all border border-white/10">
                    Cancel
                </button>
            </div>
        </div>`;

    document.body.appendChild(modal);
    // Close on backdrop click
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.remove();
    });
}

async function submitFraudReport(upiId) {
    const desc = ($("reportDescription")?.value || "").trim();

    try {
        const res = await fetch(`${API_BASE}/api/report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ upi: upiId, description: desc })
        });
        const data = await res.json();

        document.getElementById("reportFraudModal")?.remove();

        if (data.success) {
            showToast("✅ Fraud report submitted! Thank you.", "success", 4000);
            // Refresh local blacklist so this UPI is instantly blocked
            syncOfflineBlacklist();
        } else {
            showToast("Failed to submit report: " + (data.error || "Unknown error"), "error");
        }
    } catch (e) {
        document.getElementById("reportFraudModal")?.remove();
        showToast("Could not reach server to file report", "error");
    }
}


// -----------------------------
// 📊 LIVE STATS COUNTER
// -----------------------------
function animateCounter(el, target, duration = 1800) {
    if (!el) return;
    const start = 0;
    const step = (timestamp) => {
        if (!step.startTime) step.startTime = timestamp;
        const progress = Math.min((timestamp - step.startTime) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3); // cubic ease-out
        el.textContent = Math.floor(ease * target).toLocaleString("en-IN");
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (!res.ok) return;
        const data = await res.json();
        if (!data.success || !data.stats) return;

        const s = data.stats;
        animateCounter($("statScans"),    s.total_scans    || 0);
        animateCounter($("statThreats"),  s.threats_caught || 0);
        animateCounter($("statFrauds"),   s.unique_frauds  || 0);
        animateCounter($("statReports"),  s.total_reports  || 0);
    } catch (e) {
        console.log("Stats not available:", e);
    }
}

// -----------------------------
// 🖼 IMAGE PREVIEW
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {

    $("imageInput")?.addEventListener("change", (e) => {

        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();

        reader.onload = (e) => {
            $("previewImage").src = e.target.result;
            toggle($("previewImage"), true);
            toggle($("uploadText"), true);
            document.getElementById("imageSection")
            ?.scrollIntoView({
            behavior: "smooth",
            block: "center"
            });
        };

        reader.readAsDataURL(file);
    });

});


// -----------------------------
// 🎬 RESULT POPUP
// -----------------------------
function showResultPopup(apiResponse) {
    if (!apiResponse || !apiResponse.success || !apiResponse.data) {
        console.warn("Skipping result popup: Invalid or unsuccessful API response.", apiResponse);
        return;
    }
    const analysis = apiResponse.data.analysis;
    if (!analysis) {
        console.warn("Skipping result popup: Missing analysis content.", apiResponse);
        return;
    }
    
    // ---------------------------------
    // 🖼 SCREENSHOT TAMPER & METADATA RISK MERGER 🔥
    // ---------------------------------
    const metadata = apiResponse.data.metadata;
    const tamper = apiResponse.data.tamper_analysis;

    let ocrScore = analysis.risk?.risk_score ?? analysis.risk_score ?? 0;
    let metadataScore = (metadata && metadata.risk_score != null) ? metadata.risk_score * 10 : 0;
    let tamperScore = (tamper && tamper.risk_score != null) ? tamper.risk_score : 0;

    // Take max of OCR, EXIF, and opencv tamper risk
    let riskScore = Math.max(ocrScore, metadataScore, tamperScore);

    // Risk level
    let riskLevel = "SAFE";
    if (riskScore >= 75) {
        riskLevel = "CRITICAL";
    } else if (riskScore >= 40) {
        riskLevel = "HIGH";
    } else if (riskScore >= 20) {
        riskLevel = "MEDIUM";
    } else if (riskScore > 0) {
        riskLevel = "LOW";
    }

    // Merge fraud details
    let isScreenshotCheck = (metadata || tamper) ? true : false;
    let fraudType = isScreenshotCheck ? "Screenshot Forgery" : (analysis.fraud?.fraud_type ?? analysis.fraud_type ?? "General");
    let detectedAction = isScreenshotCheck ? "Inspect receipt details carefully" : (analysis.detected_action?.action ?? analysis.detected_action ?? "-");
    if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
        detectedAction = isScreenshotCheck ? "Forged Receipt Blocked" : detectedAction;
    }

    // Merge reasons
    let combinedReasons = [];
    const ocrReasons = analysis.analysis?.reasons ?? analysis.reasons ?? [];
    ocrReasons.forEach(r => combinedReasons.push(r));

    if (metadata && metadata.reasons) {
        metadata.reasons.forEach(r => combinedReasons.push("EXIF: " + r));
    }
    if (tamper && tamper.reasons) {
        tamper.reasons.forEach(r => combinedReasons.push("Tamper: " + r));
    }

    const data = {
        risk_score: riskScore,
        risk_level: riskLevel,
        fraud_type: fraudType,
        detected_action: detectedAction,
        fraud_confidence: apiResponse.data.tamper_analysis?.confidence ?? apiResponse.data.metadata?.confidence ?? analysis.confidence ?? analysis.fraud_confidence ?? 0.85,
        reasons: combinedReasons
    };

    const popup = $("resultPopup");
    if (!popup) return;

    popup.classList.remove("hidden");
    
    popup.classList.add(
    "flex",
    "animate-fadeIn"
    );
    toggle($("loader"), false);
    window.scrollTo({
    top: 0,
    behavior: "smooth"
    });

    // -----------------------------
    // 📊 BASIC DATA
    // -----------------------------
    safeText($("popupScore"), data?.risk_score ?? "-");
    safeText($("popupLevel"), data?.risk_level ?? "-");
    safeText($("popupType"), data?.fraud_type ?? "General");
    safeText($("popupAction"), data?.detected_action ?? "-");

    safeText(
    $("popupConfidence"),
    data?.fraud_confidence != null
        ? `${(data.fraud_confidence * 100).toFixed(0)}%`
        : "-"
    );

    // -----------------------------
    // 📈 RISK BAR
    // -----------------------------
    const riskBar = $("riskBar");

    if (riskBar) {

        riskBar.style.width =
            `${data?.risk_score ?? 0}%`

        riskBar.className =
            "h-full rounded-full transition-all duration-500";

        if (
            data.risk_level === "CRITICAL"
            || data.risk_level === "HIGH"
        ) {

            riskBar.classList.add("bg-red-500");

        } else if (data.risk_level === "MEDIUM") {

            riskBar.classList.add("bg-yellow-400");

        } else {

            riskBar.classList.add("bg-green-500");

        }
    }

    // -----------------------------
    // 🚨 ALERT UI
    // -----------------------------
    const alert = $("popupAlert");
    const safe = $("popupSafe");

    if (
        data.risk_level === "CRITICAL"
        || data.risk_level === "HIGH"
    ) {

        alert.className =
            "text-red-500 text-2xl font-bold animate-pulse";

        safeText(alert, isScreenshotCheck ? "🚨 Screenshot Forgery Detected" : "🚨 High Risk Detected");

        safeText(safe, "❌ DO NOT PAY");

        $("alertSound")?.play();

    } else if (data.risk_level === "MEDIUM") {

        alert.className =
            "text-yellow-400 text-2xl font-bold";

        safeText(alert, isScreenshotCheck ? "⚠ Suspect Screenshot" : "⚠ Medium Risk");

        safeText(safe, "⚠ Verify Carefully");

    } else {

        alert.className =
            "text-green-500 text-2xl font-bold";

        safeText(alert, isScreenshotCheck ? "✅ Authentic Receipt" : "✅ Safe Transaction");

        safeText(safe, "✔ Safe To Proceed");

    }

    // -----------------------------
    // 📋 REASONS
    // -----------------------------
    const list = $("popupReasons");

    if (list) {

        list.innerHTML = "";

        (data?.reasons ?? []).forEach(reason => {

            const li = document.createElement("li");

            li.textContent = "⚠ " + reason;

            li.className = "text-sm text-gray-300";

            list.appendChild(li);

        });

    }

    // -----------------------------
    // 💳 UPI PAYMENT LINK GENERATION 🔥
    // -----------------------------
    const parsed = apiResponse.data?.qr?.parsed || {};
    const pa = (parsed.pa && parsed.pa[0]) || "";
    const pn = (parsed.pn && parsed.pn[0]) || "Recipient";
    const am = (parsed.am && parsed.am[0]) || "";
    const tn = (parsed.tn && parsed.tn[0]) || "SuRaksha Verified";

    let upiLink = "upi://pay?pa=" + encodeURIComponent(pa);
    if (pn) upiLink += "&pn=" + encodeURIComponent(pn);
    if (am) upiLink += "&am=" + encodeURIComponent(am);
    if (tn) upiLink += "&tn=" + encodeURIComponent(tn);
    upiLink += "&cu=INR";

    // Set links on app buttons
    const btnProceedPay = $("btnProceedPay");
    if (btnProceedPay) {
        if (data.risk_level === "CRITICAL" || data.risk_level === "HIGH") {
            btnProceedPay.innerText = "Bypass Warning & Pay Anyway";
            btnProceedPay.className = "w-full bg-gradient-to-r from-yellow-600 to-amber-700 hover:from-amber-700 hover:to-yellow-600 active:scale-[0.99] text-white py-3.5 rounded-xl font-bold tracking-wide transition-all shadow-lg shadow-yellow-600/10 cursor-pointer text-center text-sm uppercase";
        } else {
            btnProceedPay.innerText = "Proceed to Pay";
            btnProceedPay.className = "w-full bg-gradient-to-r from-primary to-blue-600 hover:from-blue-600 hover:to-primary active:scale-[0.99] text-white py-3.5 rounded-xl font-bold tracking-wide transition-all shadow-lg shadow-primary/20 cursor-pointer text-center text-sm uppercase";
        }
    }

    const appIds = ["payGPay", "payPhonePe", "payPaytm", "payBHIM"];
    appIds.forEach(id => {
        const el = $(id);
        if (el) el.href = upiLink;
    });

    // Report fraud button — show only for HIGH/CRITICAL
    const reportBtn = $("btnReportFraud");
    if (reportBtn) {
        const upiForReport = (parsed.pa && parsed.pa[0]) || AppState.lastScannedUpi || "";
        if ((data.risk_level === "CRITICAL" || data.risk_level === "HIGH") && upiForReport) {
            reportBtn.classList.remove("hidden");
            reportBtn.onclick = () => showReportModal(upiForReport);
        } else {
            reportBtn.classList.add("hidden");
        }
    }

    togglePaymentDrawer(false);

    console.log("Popup Data:", data);
}


function togglePaymentDrawer(show) {
    const drawer = $("paymentDrawer");
    const actions = $("popupActions");
    if (drawer) drawer.classList.toggle("hidden", !show);
    if (actions) actions.classList.toggle("hidden", show);
}

function simulatePaymentLaunch(appName) {
    const loader = $("loader");
    if (loader) {
        const p = loader.querySelector("p");
        if (p) p.innerText = "Redirecting to " + appName + "...";
        loader.classList.remove("hidden");
        setTimeout(() => {
            loader.classList.add("hidden");
            if (p) p.innerText = "Analyzing... AI is checking fraud";
        }, 1500);
    }
}

function closePopup() {
    const popup = $("resultPopup");
    if (popup) {
        popup.classList.add("hidden");
        popup.classList.remove("flex");
    }
}


// -----------------------------
// 🖼 SCREENSHOT AUTHENTICITY POPUP
// -----------------------------
function showScreenshotResultPopup(apiResponse) {
    if (!apiResponse || !apiResponse.success) {
        console.warn("Screenshot popup: Invalid API response", apiResponse);
        return;
    }

    const data = apiResponse.data;
    const metadata = data?.metadata;
    const tamper = data?.tamper_analysis;
    const analysis = data?.analysis;

    // ── Compute consolidated forgery risk ──
    let metaScore   = (metadata  && metadata.risk_score  != null) ? metadata.risk_score * 10 : 0;
    let tamperScore = (tamper    && tamper.risk_score    != null) ? tamper.risk_score        : 0;
    let ocrScore    = (analysis  && analysis.risk_score  != null) ? analysis.risk_score      : 0;
    let riskScore   = Math.max(metaScore, tamperScore, ocrScore);

    // ── Risk level ──
    let riskLevel = "SAFE";
    if      (riskScore >= 75) riskLevel = "CRITICAL";
    else if (riskScore >= 50) riskLevel = "HIGH";
    else if (riskScore >= 25) riskLevel = "MEDIUM";
    else if (riskScore >  0 ) riskLevel = "LOW";

    // ── Confidence ──
    let confidence = tamper?.confidence ?? metadata?.confidence ?? analysis?.confidence ?? 0.85;

    // ── Recommended action ──
    let action = "Screenshot appears authentic";
    if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
        action = "⛔ Likely forged — do not trust this receipt";
    } else if (riskLevel === "MEDIUM") {
        action = "⚠ Some anomalies found — verify carefully";
    }

    // ── Build combined reasons list ──
    let reasons = [];
    if (metadata?.reasons)  metadata.reasons.forEach(r  => reasons.push("🔍 EXIF: "   + r));
    if (tamper?.reasons)    tamper.reasons.forEach(r    => reasons.push("🖼 Tamper: " + r));
    if (analysis?.reasons)  analysis.reasons.forEach(r  => reasons.push("📄 OCR: "    + r));
    if (reasons.length === 0) reasons.push("No suspicious indicators detected.");

    // ── Populate popup DOM ──
    const popup = $("screenshotResultPopup");
    if (!popup) return;

    // Icon container
    const iconContainer = $("screenshotIconContainer");
    if (iconContainer) {
        if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
            iconContainer.className = "inline-flex p-3 rounded-full mb-2 bg-red-500/15 text-red-500";
        } else if (riskLevel === "MEDIUM") {
            iconContainer.className = "inline-flex p-3 rounded-full mb-2 bg-yellow-500/15 text-yellow-400";
        } else {
            iconContainer.className = "inline-flex p-3 rounded-full mb-2 bg-green-500/15 text-green-400";
        }
    }

    // Title
    const alertEl = $("screenshotAlert");
    if (alertEl) {
        if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
            alertEl.className = "text-2xl font-bold tracking-tight text-center text-red-400 animate-pulse";
            alertEl.textContent = "🚨 Screenshot Forgery Detected";
        } else if (riskLevel === "MEDIUM") {
            alertEl.className = "text-2xl font-bold tracking-tight text-center text-yellow-400";
            alertEl.textContent = "⚠ Suspicious Screenshot";
        } else {
            alertEl.className = "text-2xl font-bold tracking-tight text-center text-green-400";
            alertEl.textContent = "✅ Authentic Screenshot";
        }
    }

    // Safe label
    const safeEl = $("screenshotSafe");
    if (safeEl) {
        if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
            safeEl.className = "text-sm font-semibold tracking-wide uppercase text-red-400";
            safeEl.textContent = "❌ DO NOT TRUST THIS RECEIPT";
        } else if (riskLevel === "MEDIUM") {
            safeEl.className = "text-sm font-semibold tracking-wide uppercase text-yellow-400";
            safeEl.textContent = "⚠ Verify Independently";
        } else {
            safeEl.className = "text-sm font-semibold tracking-wide uppercase text-green-400";
            safeEl.textContent = "✔ Receipt Looks Genuine";
        }
    }

    // Score & confidence
    safeText($("screenshotScore"),      riskScore.toFixed(0) + " / 100");
    safeText($("screenshotConfidence"), (confidence * 100).toFixed(0) + "%");
    safeText($("screenshotLevel"),      riskLevel);

    // Risk bar
    const bar = $("screenshotRiskBar");
    if (bar) {
        bar.style.width = riskScore + "%";
        bar.className = "h-full rounded-full transition-all duration-700 ";
        if      (riskLevel === "CRITICAL" || riskLevel === "HIGH") bar.className += "bg-red-500";
        else if (riskLevel === "MEDIUM")                           bar.className += "bg-yellow-400";
        else                                                        bar.className += "bg-green-500";
    }

    // Action label
    safeText($("screenshotAction"), action);

    // Reasons list
    const list = $("screenshotReasons");
    if (list) {
        list.innerHTML = "";
        reasons.forEach(reason => {
            const li = document.createElement("li");
            li.textContent = reason;
            li.className = "text-sm text-gray-300 py-0.5";
            list.appendChild(li);
        });
    }

    // Show popup
    popup.classList.remove("hidden");
    popup.classList.add("flex");
    toggle($("loader"), false);
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function closeScreenshotPopup() {
    const popup = $("screenshotResultPopup");
    if (popup) {
        popup.classList.add("hidden");
        popup.classList.remove("flex");
    }
}


// -----------------------------
// 🖼 QR IMAGE SCAN
// -----------------------------
$("qrImageInput")?.addEventListener("change", async (e) => {

    const file = e.target.files[0];
    if (!file) return;

    let scanner;

    try {
        scanner = new Html5Qrcode("reader");
        const text = await scanner.scanFile(file, true);

        await sendQR(text);

    } catch {
        alert("QR image scan failed ❌");
    } finally {
        if (scanner) {
            scanner.clear().catch(() => {});
        }
    }
});

// -----------------------------
// 🌐 OFFLINE BLACKLIST SYNCER
// -----------------------------
async function syncOfflineBlacklist() {
    try {
        if (!navigator.onLine) {
            console.log("Offline: Loading blacklist from localStorage cache...");
            const cached = localStorage.getItem("suraksha_blacklist_cache");
            if (cached) {
                localBlacklist = JSON.parse(cached);
            }
            return;
        }

        const res = await fetch(`${API_BASE}/api/blacklist/sync`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        
        if (data && data.success && data.blacklist) {
            localBlacklist = data.blacklist;
            localStorage.setItem("suraksha_blacklist_cache", JSON.stringify(localBlacklist));
            console.log("Offline Blacklist sync completed. Cached " + localBlacklist.length + " reported accounts.");
        }
    } catch (err) {
        console.warn("Failed to sync offline blacklist cache:", err);
        // Fallback to cache if exists
        const cached = localStorage.getItem("suraksha_blacklist_cache");
        if (cached) {
            localBlacklist = JSON.parse(cached);
        }
    }
}



// -----------------------------
// 🚀 INIT
// -----------------------------
window.onload = () => {
    selectIntent("pay");
    syncOfflineBlacklist();
    loadStats();

    // Live UPI format validator
    const upiInput = $("manualUpiInput");
    if (upiInput) {
        upiInput.addEventListener("input", validateUpiLive);
        upiInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") checkUpiManual();
        });
    }
};
window.addEventListener("beforeunload", () => {
    stopScanner();
});


// -----------------------------
// 🧩 HELPER: Live UPI Validator
// -----------------------------
function validateUpiLive() {
    const input = $("manualUpiInput");
    const badge = $("upiFormatBadge");
    if (!input || !badge) return;

    const val = input.value.trim();
    const upiPattern = /^[a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20}$/;

    if (!val) {
        badge.classList.add("hidden");
        input.classList.remove("border-success/50", "border-error/50");
        return;
    }

    badge.classList.remove("hidden");
    if (upiPattern.test(val)) {
        badge.textContent = "✓ Valid format";
        badge.className = "text-xs px-2 py-0.5 rounded-full bg-success/20 text-success";
        input.classList.remove("border-error/50");
        input.classList.add("border-success/50");
    } else {
        badge.textContent = "✗ Invalid";
        badge.className = "text-xs px-2 py-0.5 rounded-full bg-error/20 text-error";
        input.classList.remove("border-success/50");
        input.classList.add("border-error/50");
    }
}


// -----------------------------
// 🧩 HELPER: Char Counter
// -----------------------------
function updateCharCount() {
    const ta = $("messageInput");
    const counter = $("charCount");
    if (!ta || !counter) return;
    counter.textContent = `${ta.value.length} / 5000`;
}


// -----------------------------
// 🧩 HELPER: Scam Sample Paster
// -----------------------------
const SCAM_SAMPLES = [
    // 0 — Cashback Scam
    `🎉 Congratulations! You have won ₹5000 cashback reward from NPCI!\nScan the QR code below to claim your reward immediately.\nOffer expires in 24 hours. UPI: cashback@ybl\nDo NOT share this with anyone.`,

    // 1 — KYC Fraud
    `[SBI Alert] Your account will be blocked within 24 hours due to incomplete KYC.\nClick here to update your KYC now: http://sbi-kyc-update.in\nOr call our helpline: 9876543210\nEnter your UPI PIN to verify identity.`,

    // 2 — Prize Winner
    `Dear Customer, you are the LUCKY WINNER of ₹25,000 in our annual prize draw!\nTo receive your prize money, send ₹299 registration fee to:\nUPI: prizedraw@paytm\nReference: WIN2024\nMoney will be credited within 2 hours!`,

    // 3 — Legitimate (should score LOW/SAFE)
    `Hi, this is Rahul. I'm sending ₹500 for the dinner split.\nUPI: rahul.sharma@okicici\nPlease confirm once received. Thanks!`
];

function pasteScamSample(index) {
    const ta = $("messageInput");
    if (!ta) return;
    ta.value = SCAM_SAMPLES[index] || "";
    updateCharCount();
    ta.focus();
    ta.scrollIntoView({ behavior: "smooth", block: "center" });
}
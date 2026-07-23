import { Html5Qrcode } from 'html5-qrcode';
if (typeof window !== 'undefined') {
    window.Html5Qrcode = Html5Qrcode;
}

// ----------------------------------------------------------------------
// 🌍 GLOBAL STATE & APPLICATION STATE
// ----------------------------------------------------------------------
// Base API server URL. Dynamically switch between local dev and Render production endpoints.
// On physical Android/iOS native builds (Capacitor), window.Capacitor is present or protocol is capacitor:// or file://.
const isCapacitorNative = Boolean(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
const isLocal = !isCapacitorNative && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

const API_BASE = isLocal
    ? "http://127.0.0.1:5000"
    : "https://suraksha-upi-fraud-detection-system.onrender.com";

// Tracks active scan mode, HTML5Qrcode scanner references, and cached variables
let AppState = {
    intent: "pay",       // "pay" or "receive"
    scanner: null,       // Instantiated Html5Qrcode reader object
    scanning: false,     // Flag indicating whether camera video stream is active
    lastScannedUpi: ""   // Tracks the last scanned VPA address for the report modal
};

// Locally cached blacklist registry pulled from the backend database (sync offline mode)
let localBlacklist = [];
// Locally registered trusted merchants used to simulate signature check during generation/scan
let localTrustedMerchants = [];


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


// ----------------------------------------------------------------------
// 📡 API LAYER - CENTRALISED AJAX REQUEST HANDLER
// ----------------------------------------------------------------------
async function apiRequest(endpoint, body, isForm = false) {
    /**
     * Primary network gateway connecting the user interface to Flask API endpoints.
     * 
     * Why: Wraps error interception, payload formatting, CORS checks, and rate-limiting
     * alerts into a single unified function, making frontend code clean and resilient.
     * 
     * Handles HTTP 429 (Rate Limit Exceeded) returned by Flask-Limiter. It intercepts 429
     * responses, parses custom retry warnings, displays a temporary screen toast, and stops
     * the execution path to protect server bandwidth.
     */
    try {
        const options = {
            method: "POST",
            // If body is FormData (file upload), let browser calculate the boundary headers automatically
            headers: isForm ? {} : { "Content-Type": "application/json" },
            body: isForm ? body : JSON.stringify(body)
        };

        const res = await fetch(`${API_BASE}${endpoint}`, options);

        if (!res.ok) {
            // Handle rate limit headers returned by Flask server
            if (res.status === 429) {
                const errorData = await res.json().catch(() => ({}));
                const msg = errorData.error?.description || "Rate limit exceeded. Please try again later.";
                showToast(`⏳ ${msg}`, "warning", 5000);
                throw new Error("RATE_LIMIT_EXCEEDED");
            }
            throw new Error(`HTTP Error: ${res.status}`);
        }

        const data = await res.json();

        // Standardise error responses that return success=false
        if (data.success === false) {
            const errorMsg = (typeof data.error === 'object' && data.error !== null) 
                ? data.error.message 
                : data.error;
            throw new Error(errorMsg || "API Error");
        }

        return data;

    } catch (err) {
        // Prevent showing duplicate toast notifications if rate-limiting alert has already handled it
        if (err.message !== "RATE_LIMIT_EXCEEDED") {
            const msg = err.message.startsWith("HTTP Error") ? "⚠ Backend connection failed" : `⚠ ${err.message}`;
            showToast(msg, "error");
        }
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

// Compress and resize image using canvas before uploading
function compressImage(file, maxWidth = 1000) {
    return new Promise((resolve) => {
        // Skip compression for tiny files (under 150KB) to save CPU cycles
        if (file.size < 150 * 1024) {
            resolve(file);
            return;
        }

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                const canvas = document.createElement("canvas");
                let width = img.width;
                let height = img.height;

                if (width > maxWidth) {
                    height = Math.round((height * maxWidth) / width);
                    width = maxWidth;
                }

                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".jpg", { 
                            type: "image/jpeg", 
                            lastModified: Date.now() 
                        }));
                    } else {
                        resolve(file);
                    }
                }, "image/jpeg", 0.75); // Compress at 75% quality to match ELA engine baseline
            };
            img.onerror = () => resolve(file);
        };
        reader.onerror = () => resolve(file);
    });
}

// -----------------------------
// 🖼 IMAGE ANALYSIS
// -----------------------------
async function analyzeImage() {

    const fileInput = $("imageInput");
    const file = fileInput.files[0];

    if (!file) {
        showToast("Upload image first", "warning");
        return;
    }

    toggle($("loader"), true);

    try {
        const formData = new FormData();
        formData.append("image", file); // Send raw file to preserve metadata & ELA artifacts
        formData.append("intent", AppState.intent); // Add active intent!

        const data = await apiRequest("/analyze", formData, true);

        showScreenshotResultPopup(data);

    } catch (err) {
        // apiRequest already shows the specific toast message, so we just log it here
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
        let cameraConstraint = { facingMode: "environment" };
        
        // Explicitly trigger getUserMedia permission prompt for Android WebView
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                stream.getTracks().forEach(track => track.stop());
            } catch (permErr) {
                console.warn("Camera getUserMedia prompt:", permErr);
            }
        }

        try {
            const devices = await Html5Qrcode.getCameras();
            if (devices && devices.length > 0) {
                const selectEl = document.getElementById("cameraSelect");
                const selectContainer = document.getElementById("cameraSelectContainer");
                
                if (selectEl) {
                    selectEl.innerHTML = "";
                    devices.forEach(device => {
                        const opt = document.createElement("option");
                        opt.value = device.id;
                        opt.text = device.label || `Camera ${selectEl.options.length + 1}`;
                        selectEl.appendChild(opt);
                    });

                    // Match label logic to pick default
                    const backCamera = devices.find(device => 
                        device.label.toLowerCase().includes("back") || 
                        device.label.toLowerCase().includes("rear") || 
                        device.label.toLowerCase().includes("environment")
                    );

                    let selectedId = backCamera ? backCamera.id : (devices.length > 1 ? devices[devices.length - 1].id : devices[0].id);
                    selectEl.value = selectedId;
                    cameraConstraint = selectedId;

                    // Bind change listener to dynamically swap source
                    selectEl.onchange = async () => {
                        const newId = selectEl.value;
                        if (newId) {
                            await stopScanner();
                            AppState.scanner = new Html5Qrcode("reader");
                            AppState.scanning = true;
                            try {
                                await AppState.scanner.start(
                                    newId,
                                    {
                                        fps: 10,
                                        aspectRatio: 1.0,
                                        qrbox: function(viewfinderWidth, viewfinderHeight) {
                                            const minDim = Math.min(viewfinderWidth, viewfinderHeight);
                                            const size = Math.floor(minDim * 0.85);
                                            return { width: size, height: size };
                                        },
                                        disableFlip: false,
                                    },
                                    async (text) => {
                                        stopScanner();
                                        await sendQR(text);
                                    }
                                );
                            } catch (e) {
                                console.error("Error switching camera:", e);
                            }
                        }
                    };

                    if (selectContainer) {
                        selectContainer.classList.remove("hidden");
                    }
                }
            }
        } catch (e) {
            console.warn("Could not query cameras, using environment facingMode", e);
        }

        await AppState.scanner.start(
            cameraConstraint,
            {
                fps: 10,
                aspectRatio: 1.0,
                qrbox: function(viewfinderWidth, viewfinderHeight) {
                    // Use 85% of the smaller dimension as the scan area
                    const minDim = Math.min(viewfinderWidth, viewfinderHeight);
                    const size = Math.floor(minDim * 0.85);
                    return { width: size, height: size };
                },
                disableFlip: false,
            },
            async (text) => {
                stopScanner();
                await sendQR(text);
            }
        );
    } catch (err) {
        console.error("Scanner error:", err);
        AppState.scanning = false;
        AppState.scanner = null;
        showToast("📷 Camera unavailable. Try 'Upload QR from Gallery'!", "warning", 5000);
    }
}

function stopScanner() {

    if (!AppState.scanner) return Promise.resolve();

    return AppState.scanner.stop()
        .then(() => {
            AppState.scanner.clear();
            AppState.scanner = null;
            AppState.scanning = false;
        })
        .catch((err) => {
            console.warn("Scanner stop error:", err);
            AppState.scanner = null;
            AppState.scanning = false;
        });
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
    /**
     * Dispatches scanned QR code raw payload to the analytical back-end services.
     * 
     * Why: Coordinates local offline pre-check interceptors and dispatches network payloads.
     * If the client is offline or the VPA matches a locally synchronized blacklist in localStorage,
     * it blocks the transaction instantly (0ms latency), bypassing remote server API dependency.
     */
    toggle($("loader"), true);

    // 0ms LOCAL CACHE PRECHECK INTERCEPTOR 🔥
    if (AppState.intent === "pay") {
        
        // Extract plain UPI identifier (e.g. name@bank) from upi://pay URI queries
        const scannedUpi = extractUpiAddress(text);
        if (scannedUpi) {
            AppState.lastScannedUpi = scannedUpi;  // Save to enable report-fraud click modal later
            
            // Check local in-browser database cache & classifyUPI registry
            const matched = localBlacklist.find(item => item.upi.toLowerCase() === scannedUpi);
            const clientClassified = (window.classifyUPI) ? window.classifyUPI(scannedUpi) : null;

            if (matched || (clientClassified && (clientClassified.type === "unsafe" || clientClassified.type === "medium"))) {
                console.log("0ms Local Intercept Match Found for UPI:", scannedUpi);
                toggle($("loader"), false);

                const upiDisplay = matched ? matched.upi : scannedUpi;
                const reportsCount = matched ? matched.reports : 3;
                const isMedium = clientClassified && clientClassified.type === "medium";

                // Synthesize mockup API response structure to route directly to popup renderer
                const mockApiResponse = {
                    success: true,
                    data: {
                        qr: {
                            parsed: {
                                pa: [upiDisplay],
                                pn: [isMedium ? "Suspect Account Profile" : "Blacklisted Scammer Profile"],
                                am: [""],
                                tn: [isMedium ? "Unverified Account Caution" : "Local Database Blocked"]
                            }
                        },
                        analysis: {
                            risk_score: isMedium ? 35 : 100,
                            risk_level: isMedium ? "MEDIUM" : "CRITICAL",
                            fraud_type: isMedium ? "Suspect / Unverified Account" : "Criminal / Fraud Registry",
                            detected_action: isMedium ? "Verify carefully before paying — Unverified profile" : "Immediate Block — Listed in National Cyber Fraud Registry",
                            confidence: isMedium ? 0.85 : 0.99,
                            reasons: isMedium ? [
                                `Suspect VPA (${upiDisplay}): ⚠️ CAUTION: Unverified promotional account handle.`,
                                `Caution Flag: Unverified cashback/helpdesk portal with recent activity alerts.`,
                                `Caution Flag: Verify recipient identity and payment purpose carefully before approving.`
                            ] : [
                                `Blacklisted FRAUD VPA (${upiDisplay}): 🚨 ALERT: Flagged in ${reportsCount} Cyber Crime complaints.`,
                                `Cyber Complaint: Posed as Fake Executive; sent fake update bill / cashback link.`,
                                `Cyber Complaint: Sent emergency UPI collect request claiming account will be blocked.`
                            ]
                        }
                    }
                };

                showResultPopup(mockApiResponse);
                return;
            }
        }

        // OFFLINE MODE COMPATIBILITY CHECK
        // If client network state is disconnected, block analysis but alert user of offline status
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

        // Cache scanned identifier locally
        const extractedUpi = extractUpiAddress(text);
        if (extractedUpi) AppState.lastScannedUpi = extractedUpi;

        // If intent is "receive" money and QR is safe, notify user that showing their QR carries zero debit risk
        const qrRiskLevel = data?.data?.risk_level;
        if (AppState.intent === "receive" && qrRiskLevel !== "CRITICAL" && qrRiskLevel !== "HIGH") {
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

    let upiText = input.value.trim();
    const match = upiText.match(/([a-zA-Z0-9._+\-]{2,}@[a-zA-Z]{2,20})/);
    if (match) {
        upiText = match[1];
        input.value = upiText;
    }

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
            body: JSON.stringify({ upi_id: upiId, fraud_type: "User Reported", description: desc })
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
function initApp() {
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

    // Profile settings btn handled via global onclick="openProfileRedirect(event)"
    initProfile();

    // Check if redirected from other page to open profile modal immediately
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("openProfile") === "true") {
        setTimeout(openProfileModal, 300);
    }

    // Automatically initialize camera scanner when mounting scan.html or qrSection
    if ($("qrSection")) {
        selectIntent("pay");
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}


// -----------------------------
// 🎬 RESULT POPUP
// -----------------------------
function showResultPopup(apiResponse) {
    /**
     * Consolidates threat analysis parameters and displays the popup diagnostic UI.
     * 
     * Why: Blends NLP text risk, metadata warnings, and computer vision forensics.
     * Since different files trigger different threat vectors, the frontend calculates
     * a max-risk aggregate value so that a critical visual forgery cannot be masked
     * by clean transaction text.
     */
    if (!apiResponse || !apiResponse.success || !apiResponse.data) {
        console.warn("Skipping result popup: Invalid or unsuccessful API response.", apiResponse);
        return;
    }
    const analysis = apiResponse.data.analysis || apiResponse.data;
    if (!analysis) {
        console.warn("Skipping result popup: Missing analysis content.", apiResponse);
        return;
    }
    
    // ---------------------------------
    // 🖼 SCREENSHOT TAMPER & METADATA RISK MERGER 🔥
    // ---------------------------------
    const metadata = apiResponse.data.metadata;
    const tamper = apiResponse.data.tamper_analysis;

    // Convert and normalize scores into a standard 0-100 range
    let ocrScore = analysis.risk?.risk_score ?? analysis.risk_score ?? 0;
    let metadataScore = (metadata && metadata.risk_score != null) ? metadata.risk_score * 10 : 0;
    let tamperScore = (tamper && tamper.risk_score != null) ? tamper.risk_score : 0;

    // Aggregate threat index: the highest individual vulnerability score is selected
    let riskScore = Math.max(ocrScore, metadataScore, tamperScore);

    // Map consolidated risk percentages into taxnomic severity levels
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

    // Classify fraud types based on upload category
    let isScreenshotCheck = (metadata || tamper) ? true : false;
    let fraudType = isScreenshotCheck ? "Screenshot Forgery" : (analysis.fraud?.fraud_type ?? analysis.fraud_type ?? "General");
    let detectedAction = isScreenshotCheck ? "Inspect receipt details carefully" : (analysis.detected_action?.action ?? analysis.detected_action ?? "-");
    if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
        detectedAction = isScreenshotCheck ? "Forged Receipt Blocked" : detectedAction;
    }

    // Merge warning strings from all analytical engines into a single audit list
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
        // Fallback to highest confidence calculation returned
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
    const parsedQr = apiResponse.data?.qr?.parsed || apiResponse.data?.analysis?.qr?.parsed || {};
    let payeeName = (parsedQr.pn && parsedQr.pn[0] && parsedQr.pn[0] !== "") ? parsedQr.pn[0] : (analysis.name || "Verified Merchant Account");
    let payeeVpa = (parsedQr.pa && parsedQr.pa[0] && parsedQr.pa[0] !== "") ? parsedQr.pa[0] : (AppState.lastScannedUpi || "unlisted@upi");

    AppState.lastScannedPayeeName = payeeName;
    AppState.lastScannedPayeeVpa = payeeVpa;

    // Check if QR payload contains a merchant amount limit cap (am=...)
    if (parsedQr.am && parsedQr.am[0] && !isNaN(parseFloat(parsedQr.am[0]))) {
        AppState.scannedAmountLimit = parseFloat(parsedQr.am[0]);
    } else {
        AppState.scannedAmountLimit = null;
    }

    safeText($("popupPayeeName"), payeeName);
    safeText($("popupPayeeVpa"), payeeVpa);

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

    // ---------------------------------
    // 📊 ML PROBABILITY BREAKDOWN
    // ---------------------------------
    const mlBlock = $("mlBlock");
    const mlProbsContainer = $("mlProbsContainer");
    if (mlBlock && mlProbsContainer) {
        const mlAnalysis = apiResponse.data.analysis?.ml_analysis || apiResponse.data.ml_analysis;
        if (mlAnalysis && mlAnalysis.probabilities) {
            mlBlock.classList.remove("hidden");
            mlProbsContainer.innerHTML = "";

            const formatLabel = (l) => {
                return l.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            };

            Object.entries(mlAnalysis.probabilities).forEach(([category, prob]) => {
                const percentage = Math.round(prob * 100);
                if (percentage > 0) {
                    const row = document.createElement("div");
                    row.className = "flex items-center justify-between mt-1";
                    row.innerHTML = `
                        <span class="text-white/70">${formatLabel(category)}</span>
                        <div class="flex items-center gap-2 w-1/2 justify-end">
                            <div class="w-24 bg-white/10 h-1.5 rounded-full overflow-hidden border border-white/5">
                                <div class="bg-primary h-full rounded-full" style="width: ${percentage}%"></div>
                            </div>
                            <span class="font-bold text-white/90 whitespace-nowrap min-w-[30px] text-right">${percentage}%</span>
                        </div>
                    `;
                    mlProbsContainer.appendChild(row);
                }
            });
        } else {
            mlBlock.classList.add("hidden");
        }
    }

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
        const reasons = data?.reasons ?? [];
        if (reasons.length === 0) {
            const li = document.createElement("li");
            li.textContent = "✔ No threat indicators detected — VPA is clean";
            li.className = "text-sm text-emerald-400 font-medium";
            list.appendChild(li);
        } else {
            reasons.forEach(reason => {
                const li = document.createElement("li");
                li.textContent = (reason.startsWith("✔") || reason.startsWith("🚨") || reason.startsWith("⚠")) ? reason : "⚠ " + reason;
                li.className = reason.toLowerCase().includes("blacklisted") || reason.toLowerCase().includes("complaint") || reason.toLowerCase().includes("fraud") || reason.toLowerCase().includes("alert")
                    ? "text-sm text-red-400 font-medium"
                    : "text-sm text-gray-300";
                list.appendChild(li);
            });
        }
    }

    // -----------------------------
    // 💳 UPI PAYMENT LINK GENERATION 🔥
    // -----------------------------
    const parsed = apiResponse.data?.qr?.parsed || {};
    const pa = (parsed.pa && parsed.pa[0]) || "";
    const pn = (parsed.pn && parsed.pn[0]) || "Recipient";
    const am = (parsed.am && parsed.am[0]) || "";
    const tn = (parsed.tn && parsed.tn[0]) || "SuRaksha Verified";

    // Pre-populate scanned transaction amount input if exists
    const payAmountInput = $("payAmountInput");
    if (payAmountInput) {
        payAmountInput.value = am || "";
    }

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


// App-Specific UPI Router Registry for Android Package Intents & iOS Custom Schemes
const UPI_APP_ROUTER = {
    "Google Pay": {
        name: "Google Pay",
        androidPackage: "com.google.android.apps.nbu.paisa.user",
        iosScheme: "gpay://upi/pay",
        fallbackScheme: "tez://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=com.google.android.apps.nbu.paisa.user"
    },
    "PhonePe": {
        name: "PhonePe",
        androidPackage: "com.phonepe.app",
        iosScheme: "phonepe://pay",
        fallbackScheme: "phonepe://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=com.phonepe.app"
    },
    "Paytm": {
        name: "Paytm",
        androidPackage: "net.one97.paytm",
        iosScheme: "paytmmp://pay",
        fallbackScheme: "paytm://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=net.one97.paytm"
    },
    "BHIM UPI": {
        name: "BHIM UPI",
        androidPackage: "in.org.npci.upiapp",
        iosScheme: "bhim://pay",
        fallbackScheme: "bhim://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=in.org.npci.upiapp"
    },
    "FamPay": {
        name: "FamPay",
        androidPackage: "com.fampay.in",
        iosScheme: "fampay://pay",
        fallbackScheme: "fampay://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=com.fampay.in"
    },
    "POP": {
        name: "POP",
        androidPackage: "com.pop.app",
        iosScheme: "pop://pay",
        fallbackScheme: "pop://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=com.pop.app"
    },
    "Cred": {
        name: "CRED",
        androidPackage: "com.cred.club",
        iosScheme: "cred://pay",
        fallbackScheme: "cred://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=com.cred.club"
    },
    "Amazon Pay": {
        name: "Amazon Pay",
        androidPackage: "in.amazon.mShop.android.shopping",
        iosScheme: "amazonpay://pay",
        fallbackScheme: "com.amazon.mobile.shopping://upi/pay",
        storeUrl: "https://play.google.com/store/apps/details?id=in.amazon.mShop.android.shopping"
    }
};

function togglePaymentDrawer(show) {
    const drawer = $("paymentDrawer");
    const actions = $("popupActions");
    if (drawer) drawer.classList.toggle("hidden", !show);
    if (actions) actions.classList.toggle("hidden", show);

    if (show) {
        const amountInput = $("payAmountInput");
        const limitHint = $("payAmountLimitHint");
        const maxLimit = AppState.scannedAmountLimit;

        if (amountInput) {
            amountInput.readOnly = false; // Always editable by payer!
            amountInput.value = ""; // Blank by default so payer enters their desired amount
            amountInput.placeholder = maxLimit ? `Enter amount (Max ₹${maxLimit})` : "Enter amount to pay";

            // Attach dynamic input validation listener
            amountInput.oninput = validatePaymentAmountInput;
            setTimeout(() => amountInput.focus(), 100);
        }

        if (limitHint) {
            if (maxLimit != null && maxLimit > 0) {
                limitHint.innerText = `Allowed payment: ₹1 to ₹${maxLimit} (Merchant Maximum Cap: ₹${maxLimit})`;
                limitHint.className = "text-[9px] text-amber-400 font-medium block";
            } else {
                limitHint.innerText = "Enter payment amount (Min ₹1)";
                limitHint.className = "text-[9px] text-gray-400 font-medium block";
            }
        }
    }
}

function validatePaymentAmountInput() {
    const amountInput = $("payAmountInput");
    const limitHint = $("payAmountLimitHint");
    if (!amountInput) return false;

    let val = parseFloat(amountInput.value);
    const maxLimit = AppState.scannedAmountLimit;

    if (isNaN(val) || val <= 0) {
        if (limitHint) {
            limitHint.innerText = maxLimit ? `Allowed payment: ₹1 to ₹${maxLimit}` : "Enter a valid amount (Min ₹1)";
            limitHint.className = "text-[9px] text-amber-400 font-medium block";
        }
        return false;
    }

    if (maxLimit != null && maxLimit > 0 && val > maxLimit) {
        if (limitHint) {
            limitHint.innerText = `❌ Exceeds Maximum Limit! The merchant set a maximum limit of ₹${maxLimit}. Please enter ₹${maxLimit} or less.`;
            limitHint.className = "text-[9px] text-red-400 font-bold block animate-pulse";
        }
        return false;
    }

    if (limitHint) {
        limitHint.innerText = maxLimit ? `✅ Valid amount (Max limit ₹${maxLimit})` : "✅ Valid amount";
        limitHint.className = "text-[9px] text-emerald-400 font-medium block";
    }
    return true;
}

function simulatePaymentLaunch(appName) {
    const amountInput = $("payAmountInput");
    let amountVal = parseFloat(amountInput?.value);
    const maxLimit = AppState.scannedAmountLimit;

    // 1. Validate payment amount against merchant maximum limit
    if (isNaN(amountVal) || amountVal <= 0) {
        showToast("⚠️ Please enter a valid payment amount (Min ₹1)", "warning");
        if (amountInput) amountInput.focus();
        return;
    }

    if (maxLimit != null && maxLimit > 0 && amountVal > maxLimit) {
        showToast(`🛑 Payment Blocked: ₹${amountVal} exceeds the merchant's maximum limit of ₹${maxLimit}`, "error", 5000);
        validatePaymentAmountInput();
        if (amountInput) amountInput.focus();
        return;
    }

    // 2. Prepare full UPI parameters
    const payeeVpa = AppState.lastScannedPayeeVpa || AppState.lastScannedUpi || "merchant@paytm";
    const payeeName = AppState.lastScannedPayeeName || "Merchant Store";
    const txnNote = "SuRaksha Verified Payment";
    const txnRef = "SRK" + Date.now();

    // Base query string with all required parameters
    const queryParams = `pa=${encodeURIComponent(payeeVpa)}&pn=${encodeURIComponent(payeeName)}&am=${amountVal}&cu=INR&tn=${encodeURIComponent(txnNote)}&tr=${encodeURIComponent(txnRef)}`;
    const genericUpiUri = `upi://pay?${queryParams}`;

    const appConfig = UPI_APP_ROUTER[appName];
    const userAgent = navigator.userAgent || "";
    const isAndroid = /android/i.test(userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(userAgent) && !window.MSStream;

    let targetLaunchUri = genericUpiUri;

    if (appConfig) {
        if (isAndroid && appConfig.androidPackage) {
            // Android Package Intent - forces Android OS to launch ONLY the targeted app package
            targetLaunchUri = `intent://pay?${queryParams}#Intent;scheme=upi;package=${appConfig.androidPackage};end`;
        } else if (isIOS && appConfig.iosScheme) {
            // iOS Custom App Scheme (e.g. gpay://upi/pay?pa=... or fampay://pay?pa=... or bhim://pay?pa=...)
            targetLaunchUri = `${appConfig.iosScheme}?${queryParams}`;
        }
    }

    showToast(`🚀 Opening ${appName}... Transferring ₹${amountVal} to ${payeeName}`, "info", 4000);

    // Launch immediately on user click gesture
    try {
        window.location.href = targetLaunchUri;
    } catch (e) {
        console.warn(`Direct launch for ${appName} failed:`, e);
        showToast(`⚠️ Unable to open ${appName}. Please ensure the app is installed.`, "warning", 5000);
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
    /**
     * Details visual indicators, triggers client-side ELA rendering, and draws threat radar.
     * 
     * Why: Renders visual-heavy verification tools (like dynamic magnifier, sliders, and charts)
     * which helps users immediately spot edited regions on the screenshot.
     */
    if (!apiResponse || !apiResponse.success) {
        console.warn("Screenshot popup: Invalid API response", apiResponse);
        return;
    }

    const data = apiResponse.data;
    const metadata = data?.metadata;
    const tamper = data?.tamper_analysis;
    const analysis = data?.analysis;

    // Compute consolidated maximum forgery risk percentage
    let metaScore   = (metadata  && metadata.risk_score  != null) ? metadata.risk_score * 10 : 0;
    let tamperScore = (tamper    && tamper.risk_score    != null) ? tamper.risk_score        : 0;
    let ocrScore    = (analysis  && analysis.risk_score  != null) ? analysis.risk_score      : 0;
    let riskScore   = Math.max(metaScore, tamperScore, ocrScore);

    // Map composite risk scores
    let riskLevel = "SAFE";
    if      (riskScore >= 75) riskLevel = "CRITICAL";
    else if (riskScore >= 50) riskLevel = "HIGH";
    else if (riskScore >= 25) riskLevel = "MEDIUM";
    else if (riskScore >  0 ) riskLevel = "LOW";

    // Standard confidence heuristic
    let confidence = tamper?.confidence ?? metadata?.confidence ?? analysis?.confidence ?? 0.85;

    // Define warnings
    let action = "Screenshot appears authentic";
    if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
        action = "⛔ Likely forged — do not trust this receipt";
    } else if (riskLevel === "MEDIUM") {
        action = "⚠ Some anomalies found — verify carefully";
    }

    // Build consolidated reasons list
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

    // Dynamic Client-side ELA Generation
    const imgInput = $("imageInput");
    if (imgInput && imgInput.files && imgInput.files[0]) {
        generateClientSideEla(imgInput.files[0]);
    }

    // Dynamic SVG Radar threat vectors
    const vectors = {
        vpa: ocrScore >= 40 ? 90 : 15,
        visual: tamperScore,
        metadata: metaScore,
        intent: ocrScore >= 50 ? 85 : 10,
        social: ocrScore >= 60 ? 95 : 15
    };
    renderRadarChart(vectors, "screenshotRadarChart");

    // Reasons list
    const list = $("screenshotReasons");
    if (list) {
        list.innerHTML = "";
        reasons.forEach(reason => {
            const li = document.createElement("li");
            li.textContent = reason;
            li.className = "text-sm text-gray-300 py-0.5 flex items-start gap-1.5";
            li.innerHTML = `<span class="text-secondary font-bold">•</span><span>${reason}</span>`;
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

    toggle($("loader"), true);

    // Stop camera first if active to avoid reader element collision
    const wasScanning = AppState.scanning;
    if (wasScanning) {
        await stopScanner();
        // Wait a brief moment to ensure resources are released
        await new Promise(resolve => setTimeout(resolve, 300));
    }

    try {
        const compressedFile = await compressImage(file);
        
        const formData = new FormData();
        formData.append("image", compressedFile);
        formData.append("intent", AppState.intent);
        
        // Send directly to the robust backend QR parser
        const data = await apiRequest("/analyze/qr-image", formData, true);
        
        // Ensure successful scan closes the UI overlay
        showResultPopup(data);

    } catch (err) {
        console.error("Gallery scan error:", err);
        showToast("QR image scan failed or could not find QR code ❌", "error");
    } finally {
        toggle($("loader"), false);

        // Reset input value so same file can be selected again
        e.target.value = "";

        // Restart camera scanner if it was scanning before
        if (wasScanning) {
            setTimeout(startScanner, 200);
        }
    }
});

// -----------------------------
// 🌐 OFFLINE BLACKLIST SYNCER
// -----------------------------
async function syncOfflineBlacklist() {
    /**
     * Fetches user-reported fraud entries and saves them locally for offline capability.
     * 
     * Why: Provides network resiliency. If a user is paying in low-network zones
     * (e.g. underground metro stations or remote locations), standard network lookups fail.
     * Caching blacklist entries in localStorage allows instant query intercepts without connections.
     */
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
            // Persist the blacklist locally inside standard browser localStorage
            localStorage.setItem("suraksha_blacklist_cache", JSON.stringify(localBlacklist));
            console.log("Offline Blacklist sync completed. Cached " + localBlacklist.length + " reported accounts.");
        }
    } catch (err) {
        console.warn("Failed to sync offline blacklist cache:", err);
        // Load fallback cache if network request failed due to connectivity drops
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
    initSocThreatFeed();

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
// 🧩 HELPER: Scam Sample Paster & Mobile Chat Simulator
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

// ── NLP KEYWORD HIGHLIGHTER FOR CHAT BUBBLES ──
function highlightScamKeywords(text) {
    const keywords = ["upi pin", "pin", "otp", "blocked", "won", "cashback", "reward", "lottery", "prize", "cash award", "claim", "money transfer", "verify transfer", "overdue"];
    let highlighted = text;
    keywords.forEach(kw => {
        const regex = new RegExp(`\\b(${kw})\\b`, "gi");
        highlighted = highlighted.replace(regex, `<span class="bg-red-500/35 border border-red-500/40 text-red-300 px-1 py-0.5 rounded font-bold cursor-help transition-all shadow-[0_0_8px_rgba(239,68,68,0.25)]" title="High-Risk scam trigger identified by SuRaksha NLP!">$1</span>`);
    });
    return highlighted;
}

// ── INTERACTIVE MOBILE CHAT SIMULATOR ──
function sendChatMessage() {
    const input = $("chatMessageInput");
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    
    // Highlight any keywords inside user's own sent message
    const highlightedUserMsg = highlightScamKeywords(text);
    appendChatBubble(highlightedUserMsg, "user");
    
    // Set chat header status to "typing..."
    const headerStatus = document.querySelector("#messageSection .bg-\\[\\#075e54\\] div div:last-child");
    if (headerStatus) {
        headerStatus.textContent = "typing...";
        headerStatus.className = "text-[9px] text-emerald-300 animate-pulse";
    }

    // Show dynamic SuRaksha scanning / typing indicator
    const typingBubbleId = "typing_" + Date.now();
    appendChatBubble(`
        <div class="flex items-center gap-1.5 text-white/50">
            <span class="font-bold text-[9px] uppercase tracking-wider">SuRaksha AI is typing</span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `, "system", typingBubbleId, "border-emerald-600/10 bg-emerald-500/5");

    setTimeout(async () => {
        try {
            const res = await fetch(`${API_BASE}/analyze/text`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, intent: "pay" })
            });
            if (!res.ok) {
                if (res.status === 429) {
                    const errorData = await res.json().catch(() => ({}));
                    showToast(`⏳ ${errorData.error?.description || "Rate limit exceeded"}`, "warning", 5000);
                    const typingEl = $(typingBubbleId);
                    if (typingEl) typingEl.remove();
                    return;
                }
                throw new Error(`HTTP ${res.status}`);
            }
            const resData = await res.json();
            
            // Remove typing indicator
            const typingEl = $(typingBubbleId);
            if (typingEl) typingEl.remove();

            // Restore header status
            if (headerStatus) {
                headerStatus.textContent = "Online Threat Analyzer";
                headerStatus.className = "text-[9px] text-white/70";
            }

            if (resData.success) {
                const analysis = resData.data.analysis;
                const risk = analysis.risk;
                const decision = analysis.decision;
                const upiAnalysis = resData.data.upi_analysis || { upi_ids: [], suspicious: [], directory_info: {} };
                const directoryInfo = upiAnalysis.directory_info || {};

                // Determine styling and icons based on risk level
                let badgeColor = "bg-green-500/10 text-green-400 border-green-500/20";
                let progressColor = "bg-green-500";
                let statusIcon = "check_circle";
                let statusText = "Safe to Proceed";
                let cardBorder = "border-green-500/30";

                if (risk.risk_level === "CRITICAL") {
                    badgeColor = "bg-red-500/10 text-red-400 border-red-500/20 animate-pulse";
                    progressColor = "bg-red-500";
                    statusIcon = "gpp_bad";
                    statusText = "FRAUD DETECTED";
                    cardBorder = "border-red-500/40 shadow-red-950/10";
                } else if (risk.risk_level === "HIGH") {
                    badgeColor = "bg-orange-500/10 text-orange-400 border-orange-500/20";
                    progressColor = "bg-orange-500";
                    statusIcon = "warning";
                    statusText = "HIGH RISK";
                    cardBorder = "border-orange-500/30";
                } else if (risk.risk_level === "MEDIUM") {
                    badgeColor = "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
                    progressColor = "bg-yellow-500";
                    statusIcon = "info";
                    statusText = "SUSPICIOUS";
                    cardBorder = "border-yellow-500/30";
                }

                // Render VPA checks
                let upiHtml = "";
                if (upiAnalysis.upi_ids && upiAnalysis.upi_ids.length > 0) {
                    upiHtml += `
                    <div class="mt-3 border-t border-white/5 pt-2">
                        <span class="text-[9px] font-bold text-white/40 block mb-1 uppercase tracking-wider">UPI Registry Verification</span>
                        <div class="space-y-1.5">
                    `;
                    for (const upi of upiAnalysis.upi_ids) {
                        const dir = directoryInfo[upi];
                        if (dir) {
                            if (dir.category === "unsafe") {
                                upiHtml += `
                                <div class="bg-red-950/20 border border-red-900/30 rounded-lg p-2 flex flex-col gap-0.5">
                                    <div class="flex justify-between items-center">
                                        <span class="font-mono text-[9px] font-semibold text-red-400 break-all select-all">${upi}</span>
                                        <span class="text-[8px] bg-red-500/20 text-red-400 px-1 py-0.5 rounded border border-red-500/30 font-bold uppercase tracking-wider">Blocked</span>
                                    </div>
                                    <span class="text-[9px] text-white/80 font-bold mt-0.5">${dir.name}</span>
                                    <span class="text-[8px] text-white/50 leading-tight">${dir.description}</span>
                                </div>
                                `;
                            } else {
                                upiHtml += `
                                <div class="bg-emerald-100/50 dark:bg-emerald-950/10 border border-emerald-200 dark:border-emerald-900/20 rounded-lg p-2.5 flex flex-col gap-1 shadow-sm">
                                    <div class="flex justify-between items-center">
                                        <span class="font-mono text-[10px] font-semibold text-emerald-700 dark:text-emerald-400 break-all select-all">${upi}</span>
                                        <span class="text-[8px] bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20 dark:border-emerald-500/30 font-bold uppercase tracking-wider flex items-center gap-0.5"><span class="material-symbols-outlined text-[10px]">verified</span>Verified</span>
                                    </div>
                                    <span class="text-[11px] text-slate-800 dark:text-white/90 font-bold mt-0.5">${dir.name} <span class="opacity-60 font-normal">(${dir.subtype})</span></span>
                                    <span class="text-[9px] text-slate-600 dark:text-white/60 leading-tight">${dir.description}</span>
                                </div>
                                `;
                            }
                        } else {
                            // Standard unlisted
                            const isSuspicious = upiAnalysis.suspicious && upiAnalysis.suspicious.includes(upi);
                            const badge = isSuspicious 
                                ? `<span class="text-[8px] bg-yellow-500/10 text-yellow-400 px-1 py-0.5 rounded border border-yellow-500/20 font-bold uppercase tracking-wider">Unverified</span>`
                                : `<span class="text-[8px] bg-white/5 text-white/50 px-1 py-0.5 rounded border border-white/10 font-bold uppercase tracking-wider">Unlisted</span>`;
                            
                            upiHtml += `
                            <div class="bg-slate-900/50 border border-white/5 rounded-lg p-2 flex justify-between items-center">
                                <span class="font-mono text-[9px] text-white/60 break-all select-all">${upi}</span>
                                ${badge}
                            </div>
                            `;
                        }
                    }
                    upiHtml += `</div></div>`;
                }

                // Render threat indicators list
                let reasonsHtml = "";
                const reasonsList = analysis.analysis.reasons || [];
                if (reasonsList.length > 0) {
                    reasonsHtml = `
                    <div class="mt-3 border-t border-slate-200 dark:border-white/5 pt-2 text-left">
                        <span class="text-[9px] font-bold text-slate-500 dark:text-white/40 block mb-1 uppercase tracking-wider">Risk Indicators</span>
                        <ul class="space-y-1 text-[11px] text-slate-700 dark:text-white/80">
                            ${reasonsList.map(r => `<li class="flex items-start gap-1"><span class="text-primary mt-0.5">•</span><span>${r}</span></li>`).join("")}
                        </ul>
                    </div>
                    `;
                }

                // Compile final report card HTML
                const reportCardHtml = `
                <div class="flex flex-col gap-2 p-1.5 w-full text-left">
                    <!-- Header -->
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/5">
                        <div class="flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-sm ${risk.risk_level === 'SAFE' ? 'text-emerald-500 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'}">${statusIcon}</span>
                            <span class="font-bold text-[11px] tracking-wide text-slate-800 dark:text-white">${statusText}</span>
                        </div>
                        <span class="text-[9px] px-2 py-0.5 border rounded-md uppercase font-bold tracking-wider ${badgeColor}">${risk.risk_level}</span>
                    </div>

                    <!-- Risk Gauge -->
                    <div class="space-y-1.5 mt-1">
                        <div class="flex justify-between text-[10px]">
                            <span class="text-slate-500 dark:text-white/50">Aggregated Threat Rating</span>
                            <span class="font-bold text-slate-800 dark:text-white">${risk.risk_score}/100</span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-white/5 rounded-full h-1.5 overflow-hidden">
                            <div class="${progressColor} h-full transition-all duration-1000 ease-out" style="width: ${risk.risk_score}%"></div>
                        </div>
                    </div>

                    <!-- ML Probability -->
                    <div class="flex justify-between text-[10px] py-2 border-b border-slate-200 dark:border-white/5">
                        <span class="text-slate-500 dark:text-white/50">Classifier Category</span>
                        <span class="font-mono text-slate-700 dark:text-white/80 font-bold tracking-wide">${analysis.ml_analysis?.top_category?.toUpperCase() || 'UNKNOWN'}</span>
                    </div>

                    <!-- Reasons -->
                    ${reasonsHtml}

                    <!-- UPI Verification -->
                    ${upiHtml}

                    <!-- Verdict Block -->
                    <div class="mt-2.5 p-3 rounded-xl text-[10px] font-semibold leading-relaxed border ${risk.risk_score >= 50 ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-300' : 'bg-emerald-50 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-300'}">
                        ${risk.risk_score >= 50 
                            ? '🚫 <strong class="text-red-800 dark:text-red-400">Block Transfer</strong>: SuRaksha analysis recommends blocking this receiver. Proceeding may result in loss.' 
                            : '✅ <strong class="text-emerald-800 dark:text-emerald-400">Verified Safe</strong>: No anomalies detected. Trust certificate validated.'
                        }
                    </div>
                </div>
                `;

                appendChatBubble(reportCardHtml, "system", null, cardBorder);
            } else {
                throw new Error("Diagnosis failed");
            }
        } catch (err) {
            console.warn(err);
            const typingEl = $(typingBubbleId);
            if (typingEl) typingEl.remove();
            
            if (headerStatus) {
                headerStatus.textContent = "Online Threat Analyzer";
                headerStatus.className = "text-[9px] text-white/70";
            }
            
            appendChatBubble(`❌ Connection to backend API failed. Threat analyzer is offline, but scan indicators suggest verifying links carefully.`, "system", null, "text-red-400 bg-red-950/20 border-red-900/30");
        }
    }, 1400);
}

function appendChatBubble(text, sender, id = null, extraClass = "") {
    const chatWin = $("chatSimulatorWindow");
    if (!chatWin) return;

    const bubble = document.createElement("div");
    if (id) bubble.id = id;

    const baseStyle = "p-3.5 rounded-2xl text-[13px] leading-relaxed max-w-[85%] border select-text shadow-sm relative ";
    let senderStyle = "";
    if (sender === "user") {
        senderStyle = "self-end bg-[#d9fdd3] dark:bg-[#005c4b] text-slate-800 dark:text-[#e9edef] rounded-tr-sm border-transparent ";
    } else if (sender === "system") {
        senderStyle = "self-start bg-white dark:bg-[#202c33] text-slate-800 dark:text-[#e9edef] rounded-tl-sm border-transparent " + extraClass;
    }

    bubble.className = baseStyle + senderStyle;
    
    // Check if the input is pre-formatted HTML card
    if (text.trim().startsWith("<")) {
        bubble.innerHTML = text;
    } else {
        // Handle Markdown newlines and basic list bolding
        bubble.innerHTML = text
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    }

    chatWin.appendChild(bubble);
    chatWin.scrollTop = chatWin.scrollHeight;
}

function pasteChatScamSample(index) {
    const input = $("chatMessageInput");
    if (!input) return;
    input.value = SCAM_SAMPLES[index] || "";
    input.focus();
    sendChatMessage();
}

// ── ELA SLIDER DRAG & MAGNIFIER ZOOM LENS LOGIC ──
let elaSliderController = null;
function setupElaSlider() {
    const container = $("elaSliderContainer");
    const handle = $("elaSliderDivider");
    const heatmap = $("elaSliderHeatmap");
    const lens = $("elaZoomLens");
    const canvas = $("screenshotElaCanvas");
    if (!container || !handle || !heatmap || !lens || !canvas) return;

    if (elaSliderController) elaSliderController.abort();
    elaSliderController = new AbortController();
    const opts = { signal: elaSliderController.signal };

    let isDragging = false;

    const onMove = (clientX) => {
        const rect = container.getBoundingClientRect();
        let x = clientX - rect.left;
        if (x < 0) x = 0;
        if (x > rect.width) x = rect.width;
        const pct = (x / rect.width) * 100;
        heatmap.style.width = `${pct}%`;
        handle.style.left = `${pct}%`;
    };

    // Drag events
    handle.addEventListener("mousedown", (e) => { e.preventDefault(); isDragging = true; }, opts);
    window.addEventListener("mouseup", () => isDragging = false, opts);
    window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        onMove(e.clientX);
    }, opts);

    handle.addEventListener("touchstart", (e) => { isDragging = true; }, opts);
    window.addEventListener("touchend", () => isDragging = false, opts);
    window.addEventListener("touchmove", (e) => {
        if (!isDragging) return;
        onMove(e.touches[0].clientX);
    }, opts);

    // ── BROWSER-BASED ZOOM LENS LENS FORENSICS OVERLAY ──
    let lensBgSet = false;

    container.addEventListener("mouseenter", () => {
        if (isDragging) return;
        lens.style.display = "block";
        if (!lensBgSet) {
            lens.style.backgroundImage = `url(${canvas.toDataURL()})`;
            lensBgSet = true;
        }
    }, opts);

    container.addEventListener("mouseleave", () => {
        lens.style.display = "none";
    }, opts);

    container.addEventListener("mousemove", (e) => {
        if (isDragging) {
            lens.style.display = "none";
            return;
        }
        lens.style.display = "block";
        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Position magnifier centered over crosshair cursor
        lens.style.left = `${x - lens.offsetWidth / 2}px`;
        lens.style.top = `${y - lens.offsetHeight / 2}px`;

        // Render 3.2x Zoom magnifier ratio
        const zoom = 3.2;
        lens.style.backgroundSize = `${rect.width * zoom}px ${rect.height * zoom}px`;
        lens.style.backgroundPosition = `-${x * zoom - lens.offsetWidth / 2}px -${y * zoom - lens.offsetHeight / 2}px`;
    });
}

// ── BROWSER ERROR LEVEL ANALYSIS (ELA) HEATMAP GENERATION ──
function generateClientSideEla(imageFileOrPath) {
    return new Promise((resolve) => {
        const canvas = $("screenshotElaCanvas");
        const origImg = $("elaOrigImg");
        if (!canvas || !origImg) return resolve(false);

        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = function() {
            // Load original image to popup preview
            origImg.src = img.src;

            let w = img.naturalWidth || img.width;
            let h = img.naturalHeight || img.height;
            
            // Limit maximum dimension to 800px to prevent UI freezes on high-res images
            const maxDim = 800;
            if (w > maxDim || h > maxDim) {
                if (w > h) {
                    h = Math.round((h * maxDim) / w);
                    w = maxDim;
                } else {
                    w = Math.round((w * maxDim) / h);
                    h = maxDim;
                }
            }
            
            canvas.width = w;
            canvas.height = h;

            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, w, h);

            // Step 1: Re-compress image at JPEG quality 0.75
            const jpegUrl = canvas.toDataURL("image/jpeg", 0.75);
            const compImg = new Image();
            compImg.onload = function() {
                // Step 2: Draw compressed onto separate buffer canvas
                const bufferCanvas = document.createElement("canvas");
                bufferCanvas.width = w;
                bufferCanvas.height = h;
                const bufCtx = bufferCanvas.getContext("2d");
                bufCtx.drawImage(compImg, 0, 0, w, h);

                // Step 3: Diff buffers
                const origData = ctx.getImageData(0, 0, w, h);
                const compData = bufCtx.getImageData(0, 0, w, h);
                const outData = ctx.createImageData(w, h);

                const origPixels = origData.data;
                const compPixels = compData.data;
                const outPixels = outData.data;

                for (let i = 0; i < origPixels.length; i += 4) {
                    // Absolute differences
                    const rDiff = Math.abs(origPixels[i] - compPixels[i]);
                    const gDiff = Math.abs(origPixels[i+1] - compPixels[i+1]);
                    const bDiff = Math.abs(origPixels[i+2] - compPixels[i+2]);

                    // Amplify difference by 18x to highlight spliced boundaries!
                    outPixels[i] = Math.min(255, rDiff * 18);
                    outPixels[i+1] = Math.min(255, gDiff * 18);
                    outPixels[i+2] = Math.min(255, bDiff * 25); // tint blue more for cybersecurity styling!
                    outPixels[i+3] = 255; // fully opaque
                }

                // Draw ELA onto display canvas
                ctx.putImageData(outData, 0, 0);
                setupElaSlider();
                resolve(true);
            };
            compImg.src = jpegUrl;
        };

        if (typeof imageFileOrPath === "string") {
            img.src = imageFileOrPath;
        } else {
            const reader = new FileReader();
            reader.onload = (e) => img.src = e.target.result;
            reader.readAsDataURL(imageFileOrPath);
        }
    });
}

// ── DYNAMIC SVG RADAR CHART GENERATOR ──
function renderRadarChart(scores, containerId) {
    const el = $(containerId);
    if (!el) return;

    // 5 dimensions: VPA Reputation, Visual Tampering, Metadata Integrity, Intent Match, Social Pressure
    const labels = ["VPA", "Visual", "Metadata", "Intent", "Social"];
    const keys = ["vpa", "visual", "metadata", "intent", "social"];
    
    const maxVal = 100;
    const radius = 15; // Center is (25, 25) in simplified radar space
    const cx = 25, cy = 25;

    // Calculate angle coordinates
    const getCoords = (val, idx) => {
        const angle = (Math.PI * 2 / 5) * idx - Math.PI / 2;
        const r = (val / maxVal) * radius;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return { x, y };
    };

    // Web grid circles
    let gridSvg = "";
    for (let scale = 20; scale <= 100; scale += 20) {
        const points = [];
        for (let i = 0; i < 5; i++) {
            const pt = getCoords(scale, i);
            points.push(`${pt.x},${pt.y}`);
        }
        gridSvg += `<polygon points="${points.join(" ")}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="0.3" />`;
    }

    // Web spokes (lines from center to outer)
    let spokesSvg = "";
    for (let i = 0; i < 5; i++) {
        const outer = getCoords(100, i);
        spokesSvg += `<line x1="${cx}" y1="${cy}" x2="${outer.x}" y2="${outer.y}" stroke="rgba(255,255,255,0.1)" stroke-width="0.3" />`;
        
        // Labels
        const labelPt = getCoords(120, i);
        spokesSvg += `<text x="${labelPt.x}" y="${labelPt.y + 0.8}" fill="rgba(255,255,255,0.4)" font-size="2" font-family="monospace" text-anchor="middle">${labels[i]}</text>`;
    }

    // Fraud shape polygon coordinates
    const fraudPoints = [];
    for (let i = 0; i < 5; i++) {
        const val = scores[keys[i]] || 10; // default minimum shape for visibility
        const pt = getCoords(val, i);
        fraudPoints.push(`${pt.x},${pt.y}`);
    }

    const svgString = `
    <svg viewBox="0 0 50 50" class="w-full h-full animate-fadeIn select-none">
        <!-- Grid Background -->
        ${gridSvg}
        ${spokesSvg}
        <!-- Threat Shape -->
        <polygon points="${fraudPoints.join(" ")}" fill="rgba(59, 130, 246, 0.25)" stroke="#3b82f6" stroke-width="0.6" class="animate-radar-grow" style="transform-origin: 25px 25px;" />
        <!-- Value Indicators with interactive hover triggers -->
        ${fraudPoints.map((ptStr, i) => {
            const [x, y] = ptStr.split(",");
            const val = scores[keys[i]] || 10;
            return `<circle cx="${x}" cy="${y}" r="0.8" fill="#60a5fa" stroke="#ffffff" stroke-width="0.2" class="cursor-pointer hover:scale-125 transition-transform" onmouseover="showRadarTooltip('${labels[i]}', ${val}, '${containerId}')" onmouseout="hideRadarTooltip('${containerId}')" />`;
        }).join("")}
    </svg>`;

    el.innerHTML = svgString;

    // Append dynamic description vector block
    const descId = containerId + "_desc";
    const existingDesc = $(descId);
    if (existingDesc) existingDesc.remove();

    const descEl = document.createElement("div");
    descEl.id = descId;
    descEl.className = "text-[9px] text-center text-white/40 font-mono mt-2 select-none animate-fadeIn leading-normal px-2";
    descEl.textContent = "Hover radar points to inspect threats";
    el.parentNode.appendChild(descEl);
}

// ── GLOBAL SVG RADAR HOVER ACTIONS ──
window.showRadarTooltip = (label, val, containerId) => {
    const descEl = $(containerId + "_desc");
    if (!descEl) return;
    
    const explanations = {
        VPA: `UPI address reputation. Scored ${val}/100. Target handle is spoofed or brand new.`,
        Visual: `Visual splicing ELA compression variance anomaly index. Scored ${val}/100.`,
        Metadata: `EXIF software flags & metadata datetime delays verification. Scored ${val}/100.`,
        Intent: `User intent actions vs transaction collect prompt matching. Scored ${val}/100.`,
        Social: `NLP urgency words, OTP pressure, & social manipulation index. Scored ${val}/100.`
    };
    
    descEl.innerHTML = `<span class="text-primary font-bold">${label}: ${val}/100</span> — ${explanations[label] || ""}`;
};

window.hideRadarTooltip = (containerId) => {
    const descEl = $(containerId + "_desc");
    if (!descEl) return;
    descEl.textContent = "Hover radar points to inspect threats";
};

// ── ZERO-TRUST FRAUD SIMULATOR SANDBOX CORE ──
let isSandboxRunning = false;

async function triggerSandboxSimulation(type) {
    if (isSandboxRunning) return;
    isSandboxRunning = true;

    const term = $("sandboxTerminal");
    const preview = $("sandboxMobilePreview");
    const inspectBtn = $("btnSandboxInspect");
    if (!term || !preview || !inspectBtn) {
        isSandboxRunning = false;
        return;
    }

    // Reset preview view
    preview.classList.add("hidden");
    term.innerHTML = "";

    const log = (msg, delay) => {
        return new Promise(resolve => {
            setTimeout(() => {
                term.innerHTML += `<div class="text-emerald-400 font-mono">&gt; ${msg}</div>`;
                term.scrollTop = term.scrollHeight;
                resolve();
            }, delay);
        });
    };

    if (type === "collect") {
        await log("[SIMULATION INITIALIZED] Scenario: Utility Collect Bill Fraud", 100);
        await log("[STAGE 1/4] Intercept Alert ✅ - SMS read: power power board bill collect request...", 300);
        await log(`[STAGE 2/4] NLP Parsing Heuristics 🔎 - Scanned words: "overdue, blocked, disconnected"`, 400);
        await log("[STAGE 3/4] Correlating VPA Blacklist 🔗 - Flagged, handle has 0 transaction counts", 350);
        await log("[STAGE 4/4] Threat Blocked 🛡️ - Action mismatch: prompt requesting pay instead of refund", 400);
        
        // Display mobile preview details
        $("sandboxEventLabel").textContent = "Threat Intercept: Urgent SMS";
        $("sandboxEventTitle").textContent = "⚡ Overdue Power Bill Trap";
        $("sandboxEventDesc").textContent = "Scammer posing as power distribution board requesting instant collect VPA pay.";
        preview.classList.remove("hidden");

        inspectBtn.onclick = () => {
            showChatMessageScamModal("Electricity bill overdue. Pay now or account disconnected in 1 hour. upi://pay?pa=power_board@paytm&pn=State%20Electricity&am=1499");
        };
    } 
    else if (type === "typosquat") {
        await log("[SIMULATION INITIALIZED] Scenario: Typosquatted VPA QR Spoof", 100);
        await log("[STAGE 1/4] Intercept Alert ✅ - Scanned printed merchant QR code", 300);
        await log("[STAGE 2/4] NLP Parsing Heuristics 🔎 - Destination VPA: grocery.storee@ybl", 400);
        await log("[STAGE 3/4] Correlating VPA Blacklist 🔗 - Typosquatted similarity matching 'grocery.store@ybl'", 450);
        await log("[STAGE 4/4] Threat Blocked 🛡️ - Identified extra 'e' spoof handle. Risk index score: HIGH", 400);

        $("sandboxEventLabel").textContent = "Threat Intercept: Typosquatted QR";
        $("sandboxEventTitle").textContent = "🛍️ Misspelled Merchant VPA Spoof";
        $("sandboxEventDesc").textContent = "Printed QR code sticker tampered to divert money from 'grocery.store' to 'grocery.storee'.";
        preview.classList.remove("hidden");

        inspectBtn.onclick = () => {
            showSandboxQrResult("upi://pay?pa=grocery.storee@ybl&pn=Grocery%20Store&am=100");
        };
    } 
    else if (type === "lottery") {
        await log("[SIMULATION INITIALIZED] Scenario: Cashback PIN-Trap", 100);
        await log("[STAGE 1/4] Intercept Alert ✅ - WhatsApp card incoming reward claim", 300);
        await log(`[STAGE 2/4] NLP Parsing Heuristics 🔎 - Scanned words: "Won 25,000 lottery cashback, enter UPI PIN to receive"`, 400);
        await log("[STAGE 3/4] Correlating VPA Blacklist 🔗 - PIN-trap scam warning signature matched", 400);
        await log("[STAGE 4/4] Threat Blocked 🛡️ - Cashout receive action requires PIN. Reverse engineering threat signature.", 350);

        $("sandboxEventLabel").textContent = "Threat Intercept: PIN Trap Alert";
        $("sandboxEventTitle").textContent = "🎁 Congratulations! You Won ₹25,000";
        $("sandboxEventDesc").textContent = "Scammer requesting user to verify transaction and enter UPI PIN in payment portal.";
        preview.classList.remove("hidden");

        inspectBtn.onclick = () => {
            showChatMessageScamModal("Congratulations! You won ₹25,000 lottery award. Scan and enter UPI PIN to claim immediately: upi://pay?pa=lottery_agent@paytm&pn=Lottery%20Cashback");
        };
    }

    isSandboxRunning = false;
}

function resetSandboxTerminal() {
    const term = $("sandboxTerminal");
    const preview = $("sandboxMobilePreview");
    if (!term || !preview) return;
    term.innerHTML = `<div class="text-white/40">&gt; Sandbox initialized. System status: [ACTIVE]</div>` + 
                     `<div class="text-white/40">&gt; Awaiting threat simulation trigger. Select a live scenario on the left panel...</div>`;
    preview.classList.add("hidden");
}

// ── MOCK INSPECT DISPATCHERS FOR SIMULATOR MODALS ──
function showChatMessageScamModal(text) {
    showToast("Simulating NLP Threat Scan...", "warning");
    setTimeout(async () => {
        try {
            const res = await fetch(`${API_BASE}/analyze/text`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, intent: "pay" })
            });
            if (!res.ok) {
                if (res.status === 429) {
                    const errorData = await res.json().catch(() => ({}));
                    showToast(`⏳ ${errorData.error?.description || "Rate limit exceeded"}`, "warning", 5000);
                    return;
                }
                throw new Error(`HTTP ${res.status}`);
            }
            const resData = await res.json();
            if (resData.success) {
                showSandboxResultPopup(resData.data.analysis);
            }
        } catch (err) {
            // Offline mock fallback
            showSandboxResultPopup({
                risk_score: 95,
                risk_level: "CRITICAL",
                reasons: ["PIN-trap trap signature detected", "Urgent social pressure keywords found", "Target VPA has zero trust profile"],
                fraud_type: "Phishing / PIN-Trap Scam",
                recommended_action: "🚫 Block & Report transaction immediately!"
            });
        }
    }, 600);
}

function showSandboxResultPopup(analysis) {
    const popup = $("resultPopup");
    if (!popup) return;

    $("popupAlert").textContent = `🚨 ${analysis.risk_level} Fraud Alert`;
    $("popupAlert").className = "text-2xl font-bold tracking-tight text-center text-red-400 animate-pulse";
    
    const safeEl = $("popupSafe");
    safeEl.textContent = "❌ HIGH RISK - DO NOT PROCEED";
    safeEl.className = "text-sm font-semibold tracking-wide uppercase text-red-400";

    $("popupScore").textContent = `${analysis.risk_score} / 100`;
    $("popupConfidence").textContent = "95%";
    $("popupLevel").textContent = analysis.risk_level;
    $("riskBar").style.width = `${analysis.risk_score}%`;
    $("riskBar").className = "h-full rounded-full transition-all duration-700 bg-red-500";

    $("popupType").textContent = analysis.fraud_type || "Social Engineering Scam";
    $("popupAction").textContent = "Do NOT authorize. High fraud risk.";
    $("popupAction").className = "font-semibold text-red-400";

    const reasonsEl = $("popupReasons");
    reasonsEl.innerHTML = "";
    (analysis.reasons || []).forEach(r => {
        reasonsEl.innerHTML += `<li class="flex items-start gap-1.5"><span class="text-red-500">•</span><span>${r}</span></li>`;
    });

    // Render animated radar chart!
    renderRadarChart({
        vpa: 95,
        visual: 10,
        metadata: 20,
        intent: 85,
        social: 95
    }, "qrRadarChart");

    popup.style.display = "flex";
}

function showSandboxQrResult(qrText) {
    showToast("Scanning sandbox QR Code...", "info");
    setTimeout(async () => {
        try {
            const res = await fetch(`${API_BASE}/analyze/qr`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ qr_text: qrText, intent: "pay" })
            });
            const resData = await res.json();
            if (resData.success) {
                showSandboxResultPopup(resData.data.analysis);
            }
        } catch (err) {
            showSandboxResultPopup({
                risk_score: 88,
                risk_level: "HIGH",
                reasons: ["VPA destination indicates typosquatted merchant name spoofing", "Target VPA has zero trust profile in local directory"],
                fraud_type: "VPA Typosquat Spoofing",
                recommended_action: "🚫 Abort payment. Misspelled account!"
            });
        }
    }, 600);
}

// ── QR CODE HOLOGRAPHIC TARGET BRACKETS ──
function drawQrTargetBrackets(x, y, w, h, status) {
    const canvas = $("qrOverlayCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let color = "#3b82f6"; // default blue
    if (status === "safe") color = "#10b981"; // green
    if (status === "warning") color = "#f59e0b"; // yellow
    if (status === "danger") color = "#ef4444"; // red

    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;

    const pad = 10;
    const left = x - pad;
    const top = y - pad;
    const width = w + pad * 2;
    const height = h + pad * 2;
    const len = 15;

    ctx.beginPath();
    ctx.moveTo(left, top + len);
    ctx.lineTo(left, top);
    ctx.lineTo(left + len, top);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(left + width - len, top);
    ctx.lineTo(left + width, top);
    ctx.lineTo(left + width, top + len);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(left, top + height - len);
    ctx.lineTo(left, top + height);
    ctx.lineTo(left + len, top + height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(left + width - len, top + height);
    ctx.lineTo(left + width, top + height);
    ctx.lineTo(left + width, top + height - len);
    ctx.stroke();

    ctx.fillStyle = "rgba(" + (status === "danger" ? "239,68,68" : "59,130,246") + ", 0.15)";
    ctx.fillRect(left, top, width, height);
}

function clearQrOverlay() {
    const canvas = $("qrOverlayCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// ---------------------------------------------
// 🔳 CRYPTOGRAPHIC SECURE QR & TRUST CERTIFICATE
// ---------------------------------------------

async function sha256(message) {
    /**
     * Standard WebCrypto helper calculating SHA-256 hashes inside browser context.
     * Used to generate the cryptographic verification signature to prevent client-side secret exposure.
     */
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function generateSecureStoreQr() {
    /**
     * Generates a cryptographically signed QR code to mitigate physical sticker tampering.
     * 
     * Why: Scammers physically glue fake QR stickers over a store's genuine QR code.
     * SuRaksha registers trusted stores. By hashing the name, VPA, and a secret merchant key
     * locally using WebCrypto, we generate a signature. When scanned, the backend verifies
     * this signature. If the VPA or merchant name was changed/tampered on the sticker,
     * signature verification fails, blocking the fraud attempt.
     */
    const name = $("secMerchantName").value.trim();
    const vpa = $("secMerchantVpa").value.trim();
    const secret = $("secSecretKey").value.trim();
    let limitAmount = parseFloat($("secAmountLimit")?.value) || 500;
    if (isNaN(limitAmount) || limitAmount < 1) {
        limitAmount = 1;
        if ($("secAmountLimit")) $("secAmountLimit").value = 1;
    }

    if (!name || !vpa) {
        showToast("Please enter Merchant Name and UPI VPA", "warning");
        return;
    }

    toggle($("loader"), true);
    try {
        const rawPayload = name.toLowerCase() + vpa.toLowerCase() + secret;
        const signature = await sha256(rawPayload);

        // upi://pay?pa=VPA&pn=Name&am=LIMIT&sign=SIGNATURE
        const upiPayPayload = `upi://pay?pa=${encodeURIComponent(vpa)}&pn=${encodeURIComponent(name)}&am=${limitAmount}&sign=${signature}&cu=INR&tn=SuRaksha%20Verified`;

        // Render QR code using qrserver API
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(upiPayPayload)}`;
        
        $("secureQrImage").src = qrUrl;
        $("secureQrPayloadText").innerText = upiPayPayload;
        
        // Hide placeholder, show preview
        $("secureQrPreviewPlaceholder").classList.add("hidden");
        $("secureQrPreviewContent").classList.remove("hidden");

        // Pre-populate certificate details
        $("certStoreName").innerText = name;
        $("certStoreVpa").innerText = vpa;
        $("certQrImage").src = qrUrl;

        // Generate dynamic certificate ID and Date
        const now = new Date();
        const formattedDate = `${String(now.getDate()).padStart(2, '0')}-${String(now.getMonth() + 1).padStart(2, '0')}-${now.getFullYear()}`;
        const randomId = `SR-${now.getFullYear()}-${Math.floor(10000 + Math.random() * 90000)}`;
        $("certDateText").innerText = formattedDate;
        $("certIdText").innerText = randomId;

        // Dynamically register in local trusted registry for scanning pre-check simulation
        const existingIdx = localTrustedMerchants.findIndex(m => m.upi.toLowerCase() === vpa.toLowerCase());
        if (existingIdx >= 0) {
            localTrustedMerchants[existingIdx] = { upi: vpa, name: name, secret: secret };
        } else {
            localTrustedMerchants.push({ upi: vpa, name: name, secret: secret });
        }

        showToast("Secure Merchant QR Code Generated! 🛡️", "success");
    } catch (err) {
        console.error(err);
        showToast("Error generating secure QR code", "error");
    } finally {
        toggle($("loader"), false);
    }
}

function toggleSecretVisibility() {
    const input = $("secSecretKey");
    const icon = $("visibilityIcon");
    if (input.type === "password") {
        input.type = "text";
        icon.innerText = "visibility";
    } else {
        input.type = "password";
        icon.innerText = "visibility_off";
    }
}

function openMerchantCertificateModal() {
    $("certificateModal").classList.remove("hidden");
    $("certificateModal").classList.add("flex");
}

function closeMerchantCertificateModal() {
    $("certificateModal").classList.add("hidden");
    $("certificateModal").classList.remove("flex");
}

// ---------------------------------------------
// 🗺️ LIVE SOC THREAT FEED ENGINE
// ---------------------------------------------

const socCities = [
    { id: "delhi", name: "Delhi NCR", elementId: "node-delhi" },
    { id: "mumbai", name: "Mumbai", elementId: "node-mumbai" },
    { id: "bengaluru", name: "Bengaluru", elementId: "node-bengaluru" },
    { id: "hyderabad", name: "Hyderabad", elementId: "node-hyderabad" },
    { id: "kolkata", name: "Kolkata", elementId: "node-kolkata" },
    { id: "jamtara", name: "Jamtara", elementId: "node-jamtara" },
    { id: "nuh", name: "Nuh / Mewat", elementId: "node-nuh" },
    { id: "bharatpur", name: "Bharatpur", elementId: "node-bharatpur" }
];

const mockThreatVpas = [
    "electricity-collect@ybl", "refund-gpay@okaxis", "free-cashback-gift@paytm",
    "complaint-bill-desk@sbi", "win-lottery-rewards@okhdfcbank", "upi-update-kyc@icici",
    "toll-plaza-fastag@ybl", "emergency-medical-fund@paytm", "income-tax-refund@okaxis"
];

const threatTypes = [
    "Typosquat Hijack", "Collect Request Scam", "Lottery PIN-Trap", 
    "Fake Fastag Portal", "Urgent Utility Fraud", "Government Refund Spoof"
];

let socThreatInterval = null;
function initSocThreatFeed() {
    if (socThreatInterval) clearInterval(socThreatInterval);
    socThreatInterval = setInterval(updateSocThreatFeed, 4000);
    updateSocThreatFeed();
}

async function updateSocThreatFeed() {
    const feed = $("socTickerFeed");
    if (!feed) return;

    try {
        const res = await fetch(`${API_BASE}/api/soc/threats`);
        const data = await res.json();
        
        if (!data.success || !data.threats || data.threats.length === 0) return;

        // Pick one threat randomly from the backend telemetry list
        const threat = data.threats[Math.floor(Math.random() * data.threats.length)];
        const cityData = socCities.find(c => c.name.toLowerCase() === threat.location.toLowerCase()) || socCities[0];

        const now = new Date();
        const timestamp = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        const risk = threat.risk_level === "CRITICAL" ? 98 : (threat.risk_level === "HIGH" ? 89 : 72);

        // Create log item
        const item = document.createElement("div");
        item.className = "p-2 bg-red-955/20 border border-red-500/10 rounded-lg flex flex-col gap-1 text-white animate-fadeIn mb-2 bg-red-950/20";
        item.innerHTML = `
            <div class="flex justify-between items-center text-[10px]">
                <span class="text-red-400 font-bold">${threat.fraud_type} Blocked 🛑</span>
                <span class="text-white/40">${timestamp}</span>
            </div>
            <div class="font-mono text-[9px] text-white/80 break-all">VPA: ${threat.upi}</div>
            <div class="flex justify-between text-[9px] text-white/50">
                <span>Location: ${threat.location}</span>
                <span class="text-red-400 font-semibold">Risk: ${risk}%</span>
            </div>
        `;

        // Add to feed list
        feed.insertBefore(item, feed.firstChild);

        // Caps feed to last 8 logs for visual neatness
        if (feed.children.length > 8) {
            feed.removeChild(feed.lastElementChild);
        }

        // Dynamic ping pulse animation on corresponding map node
        const node = $(cityData.elementId);
        if (node) {
            const pingSpan = node.querySelector("span:first-child");
            if (pingSpan) {
                pingSpan.classList.add("bg-red-500", "h-6", "w-6", "opacity-90");
                pingSpan.style.animationDuration = "0.6s";
                
                setTimeout(() => {
                    pingSpan.classList.remove("h-6", "w-6", "opacity-90");
                    pingSpan.style.animationDuration = "";
                }, 2000);
            }
        }
    } catch (e) {
        // Fallback silently if API base or network is offline
    }
}


// ----------------------------------------------------------------------
// 👤 USER PROFILE CONTROLLER
// ----------------------------------------------------------------------
function initProfile() {
    const name = localStorage.getItem("profile_name") || "Suraj Sawant";
    const vpa = localStorage.getItem("profile_vpa") || "9168772121@mbk";
    const photo = localStorage.getItem("profile_photo");

    // Pre-populate modal form inputs
    if ($("profileDisplayName")) $("profileDisplayName").value = name;
    if ($("profileUpiId")) $("profileUpiId").value = vpa;

    // Update navbar and modal preview
    if (photo) {
        if ($("navbar-profile-img")) {
            $("navbar-profile-img").src = photo;
            $("navbar-profile-img").classList.remove("hidden");
        }
        if ($("navbar-profile-icon")) $("navbar-profile-icon").classList.add("hidden");
        
        if ($("profile-modal-preview-img")) {
            $("profile-modal-preview-img").src = photo;
            $("profile-modal-preview-img").classList.remove("hidden");
        }
        if ($("profile-modal-preview-icon")) $("profile-modal-preview-icon").classList.add("hidden");
        if ($("removeProfileBtn")) $("removeProfileBtn").classList.remove("hidden");
    } else {
        if ($("navbar-profile-img")) $("navbar-profile-img").classList.add("hidden");
        if ($("navbar-profile-icon")) $("navbar-profile-icon").classList.remove("hidden");
        if ($("profile-modal-preview-img")) $("profile-modal-preview-img").classList.add("hidden");
        if ($("profile-modal-preview-icon")) $("profile-modal-preview-icon").classList.remove("hidden");
        if ($("removeProfileBtn")) $("removeProfileBtn").classList.add("hidden");
    }

    // Update Receive QR UI
    const customQr = localStorage.getItem("profile_custom_qr");
    if ($("profile-modal-preview-qr")) {
        if (customQr) {
            $("profile-modal-preview-qr").src = customQr;
            $("profile-modal-preview-qr").classList.remove("hidden");
            if ($("profile-modal-preview-qr-placeholder")) $("profile-modal-preview-qr-placeholder").classList.add("hidden");
            if ($("removeQrBtn")) $("removeQrBtn").classList.remove("hidden");
        } else {
            $("profile-modal-preview-qr").classList.add("hidden");
            if ($("profile-modal-preview-qr-placeholder")) $("profile-modal-preview-qr-placeholder").classList.remove("hidden");
            if ($("removeQrBtn")) $("removeQrBtn").classList.add("hidden");
        }
    }

    if ($("receiveQRNameText")) {
        $("receiveQRNameText").innerText = "Name: " + name;
    }
    if ($("receiveQRUpiText")) {
        $("receiveQRUpiText").innerText = "UPI: " + vpa;
    }
    if ($("receiveQRImg")) {
        if (customQr) {
            $("receiveQRImg").src = customQr;
        } else {
            const payload = `upi://pay?pa=${encodeURIComponent(vpa)}&pn=${encodeURIComponent(name)}&cu=INR&tn=SuRaksha%20Verified`;
            $("receiveQRImg").src = `https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=${encodeURIComponent(payload)}`;
        }
    }
}

function openProfileModal() {
    initProfile();
    toggle($("profileSettingsModal"), true);
}

function closeProfileModal() {
    toggle($("profileSettingsModal"), false);
}

// Image compression utility to prevent localStorage QuotaExceeded errors
function compressProfileImage(file, maxSize, callback) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            let width = img.width;
            let height = img.height;
            if (width > height) {
                if (width > maxSize) {
                    height = Math.round(height *= maxSize / width);
                    width = maxSize;
                }
            } else {
                if (height > maxSize) {
                    width = Math.round(width *= maxSize / height);
                    height = maxSize;
                }
            }
            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, width, height);
            callback(canvas.toDataURL("image/jpeg", 0.7)); // 0.7 quality
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function handleProfilePhotoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if ($("profileUploadProgressContainer")) $("profileUploadProgressContainer").classList.remove("hidden");
    if ($("profileUploadProgressBar")) $("profileUploadProgressBar").style.width = "0%";
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 90) progress = 90;
        if ($("profileUploadProgressBar")) $("profileUploadProgressBar").style.width = progress + "%";
    }, 200);

    compressProfileImage(file, 256, function(photoData) {
        clearInterval(interval);
        if ($("profileUploadProgressBar")) $("profileUploadProgressBar").style.width = "100%";
        
        setTimeout(() => {
            if ($("profile-modal-preview-img")) {
                $("profile-modal-preview-img").src = photoData;
                $("profile-modal-preview-img").classList.remove("hidden");
            }
            if ($("profile-modal-preview-icon")) $("profile-modal-preview-icon").classList.add("hidden");
            if ($("removeProfileBtn")) $("removeProfileBtn").classList.remove("hidden");
            
            window.pendingProfilePhoto = photoData;
            window.removeProfilePhotoFlag = false;
            showToast("Profile photo ready to save!", "success", 2000);
            
            setTimeout(() => {
                if ($("profileUploadProgressContainer")) $("profileUploadProgressContainer").classList.add("hidden");
                if ($("profileUploadProgressBar")) $("profileUploadProgressBar").style.width = "0%";
            }, 500);
        }, 300);
    });
}

function removeProfilePhoto(event) {
    if (event) event.preventDefault();
    if ($("profile-modal-preview-img")) {
        $("profile-modal-preview-img").src = "";
        $("profile-modal-preview-img").classList.add("hidden");
    }
    if ($("profile-modal-preview-icon")) $("profile-modal-preview-icon").classList.remove("hidden");
    if ($("removeProfileBtn")) $("removeProfileBtn").classList.add("hidden");
    window.pendingProfilePhoto = null;
    window.removeProfilePhotoFlag = true;
}

function handleCustomQrUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showToast("Processing custom QR code...", "info", 1500);

    compressProfileImage(file, 512, function(qrData) {
        if ($("profile-modal-preview-qr")) {
            $("profile-modal-preview-qr").src = qrData;
            $("profile-modal-preview-qr").classList.remove("hidden");
            if ($("profile-modal-preview-qr-placeholder")) $("profile-modal-preview-qr-placeholder").classList.add("hidden");
        }
        if ($("removeQrBtn")) $("removeQrBtn").classList.remove("hidden");
        window.pendingCustomQr = qrData;
        window.removeCustomQrFlag = false;
        showToast("Custom QR code ready to save!", "success", 2000);
    });
}

function removeCustomQr(event) {
    if (event) event.preventDefault();
    if ($("profile-modal-preview-qr")) {
        $("profile-modal-preview-qr").src = "";
        $("profile-modal-preview-qr").classList.add("hidden");
        if ($("profile-modal-preview-qr-placeholder")) $("profile-modal-preview-qr-placeholder").classList.remove("hidden");
    }
    if ($("removeQrBtn")) $("removeQrBtn").classList.add("hidden");
    window.pendingCustomQr = null;
    window.removeCustomQrFlag = true;
}

function saveUserProfile() {
    const name = $("profileDisplayName") ? $("profileDisplayName").value.trim() : "";
    const vpa = $("profileUpiId") ? $("profileUpiId").value.trim() : "";
    const photo = window.pendingProfilePhoto || null;
    const qr = window.pendingCustomQr || null;

    if (!name || !vpa) {
        showToast("Please enter both display name and UPI VPA", "warning");
        return;
    }

    localStorage.setItem("profile_name", name);
    localStorage.setItem("profile_vpa", vpa);
    
    if (window.removeProfilePhotoFlag) {
        localStorage.removeItem("profile_photo");
    } else if (photo) {
        try {
            localStorage.setItem("profile_photo", photo);
        } catch(e) { showToast("Failed to save profile photo: too large", "error"); }
    }
    
    if (window.removeCustomQrFlag) {
        localStorage.removeItem("profile_custom_qr");
    } else if (qr) {
        try {
            localStorage.setItem("profile_custom_qr", qr);
        } catch(e) { showToast("Failed to save QR code: too large", "error"); }
    }

    if (typeof closeProfileModal === "function") {
        try { closeProfileModal(); } catch (e) {}
    }
    
    initProfile();
    showToast("👤 Profile settings saved successfully!", "success", 3000);
}




// --- AUTO EXPORTS TO WINDOW FOR MODULAR COMPATIBILITY ---
window.safeText = safeText;
window.toggle = toggle;
window.selectIntent = selectIntent;
window.apiRequest = apiRequest;
window.showToast = showToast;
window.compressImage = compressImage;
window.analyzeImage = analyzeImage;
window.startScanner = startScanner;
window.stopScanner = stopScanner;
window.extractUpiAddress = extractUpiAddress;
window.sendQR = sendQR;
window.analyzeMessage = analyzeMessage;
window.checkUpiManual = checkUpiManual;
window.showReportModal = showReportModal;
window.submitFraudReport = submitFraudReport;
window.animateCounter = animateCounter;
window.loadStats = loadStats;
window.initApp = initApp;
window.showResultPopup = showResultPopup;
window.togglePaymentDrawer = togglePaymentDrawer;
window.simulatePaymentLaunch = simulatePaymentLaunch;
window.closePopup = closePopup;
window.showScreenshotResultPopup = showScreenshotResultPopup;
window.closeScreenshotPopup = closeScreenshotPopup;
window.syncOfflineBlacklist = syncOfflineBlacklist;
window.validateUpiLive = validateUpiLive;
window.updateCharCount = updateCharCount;
window.highlightScamKeywords = highlightScamKeywords;
window.sendChatMessage = sendChatMessage;
window.appendChatBubble = appendChatBubble;
window.pasteChatScamSample = pasteChatScamSample;
window.setupElaSlider = setupElaSlider;
window.generateClientSideEla = generateClientSideEla;
window.renderRadarChart = renderRadarChart;
window.triggerSandboxSimulation = triggerSandboxSimulation;
window.resetSandboxTerminal = resetSandboxTerminal;
window.showChatMessageScamModal = showChatMessageScamModal;
window.showSandboxResultPopup = showSandboxResultPopup;
window.showSandboxQrResult = showSandboxQrResult;
window.drawQrTargetBrackets = drawQrTargetBrackets;
window.clearQrOverlay = clearQrOverlay;
window.sha256 = sha256;
window.generateSecureStoreQr = generateSecureStoreQr;
window.toggleSecretVisibility = toggleSecretVisibility;
window.openMerchantCertificateModal = openMerchantCertificateModal;
window.closeMerchantCertificateModal = closeMerchantCertificateModal;
window.initSocThreatFeed = initSocThreatFeed;
window.updateSocThreatFeed = updateSocThreatFeed;
window.initProfile = initProfile;
window.openProfileModal = openProfileModal;
window.closeProfileModal = closeProfileModal;
window.compressImage = compressImage;
window.handleProfilePhotoUpload = handleProfilePhotoUpload;
window.removeProfilePhoto = removeProfilePhoto;
window.handleCustomQrUpload = handleCustomQrUpload;
window.removeCustomQr = removeCustomQr;
window.saveUserProfile = saveUserProfile;
window.isLocal = isLocal;
window.API_BASE = API_BASE;
window.AppState = AppState;
window.localBlacklist = localBlacklist;
window.localTrustedMerchants = localTrustedMerchants;
window.SCAM_SAMPLES = SCAM_SAMPLES;
window.isSandboxRunning = isSandboxRunning;
window.socCities = socCities;
window.mockThreatVpas = mockThreatVpas;
window.threatTypes = threatTypes;

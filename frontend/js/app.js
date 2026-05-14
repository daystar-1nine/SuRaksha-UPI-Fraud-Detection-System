// -----------------------------
// 🌍 GLOBAL STATE
// -----------------------------
const API_BASE = "http://127.0.0.1:5000";

let AppState = {
    intent: "pay",
    scanner: null,
    scanning: false
};


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
    toggle(UI.qr, false);

    if (intent === "pay") {

        safeText(UI.scanText, "Align QR code within the frame");
        UI.scanStatus.style.display = "block";

        UI.payTick?.classList.remove("hidden");
        UI.payCard?.classList.add("border-primary", "border-2");

        toggle(UI.reader, true);

        startScanner();

    } else {

        safeText(UI.scanText, "Show this QR to receive money");
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

        // ❗ HANDLE HTTP ERRORS
        if (!res.ok) {
            throw new Error(`HTTP Error: ${res.status}`);
        }

        const data = await res.json();

        if (data.success === false) {
            throw new Error(data.error || "API Error");
        }

        return data;

    } catch (err) {
        alert("⚠ Backend connection failed");
        console.error("API ERROR:", err);
        throw err;
    }
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
    formData.append("file", file);

    toggle($("loader"), true);

    try {

        const data = await apiRequest("/analyze", formData, true);

        showResultPopup(data);

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
// 📦 QR SEND
// -----------------------------
async function sendQR(text) {

    toggle($("loader"), true);

    try {
        const data = await apiRequest("/analyze/qr", {
            text,
            intent: AppState.intent
        });

        // 🔥 ADD THIS BLOCK
        if (AppState.intent === "receive") {

            toggle($("loader"), false);

            // ❌ STOP fraud popup
            $("resultPopup")?.classList.add("hidden");

            // ✅ Show receive UI
            alert("✅ This QR is for receiving money. Safe.");

            return;
        }

        showResultPopup(data);

    } catch {
        alert("QR scan failed ❌");
    } finally {
        toggle($("loader"), false);
    }
}
// -----------------------------
// 💬 MESSAGE ANALYSIS
// -----------------------------
async function analyzeMessage() {

    const text = $("messageInput").value;

    if (!text) {
        alert("Enter message first");
        return;
    }

    toggle($("loader"), true);

    try {

        const data = await apiRequest("/analyze_text", { text });

        showResultPopup(data);

    } catch (err) {

        alert("Error analyzing message");
        console.error(err);

    } finally {
        toggle($("loader"), false);
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
function showResultPopup(data) {
    

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

        safeText(alert, "🚨 High Risk Detected");

        safeText(safe, "❌ DO NOT PAY");

        $("alertSound")?.play();

    } else if (data.risk_level === "MEDIUM") {

        alert.className =
            "text-yellow-400 text-2xl font-bold";

        safeText(alert, "⚠ Medium Risk");

        safeText(safe, "⚠ Verify Carefully");

    } else {

        alert.className =
            "text-green-500 text-2xl font-bold";

        safeText(alert, "✅ Safe Transaction");

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

    console.log("Popup Data:", data);
}


// -----------------------------
// ❌ CLOSE POPUP
// -----------------------------
function closePopup() {
    $("resultPopup")?.classList.add("hidden");
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
// 🚀 INIT
// -----------------------------
window.onload = () => selectIntent("pay");
window.addEventListener("beforeunload", () => {

    stopScanner();

});
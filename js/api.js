/**
 * js/api.js — Centralised API helper (thin wrapper around fetch)
 * Provides environment-aware endpoint resolution, JWT/token injection, and error handling.
 */

const isLocal = typeof window !== "undefined" && (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === ""
);

export const API_BASE = isLocal
    ? "http://127.0.0.1:5000"
    : "https://suraksha-upi-fraud-detection-system.onrender.com";

/**
 * Generic fetch wrapper with unified error handling.
 * Returns parsed JSON on success, or throws a descriptive Error on failure.
 */
async function _request(endpoint, options = {}) {
    const token = typeof localStorage !== "undefined" ? localStorage.getItem("auth_token") : null;
    const headers = { ...(options.headers || {}) };
    if (token && !headers["Authorization"]) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (!res.ok) {
        if (res.status === 429) {
            const body = await res.json().catch(() => ({}));
            const msg = body?.error?.description || "Rate limit exceeded. Please try again later.";
            throw Object.assign(new Error(msg), { code: "RATE_LIMIT" });
        }
        const errorBody = await res.json().catch(() => null);
        const errMsg = errorBody?.error?.message || errorBody?.message || `HTTP ${res.status}: ${res.statusText}`;
        throw new Error(errMsg);
    }

    const data = await res.json();

    if (data.success === false) {
        const msg = (typeof data.error === "object" && data.error !== null)
            ? data.error.message
            : data.error;
        throw new Error(msg || "API Error");
    }

    return data;
}

/** GET request — for /api/stats, /api/blacklist/sync, /api/soc/threats, /api/auth/me */
export function apiGet(endpoint) {
    return _request(endpoint, { method: "GET" });
}

/** POST with JSON body — for /analyze/text, /analyze/qr, /api/auth/login, /api/auth/signup */
export function apiPost(endpoint, body) {
    return _request(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

/** PUT with JSON body — for /api/auth/profile */
export function apiPut(endpoint, body) {
    return _request(endpoint, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

/** POST with FormData — for /analyze (image upload) */
export function apiForm(endpoint, formData) {
    return _request(endpoint, {
        method: "POST",
        body: formData, // Browser sets multipart boundary automatically
    });
}


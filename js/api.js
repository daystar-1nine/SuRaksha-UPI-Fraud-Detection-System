/**
 * js/api.js — Centralised API helper (thin wrapper around fetch)
 *
 * Why this exists: Provides a single import point for all pages that need
 * to call the backend, so the base URL, error handling, and retry logic
 * live in one place rather than being duplicated in every inline <script>.
 *
 * Usage (ES module):
 *   import { apiGet, apiPost, apiForm } from '/js/api.js';
 *   const data = await apiPost('/analyze/text', { text: '...' });
 */

export const API_BASE = "https://suraksha-upi-fraud-detection-system.onrender.com";

/**
 * Generic fetch wrapper with unified error handling.
 * Returns parsed JSON on success, or throws a descriptive Error on failure.
 */
async function _request(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, options);

    if (!res.ok) {
        if (res.status === 429) {
            const body = await res.json().catch(() => ({}));
            const msg = body?.error?.description || "Rate limit exceeded. Please try again later.";
            throw Object.assign(new Error(msg), { code: "RATE_LIMIT" });
        }
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
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

/** GET request — for /api/stats, /api/blacklist/sync, /api/soc/threats */
export function apiGet(endpoint) {
    return _request(endpoint, { method: "GET" });
}

/** POST with JSON body — for /analyze/text, /analyze/qr */
export function apiPost(endpoint, body) {
    return _request(endpoint, {
        method: "POST",
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

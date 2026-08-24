package com.daystar.suraksha.security

import java.security.MessageDigest

/**
 * Computes canonical multi-parameter SHA-256 signatures matching the SuRaksha backend specification:
 * canonical = "vpa|name|mam|am|cu|qr_id|ts|exp|secret"
 */
object CanonicalSigner {

    const val DEFAULT_MERCHANT_SECRET = "SuRakshaShield2026"

    fun computeSignature(
        vpa: String,
        name: String,
        mam: String = "",
        am: String = "",
        cu: String = "INR",
        qrId: String,
        ts: String,
        exp: String = "",
        secret: String = DEFAULT_MERCHANT_SECRET
    ): String {
        val canonical = "${vpa.trim().lowercase()}|${name.trim().lowercase()}|${mam.trim()}|${am.trim()}|${cu.trim().uppercase()}|${qrId.trim()}|${ts.trim()}|${exp.trim()}|${secret.trim()}"
        return sha256(canonical)
    }

    fun sha256(input: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val hashBytes = digest.digest(input.toByteArray(Charsets.UTF_8))
        return hashBytes.joinToString("") { "%02x".format(it) }
    }
}

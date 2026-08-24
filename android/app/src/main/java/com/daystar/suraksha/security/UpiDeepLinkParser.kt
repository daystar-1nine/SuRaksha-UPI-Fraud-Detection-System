package com.daystar.suraksha.security

import android.net.Uri
import java.net.URLDecoder
import java.nio.charset.StandardCharsets

data class ParsedUpiData(
    val rawPayload: String,
    val vpa: String = "",
    val payeeName: String = "",
    val fixedAmount: Double? = null,
    val maxAmount: Double? = null,
    val currency: String = "INR",
    val qrId: String = "",
    val timestamp: String = "",
    val expiry: String = "",
    val signature: String = "",
    val transactionNote: String = "",
    val transactionRef: String = "",
    val isSigned: Boolean = false,
    val qrMode: String = "open" // "fixed_amount", "max_limit", "open"
)

object UpiDeepLinkParser {

    fun parse(qrText: String): ParsedUpiData {
        val trimmed = qrText.trim()
        if (!trimmed.startsWith("upi://", ignoreCase = true)) {
            // Check if it's a plain VPA (e.g. merchant@upi)
            val vpaPattern = Regex("[a-zA-Z0-9._+\\-]{2,}@[a-zA-Z]{2,20}")
            val match = vpaPattern.find(trimmed)
            return if (match != null) {
                ParsedUpiData(
                    rawPayload = trimmed,
                    vpa = match.value.lowercase(),
                    payeeName = "Recipient",
                    qrMode = "open"
                )
            } else {
                ParsedUpiData(rawPayload = trimmed)
            }
        }

        return try {
            // Handle URL format
            val uri = Uri.parse(trimmed)
            val params = mutableMapOf<String, String>()

            val query = uri.query ?: (if (trimmed.contains("?")) trimmed.substringAfter("?") else "")
            if (query.isNotEmpty()) {
                val pairs = query.split("&")
                for (pair in pairs) {
                    val parts = pair.split("=", limit = 2)
                    if (parts.size == 2) {
                        val key = parts[0].trim()
                        val value = try {
                            URLDecoder.decode(parts[1], StandardCharsets.UTF_8.name())
                        } catch (e: Exception) {
                            parts[1]
                        }
                        params[key] = value
                    }
                }
            }

            val pa = params["pa"]?.trim()?.lowercase() ?: ""
            val pn = params["pn"]?.trim() ?: "Merchant"
            val amStr = params["am"]?.trim()
            val mamStr = params["mam"]?.trim()
            val cu = params["cu"]?.trim()?.uppercase() ?: "INR"
            val qrId = params["qr_id"]?.trim() ?: ""
            val ts = params["ts"]?.trim() ?: ""
            val exp = params["exp"]?.trim() ?: ""
            val sign = params["sign"]?.trim() ?: ""
            val tn = params["tn"]?.trim() ?: ""
            val tr = params["tr"]?.trim() ?: ""

            val amVal = amStr?.toDoubleOrNull()
            val mamVal = mamStr?.toDoubleOrNull()

            val mode = when {
                mamVal != null && mamVal > 0 -> "max_limit"
                amVal != null && amVal > 0 -> "fixed_amount"
                else -> "open"
            }

            ParsedUpiData(
                rawPayload = trimmed,
                vpa = pa,
                payeeName = pn,
                fixedAmount = amVal,
                maxAmount = mamVal,
                currency = cu,
                qrId = qrId,
                timestamp = ts,
                expiry = exp,
                signature = sign,
                transactionNote = tn,
                transactionRef = tr,
                isSigned = sign.isNotEmpty(),
                qrMode = mode
            )
        } catch (e: Exception) {
            ParsedUpiData(rawPayload = trimmed)
        }
    }
}

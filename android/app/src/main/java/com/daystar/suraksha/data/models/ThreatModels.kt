package com.daystar.suraksha.data.models

import com.google.gson.annotations.SerializedName

data class UserHistoryData(
    @SerializedName("analyses") val analyses: List<AnalysisHistoryItem> = emptyList(),
    @SerializedName("qr_codes") val qrCodes: List<QrRecordItem> = emptyList(),
    @SerializedName("user") val user: UserProfile? = null
)

data class AnalysisHistoryItem(
    @SerializedName("id") val id: Int = 0,
    @SerializedName("type") val type: String = "qr_scan",
    @SerializedName("input_data") val inputData: String? = null,
    @SerializedName("upi_id") val upiId: String? = null,
    @SerializedName("payee_name") val payeeName: String? = null,
    @SerializedName("risk_score") val riskScore: Int = 0,
    @SerializedName("risk_level") val riskLevel: String = "SAFE",
    @SerializedName("fraud_type") val fraudType: String? = null,
    @SerializedName("confidence") val confidence: Double = 0.95,
    @SerializedName("qr_mode") val qrMode: String? = null,
    @SerializedName("max_amount") val maxAmount: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("signature_valid") val signatureValid: Boolean = false,
    @SerializedName("is_tampered") val isTampered: Boolean = false,
    @SerializedName("reasons") val reasons: List<String> = emptyList(),
    @SerializedName("created_at") val createdAt: String? = null
)

data class QrRecordItem(
    @SerializedName("qr_id") val qrId: String,
    @SerializedName("vpa") val vpa: String,
    @SerializedName("payee_name") val payeeName: String,
    @SerializedName("qr_mode") val qrMode: String,
    @SerializedName("max_amount") val maxAmount: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("currency") val currency: String = "INR",
    @SerializedName("signature") val signature: String,
    @SerializedName("payload") val payload: String,
    @SerializedName("created_at") val createdAt: String? = null
)

data class HealthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("message") val message: String? = null
)

data class BlacklistSyncResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("blacklist") val blacklist: List<BlacklistItem> = emptyList()
)

data class BlacklistItem(
    @SerializedName("upi") val upi: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("reports") val reports: Int
)

data class ReportFraudRequest(
    @SerializedName("upi_id") val upiId: String,
    @SerializedName("fraud_type") val fraudType: String = "Suspicious Transaction",
    @SerializedName("description") val description: String? = null
)

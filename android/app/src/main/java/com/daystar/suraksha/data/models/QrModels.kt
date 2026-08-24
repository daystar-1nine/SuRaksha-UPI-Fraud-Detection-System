package com.daystar.suraksha.data.models

import com.google.gson.annotations.SerializedName

data class QrAnalysisRequest(
    @SerializedName("qr_data") val qrData: String,
    @SerializedName("payment_amount") val paymentAmount: Double? = null
)

data class QrAnalysisResponseData(
    @SerializedName("qr") val qr: QrParsedPayload,
    @SerializedName("analysis") val analysis: QrRiskAnalysis
)

data class QrParsedPayload(
    @SerializedName("raw") val raw: String? = null,
    @SerializedName("parsed") val parsed: Map<String, List<String>>? = null
)

data class QrRiskAnalysis(
    @SerializedName("risk_score") val riskScore: Int = 0,
    @SerializedName("risk_level") val riskLevel: String = "SAFE",
    @SerializedName("confidence") val confidence: Double = 0.95,
    @SerializedName("suspicious") val suspicious: Boolean = false,
    @SerializedName("fraud_type") val fraudType: String? = null,
    @SerializedName("detected_action") val detectedAction: String? = null,
    @SerializedName("signals") val signals: List<ThreatSignal> = emptyList(),
    @SerializedName("reasons") val reasons: List<String> = emptyList(),
    @SerializedName("constraints") val constraints: QrConstraints = QrConstraints()
)

data class ThreatSignal(
    @SerializedName("type") val type: String = "",
    @SerializedName("score") val score: Double = 0.0,
    @SerializedName("confidence") val confidence: Double = 0.0,
    @SerializedName("reason") val reason: String = ""
)

data class QrConstraints(
    @SerializedName("qr_mode") val qrMode: String? = null,
    @SerializedName("max_amount") val maxAmount: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("currency") val currency: String = "INR",
    @SerializedName("qr_id") val qrId: String? = null,
    @SerializedName("timestamp") val timestamp: String? = null,
    @SerializedName("expiry") val expiry: String? = null,
    @SerializedName("is_expired") val isExpired: Boolean = false,
    @SerializedName("is_signed") val isSigned: Boolean = false,
    @SerializedName("signature_valid") val signatureValid: Boolean = false,
    @SerializedName("payment_validation") val paymentValidation: PaymentValidationResult? = null
)

data class PaymentValidationResult(
    @SerializedName("requested_amount") val requestedAmount: Double? = null,
    @SerializedName("max_limit") val maxLimit: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("allowed") val allowed: Boolean = false,
    @SerializedName("reason") val reason: String = ""
)

data class ValidatePaymentRequest(
    @SerializedName("qr_data") val qrData: String,
    @SerializedName("payment_amount") val paymentAmount: Double
)

data class ValidatePaymentResponseData(
    @SerializedName("allowed") val allowed: Boolean,
    @SerializedName("reason") val reason: String,
    @SerializedName("qr_mode") val qrMode: String? = null,
    @SerializedName("max_amount") val maxAmount: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("requested_amount") val requestedAmount: Double? = null,
    @SerializedName("is_signed") val isSigned: Boolean = false,
    @SerializedName("signature_valid") val signatureValid: Boolean = false,
    @SerializedName("risk_level") val riskLevel: String = "SAFE"
)

data class SaveQrRecordRequest(
    @SerializedName("qr_id") val qrId: String,
    @SerializedName("vpa") val vpa: String,
    @SerializedName("payee_name") val payeeName: String,
    @SerializedName("qr_mode") val qrMode: String,
    @SerializedName("max_amount") val maxAmount: Double? = null,
    @SerializedName("fixed_amount") val fixedAmount: Double? = null,
    @SerializedName("signature") val signature: String,
    @SerializedName("payload") val payload: String
)

data class SaveQrRecordData(
    @SerializedName("record_id") val recordId: Int,
    @SerializedName("qr_id") val qrId: String
)

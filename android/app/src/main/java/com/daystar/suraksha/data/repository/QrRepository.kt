package com.daystar.suraksha.data.repository

import android.content.Context
import com.daystar.suraksha.data.api.ApiClient
import com.daystar.suraksha.data.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class QrRepository(private val context: Context) {

    private val apiService = ApiClient.getService(context)

    suspend fun analyzeQr(qrPayload: String, requestedAmount: Double? = null): Result<QrRiskAnalysis> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.analyzeQr(
                QrAnalysisRequest(qrData = qrPayload, paymentAmount = requestedAmount)
            )
            if (response.isSuccessful && response.body()?.success == true) {
                val analysis = response.body()?.data?.analysis
                if (analysis != null) {
                    Result.success(analysis)
                } else {
                    Result.failure(Exception("Empty analysis payload returned"))
                }
            } else {
                val errMsg = response.body()?.getErrorMessage() ?: "QR analysis failed (${response.code()})"
                Result.failure(Exception(errMsg))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Unable to connect to SuRaksha security server"))
        }
    }

    suspend fun validatePaymentAmount(qrPayload: String, amount: Double): Result<ValidatePaymentResponseData> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.validatePayment(
                ValidatePaymentRequest(qrData = qrPayload, paymentAmount = amount)
            )
            if (response.isSuccessful && response.body()?.success == true) {
                val valData = response.body()?.data
                if (valData != null) {
                    Result.success(valData)
                } else {
                    Result.failure(Exception("No validation result returned"))
                }
            } else {
                val errMsg = response.body()?.getErrorMessage() ?: "Payment validation failed"
                Result.failure(Exception(errMsg))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Connection error during payment validation"))
        }
    }

    suspend fun saveQrRecord(
        qrId: String,
        vpa: String,
        payeeName: String,
        qrMode: String,
        maxAmount: Double?,
        fixedAmount: Double?,
        signature: String,
        payload: String
    ): Result<SaveQrRecordData> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.saveQrRecord(
                SaveQrRecordRequest(
                    qrId = qrId,
                    vpa = vpa,
                    payeeName = payeeName,
                    qrMode = qrMode,
                    maxAmount = maxAmount,
                    fixedAmount = fixedAmount,
                    signature = signature,
                    payload = payload
                )
            )
            if (response.isSuccessful && response.body()?.success == true) {
                val data = response.body()?.data
                if (data != null) {
                    Result.success(data)
                } else {
                    Result.failure(Exception("QR saved without ID"))
                }
            } else {
                Result.failure(Exception(response.body()?.getErrorMessage() ?: "Failed to save QR"))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Network error while saving QR"))
        }
    }
}

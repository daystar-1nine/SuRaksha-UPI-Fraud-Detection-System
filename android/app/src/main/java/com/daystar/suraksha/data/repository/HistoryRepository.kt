package com.daystar.suraksha.data.repository

import android.content.Context
import com.daystar.suraksha.data.api.ApiClient
import com.daystar.suraksha.data.models.ReportFraudRequest
import com.daystar.suraksha.data.models.UserHistoryData
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class HistoryRepository(private val context: Context) {

    private val apiService = ApiClient.getService(context)

    suspend fun fetchHistory(): Result<UserHistoryData> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getHistory()
            if (response.isSuccessful && response.body()?.success == true) {
                val data = response.body()?.data
                if (data != null) {
                    Result.success(data)
                } else {
                    Result.success(UserHistoryData())
                }
            } else {
                Result.failure(Exception(response.body()?.getErrorMessage() ?: "Failed to fetch history"))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Failed to fetch security audit logs"))
        }
    }

    suspend fun reportFraud(upiId: String, description: String?): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.reportFraud(
                ReportFraudRequest(upiId = upiId.trim(), description = description?.trim())
            )
            if (response.isSuccessful && response.body()?.success == true) {
                Result.success(Unit)
            } else {
                Result.failure(Exception(response.body()?.getErrorMessage() ?: "Failed to submit fraud report"))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Network error submitting report"))
        }
    }
}

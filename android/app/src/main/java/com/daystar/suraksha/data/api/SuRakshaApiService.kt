package com.daystar.suraksha.data.api

import com.daystar.suraksha.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface SuRakshaApiService {

    @GET("/health")
    suspend fun getHealth(): Response<HealthResponse>

    @POST("/api/auth/signup")
    suspend fun signup(@Body request: SignupRequest): Response<ApiResponse<AuthData>>

    @POST("/api/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<ApiResponse<AuthData>>

    @POST("/api/auth/logout")
    suspend fun logout(): Response<ApiResponse<Any>>

    @GET("/api/auth/me")
    suspend fun getMe(): Response<ApiResponse<UserDataWrapper>>

    @PUT("/api/auth/profile")
    suspend fun updateProfile(@Body request: UpdateProfileRequest): Response<ApiResponse<UserDataWrapper>>

    @GET("/api/auth/history")
    suspend fun getHistory(): Response<ApiResponse<UserHistoryData>>

    @POST("/analyze/qr")
    suspend fun analyzeQr(@Body request: QrAnalysisRequest): Response<ApiResponse<QrAnalysisResponseData>>

    @POST("/qr/validate-payment")
    suspend fun validatePayment(@Body request: ValidatePaymentRequest): Response<ApiResponse<ValidatePaymentResponseData>>

    @POST("/api/qr/save-record")
    suspend fun saveQrRecord(@Body request: SaveQrRecordRequest): Response<ApiResponse<SaveQrRecordData>>

    @GET("/api/blacklist/sync")
    suspend fun syncBlacklist(): Response<BlacklistSyncResponse>

    @POST("/api/report")
    suspend fun reportFraud(@Body request: ReportFraudRequest): Response<ApiResponse<Any>>
}

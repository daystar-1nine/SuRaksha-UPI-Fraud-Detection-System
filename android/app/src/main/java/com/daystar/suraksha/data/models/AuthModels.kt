package com.daystar.suraksha.data.models

import com.google.gson.annotations.SerializedName

data class ApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String? = null,
    @SerializedName("data") val data: T? = null,
    @SerializedName("request_id") val requestId: String? = null,
    @SerializedName("error") val error: Any? = null
) {
    fun getErrorMessage(): String {
        return when (error) {
            is String -> error
            is Map<*, *> -> (error["message"] ?: error["description"] ?: "Unknown error").toString()
            else -> message ?: "Request failed"
        }
    }
}

data class LoginRequest(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String
)

data class SignupRequest(
    @SerializedName("username") val username: String,
    @SerializedName("email") val email: String,
    @SerializedName("password") val password: String,
    @SerializedName("full_name") val fullName: String = "",
    @SerializedName("upi_id") val upiId: String = ""
)

data class AuthData(
    @SerializedName("token") val token: String,
    @SerializedName("user") val user: UserProfile
)

data class UserProfile(
    @SerializedName("id") val id: Int,
    @SerializedName("username") val username: String,
    @SerializedName("email") val email: String,
    @SerializedName("full_name") val fullName: String? = null,
    @SerializedName("upi_id") val upiId: String? = null,
    @SerializedName("role") val role: String = "user",
    @SerializedName("created_at") val createdAt: String? = null
)

data class UpdateProfileRequest(
    @SerializedName("full_name") val fullName: String? = null,
    @SerializedName("upi_id") val upiId: String? = null
)

data class UserDataWrapper(
    @SerializedName("user") val user: UserProfile
)

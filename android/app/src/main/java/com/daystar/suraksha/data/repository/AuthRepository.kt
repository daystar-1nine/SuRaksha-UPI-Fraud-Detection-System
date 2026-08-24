package com.daystar.suraksha.data.repository

import android.content.Context
import com.daystar.suraksha.data.api.ApiClient
import com.daystar.suraksha.data.models.*
import com.daystar.suraksha.security.TokenManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AuthRepository(private val context: Context) {

    private val apiService = ApiClient.getService(context)
    private val tokenManager = TokenManager.getInstance(context)

    suspend fun login(username: String, pass: String): Result<UserProfile> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.login(LoginRequest(username = username.trim(), password = pass))
            if (response.isSuccessful && response.body()?.success == true) {
                val authData = response.body()?.data
                if (authData != null) {
                    tokenManager.saveToken(authData.token)
                    tokenManager.saveUserProfile(authData.user)
                    Result.success(authData.user)
                } else {
                    Result.failure(Exception("No authentication data returned"))
                }
            } else {
                val errorMsg = response.body()?.getErrorMessage() ?: "Authentication failed (${response.code()})"
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Network connection error"))
        }
    }

    suspend fun signup(username: String, email: String, pass: String, fullName: String, upiId: String): Result<UserProfile> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.signup(
                SignupRequest(
                    username = username.trim(),
                    email = email.trim(),
                    password = pass,
                    fullName = fullName.trim(),
                    upiId = upiId.trim()
                )
            )
            if (response.isSuccessful && response.body()?.success == true) {
                val authData = response.body()?.data
                if (authData != null) {
                    tokenManager.saveToken(authData.token)
                    tokenManager.saveUserProfile(authData.user)
                    Result.success(authData.user)
                } else {
                    Result.failure(Exception("No user data returned"))
                }
            } else {
                val errorMsg = response.body()?.getErrorMessage() ?: "Registration failed (${response.code()})"
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Network connection error"))
        }
    }

    suspend fun logout(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            apiService.logout()
        } catch (e: Exception) {
            // Ignore network errors on logout
        } finally {
            tokenManager.clearAuth()
        }
        Result.success(Unit)
    }

    suspend fun fetchCurrentUser(): Result<UserProfile> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getMe()
            if (response.isSuccessful && response.body()?.success == true) {
                val user = response.body()?.data?.user
                if (user != null) {
                    tokenManager.saveUserProfile(user)
                    Result.success(user)
                } else {
                    Result.failure(Exception("Failed to load user profile"))
                }
            } else {
                Result.failure(Exception("Session expired or invalid"))
            }
        } catch (e: Exception) {
            val cached = tokenManager.getUserProfile()
            if (cached != null) Result.success(cached) else Result.failure(e)
        }
    }

    suspend fun updateProfile(fullName: String?, upiId: String?): Result<UserProfile> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.updateProfile(UpdateProfileRequest(fullName = fullName, upiId = upiId))
            if (response.isSuccessful && response.body()?.success == true) {
                val user = response.body()?.data?.user
                if (user != null) {
                    tokenManager.saveUserProfile(user)
                    Result.success(user)
                } else {
                    Result.failure(Exception("Failed to update profile"))
                }
            } else {
                val err = response.body()?.getErrorMessage() ?: "Profile update failed"
                Result.failure(Exception(err))
            }
        } catch (e: Exception) {
            Result.failure(Exception(e.localizedMessage ?: "Network connection error"))
        }
    }

    fun isUserLoggedIn(): Boolean = tokenManager.isAuthenticated()

    fun getCachedUser(): UserProfile? = tokenManager.getUserProfile()
}

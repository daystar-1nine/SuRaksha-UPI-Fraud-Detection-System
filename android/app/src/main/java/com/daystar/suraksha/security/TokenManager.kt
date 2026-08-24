package com.daystar.suraksha.security

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.daystar.suraksha.data.models.UserProfile

class TokenManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()

    companion object {
        private const val PREF_NAME = "suraksha_secure_prefs"
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_USER_PROFILE = "user_profile"
        private const val KEY_API_BASE_URL = "api_base_url"

        @Volatile
        private var INSTANCE: TokenManager? = null

        fun getInstance(context: Context): TokenManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: TokenManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }

    fun saveToken(token: String) {
        prefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getToken(): String? {
        return prefs.getString(KEY_AUTH_TOKEN, null)
    }

    fun saveUserProfile(user: UserProfile) {
        val json = gson.toJson(user)
        prefs.edit().putString(KEY_USER_PROFILE, json).apply()
    }

    fun getUserProfile(): UserProfile? {
        val json = prefs.getString(KEY_USER_PROFILE, null) ?: return null
        return try {
            gson.fromJson(json, UserProfile::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun clearAuth() {
        prefs.edit()
            .remove(KEY_AUTH_TOKEN)
            .remove(KEY_USER_PROFILE)
            .apply()
    }

    fun isAuthenticated(): Boolean {
        return !getToken().isNullOrBlank()
    }

    fun getBaseUrl(): String {
        return prefs.getString(KEY_API_BASE_URL, null) ?: "http://10.0.2.2:5000" // Android Emulator localhost bridge
    }

    fun setBaseUrl(url: String) {
        prefs.edit().putString(KEY_API_BASE_URL, url).apply()
    }
}

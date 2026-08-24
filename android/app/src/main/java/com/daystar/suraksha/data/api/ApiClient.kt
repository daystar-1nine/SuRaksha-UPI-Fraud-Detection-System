package com.daystar.suraksha.data.api

import android.content.Context
import com.daystar.suraksha.security.TokenManager
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private var retrofit: Retrofit? = null
    private var apiService: SuRakshaApiService? = null
    private var currentBaseUrl: String = ""

    fun getService(context: Context): SuRakshaApiService {
        val tokenManager = TokenManager.getInstance(context)
        val baseUrl = tokenManager.getBaseUrl().trimEnd('/') + "/"

        if (apiService != null && currentBaseUrl == baseUrl) {
            return apiService!!
        }

        currentBaseUrl = baseUrl

        val authInterceptor = Interceptor { chain ->
            val original = chain.request()
            val requestBuilder = original.newBuilder()

            val token = tokenManager.getToken()
            if (!token.isNullOrBlank()) {
                requestBuilder.header("Authorization", "Bearer $token")
            }
            requestBuilder.header("Accept", "application/json")
            requestBuilder.header("Content-Type", "application/json")

            chain.proceed(requestBuilder.build())
        }

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .writeTimeout(20, TimeUnit.SECONDS)
            .build()

        retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit!!.create(SuRakshaApiService::class.java)
        return apiService!!
    }

    fun resetClient() {
        retrofit = null
        apiService = null
        currentBaseUrl = ""
    }
}

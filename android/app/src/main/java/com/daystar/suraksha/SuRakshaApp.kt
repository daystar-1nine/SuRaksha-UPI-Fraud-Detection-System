package com.daystar.suraksha

import android.app.Application
import com.daystar.suraksha.security.TokenManager

class SuRakshaApp : Application() {

    override fun onCreate() {
        super.onCreate()
        // Initialize token manager and singleton dependencies
        TokenManager.getInstance(this)
    }
}

package com.daystar.suraksha.navigation

sealed class Screen(val route: String) {
    data object Splash : Screen("splash")
    data object Auth : Screen("auth")
    data object Dashboard : Screen("dashboard")
    data object Scanner : Screen("scanner")
    data object Verification : Screen("verification?payload={payload}") {
        fun createRoute(payload: String): String = "verification?payload=$payload"
    }
    data object GenerateQr : Screen("generate_qr")
    data object History : Screen("history")
    data object Profile : Screen("profile")
}

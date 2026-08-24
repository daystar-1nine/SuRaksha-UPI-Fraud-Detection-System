package com.daystar.suraksha.navigation

import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.daystar.suraksha.data.models.QrRiskAnalysis
import com.daystar.suraksha.security.ParsedUpiData
import com.daystar.suraksha.security.TokenManager
import com.daystar.suraksha.ui.auth.AuthScreen
import com.daystar.suraksha.ui.dashboard.DashboardScreen
import com.daystar.suraksha.ui.generator.GenerateQrScreen
import com.daystar.suraksha.ui.history.HistoryScreen
import com.daystar.suraksha.ui.profile.ProfileScreen
import com.daystar.suraksha.ui.result.RiskResultScreen
import com.daystar.suraksha.ui.scanner.ScannerScreen
import com.daystar.suraksha.ui.verification.VerificationScreen
import java.net.URLDecoder
import java.net.URLEncoder

@Composable
fun SuRakshaNavGraph(
    navController: NavHostController,
    startDestination: String = Screen.Dashboard.route
) {
    val context = LocalContext.current
    val tokenManager = remember { TokenManager.getInstance(context) }

    // Temporary storage for result screen
    var lastParsedData by remember { mutableStateOf<ParsedUpiData?>(null) }
    var lastAnalysis by remember { mutableStateOf<QrRiskAnalysis?>(null) }

    NavHost(
        navController = navController,
        startDestination = if (tokenManager.isAuthenticated()) Screen.Dashboard.route else Screen.Auth.route,
        enterTransition = { fadeIn(animationSpec = tween(250)) + slideIntoContainer(AnimatedContentTransitionScope.SlideDirection.Start, tween(250)) },
        exitTransition = { fadeOut(animationSpec = tween(250)) + slideOutOfContainer(AnimatedContentTransitionScope.SlideDirection.Start, tween(250)) },
        popEnterTransition = { fadeIn(animationSpec = tween(250)) + slideIntoContainer(AnimatedContentTransitionScope.SlideDirection.End, tween(250)) },
        popExitTransition = { fadeOut(animationSpec = tween(250)) + slideOutOfContainer(AnimatedContentTransitionScope.SlideDirection.End, tween(250)) }
    ) {
        // 1. Auth Screen
        composable(Screen.Auth.route) {
            AuthScreen(
                onAuthSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Auth.route) { inclusive = true }
                    }
                }
            )
        }

        // 2. Dashboard Screen
        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToScanner = { navController.navigate(Screen.Scanner.route) },
                onNavigateToGenerator = { navController.navigate(Screen.GenerateQr.route) },
                onNavigateToHistory = { navController.navigate(Screen.History.route) },
                onNavigateToProfile = { navController.navigate(Screen.Profile.route) }
            )
        }

        // 3. Scanner Screen
        composable(Screen.Scanner.route) {
            ScannerScreen(
                onQrScanned = { payload ->
                    val encoded = URLEncoder.encode(payload, "UTF-8")
                    navController.navigate(Screen.Verification.createRoute(encoded)) {
                        popUpTo(Screen.Scanner.route) { inclusive = true }
                    }
                },
                onBackClick = { navController.popBackStack() }
            )
        }

        // 4. Verification & Risk Result Flow
        composable(
            route = Screen.Verification.route,
            arguments = listOf(navArgument("payload") { type = NavType.StringType; defaultValue = "" })
        ) { backStackEntry ->
            val encodedPayload = backStackEntry.arguments?.getString("payload") ?: ""
            val rawPayload = try {
                URLDecoder.decode(encodedPayload, "UTF-8")
            } catch (e: Exception) {
                encodedPayload
            }

            if (lastAnalysis != null && lastParsedData != null) {
                RiskResultScreen(
                    parsedData = lastParsedData!!,
                    analysis = lastAnalysis!!,
                    onBackToDashboard = {
                        lastParsedData = null
                        lastAnalysis = null
                        navController.navigate(Screen.Dashboard.route) {
                            popUpTo(Screen.Dashboard.route) { inclusive = true }
                        }
                    },
                    onScanAnother = {
                        lastParsedData = null
                        lastAnalysis = null
                        navController.navigate(Screen.Scanner.route) {
                            popUpTo(Screen.Dashboard.route)
                        }
                    }
                )
            } else {
                VerificationScreen(
                    rawQrPayload = rawPayload,
                    onVerificationComplete = { parsed, analysis ->
                        lastParsedData = parsed
                        lastAnalysis = analysis
                    },
                    onBackClick = { navController.popBackStack() }
                )
            }
        }

        // 5. QR Generator Screen
        composable(Screen.GenerateQr.route) {
            GenerateQrScreen(
                onBackClick = { navController.popBackStack() }
            )
        }

        // 6. History Screen
        composable(Screen.History.route) {
            HistoryScreen(
                onBackClick = { navController.popBackStack() }
            )
        }

        // 7. Profile Screen
        composable(Screen.Profile.route) {
            ProfileScreen(
                onBackClick = { navController.popBackStack() },
                onLogoutSuccess = {
                    navController.navigate(Screen.Auth.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
    }
}

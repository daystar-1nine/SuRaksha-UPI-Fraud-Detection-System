package com.daystar.suraksha.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = SuRakshaBlueLight,
    onPrimary = DarkBackground,
    primaryContainer = SuRakshaBlueDark,
    onPrimaryContainer = DarkOnBackground,
    secondary = SuRakshaCyan,
    onSecondary = DarkBackground,
    background = DarkBackground,
    onBackground = DarkOnBackground,
    surface = DarkSurface,
    onSurface = DarkOnSurface,
    surfaceVariant = DarkSurfaceVariant,
    onSurfaceVariant = DarkTextMuted,
    error = RiskCriticalRed,
    onError = DarkBackground
)

private val LightColorScheme = lightColorScheme(
    primary = SuRakshaBlue,
    onPrimary = LightSurface,
    primaryContainer = SuRakshaBlueLight,
    onPrimaryContainer = LightSurface,
    secondary = SuRakshaCyan,
    onSecondary = LightSurface,
    background = LightBackground,
    onBackground = LightOnBackground,
    surface = LightSurface,
    onSurface = LightOnSurface,
    surfaceVariant = LightSurfaceVariant,
    onSurfaceVariant = LightTextMuted,
    error = RiskCriticalRed,
    onError = LightSurface
)

@Composable
fun SuRakshaTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = SuRakshaTypography,
        content = content
    )
}

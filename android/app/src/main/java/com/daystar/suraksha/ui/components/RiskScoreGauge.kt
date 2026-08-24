package com.daystar.suraksha.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.GppBad
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.daystar.suraksha.ui.theme.*

@Composable
fun RiskScoreGauge(
    score: Int,
    level: String,
    confidence: Double = 0.95,
    size: Dp = 180.dp,
    strokeWidth: Dp = 14.dp
) {
    val animatedScore = remember { Animatable(0f) }

    LaunchedEffect(score) {
        animatedScore.animateTo(
            targetValue = score.coerceIn(0, 100).toFloat(),
            animationSpec = tween(durationMillis = 1200)
        )
    }

    val riskColor = when {
        score >= 75 || level.equals("CRITICAL", ignoreCase = true) -> RiskCriticalRed
        score >= 50 || level.equals("HIGH", ignoreCase = true) -> RiskHighOrange
        score >= 25 || level.equals("MEDIUM", ignoreCase = true) -> RiskMediumYellow
        score >= 10 || level.equals("LOW", ignoreCase = true) -> RiskLowBlue
        else -> RiskSafeGreen
    }

    val riskIcon = when {
        score >= 75 || level.equals("CRITICAL", ignoreCase = true) -> Icons.Default.GppBad
        score >= 25 -> Icons.Default.Warning
        else -> Icons.Default.CheckCircle
    }

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Box(
            modifier = Modifier.size(size),
            contentAlignment = Alignment.Center
        ) {
            val trackColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
            Canvas(modifier = Modifier.size(size)) {
                val sweepAngle = 260f
                val startAngle = 140f

                // Background track
                drawArc(
                    color = trackColor,
                    startAngle = startAngle,
                    sweepAngle = sweepAngle,
                    useCenter = false,
                    style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
                )

                // Animated risk sweep
                val progressAngle = (animatedScore.value / 100f) * sweepAngle
                if (progressAngle > 0) {
                    drawArc(
                        color = riskColor,
                        startAngle = startAngle,
                        sweepAngle = progressAngle,
                        useCenter = false,
                        style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
                    )
                }
            }

            // Inside Center Content
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "${animatedScore.value.toInt()}",
                    style = MaterialTheme.typography.headlineLarge.copy(
                        fontSize = 42.sp,
                        fontWeight = FontWeight.ExtraBold
                    ),
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = "/ 100",
                    style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // Risk Level Badge
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = riskColor.copy(alpha = 0.15f),
            border = null
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Icon(
                    imageVector = riskIcon,
                    contentDescription = level,
                    tint = riskColor,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = "$level RISK",
                    style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                    color = riskColor
                )
            }
        }

        // Confidence
        Text(
            text = "AI Model Confidence: ${(confidence * 100).toInt()}%",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

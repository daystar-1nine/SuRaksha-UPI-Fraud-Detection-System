package com.daystar.suraksha.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.daystar.suraksha.ui.theme.*

@Composable
fun ThreatFactorCard(
    reasons: List<String>,
    isSafe: Boolean,
    isTampered: Boolean = false,
    isExpired: Boolean = false
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = if (isSafe) Icons.Default.CheckCircle else Icons.Default.Warning,
                    contentDescription = "Threat Factors",
                    tint = if (isSafe) RiskSafeGreen else if (isTampered || isExpired) RiskCriticalRed else RiskHighOrange,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    text = if (isSafe) "Security Verification Signals" else "Detected Threat Indicators",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            HorizontalDivider(
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f),
                thickness = 1.dp
            )

            if (isTampered) {
                ThreatSignalRow(
                    text = "CRITICAL: Cryptographic signature mismatch! Maximum payment limit or merchant identity was modified / tampered.",
                    isCritical = true
                )
            }

            if (isExpired) {
                ThreatSignalRow(
                    text = "CRITICAL: QR code has expired and cannot be accepted for payment.",
                    isCritical = true
                )
            }

            if (reasons.isEmpty() && isSafe) {
                ThreatSignalRow(
                    text = "✔ Verified merchant identity confirmed.",
                    isPositive = true
                )
                ThreatSignalRow(
                    text = "✔ QR cryptographic signature verified against SuRaksha directory.",
                    isPositive = true
                )
                ThreatSignalRow(
                    text = "✔ No fraud complaints or blacklist entries detected.",
                    isPositive = true
                )
            } else {
                reasons.forEach { reason ->
                    val isPos = reason.startsWith("✔") || reason.contains("clean", ignoreCase = true) || reason.contains("verified", ignoreCase = true)
                    val isCrit = reason.contains("tamper", ignoreCase = true) || reason.contains("blacklist", ignoreCase = true) || reason.contains("fraud", ignoreCase = true) || reason.contains("expired", ignoreCase = true)
                    ThreatSignalRow(
                        text = reason,
                        isPositive = isPos,
                        isCritical = isCrit
                    )
                }
            }
        }
    }
}

@Composable
private fun ThreatSignalRow(
    text: String,
    isPositive: Boolean = false,
    isCritical: Boolean = false
) {
    val tintColor = when {
        isCritical -> RiskCriticalRed
        isPositive -> RiskSafeGreen
        else -> RiskMediumYellow
    }

    val icon = when {
        isCritical -> Icons.Default.Error
        isPositive -> Icons.Default.CheckCircle
        else -> Icons.Default.Info
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.Top
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = tintColor,
            modifier = Modifier
                .size(16.dp)
                .padding(top = 2.dp)
        )
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = if (isCritical) RiskCriticalRed else MaterialTheme.colorScheme.onSurface
        )
    }
}

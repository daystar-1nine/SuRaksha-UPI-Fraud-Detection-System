package com.daystar.suraksha.ui.result

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.daystar.suraksha.data.models.QrRiskAnalysis
import com.daystar.suraksha.data.repository.HistoryRepository
import com.daystar.suraksha.security.ParsedUpiData
import com.daystar.suraksha.ui.components.RiskScoreGauge
import com.daystar.suraksha.ui.components.SuRakshaTopBar
import com.daystar.suraksha.ui.components.ThreatFactorCard
import com.daystar.suraksha.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun RiskResultScreen(
    parsedData: ParsedUpiData,
    analysis: QrRiskAnalysis,
    onBackToDashboard: () -> Unit,
    onScanAnother: () -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val historyRepository = remember { HistoryRepository(context) }

    var showPaymentDialog by remember { mutableStateOf(false) }
    var isReportingFraud by remember { mutableStateOf(false) }

    val isTampered = !analysis.constraints.signatureValid && analysis.constraints.isSigned
    val isExpired = analysis.constraints.isExpired
    val isCritical = analysis.riskScore >= 75 || isTampered || isExpired
    val isHigh = analysis.riskScore >= 50
    val isSafe = analysis.riskScore < 25 && !isTampered && !isExpired

    Scaffold(
        topBar = {
            SuRakshaTopBar(
                title = "Security Risk Analysis",
                showBack = true,
                onBackClick = onBackToDashboard
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            // Risk Gauge & Level
            RiskScoreGauge(
                score = analysis.riskScore,
                level = analysis.riskLevel,
                confidence = analysis.confidence
            )

            // Critical Tamper Alert Banner
            if (isTampered) {
                Surface(
                    shape = RoundedCornerShape(14.dp),
                    color = RiskCriticalRed.copy(alpha = 0.15f),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.GppBad,
                            contentDescription = "Tampered",
                            tint = RiskCriticalRed,
                            modifier = Modifier.size(24.dp)
                        )
                        Column {
                            Text(
                                text = "INVALID — QR DATA TAMPERED",
                                style = MaterialTheme.typography.titleMedium.copy(
                                    fontWeight = FontWeight.ExtraBold,
                                    fontSize = 13.sp
                                ),
                                color = RiskCriticalRed
                            )
                            Text(
                                text = "Cryptographic signature failed. Maximum payment limit or merchant identity was modified!",
                                style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp),
                                color = RiskCriticalRed.copy(alpha = 0.9f)
                            )
                        }
                    }
                }
            }

            // Payee Details & Constraint Summary Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
                )
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Payment Destination Details",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    DetailRow(label = "Payee VPA", value = parsedData.vpa.ifBlank { "Not Specified" })
                    DetailRow(label = "Merchant Name", value = parsedData.payeeName.ifBlank { "Recipient" })

                    // Mode Badge
                    val qrMode = analysis.constraints.qrMode ?: parsedData.qrMode
                    val maxAmount = analysis.constraints.maxAmount ?: parsedData.maxAmount
                    val fixedAmount = analysis.constraints.fixedAmount ?: parsedData.fixedAmount

                    when (qrMode) {
                        "max_limit" -> {
                            DetailRow(
                                label = "QR Protection Mode",
                                value = "Maximum Limit (Max ₹${"%,.2f".format(maxAmount ?: 0.0)})"
                            )
                        }
                        "fixed_amount" -> {
                            DetailRow(
                                label = "QR Protection Mode",
                                value = "Fixed Transaction (₹${"%,.2f".format(fixedAmount ?: 0.0)})"
                            )
                        }
                        else -> {
                            DetailRow(label = "QR Protection Mode", value = "Open Payment QR")
                        }
                    }

                    // Cryptographic Status
                    DetailRow(
                        label = "Cryptographic Shield",
                        value = if (analysis.constraints.signatureValid) "✔ Validated Signature (Shield Active)"
                        else if (analysis.constraints.isSigned) "❌ Tampered Signature"
                        else "Unsigned Static QR"
                    )
                }
            }

            // Threat Indicators Card
            ThreatFactorCard(
                reasons = analysis.reasons,
                isSafe = isSafe,
                isTampered = isTampered,
                isExpired = isExpired
            )

            // Action Buttons
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Proceed to Pay Button
                Button(
                    onClick = { showPaymentDialog = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isCritical) RiskHighOrange else SuRakshaBlue
                    )
                ) {
                    Text(
                        text = if (isCritical) "Bypass Warning & Pay Anyway" else "Proceed to Pay",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        color = Color.White
                    )
                }

                // Report Fraud Button (If High/Critical)
                if (isHigh || isCritical) {
                    OutlinedButton(
                        onClick = {
                            coroutineScope.launch {
                                isReportingFraud = true
                                val upi = parsedData.vpa.ifBlank { "unknown@upi" }
                                historyRepository.reportFraud(upi, "Reported via SuRaksha Android App")
                                isReportingFraud = false
                                Toast.makeText(context, "Fraud report submitted for $upi", Toast.LENGTH_SHORT).show()
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = RiskCriticalRed),
                        enabled = !isReportingFraud
                    ) {
                        if (isReportingFraud) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = RiskCriticalRed
                            )
                        } else {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(Icons.Default.Report, contentDescription = null, modifier = Modifier.size(18.dp))
                                Text("Report Merchant as Fraud", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                // Scan Another QR Button
                TextButton(
                    onClick = onScanAnother,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Scan Another QR Code", color = MaterialTheme.colorScheme.primary)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }

        // Payment Amount Validation Dialog
        if (showPaymentDialog) {
            PaymentValidationDialog(
                parsedData = parsedData,
                constraints = analysis.constraints,
                onDismiss = { showPaymentDialog = false }
            )
        }
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

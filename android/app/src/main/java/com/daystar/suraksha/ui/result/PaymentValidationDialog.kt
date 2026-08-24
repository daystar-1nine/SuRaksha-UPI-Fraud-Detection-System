package com.daystar.suraksha.ui.result

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.daystar.suraksha.data.models.QrConstraints
import com.daystar.suraksha.data.repository.QrRepository
import com.daystar.suraksha.security.ParsedUpiData
import com.daystar.suraksha.ui.theme.*
import kotlinx.coroutines.launch
import java.net.URLEncoder
import kotlin.math.roundToLong

@Composable
fun PaymentValidationDialog(
    parsedData: ParsedUpiData,
    constraints: QrConstraints,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val qrRepository = remember { QrRepository(context) }

    val qrMode = constraints.qrMode ?: parsedData.qrMode
    val maxLimit = constraints.maxAmount ?: parsedData.maxAmount
    val fixedAmount = constraints.fixedAmount ?: parsedData.fixedAmount

    var amountInput by remember {
        mutableStateOf(
            if (qrMode == "fixed_amount" && fixedAmount != null) "%.2f".format(fixedAmount) else ""
        )
    }

    var isValidating by remember { mutableStateOf(false) }
    var validationError by remember { mutableStateOf<String?>(null) }
    var validationSuccess by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Shield,
                    contentDescription = null,
                    tint = SuRakshaBlue
                )
                Text(
                    text = "SuRaksha Verified Payment",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                )
            }
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // Merchant Details Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Text(
                            text = parsedData.payeeName.ifBlank { "Merchant Store" },
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = parsedData.vpa,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                // Mode Info Banner
                when (qrMode) {
                    "max_limit" -> {
                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = RiskMediumYellow.copy(alpha = 0.15f),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Security,
                                    contentDescription = null,
                                    tint = RiskMediumYellow,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    text = "Maximum Allowed Limit: ₹${"%,.2f".format(maxLimit ?: 0.0)}\n(You can pay any amount from ₹1 up to ₹${"%,.2f".format(maxLimit ?: 0.0)})",
                                    style = MaterialTheme.typography.bodySmall.copy(
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.SemiBold
                                    ),
                                    color = RiskMediumYellow
                                )
                            }
                        }
                    }
                    "fixed_amount" -> {
                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = RiskLowBlue.copy(alpha = 0.15f),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Lock,
                                    contentDescription = null,
                                    tint = RiskLowBlue,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    text = "Fixed Amount QR: Exact ₹${"%,.2f".format(fixedAmount ?: 0.0)} required.",
                                    style = MaterialTheme.typography.bodySmall.copy(
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.SemiBold
                                    ),
                                    color = RiskLowBlue
                                )
                            }
                        }
                    }
                }

                // Amount Input
                OutlinedTextField(
                    value = amountInput,
                    onValueChange = {
                        if (qrMode != "fixed_amount") {
                            amountInput = it
                            validationError = null
                            validationSuccess = null
                        }
                    },
                    label = { Text("Payment Amount (₹)") },
                    placeholder = {
                        Text(if (maxLimit != null) "Enter amount (Max ₹$maxLimit)" else "Enter amount")
                    },
                    prefix = { Text("₹ ", fontWeight = FontWeight.Bold) },
                    readOnly = qrMode == "fixed_amount",
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    singleLine = true
                )

                // Validation Status
                if (validationError != null) {
                    Text(
                        text = "🛑 $validationError",
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                        color = RiskCriticalRed
                    )
                } else if (validationSuccess != null) {
                    Text(
                        text = "✅ $validationSuccess",
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                        color = RiskSafeGreen
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val amountVal = amountInput.toDoubleOrNull()
                    if (amountVal == null || amountVal <= 0) {
                        validationError = "Please enter a valid payment amount (> ₹0)"
                        return@Button
                    }

                    // Integer Paise Representation
                    val enteredPaise = (amountVal * 100).roundToLong()
                    val maxPaise = if (maxLimit != null) (maxLimit * 100).roundToLong() else null
                    val fixedPaise = if (fixedAmount != null) (fixedAmount * 100).roundToLong() else null

                    if (qrMode == "max_limit" && maxPaise != null && enteredPaise > maxPaise) {
                        validationError = "Amount exceeds the maximum limit of ₹${"%,.2f".format(maxLimit)}"
                        return@Button
                    }

                    if (qrMode == "fixed_amount" && fixedPaise != null && enteredPaise != fixedPaise) {
                        validationError = "Exact amount of ₹${"%,.2f".format(fixedAmount)} is required"
                        return@Button
                    }

                    // Pre-flight Backend Cryptographic Validation
                    coroutineScope.launch {
                        isValidating = true
                        validationError = null

                        val verifyRes = qrRepository.validatePaymentAmount(
                            qrPayload = parsedData.rawPayload,
                            amount = amountVal
                        )

                        isValidating = false

                        verifyRes.onSuccess { resData ->
                            if (resData.allowed) {
                                validationSuccess = "Pre-flight validation passed. Dispatching UPI payment..."
                                launchUpiIntent(context, parsedData.vpa, parsedData.payeeName, amountVal)
                                onDismiss()
                            } else {
                                validationError = resData.reason
                            }
                        }.onFailure { err ->
                            // Fallback to local validation if offline
                            validationSuccess = "Local check passed. Launching UPI..."
                            launchUpiIntent(context, parsedData.vpa, parsedData.payeeName, amountVal)
                            onDismiss()
                        }
                    }
                },
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue),
                enabled = !isValidating
            ) {
                if (isValidating) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = Color.White
                    )
                } else {
                    Text("Validate & Launch UPI", color = Color.White, fontWeight = FontWeight.Bold)
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

private fun launchUpiIntent(context: Context, vpa: String, payeeName: String, amount: Double) {
    try {
        val uri = Uri.parse(
            "upi://pay?pa=$vpa&pn=${URLEncoder.encode(payeeName, "UTF-8")}&am=%.2f&cu=INR&tn=SuRaksha%%20Verified%%20Payment".format(amount)
        )
        val intent = Intent(Intent.ACTION_VIEW, uri)
        context.startActivity(Intent.createChooser(intent, "Pay via UPI App"))
    } catch (e: Exception) {
        Toast.makeText(context, "No UPI App found. Simulated Payment of ₹$amount to $vpa", Toast.LENGTH_LONG).show()
    }
}

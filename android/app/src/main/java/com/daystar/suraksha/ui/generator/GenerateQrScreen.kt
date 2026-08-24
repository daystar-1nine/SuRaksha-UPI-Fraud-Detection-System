package com.daystar.suraksha.ui.generator

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.provider.MediaStore
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.daystar.suraksha.ui.components.SuRakshaTopBar
import com.daystar.suraksha.ui.theme.*
import java.io.ByteArrayOutputStream

@Composable
fun GenerateQrScreen(
    onBackClick: () -> Unit,
    viewModel: GenerateQrViewModel = viewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()

    var storeName by remember { mutableStateOf(viewModel.getDefaultStoreName()) }
    var vpa by remember { mutableStateOf(viewModel.getDefaultUserVpa()) }
    var selectedMode by remember { mutableStateOf("max_limit") } // "max_limit" vs "fixed_amount"
    var amountLimitInput by remember { mutableStateOf("10000") }
    var expiryHours by remember { mutableIntStateOf(24) }

    Scaffold(
        topBar = {
            SuRakshaTopBar(
                title = "Cryptographic QR Generator",
                showBack = true,
                onBackClick = onBackClick
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
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Description Banner
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = SuRakshaBlue.copy(alpha = 0.12f)
                )
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Shield,
                        contentDescription = null,
                        tint = SuRakshaBlue,
                        modifier = Modifier.size(24.dp)
                    )
                    Text(
                        text = "Create a cryptographically signed QR that limits transactions to an upper maximum or exact amount.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            // Input Fields
            OutlinedTextField(
                value = storeName,
                onValueChange = { storeName = it },
                label = { Text("Merchant / Store Name") },
                leadingIcon = { Icon(Icons.Default.Store, contentDescription = null) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                singleLine = true
            )

            OutlinedTextField(
                value = vpa,
                onValueChange = { vpa = it },
                label = { Text("Receive UPI VPA") },
                leadingIcon = { Icon(Icons.Default.AccountBalance, contentDescription = null) },
                placeholder = { Text("e.g. sharmakirana@upi") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                singleLine = true
            )

            // Protection Mode Selector
            Text(
                text = "QR Protection Mode",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                color = MaterialTheme.colorScheme.onBackground
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                FilterChip(
                    selected = selectedMode == "max_limit",
                    onClick = { selectedMode = "max_limit" },
                    label = {
                        Text(
                            "Maximum Limit QR",
                            fontWeight = if (selectedMode == "max_limit") FontWeight.Bold else FontWeight.Normal
                        )
                    },
                    leadingIcon = {
                        if (selectedMode == "max_limit") {
                            Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp))
                        }
                    },
                    modifier = Modifier.weight(1f)
                )

                FilterChip(
                    selected = selectedMode == "fixed_amount",
                    onClick = { selectedMode = "fixed_amount" },
                    label = {
                        Text(
                            "Fixed Amount QR",
                            fontWeight = if (selectedMode == "fixed_amount") FontWeight.Bold else FontWeight.Normal
                        )
                    },
                    leadingIcon = {
                        if (selectedMode == "fixed_amount") {
                            Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp))
                        }
                    },
                    modifier = Modifier.weight(1f)
                )
            }

            // Mode explainer
            Text(
                text = if (selectedMode == "max_limit")
                    "ℹ Customers can pay any amount from ₹1 up to your maximum limit (0 < Amount ≤ Limit)."
                else
                    "ℹ Customers must pay the exact transaction amount specified.",
                style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp),
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            // Amount Input
            OutlinedTextField(
                value = amountLimitInput,
                onValueChange = { amountLimitInput = it },
                label = { Text(if (selectedMode == "max_limit") "Maximum Payment Limit (₹)" else "Fixed Amount (₹)") },
                leadingIcon = { Icon(Icons.Default.CurrencyRupee, contentDescription = null) },
                prefix = { Text("₹ ", fontWeight = FontWeight.Bold) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                singleLine = true
            )

            // Generate Button
            Button(
                onClick = {
                    val amount = amountLimitInput.toDoubleOrNull() ?: 10000.0
                    viewModel.generateSecureQr(
                        vpa = vpa,
                        storeName = storeName,
                        mode = selectedMode,
                        amountLimit = amount,
                        expiryHours = expiryHours
                    )
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue),
                enabled = !uiState.isGenerating
            ) {
                if (uiState.isGenerating) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = Color.White
                    )
                } else {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(Icons.Default.QrCode, contentDescription = null)
                        Text(
                            "Generate Cryptographic QR",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = Color.White
                        )
                    }
                }
            }

            // Generated QR Display Card (Branded Merchant Standee)
            if (uiState.qrBitmap != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = DarkSurfaceCard
                    ),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = Brush.verticalGradient(
                            listOf(SuRakshaBlue, SuRakshaCyan.copy(alpha = 0.6f))
                        )
                    )
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        // Top Header: SuRaksha Shield & NPCI Badge
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(32.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(Brush.linearGradient(listOf(SuRakshaBlue, SuRakshaCyan))),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Shield,
                                        contentDescription = "Shield",
                                        tint = Color.White,
                                        modifier = Modifier.size(20.dp)
                                    )
                                }
                                Column {
                                    Text(
                                        text = "SURAKSHA AI",
                                        style = MaterialTheme.typography.titleMedium.copy(
                                            fontWeight = FontWeight.ExtraBold,
                                            fontSize = 13.sp,
                                            letterSpacing = 0.5.sp
                                        ),
                                        color = SuRakshaCyan
                                    )
                                    Text(
                                        text = "Zero-Trust Payment Shield",
                                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                                        color = DarkTextMuted
                                    )
                                }
                            }

                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = RiskSafeGreen.copy(alpha = 0.15f),
                                border = null
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Verified,
                                        contentDescription = null,
                                        tint = RiskSafeGreen,
                                        modifier = Modifier.size(12.dp)
                                    )
                                    Text(
                                        text = "NPCI COMPLIANT",
                                        style = MaterialTheme.typography.labelSmall.copy(
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 8.sp
                                        ),
                                        color = RiskSafeGreen
                                    )
                                }
                            }
                        }

                        // Storefront Name & VPA
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Text(
                                text = storeName,
                                style = MaterialTheme.typography.titleLarge.copy(
                                    fontWeight = FontWeight.ExtraBold,
                                    fontSize = 18.sp
                                ),
                                color = Color.White
                            )
                            Surface(
                                shape = RoundedCornerShape(10.dp),
                                color = Color.Black.copy(alpha = 0.4f),
                                border = null
                            ) {
                                Text(
                                    text = vpa,
                                    style = MaterialTheme.typography.bodySmall.copy(
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 11.sp
                                    ),
                                    color = SuRakshaCyan,
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                                )
                            }
                        }

                        // High-Contrast QR Code Card with Center Shield Badge
                        Box(
                            modifier = Modifier
                                .size(240.dp)
                                .clip(RoundedCornerShape(20.dp))
                                .background(Color.White)
                                .padding(12.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Image(
                                bitmap = uiState.qrBitmap!!.asImageBitmap(),
                                contentDescription = "Generated Secure QR",
                                modifier = Modifier.fillMaxSize()
                            )
                        }

                        // Security Limit Banner
                        Surface(
                            shape = RoundedCornerShape(14.dp),
                            color = SuRakshaBlue.copy(alpha = 0.15f),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.padding(10.dp),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(2.dp)
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Lock,
                                        contentDescription = null,
                                        tint = RiskMediumYellow,
                                        modifier = Modifier.size(14.dp)
                                    )
                                    Text(
                                        text = if (selectedMode == "max_limit")
                                            "MAXIMUM PAYMENT LIMIT: ₹$amountLimitInput"
                                        else
                                            "FIXED TRANSACTION: ₹$amountLimitInput",
                                        style = MaterialTheme.typography.labelSmall.copy(
                                            fontWeight = FontWeight.ExtraBold,
                                            fontSize = 11.sp
                                        ),
                                        color = RiskMediumYellow
                                    )
                                }
                                Text(
                                    text = if (selectedMode == "max_limit")
                                        "Payer can pay any amount ≤ ₹$amountLimitInput"
                                    else
                                        "Exact transaction amount required",
                                    style = MaterialTheme.typography.bodySmall.copy(fontSize = 9.sp),
                                    color = DarkTextMuted
                                )
                            }
                        }

                        // Accepted UPI Apps Strip
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Text(
                                text = "ACCEPTED PAYMENT APPLICATIONS",
                                style = MaterialTheme.typography.labelSmall.copy(
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 8.sp,
                                    letterSpacing = 0.8.sp
                                ),
                                color = DarkTextMuted
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.Center,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                val apps = listOf("Google Pay", "PhonePe", "Paytm", "BHIM", "Cred", "Amazon Pay")
                                Text(
                                    text = apps.joinToString("  •  "),
                                    style = MaterialTheme.typography.bodySmall.copy(
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 10.sp
                                    ),
                                    color = Color.White.copy(alpha = 0.85f)
                                )
                            }
                        }

                        // Cryptographic Signature Hash
                        if (uiState.signature != null) {
                            Text(
                                text = "CANONICAL SIGNATURE: ${uiState.signature!!.substring(0, 12)}...${uiState.signature!!.substring(uiState.signature!!.length - 8)}",
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                                color = SuRakshaCyan.copy(alpha = 0.75f)
                            )
                        }

                        // Action Buttons: Share & Save
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Button(
                                onClick = {
                                    shareQrBitmap(context, uiState.qrBitmap!!, storeName)
                                },
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue),
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Default.Share, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Share QR")
                            }

                            OutlinedButton(
                                onClick = {
                                    saveQrToGallery(context, uiState.qrBitmap!!, storeName)
                                },
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Default.Download, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Save Image")
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

private fun shareQrBitmap(context: Context, bitmap: Bitmap, title: String) {
    try {
        val path = MediaStore.Images.Media.insertImage(context.contentResolver, bitmap, "SuRaksha_QR_$title", "SuRaksha Cryptographic QR")
        val uri = Uri.parse(path)
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "image/png"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TEXT, "SuRaksha Cryptographically Signed UPI Payment QR for $title")
        }
        context.startActivity(Intent.createChooser(shareIntent, "Share SuRaksha QR"))
    } catch (e: Exception) {
        Toast.makeText(context, "QR ready to share", Toast.LENGTH_SHORT).show()
    }
}

private fun saveQrToGallery(context: Context, bitmap: Bitmap, title: String) {
    try {
        MediaStore.Images.Media.insertImage(context.contentResolver, bitmap, "SuRaksha_QR_$title", "SuRaksha Cryptographic QR")
        Toast.makeText(context, "QR saved to Photo Gallery!", Toast.LENGTH_SHORT).show()
    } catch (e: Exception) {
        Toast.makeText(context, "Error saving QR", Toast.LENGTH_SHORT).show()
    }
}

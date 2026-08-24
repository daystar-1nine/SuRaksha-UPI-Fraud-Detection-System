package com.daystar.suraksha.ui.verification

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Error
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.daystar.suraksha.data.models.QrRiskAnalysis
import com.daystar.suraksha.security.ParsedUpiData
import com.daystar.suraksha.ui.components.StagedVerificationView
import com.daystar.suraksha.ui.components.SuRakshaTopBar
import com.daystar.suraksha.ui.theme.RiskCriticalRed
import com.daystar.suraksha.ui.theme.SuRakshaBlue

@Composable
fun VerificationScreen(
    rawQrPayload: String,
    onVerificationComplete: (ParsedUpiData, QrRiskAnalysis) -> Unit,
    onBackClick: () -> Unit,
    viewModel: VerificationViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(rawQrPayload) {
        viewModel.startAnalysis(rawQrPayload)
    }

    LaunchedEffect(uiState) {
        if (uiState is VerificationUiState.Success) {
            val success = uiState as VerificationUiState.Success
            onVerificationComplete(success.parsedData, success.analysis)
        }
    }

    Scaffold(
        topBar = {
            SuRakshaTopBar(
                title = "Security Verification",
                showBack = true,
                onBackClick = onBackClick
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentAlignment = Alignment.Center
        ) {
            when (val state = uiState) {
                is VerificationUiState.Verifying -> {
                    StagedVerificationView(currentStage = state.stage)
                }
                is VerificationUiState.Error -> {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Error,
                            contentDescription = "Error",
                            tint = RiskCriticalRed,
                            modifier = Modifier.size(56.dp)
                        )
                        Text(
                            text = "Security Inspection Interrupted",
                            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onBackground
                        )
                        Text(
                            text = state.message,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Button(
                            onClick = { viewModel.startAnalysis(rawQrPayload) },
                            colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue)
                        ) {
                            Text("Retry Analysis", color = Color.White, fontWeight = FontWeight.Bold)
                        }
                    }
                }
                is VerificationUiState.Success -> {
                    // Automatically navigated
                }
            }
        }
    }
}

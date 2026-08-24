package com.daystar.suraksha.ui.verification

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.daystar.suraksha.data.models.QrRiskAnalysis
import com.daystar.suraksha.data.repository.QrRepository
import com.daystar.suraksha.security.ParsedUpiData
import com.daystar.suraksha.security.UpiDeepLinkParser
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class VerificationUiState {
    data class Verifying(val stage: Int, val parsedData: ParsedUpiData) : VerificationUiState()
    data class Success(val parsedData: ParsedUpiData, val analysis: QrRiskAnalysis) : VerificationUiState()
    data class Error(val message: String, val parsedData: ParsedUpiData) : VerificationUiState()
}

class VerificationViewModel(application: Application) : AndroidViewModel(application) {

    private val qrRepository = QrRepository(application)

    private val _uiState = MutableStateFlow<VerificationUiState>(
        VerificationUiState.Verifying(stage = 1, parsedData = ParsedUpiData(rawPayload = ""))
    )
    val uiState: StateFlow<VerificationUiState> = _uiState.asStateFlow()

    fun startAnalysis(rawQrPayload: String) {
        val parsed = UpiDeepLinkParser.parse(rawQrPayload)

        viewModelScope.launch {
            // Stage 1: Decoding
            _uiState.value = VerificationUiState.Verifying(stage = 1, parsedData = parsed)
            delay(350)

            // Stage 2: Cryptographic Signature check
            _uiState.value = VerificationUiState.Verifying(stage = 2, parsedData = parsed)
            delay(350)

            // Stage 3: Querying Threat Database
            _uiState.value = VerificationUiState.Verifying(stage = 3, parsedData = parsed)
            delay(350)

            // Stage 4: Calling Backend Risk Analyzer
            _uiState.value = VerificationUiState.Verifying(stage = 4, parsedData = parsed)

            val result = qrRepository.analyzeQr(rawQrPayload)
            result.onSuccess { analysis ->
                _uiState.value = VerificationUiState.Success(parsedData = parsed, analysis = analysis)
            }.onFailure { error ->
                _uiState.value = VerificationUiState.Error(
                    message = error.message ?: "Failed to connect to SuRaksha security service",
                    parsedData = parsed
                )
            }
        }
    }
}

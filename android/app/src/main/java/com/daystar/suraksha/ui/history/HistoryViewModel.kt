package com.daystar.suraksha.ui.history

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.daystar.suraksha.data.models.AnalysisHistoryItem
import com.daystar.suraksha.data.models.QrRecordItem
import com.daystar.suraksha.data.repository.HistoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HistoryUiState(
    val isLoading: Boolean = false,
    val analyses: List<AnalysisHistoryItem> = emptyList(),
    val qrCodes: List<QrRecordItem> = emptyList(),
    val errorMessage: String? = null
)

class HistoryViewModel(application: Application) : AndroidViewModel(application) {

    private val historyRepository = HistoryRepository(application)

    private val _uiState = MutableStateFlow(HistoryUiState())
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    init {
        fetchHistory()
    }

    fun fetchHistory() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            val result = historyRepository.fetchHistory()
            result.onSuccess { data ->
                _uiState.value = HistoryUiState(
                    isLoading = false,
                    analyses = data.analyses,
                    qrCodes = data.qrCodes
                )
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = error.message
                )
            }
        }
    }
}

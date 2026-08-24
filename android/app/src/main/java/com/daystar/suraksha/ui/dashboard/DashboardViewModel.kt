package com.daystar.suraksha.ui.dashboard

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.daystar.suraksha.data.models.AnalysisHistoryItem
import com.daystar.suraksha.data.models.UserProfile
import com.daystar.suraksha.data.repository.AuthRepository
import com.daystar.suraksha.data.repository.HistoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DashboardUiState(
    val isLoading: Boolean = false,
    val user: UserProfile? = null,
    val totalScans: Int = 0,
    val safeScans: Int = 0,
    val threatsBlocked: Int = 0,
    val registeredQrs: Int = 0,
    val recentScans: List<AnalysisHistoryItem> = emptyList(),
    val errorMessage: String? = null
)

class DashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val authRepository = AuthRepository(application)
    private val historyRepository = HistoryRepository(application)

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboardData()
    }

    fun loadDashboardData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)

            // 1. Load User
            val user = authRepository.getCachedUser()
            _uiState.value = _uiState.value.copy(user = user)

            // 2. Refresh from backend
            authRepository.fetchCurrentUser().onSuccess { updatedUser ->
                _uiState.value = _uiState.value.copy(user = updatedUser)
            }

            // 3. Load History and Metrics
            val historyRes = historyRepository.fetchHistory()
            historyRes.onSuccess { data ->
                val analyses = data.analyses
                val total = analyses.size
                val safe = analyses.count { it.riskScore < 25 && !it.isTampered }
                val threats = analyses.count { it.riskScore >= 25 || it.isTampered }
                val qrCount = data.qrCodes.size

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    totalScans = total,
                    safeScans = safe,
                    threatsBlocked = threats,
                    registeredQrs = qrCount,
                    recentScans = analyses.take(5)
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

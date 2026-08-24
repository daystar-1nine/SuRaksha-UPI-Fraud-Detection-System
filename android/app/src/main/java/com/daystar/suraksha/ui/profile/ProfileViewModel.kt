package com.daystar.suraksha.ui.profile

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.daystar.suraksha.data.models.UserProfile
import com.daystar.suraksha.data.repository.AuthRepository
import com.daystar.suraksha.security.TokenManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ProfileUiState(
    val isLoading: Boolean = false,
    val isUpdating: Boolean = false,
    val user: UserProfile? = null,
    val baseUrl: String = "",
    val successMessage: String? = null,
    val errorMessage: String? = null,
    val isLoggedOut: Boolean = false
)

class ProfileViewModel(application: Application) : AndroidViewModel(application) {

    private val authRepository = AuthRepository(application)
    private val tokenManager = TokenManager.getInstance(application)

    private val _uiState = MutableStateFlow(ProfileUiState(baseUrl = tokenManager.getBaseUrl()))
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    init {
        loadProfile()
    }

    fun loadProfile() {
        val cached = authRepository.getCachedUser()
        _uiState.value = _uiState.value.copy(user = cached, baseUrl = tokenManager.getBaseUrl())

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val result = authRepository.fetchCurrentUser()
            result.onSuccess { user ->
                _uiState.value = _uiState.value.copy(isLoading = false, user = user)
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }

    fun updateProfile(fullName: String, upiId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isUpdating = true, errorMessage = null, successMessage = null)
            val result = authRepository.updateProfile(fullName, upiId)
            result.onSuccess { updatedUser ->
                _uiState.value = _uiState.value.copy(
                    isUpdating = false,
                    user = updatedUser,
                    successMessage = "Profile updated and persisted successfully!"
                )
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(
                    isUpdating = false,
                    errorMessage = error.message ?: "Failed to update profile"
                )
            }
        }
    }

    fun updateBaseUrl(newUrl: String) {
        tokenManager.setBaseUrl(newUrl)
        _uiState.value = _uiState.value.copy(
            baseUrl = newUrl,
            successMessage = "API Endpoint updated to: $newUrl"
        )
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = _uiState.value.copy(isLoggedOut = true)
        }
    }
}

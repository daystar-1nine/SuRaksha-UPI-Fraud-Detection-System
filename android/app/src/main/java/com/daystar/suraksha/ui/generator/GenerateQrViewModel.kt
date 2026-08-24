package com.daystar.suraksha.ui.generator

import android.app.Application
import android.graphics.Bitmap
import android.graphics.Color as AndroidColor
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.daystar.suraksha.data.repository.AuthRepository
import com.daystar.suraksha.data.repository.QrRepository
import com.daystar.suraksha.security.CanonicalSigner
import com.google.zxing.BarcodeFormat
import com.google.zxing.qrcode.QRCodeWriter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.URLEncoder

data class GenerateQrUiState(
    val isGenerating: Boolean = false,
    val generatedPayload: String? = null,
    val qrBitmap: Bitmap? = null,
    val qrId: String? = null,
    val signature: String? = null,
    val successMessage: String? = null,
    val errorMessage: String? = null
)

class GenerateQrViewModel(application: Application) : AndroidViewModel(application) {

    private val authRepository = AuthRepository(application)
    private val qrRepository = QrRepository(application)

    private val _uiState = MutableStateFlow(GenerateQrUiState())
    val uiState: StateFlow<GenerateQrUiState> = _uiState.asStateFlow()

    fun getDefaultUserVpa(): String {
        return authRepository.getCachedUser()?.upiId ?: "sharmakirana@upi"
    }

    fun getDefaultStoreName(): String {
        return authRepository.getCachedUser()?.fullName ?: "Sharma Kirana Store"
    }

    fun generateSecureQr(
        vpa: String,
        storeName: String,
        mode: String, // "max_limit" or "fixed_amount"
        amountLimit: Double,
        expiryHours: Int = 24
    ) {
        if (vpa.isBlank() || storeName.isBlank() || amountLimit <= 0) {
            _uiState.value = _uiState.value.copy(errorMessage = "Please fill all required fields with valid values")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isGenerating = true, errorMessage = null, successMessage = null)

            val qrId = "SRK-${if (mode == "max_limit") "MAX" else "FIXED"}-${System.currentTimeMillis()}"
            val ts = "${System.currentTimeMillis() / 1000}"
            val exp = if (expiryHours > 0) "${(System.currentTimeMillis() / 1000) + (expiryHours * 3600)}" else ""

            val mamStr = if (mode == "max_limit") "%.2f".format(amountLimit) else ""
            val amStr = if (mode == "fixed_amount") "%.2f".format(amountLimit) else ""

            // Canonical SHA-256 Signature
            val signature = CanonicalSigner.computeSignature(
                vpa = vpa,
                name = storeName,
                mam = mamStr,
                am = amStr,
                cu = "INR",
                qrId = qrId,
                ts = ts,
                exp = exp
            )

            // Construct UPI URI Payload
            val encodedName = URLEncoder.encode(storeName, "UTF-8")
            val amountParam = if (mode == "max_limit") "&mam=$mamStr" else "&am=$amStr"
            val expParam = if (exp.isNotEmpty()) "&exp=$exp" else ""

            val payload = "upi://pay?pa=$vpa&pn=$encodedName$amountParam&cu=INR&qr_id=$qrId&ts=$ts$expParam&sign=$signature&tn=SuRaksha%20Verified%20Store"

            // Generate ZXing Bitmap in background thread
            val bitmap = withContext(Dispatchers.Default) {
                renderQrBitmap(payload)
            }

            // Persist to backend SQLite
            qrRepository.saveQrRecord(
                qrId = qrId,
                vpa = vpa,
                payeeName = storeName,
                qrMode = mode,
                maxAmount = if (mode == "max_limit") amountLimit else null,
                fixedAmount = if (mode == "fixed_amount") amountLimit else null,
                signature = signature,
                payload = payload
            )

            _uiState.value = GenerateQrUiState(
                isGenerating = false,
                generatedPayload = payload,
                qrBitmap = bitmap,
                qrId = qrId,
                signature = signature,
                successMessage = "Cryptographic QR generated and synced with SuRaksha Shield!"
            )
        }
    }

    private fun renderQrBitmap(content: String, size: Int = 600): Bitmap {
        val writer = QRCodeWriter()
        val bitMatrix = writer.encode(content, BarcodeFormat.QR_CODE, size, size)
        val width = bitMatrix.width
        val height = bitMatrix.height
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565)
        for (x in 0 until width) {
            for (y in 0 until height) {
                bitmap.setPixel(x, y, if (bitMatrix[x, y]) AndroidColor.BLACK else AndroidColor.WHITE)
            }
        }
        return bitmap
    }
}

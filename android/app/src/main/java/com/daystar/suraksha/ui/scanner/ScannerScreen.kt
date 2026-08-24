package com.daystar.suraksha.ui.scanner

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.daystar.suraksha.security.CanonicalSigner
import com.daystar.suraksha.ui.theme.*
import java.net.URLEncoder

@Composable
fun ScannerScreen(
    onQrScanned: (String) -> Unit,
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { granted ->
            hasCameraPermission = granted
        }
    )

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    var isTorchOn by remember { mutableStateOf(false) }
    var cameraControl: androidx.camera.core.CameraControl? by remember { mutableStateOf(null) }

    Scaffold(
        containerColor = Color.Black
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (hasCameraPermission) {
                // CameraX Preview
                AndroidView(
                    factory = { ctx ->
                        val previewView = PreviewView(ctx)
                        val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)

                        cameraProviderFuture.addListener({
                            val cameraProvider = cameraProviderFuture.get()
                            val preview = Preview.Builder().build().also {
                                it.surfaceProvider = previewView.surfaceProvider
                            }

                            val imageAnalysis = ImageAnalysis.Builder()
                                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                .build()

                            val analyzer = QrCodeAnalyzer { qrText ->
                                onQrScanned(qrText)
                            }
                            imageAnalysis.setAnalyzer(ContextCompat.getMainExecutor(ctx), analyzer)

                            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

                            try {
                                cameraProvider.unbindAll()
                                val camera = cameraProvider.bindToLifecycle(
                                    lifecycleOwner,
                                    cameraSelector,
                                    preview,
                                    imageAnalysis
                                )
                                cameraControl = camera.cameraControl
                            } catch (e: Exception) {
                                e.printStackTrace()
                            }
                        }, ContextCompat.getMainExecutor(ctx))

                        previewView
                    },
                    modifier = Modifier.fillMaxSize()
                )

                // Animated Scanner Viewfinder Overlay
                ScannerOverlay(
                    modifier = Modifier.fillMaxSize()
                )

            } else {
                // Permission Denied View
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.CameraAlt,
                        contentDescription = "Camera Permission",
                        tint = SuRakshaCyan,
                        modifier = Modifier.size(64.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Camera Permission Required",
                        style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "SuRaksha needs camera access to scan physical QR codes and merchant payment stickers.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.7f),
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                    Button(
                        onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) },
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue)
                    ) {
                        Text("Grant Camera Access", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }
            }

            // Top Navigation Controls
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 20.dp)
                    .align(Alignment.TopCenter),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = onBackClick,
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(Color.Black.copy(alpha = 0.5f))
                ) {
                    Icon(
                        imageVector = Icons.Default.ArrowBack,
                        contentDescription = "Back",
                        tint = Color.White
                    )
                }

                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color.Black.copy(alpha = 0.5f)
                ) {
                    Text(
                        text = "Scan UPI QR Code",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp)
                    )
                }

                IconButton(
                    onClick = {
                        isTorchOn = !isTorchOn
                        cameraControl?.enableTorch(isTorchOn)
                    },
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(Color.Black.copy(alpha = 0.5f))
                ) {
                    Icon(
                        imageVector = if (isTorchOn) Icons.Default.FlashOn else Icons.Default.FlashOff,
                        contentDescription = "Flashlight",
                        tint = if (isTorchOn) Color.Yellow else Color.White
                    )
                }
            }

            // Bottom Quick Test Simulator Toolbar (For Demonstration)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .align(Alignment.BottomCenter)
                    .background(
                        Brush.verticalGradient(
                            listOf(Color.Transparent, Color.Black.copy(alpha = 0.85f), Color.Black)
                        )
                    )
                    .padding(horizontal = 16.dp, vertical = 20.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = "Quick Demo Scenarios",
                    style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                    color = Color.White.copy(alpha = 0.7f)
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 1. Max Limit QR Sample
                    Button(
                        onClick = {
                            val vpa = "sharmakirana@upi"
                            val name = "Sharma Kirana Store"
                            val mam = "10000"
                            val qid = "SRK-MAX-DEMO"
                            val ts = "${System.currentTimeMillis() / 1000}"
                            val sign = CanonicalSigner.computeSignature(
                                vpa = vpa, name = name, mam = mam, qrId = qid, ts = ts
                            )
                            val payload = "upi://pay?pa=$vpa&pn=${URLEncoder.encode(name, "UTF-8")}&mam=$mam&cu=INR&qr_id=$qid&ts=$ts&sign=$sign&tn=SuRaksha%20Verified%20Store"
                            onQrScanned(payload)
                        },
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = SuRakshaBlue.copy(alpha = 0.85f)),
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 8.dp)
                    ) {
                        Text("Max ₹10k Limit", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    }

                    // 2. Fixed Amount QR Sample
                    Button(
                        onClick = {
                            val vpa = "sharmakirana@upi"
                            val name = "Sharma Kirana Store"
                            val am = "500"
                            val qid = "SRK-FIXED-DEMO"
                            val ts = "${System.currentTimeMillis() / 1000}"
                            val sign = CanonicalSigner.computeSignature(
                                vpa = vpa, name = name, am = am, qrId = qid, ts = ts
                            )
                            val payload = "upi://pay?pa=$vpa&pn=${URLEncoder.encode(name, "UTF-8")}&am=$am&cu=INR&qr_id=$qid&ts=$ts&sign=$sign&tn=SuRaksha%20Verified%20Store"
                            onQrScanned(payload)
                        },
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = RiskSafeGreen.copy(alpha = 0.85f)),
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 8.dp)
                    ) {
                        Text("Fixed ₹500 QR", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    }

                    // 3. Tampered QR Sample
                    Button(
                        onClick = {
                            val vpa = "sharmakirana@upi"
                            val name = "Sharma Kirana Store"
                            val mam = "10000"
                            val qid = "SRK-MAX-DEMO"
                            val ts = "${System.currentTimeMillis() / 1000}"
                            val originalSign = CanonicalSigner.computeSignature(
                                vpa = vpa, name = name, mam = mam, qrId = qid, ts = ts
                            )
                            // Tamper: Changed mam to 50000 while keeping original signature!
                            val tamperedPayload = "upi://pay?pa=$vpa&pn=${URLEncoder.encode(name, "UTF-8")}&mam=50000&cu=INR&qr_id=$qid&ts=$ts&sign=$originalSign&tn=SuRaksha%20Verified%20Store"
                            onQrScanned(tamperedPayload)
                        },
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = RiskCriticalRed.copy(alpha = 0.85f)),
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 8.dp)
                    ) {
                        Text("Tampered QR", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        }
    }
}

@Composable
private fun ScannerOverlay(modifier: Modifier = Modifier) {
    val infiniteTransition = rememberInfiniteTransition(label = "scan_laser")
    val laserY by infiniteTransition.animateFloat(
        initialValue = 0.15f,
        targetValue = 0.85f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "laser_anim"
    )

    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height
        val boxSize = width * 0.72f
        val left = (width - boxSize) / 2
        val top = (height - boxSize) / 2.5f

        // Draw Darkened Scrim around viewfinder box
        drawRect(
            color = Color.Black.copy(alpha = 0.55f),
            size = Size(width, height)
        )

        // Clear center transparent viewfinder box
        drawRoundRect(
            color = Color.Transparent,
            topLeft = Offset(left, top),
            size = Size(boxSize, boxSize),
            cornerRadius = CornerRadius(24.dp.toPx()),
            blendMode = BlendMode.Clear
        )

        // Viewfinder Border
        drawRoundRect(
            color = SuRakshaCyan.copy(alpha = 0.8f),
            topLeft = Offset(left, top),
            size = Size(boxSize, boxSize),
            cornerRadius = CornerRadius(24.dp.toPx()),
            style = Stroke(width = 3.dp.toPx())
        )

        // Corner Highlights
        val cornerLength = 36.dp.toPx()
        val cornerStroke = 5.dp.toPx()

        // Top Left
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(left, top + cornerLength),
            end = Offset(left, top + 12.dp.toPx()),
            strokeWidth = cornerStroke
        )
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(left + 12.dp.toPx(), top),
            end = Offset(left + cornerLength, top),
            strokeWidth = cornerStroke
        )

        // Top Right
        val right = left + boxSize
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(right, top + cornerLength),
            end = Offset(right, top + 12.dp.toPx()),
            strokeWidth = cornerStroke
        )
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(right - 12.dp.toPx(), top),
            end = Offset(right - cornerLength, top),
            strokeWidth = cornerStroke
        )

        // Bottom Left
        val bottom = top + boxSize
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(left, bottom - cornerLength),
            end = Offset(left, bottom - 12.dp.toPx()),
            strokeWidth = cornerStroke
        )
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(left + 12.dp.toPx(), bottom),
            end = Offset(left + cornerLength, bottom),
            strokeWidth = cornerStroke
        )

        // Bottom Right
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(right, bottom - cornerLength),
            end = Offset(right, bottom - 12.dp.toPx()),
            strokeWidth = cornerStroke
        )
        drawLine(
            color = SuRakshaBlueLight,
            start = Offset(right - 12.dp.toPx(), bottom),
            end = Offset(right - cornerLength, bottom),
            strokeWidth = cornerStroke
        )

        // Animated Scanning Laser Beam
        val laserPos = top + (boxSize * laserY)
        drawLine(
            brush = Brush.horizontalGradient(
                listOf(Color.Transparent, SuRakshaCyan, Color.White, SuRakshaCyan, Color.Transparent),
                startX = left,
                endX = right
            ),
            start = Offset(left + 8.dp.toPx(), laserPos),
            end = Offset(right - 8.dp.toPx(), laserPos),
            strokeWidth = 3.5.dp.toPx()
        )
    }
}

package com.daystar.suraksha;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView webView = (WebView) this.bridge.getWebView();
        if (webView != null) {
            // Auto-grant camera video stream permissions in WebView
            webView.setWebChromeClient(new WebChromeClient() {
                @Override
                public void onPermissionRequest(final PermissionRequest request) {
                    runOnUiThread(() -> {
                        request.grant(request.getResources());
                    });
                }
            });

            // Native Intent Interceptor for App-Specific UPI Deep-Links (Google Pay, PhonePe, Paytm, BHIM, FamPay, POP, CRED, Amazon Pay)
            webView.setWebViewClient(new WebViewClient() {
                @Override
                public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                    Uri uri = request.getUrl();
                    if (uri != null) {
                        String url = uri.toString();
                        if (url.startsWith("intent://") || url.startsWith("upi://") || 
                            url.startsWith("gpay://") || url.startsWith("tez://") ||
                            url.startsWith("phonepe://") || url.startsWith("paytmmp://") || url.startsWith("paytm://") ||
                            url.startsWith("bhim://") || url.startsWith("fampay://") || 
                            url.startsWith("pop://") || url.startsWith("cred://") || url.startsWith("amazonpay://")) {
                            
                            try {
                                Intent intent;
                                String pkgName = null;
                                if (url.startsWith("intent://")) {
                                    intent = Intent.parseUri(url, Intent.URI_INTENT_SCHEME);
                                    if (intent != null) {
                                        pkgName = intent.getPackage();
                                    }
                                } else {
                                    intent = new Intent(Intent.ACTION_VIEW, uri);
                                }
                                
                                if (intent != null) {
                                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                                    try {
                                        startActivity(intent);
                                    } catch (ActivityNotFoundException notFoundErr) {
                                        if (pkgName != null) {
                                            try {
                                                Intent storeIntent = new Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=" + pkgName));
                                                storeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                                                startActivity(storeIntent);
                                            } catch (Exception ex) {
                                                Toast.makeText(MainActivity.this, "Selected payment app is not installed on this device.", Toast.LENGTH_LONG).show();
                                            }
                                        } else {
                                            Toast.makeText(MainActivity.this, "Selected payment app is not installed on this device.", Toast.LENGTH_LONG).show();
                                        }
                                    }
                                    return true; // Handled natively by Intent launcher!
                                }
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }
                    }
                    return super.shouldOverrideUrlLoading(view, request);
                }
            });
        }
    }
}

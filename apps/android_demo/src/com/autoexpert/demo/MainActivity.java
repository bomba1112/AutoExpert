package com.autoexpert.demo;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.JavascriptInterface;
import android.util.Base64;
import android.widget.Toast;
import android.widget.FrameLayout;

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public final class MainActivity extends Activity {
    private static final String LOCAL_HOST = "appassets.autoexpert.local";
    private static final String START_URL = "https://" + LOCAL_HOST + "/preview/";
    private WebView webView;
    private byte[] pendingPdf;
    private static final int SAVE_PDF = 620;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.parseColor("#101922"));
        getWindow().setNavigationBarColor(Color.parseColor("#0B1117"));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#F3F6F7"));
        configureWebView(webView);
        FrameLayout content = new FrameLayout(this);
        content.setBackgroundColor(Color.parseColor("#101922"));
        content.addView(webView, new FrameLayout.LayoutParams(-1, -1));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            content.setOnApplyWindowInsetsListener((view, insets) -> {
                Insets safe = insets.getInsets(WindowInsets.Type.systemBars()
                        | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                view.setPadding(safe.left, safe.top, safe.right, safe.bottom);
                return WindowInsets.CONSUMED;
            });
        }
        setContentView(content);
        content.requestApplyInsets();
        webView.loadUrl(START_URL);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.getSettings().setTextZoom(
                    Math.round(getResources().getConfiguration().fontScale * 100));
        }
    }

    private void configureWebView(WebView view) {
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setUserAgentString(
                settings.getUserAgentString() + " AutoExpertAndroidAlpha/0.8.1");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            settings.setSafeBrowsingEnabled(true);
        }
        WebView.setWebContentsDebuggingEnabled(true);
        view.addJavascriptInterface(new ReportFiles(), "AutoExpertFiles");
        view.setWebViewClient(new PackagedAssetClient(getAssets(), getString(R.string.api_base_url)));
    }

    private final class ReportFiles {
        @JavascriptInterface
        public void savePdf(String filename, String encoded) {
            if (encoded == null || encoded.length() > 28 * 1024 * 1024) return;
            final byte[] bytes;
            try { bytes = Base64.decode(encoded, Base64.DEFAULT); }
            catch (IllegalArgumentException error) { return; }
            if (bytes.length < 5 || !new String(bytes, 0, 5, StandardCharsets.US_ASCII).equals("%PDF-")) return;
            runOnUiThread(() -> {
                if (webView == null || webView.getUrl() == null
                        || !webView.getUrl().startsWith(START_URL) || pendingPdf != null) return;
                pendingPdf = bytes;
                Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                save.addCategory(Intent.CATEGORY_OPENABLE);
                save.setType("application/pdf");
                save.putExtra(Intent.EXTRA_TITLE, filename.replaceAll("[^A-Za-z0-9_.-]", "_"));
                try { startActivityForResult(save, SAVE_PDF); }
                catch (RuntimeException error) { pendingPdf = null; }
            });
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != SAVE_PDF) return;
        byte[] bytes = pendingPdf;
        pendingPdf = null;
        if (resultCode != RESULT_OK || data == null || data.getData() == null || bytes == null) return;
        try (OutputStream output = getContentResolver().openOutputStream(data.getData())) {
            if (output != null) output.write(bytes);
            Toast.makeText(this, "PDF ✓", Toast.LENGTH_SHORT).show();
        } catch (IOException error) {
            Toast.makeText(this, "PDF ×", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    private final class PackagedAssetClient extends WebViewClient {
        private final AssetManager assets;
        private final String apiBaseUrl;
        private final String apiOrigin;

        private PackagedAssetClient(AssetManager assets, String apiBaseUrl) {
            this.assets = assets;
            this.apiBaseUrl = apiBaseUrl;
            Uri apiUri = Uri.parse(apiBaseUrl);
            this.apiOrigin = apiUri.getScheme() + "://" + apiUri.getAuthority();
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return false;
            }
            String scheme = uri.getScheme();
            if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (RuntimeException ignored) {
                    // Keep the report open when no external browser can handle the source URL.
                }
            } else if (Settings.ACTION_APPLICATION_DETAILS_SETTINGS.equals(uri.toString())) {
                startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS));
            }
            return true;
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(
                WebView view,
                WebResourceRequest request
        ) {
            Uri uri = request.getUrl();
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return null;
            }
            if (!"GET".equalsIgnoreCase(request.getMethod())) {
                return response(405, "Method Not Allowed", "text/plain", "Method Not Allowed");
            }
            String path = uri.getPath();
            if (path == null || !path.startsWith("/preview")) {
                return response(403, "Forbidden", "text/plain", "Forbidden");
            }
            String assetPath = path.equals("/preview") || path.equals("/preview/")
                    ? "preview/index.html"
                    : path.substring(1);
            return serveAsset(assetPath);
        }

        private WebResourceResponse serveAsset(String assetPath) {
            try {
                byte[] bytes = readAll(assets.open(assetPath));
                if ("preview/index.html".equals(assetPath)) {
                    String html = new String(bytes, StandardCharsets.UTF_8);
                    String runtimeConfig = "<script>window.AUTOEXPERT_API_ROOT="
                            + JSONObject.quote(apiBaseUrl)
                            + ";window.AUTOEXPERT_ANDROID_ALPHA=true;</script>";
                    html = html.replace("<!-- AUTOEXPERT_RUNTIME_CONFIG -->", runtimeConfig);
                    bytes = html.getBytes(StandardCharsets.UTF_8);
                }
                Map<String, String> headers = new HashMap<>();
                headers.put("Cache-Control", assetPath.endsWith("index.html")
                        ? "no-store" : "max-age=300");
                headers.put("X-Content-Type-Options", "nosniff");
                headers.put(
                        "Content-Security-Policy",
                        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                + "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; "
                                + "connect-src 'self' " + apiOrigin + "; object-src 'none'; "
                                + "base-uri 'self'; frame-ancestors 'none'"
                );
                return new WebResourceResponse(
                        mimeType(assetPath),
                        isText(assetPath) ? "UTF-8" : null,
                        200,
                        "OK",
                        headers,
                        new ByteArrayInputStream(bytes)
                );
            } catch (IOException error) {
                return response(404, "Not Found", "text/plain", "Not found");
            }
        }

        private WebResourceResponse response(
                int status,
                String reason,
                String mimeType,
                String body
        ) {
            return new WebResourceResponse(
                    mimeType,
                    "UTF-8",
                    status,
                    reason,
                    Collections.singletonMap("Cache-Control", "no-store"),
                    new ByteArrayInputStream(body.getBytes(StandardCharsets.UTF_8))
            );
        }
    }

    private static byte[] readAll(InputStream input) throws IOException {
        try (InputStream source = input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = source.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }

    private static boolean isText(String path) {
        String lower = path.toLowerCase(Locale.ROOT);
        return lower.endsWith(".html")
                || lower.endsWith(".css")
                || lower.endsWith(".js")
                || lower.endsWith(".json")
                || lower.endsWith(".svg")
                || lower.endsWith(".txt")
                || lower.endsWith(".webmanifest");
    }

    private static String mimeType(String path) {
        String lower = path.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".html")) return "text/html";
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".js")) return "application/javascript";
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".svg")) return "image/svg+xml";
        if (lower.endsWith(".webmanifest")) return "application/manifest+json";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        return "application/octet-stream";
    }
}

package com.xfunnote.xfunnote

import android.content.Intent
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ImageButton
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 启动常驻后台服务（前台服务，防止被系统杀掉）
        ContextCompat.startForegroundService(this, Intent(this, ServerService::class.java))

        val webView = findViewById<WebView>(R.id.webview)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = false
        webView.webViewClient = WebViewClient()
        webView.loadUrl("http://127.0.0.1:8080")

        setupDraggableFab(findViewById(R.id.fab))
    }

    private fun setupDraggableFab(fab: ImageButton) {
        var dX = 0f
        var dY = 0f
        var downX = 0f
        var downY = 0f
        var moved = false

        fab.setOnTouchListener { v, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    dX = v.x - event.rawX
                    dY = v.y - event.rawY
                    downX = event.rawX
                    downY = event.rawY
                    moved = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    v.x = event.rawX + dX
                    v.y = event.rawY + dY
                    if (kotlin.math.abs(event.rawX - downX) > 8 ||
                        kotlin.math.abs(event.rawY - downY) > 8
                    ) {
                        moved = true
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    // 拖动结束且几乎未移动 -> 视为点击
                    if (!moved) {
                        startActivity(Intent(this, ManagementActivity::class.java))
                    }
                    v.performClick()
                    true
                }
                else -> false
            }
        }
    }

    override fun onBackPressed() {
        val webView = findViewById<WebView>(R.id.webview)
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}

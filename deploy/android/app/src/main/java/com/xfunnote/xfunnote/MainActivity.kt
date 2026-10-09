package com.xfunnote.xfunnote

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MotionEvent
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ImageButton
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.net.InetSocketAddress
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val mainHandler = Handler(Looper.getMainLooper())
    private var pollAttempts = 0
    private var pageLoaded = false

    private companion object {
        const val START_URL = "http://127.0.0.1:8080"
        const val HOST = "127.0.0.1"
        const val PORT = 8080
        const val POLL_INTERVAL_MS = 500L
        const val MAX_POLLS = 120 // 60s 上限
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 启动常驻后台服务（前台服务，防止被系统杀掉）
        ContextCompat.startForegroundService(this, Intent(this, ServerService::class.java))

        webView = findViewById(R.id.webview)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = false
        // 就绪前 WebView 保持窗口黑背景（xfun_bg），不做任何加载
        webView.webViewClient = WebViewClient()
        pollServerReady()

        setupDraggableFab(findViewById(R.id.fab))
    }

    /** 后台线程探测端口就绪；就绪后回主线程一次性加载，避免错误页闪烁。 */
    private fun pollServerReady() {
        if (pageLoaded || pollAttempts >= MAX_POLLS) return
        pollAttempts++
        Thread {
            var ready = false
            try {
                Socket().use { s ->
                    s.connect(InetSocketAddress(HOST, PORT), 400)
                    ready = true
                }
            } catch (_: Exception) {
            }
            mainHandler.post {
                if (pageLoaded) return@post
                if (ready) {
                    pageLoaded = true
                    webView.loadUrl(START_URL)
                } else {
                    pollServerReady()
                }
            }
        }.start()
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
        // 仅在 SPA 内有更早历史时后退；退到初始条目（黑屏占位）即直接退出应用
        val list = webView.copyBackForwardList()
        if (list.currentIndex > 0 && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}

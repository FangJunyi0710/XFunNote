package com.xfunnote.xfunnote

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.MotionEvent
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ImageButton
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    private companion object {
        const val START_URL = "file:///android_asset/www/index.html"
        const val PREFS = "xfun_prefs"
        const val KEY_ROOT_TOKEN = "root_token"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true      // 前端 zustand persist 依赖 localStorage
            allowFileAccess = true        // file:// 子资源（相对路径 assets）
            allowContentAccess = true
        }

        // 本地模式：注入 JS 桥，WebView 进程内直调共享 :core，不经过任何 HTTP/端口
        XFunBridge.configure(File(filesDir, "data"), bootstrapRootToken())
        webView.addJavascriptInterface(XFunBridge(), "XFunBridge")

        webView.webViewClient = WebViewClient()
        webView.loadUrl(START_URL)

        setupDraggableFab(findViewById(R.id.fab))
    }

    /** 每份安装生成并持久化一个本机 root token（仅本地可信设备用于自举建库/建 token）。 */
    private fun bootstrapRootToken(): String {
        val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        prefs.getString(KEY_ROOT_TOKEN, null)?.let { return it }
        val token = "sk-" + UUID.randomUUID().toString().replace("-", "")
        prefs.edit().putString(KEY_ROOT_TOKEN, token).apply()
        return token
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
        // 仅在 SPA 内有更早历史时后退；退到初始条目即直接退出应用
        val list = webView.copyBackForwardList()
        if (list.currentIndex > 0 && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}

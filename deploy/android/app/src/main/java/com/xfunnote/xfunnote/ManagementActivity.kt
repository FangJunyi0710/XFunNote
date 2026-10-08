package com.xfunnote.xfunnote

import android.app.AlertDialog
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.io.File
import java.util.UUID

class ManagementActivity : AppCompatActivity() {

    private val xfunDataDir by lazy { File(getFilesDir(), "data") }
    private val envFile by lazy { File(xfunDataDir, ".env") }
    private val dbFile by lazy { File(xfunDataDir, "default.db") }
    private val logFile by lazy { File(xfunDataDir, ".xfunnote.log") }

    private val exportLauncher = registerForActivityResult(
        ActivityResultContracts.CreateDocument("*/*")
    ) { uri ->
        uri ?: return@registerForActivityResult
        if (dbFile.exists()) {
            contentResolver.openOutputStream(uri)?.use { os ->
                dbFile.inputStream().use { it.copyTo(os) }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_management)

        findViewById<Button>(R.id.btn_open).setOnClickListener {
            startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse("http://127.0.0.1:8080"))
            )
        }

        findViewById<Button>(R.id.btn_restart).setOnClickListener {
            val intent = Intent(this, ServerService::class.java)
            stopService(intent)
            ContextCompat.startForegroundService(this, intent)
            setStatus("服务已请求重启")
        }

        findViewById<Button>(R.id.btn_root).setOnClickListener {
            val token = "sk-" + UUID.randomUUID().toString().replace("-", "")
            updateEnv("ROOT_TOKEN", token)
            showText("已设置 ROOT_TOKEN（需重启服务生效）：\n$token")
        }

        findViewById<Button>(R.id.btn_llm).setOnClickListener {
            promptLlmConfig()
        }

        findViewById<Button>(R.id.btn_export).setOnClickListener {
            exportLauncher.launch("xfunnote_default.db")
        }

        findViewById<Button>(R.id.btn_logs).setOnClickListener {
            showLogs()
        }

        setStatus("状态：服务运行中（端口 8080）")
    }

    private fun setStatus(text: String) {
        findViewById<TextView>(R.id.tv_status).text = text
    }

    private fun showText(text: String) {
        findViewById<TextView>(R.id.tv_log).text = text
    }

    private fun showLogs() {
        val log = if (logFile.exists()) {
            logFile.readLines().takeLast(200).joinToString("\n")
        } else "尚无日志"
        findViewById<TextView>(R.id.tv_log).text = log
    }

    private fun updateEnv(key: String, value: String) {
        xfunDataDir.mkdirs()
        val kv = mutableMapOf<String, String>()
        if (envFile.exists()) {
            envFile.readLines().forEach { line ->
                val idx = line.indexOf('=')
                if (idx > 0) kv[line.substring(0, idx).trim()] = line.substring(idx + 1).trim()
            }
        }
        kv[key] = value
        envFile.writeText(kv.map { "${it.key}=${it.value}" }.joinToString("\n") + "\n")
    }

    private fun promptLlmConfig() {
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(50, 40, 50, 10)
        }
        val keyInput = EditText(this).apply { hint = "LLM_API_KEY" }
        val modelInput = EditText(this).apply { hint = "LLM_MODEL (如 deepseek-v4-flash)" }
        val urlInput = EditText(this).apply { hint = "LLM_BASE_URL" }
        layout.addView(keyInput); layout.addView(modelInput); layout.addView(urlInput)

        AlertDialog.Builder(this)
            .setTitle("配置 LLM")
            .setView(layout)
            .setPositiveButton("保存") { _, _ ->
                keyInput.text.toString().takeIf { it.isNotBlank() }?.let { updateEnv("LLM_API_KEY", it) }
                modelInput.text.toString().takeIf { it.isNotBlank() }?.let { updateEnv("LLM_MODEL", it) }
                urlInput.text.toString().takeIf { it.isNotBlank() }?.let { updateEnv("LLM_BASE_URL", it) }
                showText("已保存（需重启服务生效）")
            }
            .setNegativeButton("取消", null)
            .show()
    }
}

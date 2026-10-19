package com.xfunnote.xfunnote

import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import java.io.File

class ManagementActivity : AppCompatActivity() {

    private val xfunDataDir by lazy { File(getFilesDir(), "data") }
    private val dbFile by lazy { File(xfunDataDir, "default.db") }

    private val exportLauncher = registerForActivityResult(
        ActivityResultContracts.CreateDocument("*/*")
    ) { uri: Uri? ->
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

        // 本地模式：隐藏 Python 服务器时代的无效控件（重启服务/打开http/改.env/LLM/日志）
        listOf(R.id.btn_open, R.id.btn_restart, R.id.btn_root, R.id.btn_llm, R.id.btn_logs)
            .forEach { findViewById<View>(it).visibility = View.GONE }

        findViewById<Button>(R.id.btn_export).setOnClickListener {
            exportLauncher.launch("xfunnote_default.db")
        }
        setStatus("本地模式：数据存于应用私有目录，可导出 default.db")
    }

    private fun setStatus(text: String) {
        findViewById<TextView>(R.id.tv_status).text = text
    }
}

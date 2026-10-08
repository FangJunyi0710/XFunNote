package com.xfunnote.xfunnote

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class ServerService : Service() {

    private var started = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIF_ID, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!started) {
            started = true
            Thread { startPythonServer() }.start()
        }
        // START_STICKY：被系统回收后自动重启，配合前台通知尽量保活
        return START_STICKY
    }

    private fun startPythonServer() {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        val py = Python.getInstance()
        val dataDir = getFilesDir().toString() + "/data"
        // 必须在导入 backend.main 之前设置数据目录
        // Android 普通应用无法绑定特权端口，前端服务器改用 8080（后端 API 仍在 127.0.0.1:8000）
        // 说明：不能用 builtins.exec（Java 线程无 Python frame，会报 "frame does not exist"），
        // 改为直接对 os.environ 赋值。
        val environ = py.getModule("os").get("environ")!!
        environ.callAttr("__setitem__", "XFUN_DATA_DIR", dataDir)
        environ.callAttr("__setitem__", "VITE_HTTP_PORT", "8080")
        environ.callAttr("__setitem__", "VITE_HTTPS_PORT", "8443")
        val embeddedServer = py.getModule("backend.embedded_server")
        // 阻塞在当前线程，作为常驻服务（前端 8080 代理 /api 到后端 8000）
        embeddedServer.callAttr("run_server", "0.0.0.0")
    }

    private fun buildNotification(): Notification {
        val chan = "xfunnote_service"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val mgr = getSystemService(NotificationManager::class.java)
            val c = NotificationChannel(
                chan, getString(R.string.channel_name), NotificationManager.IMPORTANCE_LOW
            )
            mgr.createNotificationChannel(c)
        }
        return NotificationCompat.Builder(this, chan)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(getString(R.string.service_running))
            .setSmallIcon(android.R.drawable.ic_menu_manage)
            .setOngoing(true)
            .build()
    }

    override fun onDestroy() {
        super.onDestroy()
    }

    companion object {
        const val NOTIF_ID = 1
    }
}

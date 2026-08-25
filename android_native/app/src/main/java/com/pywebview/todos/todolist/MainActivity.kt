package com.pywebview.todos.todolist

import android.Manifest
import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.util.Timer
import java.util.TimerTask

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private var pendingUrl: String? = null
    private var pageLoaded = false
    private val reminderHandler = Handler(Looper.getMainLooper())
    private val reminderTimer = Timer()
    private val notifiedTaskIds = mutableSetOf<String>()

    companion object {
        private const val CHANNEL_ID = "todo_reminder"
        private const val NOTIFICATION_PERMISSION = 1001
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 读取 URL scheme intent（冷启动）
        pendingUrl = intent?.data?.toString()

        createNotificationChannel()
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                if (url.startsWith("todolist://")) {
                    // 内部 URL scheme 交给 JS 处理
                    handleUrlScheme(url)
                    return true
                }
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    // 站外链接用系统浏览器
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    } catch (e: Exception) {
                        // 忽略
                    }
                    return true
                }
                return false
            }

            override fun onPageFinished(view: WebView, url: String?) {
                pageLoaded = true
                // 等页面 JS 就绪后注入待处理的 URL
                pendingUrl?.let { pushUrlToPage(it) }
                pendingUrl = null
            }
        }

        setContentView(webView)
        webView.loadUrl("file:///android_asset/web/index.html")

        // 请求通知权限（Android 13+）
        requestNotificationPermission()

        // 启动提醒轮询
        startReminderCheck()
    }

    // ---------- URL scheme ----------
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val url = intent.data?.toString()
        if (url != null) {
            pushUrlToPage(url)
        }
    }

    private fun pushUrlToPage(url: String) {
        if (!pageLoaded) {
            pendingUrl = url
            return
        }
        runOnUiThread {
            try {
                // 用 JSON 转义安全注入
                val safe = url.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
                webView.evaluateJavascript("window.__pushFromUrl('$safe');", null)
            } catch (e: Exception) {
                // 忽略
            }
        }
    }

    private fun handleUrlScheme(url: String) {
        pushUrlToPage(url)
    }

    // ---------- 通知 ----------
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "任务提醒",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "任务开始前提醒"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                    NOTIFICATION_PERMISSION
                )
            }
        }
    }

    private fun startReminderCheck() {
        // 每 30 秒扫描一次 localStorage 任务，检查开始时间前 30/10/5 分钟
        reminderTimer.schedule(object : TimerTask() {
            override fun run() {
                checkReminders()
            }
        }, 30_000L, 30_000L)
    }

    private fun checkReminders() {
        runOnUiThread {
            try {
                webView.evaluateJavascript(
                    "JSON.stringify((function(){try{return JSON.parse(localStorage.getItem('todolist_tasks')||'[]')}catch(e){return[]}})())",
                    object : android.webkit.ValueCallback<String> {
                        override fun onReceiveValue(value: String?) {
                            if (value == null || value == "null" || value == "\"null\"") return
                            try {
                                val json = value.trim()
                                // evaluateJavascript 返回带引号的 JSON 字符串，去掉外层引号
                                val tasks = JSONObject("{\"tasks\":" + json + "}").getJSONArray("tasks")
                                val now = System.currentTimeMillis()
                                for (i in 0 until tasks.length()) {
                                    val task = tasks.getJSONObject(i)
                                    val id = task.optString("id", "")
                                    if (id.isEmpty()) continue
                                    val completed = task.optBoolean("completed", false)
                                    if (completed) continue
                                    val due = task.optString("dueDate", "")
                                    if (due.isEmpty()) continue
                                    val dueMs = parseDate(due) ?: continue
                                    val remainMs = dueMs - now
                                    if (remainMs > 0 && remainMs <= 30 * 60 * 1000L) {
                                        // 30 分钟内：发送提醒（避免重复）
                                        val key = id + "_" + (remainMs / 60000)
                                        if (!notifiedTaskIds.contains(key)) {
                                            notifiedTaskIds.add(key)
                                            showReminder(task.optString("title", "任务"), remainMs)
                                        }
                                    }
                                }
                            } catch (e: Exception) {
                                // 解析失败忽略
                            }
                        }
                    }
                )
            } catch (e: Exception) {
                // 忽略
            }
        }
    }

    private fun parseDate(due: String): Long? {
        return try {
            // 支持 "YYYY-MM-DD HH:MM" 和 ISO "YYYY-MM-DDTHH:MM:SS"
            val normalized = due.replace("T", " ")
            val parts = normalized.split(" ")
            if (parts.size < 2) return null
            val dateParts = parts[0].split("-")
            val timeParts = parts[1].split(":".toRegex()).take(3).map { it.toInt() }
            val year = dateParts[0].toInt()
            val month = dateParts[1].toInt()
            val day = dateParts[2].toInt()
            val hour = timeParts[0]
            val minute = timeParts[1]
            val second = if (timeParts.size > 2) timeParts[2] else 0
            val cal = java.util.Calendar.getInstance().apply {
                set(year, month - 1, day, hour, minute, second)
                set(java.util.Calendar.MILLISECOND, 0)
            }
            cal.timeInMillis
        } catch (e: Exception) {
            null
        }
    }

    private fun showReminder(title: String, remainMs: Long) {
        val minutes = (remainMs / 60000).coerceAtLeast(1)
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("📝 任务即将开始")
            .setContentText("任务「$title」将在 $minutes 分钟后开始")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        try {
            NotificationManagerCompat.from(this).notify(
                title.hashCode() and 0xFFFFFF,
                notification
            )
        } catch (e: SecurityException) {
            // 权限未授予，忽略
        }
    }

    // ---------- 返回键 ----------
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        reminderTimer.cancel()
        webView.destroy()
    }
}

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
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
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
    // 每任务上次扫描的剩余分钟数（用于检测跨过提醒档位边界）
    private val prevRemaining = mutableMapOf<String, Double>()

    companion object {
        private const val TAG = "TodoReminder"
        private const val CHANNEL_ID = "todo_reminder"
        private const val NOTIFICATION_PERMISSION = 1001
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 读取 URL scheme intent（冷启动）
        pendingUrl = intent?.data?.toString()

        // 允许 chrome://inspect 远程调试 WebView（仅调试构建）
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)

        createNotificationChannel()
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true

        // 前端 console.log 转发到 logcat（tag=TodoWeb），配合调试模式排查
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: ConsoleMessage): Boolean {
                Log.d("TodoWeb", "console(${consoleMessage.lineNumber()}): ${consoleMessage.message()}")
                return true
            }
        }

        // 原生桥：调试模式按钮 / 获取调试信息
        webView.addJavascriptInterface(TodoNative(), "TodoNative")

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
                // 一次读取任务 + 提醒配置（enabled/offsets，缺省默认开启 30,10,5）
                webView.evaluateJavascript(
                    "JSON.stringify((function(){try{" +
                        "var tasks=JSON.parse(localStorage.getItem('todolist_tasks')||'[]');" +
                        "var enabled=localStorage.getItem('todolist_remind_enabled');" +
                        "var offsets=localStorage.getItem('todolist_remind_offsets');" +
                        "return {tasks:tasks,enabled:enabled===null?'true':enabled,offsets:offsets===null?'30,10,5':offsets};" +
                        "}catch(e){return {tasks:[],enabled:'true',offsets:'30,10,5'}}})())",
                    object : android.webkit.ValueCallback<String> {
                        override fun onReceiveValue(value: String?) {
                            if (value == null || value == "null" || value == "\"null\"") return
                            try {
                                // evaluateJavascript 对字符串返回值会整体加引号转义，先解开
                                val raw = value.trim()
                                val jsonStr = if (raw.startsWith("\"") && raw.endsWith("\"") && raw.length >= 2) {
                                    JSONObject("{\"v\":" + raw + "}").getString("v")
                                } else {
                                    raw
                                }
                                val obj = JSONObject(jsonStr)
                                if (obj.optString("enabled", "true") == "false") {
                                    Log.d(TAG, "提醒已关闭，跳过")
                                    return
                                }
                                val offsets = parseOffsets(obj.optString("offsets", "30,10,5"))
                                if (offsets.isEmpty()) return

                                val tasks = obj.getJSONArray("tasks")
                                val now = System.currentTimeMillis()
                                val minOffset = offsets.min()
                                Log.d(TAG, "扫描: ${tasks.length()} 任务, offsets=$offsets, 通知权限=${hasNotificationPermission()}")

                                for (i in 0 until tasks.length()) {
                                    val task = tasks.getJSONObject(i)
                                    val id = task.optString("id", "")
                                    if (id.isEmpty()) continue
                                    if (task.optBoolean("completed", false)) {
                                        prevRemaining.remove(id)
                                        continue
                                    }
                                    val due = task.optString("dueDate", "")
                                    if (due.isEmpty()) continue
                                    val dueMs = parseDate(due) ?: continue
                                    val remainMs = dueMs - now
                                    if (remainMs <= 0) continue

                                    val remainMin = remainMs / 60000.0
                                    val prev = prevRemaining[id]

                                    if (prev == null) {
                                        // 首次见到该任务：进入最小档窗口才补发最小档，否则仅记录
                                        if (remainMin <= minOffset) {
                                            val key = id + "_" + minOffset
                                            if (!notifiedTaskIds.contains(key)) {
                                                notifiedTaskIds.add(key)
                                                Log.d(TAG, "补发最小档 $minOffset 分钟: ${task.optString("title")}")
                                                showReminder(task.optString("title", "任务"), minOffset)
                                            }
                                        }
                                    } else {
                                        // 剩余时间跨过某档位边界时，发该档位提醒（每档每任务一次）
                                        for (offset in offsets) {
                                            val key = id + "_" + offset
                                            if (notifiedTaskIds.contains(key)) continue
                                            if (remainMin <= offset && offset < prev) {
                                                notifiedTaskIds.add(key)
                                                Log.d(TAG, "触发 $offset 分钟档: ${task.optString("title")}")
                                                showReminder(task.optString("title", "任务"), offset)
                                            }
                                        }
                                    }
                                    prevRemaining[id] = remainMin
                                }
                            } catch (e: Exception) {
                                Log.e(TAG, "提醒解析失败: ${e.message}", e)
                            }
                        }
                    }
                )
            } catch (e: Exception) {
                // 忽略
            }
        }
    }

    // 解析 "30,10,5" → 降序去重的正整数列表
    private fun parseOffsets(raw: String): List<Int> {
        return try {
            raw.split(",")
                .map { it.trim() }
                .filter { it.isNotEmpty() }
                .mapNotNull { it.toIntOrNull() }
                .filter { it > 0 }
                .distinct()
                .sortedDescending()
        } catch (e: Exception) {
            emptyList()
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

    private fun hasNotificationPermission(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
    }

    private fun showReminder(title: String, offsetMinutes: Int, isTest: Boolean = false) {
        val minutes = offsetMinutes.coerceAtLeast(1)
        val notifTitle = if (isTest) "🔔 测试通知" else "📝 任务即将开始"
        val notifText = if (isTest) "通知通道正常（测试：$title）" else "任务「$title」将在 $minutes 分钟后开始"
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(notifTitle)
            .setContentText(notifText)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        if (!hasNotificationPermission()) {
            Log.e(TAG, "通知未发送: POST_NOTIFICATIONS 权限未授予！请在系统设置中允许 TodoList 通知")
            return
        }
        try {
            // 测试通知用固定 id，避免与任务通知冲突
            val id = if (isTest) 999999 else (title.hashCode() and 0xFFFFFF)
            NotificationManagerCompat.from(this).notify(id, notification)
            Log.d(TAG, "通知已发送: $notifTitle / $notifText (id=$id)")
        } catch (e: SecurityException) {
            Log.e(TAG, "通知发送失败(SecurityException): 权限被拒或系统通知被关闭", e)
        }
    }

    // 调试模式：前端点击"发送测试通知"时调用，直接验证通知通道/权限
    private inner class TodoNative {
        @JavascriptInterface
        fun sendTestNotification(title: String?) {
            Log.d(TAG, "调试: 用户点击「发送测试通知」")
            runOnUiThread {
                showReminder(title ?: "测试通知", 5, isTest = true)
            }
        }

        @JavascriptInterface
        fun getNativeDebugInfo(): String {
            return try {
                val info = JSONObject()
                @Suppress("DEPRECATION")
                val pkg = packageManager.getPackageInfo(packageName, 0)
                info.put("versionName", pkg.versionName ?: "?")
                @Suppress("DEPRECATION")
                info.put("versionCode", pkg.versionCode)
                info.put("sdkInt", Build.VERSION.SDK_INT)
                info.put("hasNotificationPermission", hasNotificationPermission())
                info.put("notificationPermissionLabel", if (hasNotificationPermission()) "已授予" else "未授予(通知不会弹出!)")
                info.toString()
            } catch (e: Exception) {
                "{\"error\":\"" + (e.message ?: "unknown") + "\"}"
            }
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

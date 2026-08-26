package com.pywebview.todos.todolist

import android.Manifest
import android.annotation.SuppressLint
import android.app.AlarmManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private var pendingUrl: String? = null
    private var pendingOpenTaskId: String? = null
    private var pageLoaded = false

    companion object {
        private const val TAG = "TodoReminder"
        private const val NOTIFICATION_PERMISSION = 1001
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 读取 URL scheme intent（冷启动）与通知点击跳转任务
        pendingUrl = intent?.data?.toString()
        pendingOpenTaskId = intent?.getStringExtra("openTaskId")

        // 允许 chrome://inspect 远程调试 WebView（仅调试构建）
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)

        ReminderNotifier.ensureChannel(this)
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

        // 原生桥：任务/配置同步 + 调试模式
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
                // 通知点击跳转：页面就绪后打开对应任务详情
                pendingOpenTaskId?.let { openTaskDetail(it) }
                pendingOpenTaskId = null
            }
        }

        setContentView(webView)
        webView.loadUrl("file:///android_asset/web/index.html")

        // 请求通知权限（Android 13+）
        requestNotificationPermission()

        // 完全采用精确闹钟：从镜像恢复调度 + 补发 app 关闭期间错过的提醒
        ReminderAlarm.scheduleAll(this)
        ReminderAlarm.catchUpMissed(this)
    }

    // ---------- URL scheme & 通知点击 ----------
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val url = intent.data?.toString()
        if (url != null) {
            pushUrlToPage(url)
        }
        val openTaskId = intent.getStringExtra("openTaskId")
        if (openTaskId != null) {
            openTaskDetail(openTaskId)
        }
    }

    private fun openTaskDetail(taskId: String) {
        Log.d(TAG, "通知点击跳转任务详情: $taskId")
        if (!pageLoaded) {
            pendingOpenTaskId = taskId
            return
        }
        runOnUiThread {
            try {
                // 先确保任务加载完成，再打开详情
                webView.evaluateJavascript(
                    "window.todoManager && window.todoManager.loadTasks && window.todoManager.loadTasks().then(function(){ window.todoManager.viewTaskDetails('$taskId'); })",
                    null
                )
            } catch (e: Exception) {
                Log.e(TAG, "跳转任务详情失败: ${e.message}")
            }
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

    // ---------- 通知权限 & 后台服务 ----------
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

    private fun hasNotificationPermission(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
    }

    private fun canScheduleExactAlarms(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
            (getSystemService(Context.ALARM_SERVICE) as AlarmManager).canScheduleExactAlarms()
    }

    /** 检测国内 ROM：用于权限申请页展示差异化自启动引导 */
    private fun detectRom(): String {
        val m = (Build.MANUFACTURER ?: "").lowercase()
        val b = (Build.BRAND ?: "").lowercase()
        val model = (Build.MODEL ?: "").lowercase()
        val f = (Build.FINGERPRINT ?: "").lowercase()

        return when {
            m.contains("oppo") || m.contains("realme") || b.contains("oppo") || b.contains("realme") || f.contains("coloros") -> "ColorOS/realme"
            m.contains("xiaomi") || b.contains("xiaomi") || b.contains("redmi") || f.contains("miui") -> "MIUI"
            m.contains("huawei") || m.contains("honor") || b.contains("huawei") || b.contains("honor") || f.contains("emui") || f.contains("harmonyos") -> "EMUI/HarmonyOS"
            m.contains("vivo") || m.contains("bbk") || b.contains("vivo") || b.contains("iqoo") || f.contains("originos") -> "OriginOS/vivo"
            m.contains("oneplus") || b.contains("oneplus") || model.contains("oneplus") -> "一加/OPPO"
            else -> "通用/其他"
        }
    }

    // ---------- 原生桥 ----------
    private inner class TodoNative {
        // 前端任务变化时同步到镜像并重排闹钟
        @JavascriptInterface
        fun syncTasks(tasksJson: String?) {
            Log.d(TAG, "syncTasks: ${tasksJson?.length ?: 0} 字符")
            if (tasksJson.isNullOrEmpty()) return
            runOnUiThread {
                ReminderStore.setTasks(this@MainActivity, tasksJson)
                ReminderAlarm.scheduleAll(this@MainActivity)
            }
        }

        // 前端提醒配置变化时同步并重排
        @JavascriptInterface
        fun syncConfig(enabled: Boolean, offsets: String) {
            Log.d(TAG, "syncConfig: enabled=$enabled, offsets=$offsets")
            runOnUiThread {
                ReminderStore.setEnabled(this@MainActivity, enabled)
                ReminderStore.setOffsets(this@MainActivity, offsets)
                ReminderAlarm.scheduleAll(this@MainActivity)
            }
        }

        // 页面加载时一次性同步存量任务+配置（升级用户的旧数据也能设闹钟）
        @JavascriptInterface
        fun syncAll(tasksJson: String?, enabled: Boolean, offsets: String) {
            Log.d(TAG, "syncAll: ${tasksJson?.length ?: 0} 字符, enabled=$enabled, offsets=$offsets")
            runOnUiThread {
                if (!tasksJson.isNullOrEmpty()) ReminderStore.setTasks(this@MainActivity, tasksJson)
                ReminderStore.setEnabled(this@MainActivity, enabled)
                ReminderStore.setOffsets(this@MainActivity, offsets)
                ReminderAlarm.scheduleAll(this@MainActivity)
            }
        }

        // 精确闹钟权限状态（供前端引导）
        @JavascriptInterface
        fun canScheduleExactAlarms(): Boolean = this@MainActivity.canScheduleExactAlarms()

        // 跳系统设置授予精确闹钟权限
        @JavascriptInterface
        fun openExactAlarmSettings() {
            runOnUiThread {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        startActivity(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:$packageName")))
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "打开闹钟权限设置失败: ${e.message}")
                }
            }
        }

        // 电池优化豁免状态：ColorOS 后台冻结的根源，豁免后闹钟不被拦
        @JavascriptInterface
        fun isIgnoringBatteryOptimizations(): Boolean {
            return try {
                val pm = getSystemService(Context.POWER_SERVICE) as android.os.PowerManager
                pm.isIgnoringBatteryOptimizations(packageName)
            } catch (e: Exception) {
                Log.e(TAG, "检查电池优化失败: ${e.message}")
                false
            }
        }

        // 引导用户豁免电池优化（跳系统"忽略电池优化"设置）
        @JavascriptInterface
        fun requestIgnoreBatteryOptimizations() {
            runOnUiThread {
                try {
                    startActivity(Intent(
                        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:$packageName")
                    ))
                } catch (e: Exception) {
                    Log.e(TAG, "打开电池优化设置失败: ${e.message}")
                }
            }
        }

        // 跳应用通知设置（Android 13+ 权限被拒时引导）
        @JavascriptInterface
        fun openAppNotificationSettings() {
            runOnUiThread {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        val intent = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                            .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
                        startActivity(intent)
                    } else {
                        startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "打开通知设置失败: ${e.message}")
                }
            }
        }

        // 返回设备品牌信息（供前端展示差异化自启动引导）
        @JavascriptInterface
        fun getBrandInfo(): String {
            return try {
                val info = JSONObject()
                info.put("manufacturer", Build.MANUFACTURER)
                info.put("brand", Build.BRAND)
                info.put("model", Build.MODEL)
                info.put("romLabel", detectRom())
                info.toString()
            } catch (e: Exception) {
                "{\"error\":\"" + (e.message ?: "unknown") + "\"}"
            }
        }

        // 按品牌跳自启动/后台管理设置，失败回退应用详情
        @JavascriptInterface
        fun openBrandAutoStart() {
            runOnUiThread {
                try {
                    val intent = when (detectRom()) {
                        "ColorOS/realme" -> Intent().apply {
                            action = "com.coloros.safecenter.permission.startup"
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        "MIUI" -> Intent().apply {
                            action = "miui.intent.action.OP_AUTO_START"
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        "EMUI/HarmonyOS" -> Intent().apply {
                            component = android.content.ComponentName(
                                "com.huawei.systemmanager",
                                "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"
                            )
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        "OriginOS/vivo" -> Intent().apply {
                            component = android.content.ComponentName(
                                "com.vivo.permissionmanager",
                                "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"
                            )
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        "一加/OPPO" -> Intent().apply {
                            component = android.content.ComponentName(
                                "com.oneplus.security",
                                "com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity"
                            )
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        else -> null
                    }
                    if (intent != null) {
                        startActivity(intent)
                        Log.d(TAG, "跳转品牌自启动设置: ${detectRom()}")
                    } else {
                        openAppDetails()
                    }
                } catch (e: Exception) {
                    Log.d(TAG, "品牌自启动设置不可用，回退应用详情: ${e.message}")
                    openAppDetails()
                }
            }
        }

        private fun openAppDetails() {
            try {
                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName")))
            } catch (e2: Exception) {
                Log.e(TAG, "打开应用详情失败: ${e2.message}")
            }
        }

        @JavascriptInterface
        fun sendTestNotification(title: String?) {
            Log.d(TAG, "调试: 用户点击「发送测试通知」")
            runOnUiThread {
                ReminderNotifier.send(this@MainActivity, title ?: "测试通知", 5, isTest = true)
            }
        }

        // 设一个 5 秒后的真系统闹钟：若收到"测试闹钟"通知，说明 AlarmManager→Receiver 链路通
        @JavascriptInterface
        fun scheduleTestAlarm() {
            Log.d(TAG, "调试: 用户点击「发送测试闹钟」")
            runOnUiThread {
                ReminderAlarm.scheduleTestAlarm(this@MainActivity, 5_000L)
            }
        }

        // 返回调度诊断状态（镜像任务/档位/闹钟/权限/上次调度日志）
        @JavascriptInterface
        fun getScheduleStatus(): String {
            return try {
                val info = JSONObject()
                info.put("mirrorTasksJson", ReminderStore.getTasks(this@MainActivity) ?: "")
                info.put("mirrorTasksLen", (ReminderStore.getTasks(this@MainActivity)?.length ?: 0))
                info.put("enabled", ReminderStore.getEnabled(this@MainActivity))
                info.put("offsets", ReminderStore.getOffsetsRaw(this@MainActivity))
                info.put("canScheduleExactAlarms", canScheduleExactAlarms())
                info.put("scheduledCodes", ReminderStore.scheduledCodes(this@MainActivity).size)
                info.put("lastScheduleLog", ReminderAlarm.lastScheduleLog)
                info.toString()
            } catch (e: Exception) {
                "{\"error\":\"" + (e.message ?: "unknown") + "\"}"
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
                info.put("canScheduleExactAlarms", canScheduleExactAlarms())
                info.put("exactAlarmLabel", if (canScheduleExactAlarms()) "已授予" else "未授予(后台提醒可能延迟)")
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
        webView.destroy()
    }
}

package com.pywebview.todos.todolist

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.AlarmManagerCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject

/**
 * 后台提醒核心：SharedPreferences 镜像 + AlarmManager 精确闹钟 + 通知发送。
 * 前端 localStorage 是唯一数据源，通过 TodoNative.syncTasks/syncConfig 镜像到
 * SharedPreferences，闹钟 Receiver / 兜底 Service 从镜像读取（它们拿不到 WebView）。
 */
object ReminderStore {
    private const val PREFS = "todo_reminder_prefs"
    private const val KEY_TASKS = "tasks_json"
    private const val KEY_ENABLED = "remind_enabled"
    private const val KEY_OFFSETS = "remind_offsets"
    private const val KEY_NOTIFIED = "notified_keys"
    private const val KEY_SCHEDULED = "scheduled_codes"

    private fun prefs(ctx: Context) = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun setTasks(ctx: Context, json: String) {
        prefs(ctx).edit().putString(KEY_TASKS, json).apply()
    }

    fun getTasks(ctx: Context): String? = prefs(ctx).getString(KEY_TASKS, null)

    fun setEnabled(ctx: Context, enabled: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_ENABLED, enabled).apply()
    }

    fun getEnabled(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_ENABLED, true)

    fun setOffsets(ctx: Context, raw: String) {
        prefs(ctx).edit().putString(KEY_OFFSETS, raw).apply()
    }

    fun getOffsetsRaw(ctx: Context): String = prefs(ctx).getString(KEY_OFFSETS, "30,10,5") ?: "30,10,5"

    /** 已通知的去重键集合，闹钟 Receiver 与兜底 Service 共用 */
    fun notifiedKeys(ctx: Context): MutableSet<String> =
        HashSet(prefs(ctx).getStringSet(KEY_NOTIFIED, emptySet()) ?: emptySet())

    fun addNotified(ctx: Context, key: String) {
        val set = notifiedKeys(ctx)
        set.add(key)
        prefs(ctx).edit().putStringSet(KEY_NOTIFIED, set).apply()
    }

    /** 已设置的闹钟 requestCode 集合，用于任务变更时全量取消 */
    fun scheduledCodes(ctx: Context): Set<String> =
        HashSet(prefs(ctx).getStringSet(KEY_SCHEDULED, emptySet()) ?: emptySet())

    fun setScheduledCodes(ctx: Context, codes: Set<String>) {
        prefs(ctx).edit().putStringSet(KEY_SCHEDULED, codes).apply()
    }
}

object ReminderAlarm {
    private const val TAG = "TodoAlarm"

    // ---- 诊断状态（供前端调试面板展示） ----
    @Volatile var lastScheduleLog: String = "尚未调度"
        private set

    /** 解析 "30,10,5" → 升序去重正整数（最紧急档位在前） */
    fun parseOffsets(raw: String): List<Int> {
        return try {
            raw.split(",")
                .map { it.trim() }
                .filter { it.isNotEmpty() }
                .mapNotNull { it.toIntOrNull() }
                .filter { it > 0 }
                .distinct()
                .sorted()
        } catch (e: Exception) {
            emptyList()
        }
    }

    /** 解析 "YYYY-MM-DD HH:MM" 或 ISO "YYYY-MM-DDTHH:MM:SS" → epoch ms */
    fun parseDate(due: String): Long? {
        return try {
            val normalized = due.replace("T", " ")
            val parts = normalized.split(" ")
            if (parts.size < 2) return null
            val dateParts = parts[0].split("-")
            val timeParts = parts[1].split(":").take(3).map { it.toInt() }
            val cal = java.util.Calendar.getInstance().apply {
                set(dateParts[0].toInt(), dateParts[1].toInt() - 1, dateParts[2].toInt(), timeParts[0], timeParts[1], if (timeParts.size > 2) timeParts[2] else 0)
                set(java.util.Calendar.MILLISECOND, 0)
            }
            cal.timeInMillis
        } catch (e: Exception) {
            null
        }
    }

    fun requestCode(taskId: String, offset: String): Int =
        (taskId + "_" + offset).hashCode() and 0x7FFFFFFF

    /** 任务/配置变化后全量重排闹钟 */
    fun scheduleAll(ctx: Context) {
        val enabled = ReminderStore.getEnabled(ctx)
        val offsets = parseOffsets(ReminderStore.getOffsetsRaw(ctx))
        val tasksJson = ReminderStore.getTasks(ctx)

        cancelAll(ctx)

        if (!enabled || offsets.isEmpty() || tasksJson == null) {
            val why = if (!enabled) "提醒已关闭" else if (offsets.isEmpty()) "档位为空" else "镜像无任务"
            lastScheduleLog = "$why（tasks=${tasksJson?.length ?: 0} 字符）"
            Log.d(TAG, "调度跳过: $why")
            return
        }

        val now = System.currentTimeMillis()
        val scheduled = HashSet<String>()
        var parsedTasks = 0
        var skippedNoTime = 0
        var skippedPast = 0
        val detail = StringBuilder()

        try {
            val tasks = JSONArray(tasksJson)
            for (i in 0 until tasks.length()) {
                val task = tasks.getJSONObject(i)
                val title = task.optString("title", "任务")
                val id = task.optString("id", "")
                if (id.isEmpty()) continue
                if (task.optBoolean("completed", false)) continue
                val due = task.optString("dueDate", "")
                if (due.isEmpty()) { skippedNoTime++; continue }
                val dueMs = parseDate(due)
                if (dueMs == null) {
                    skippedNoTime++
                    detail.append("\n  [${title}] dueDate 解析失败: \"$due\"")
                    continue
                }
                parsedTasks++
                val dueStr = java.text.SimpleDateFormat("MM-dd HH:mm", java.util.Locale.getDefault()).format(java.util.Date(dueMs))

                for (offset in offsets) {
                    val targetMs = dueMs - offset * 60_000L
                    if (targetMs <= now) { skippedPast++; continue } // 已过的档位不设
                    val code = requestCode(id, offset.toString())
                    val pi = pendingIntent(ctx, code, id, offset, dueMs, title)
                    scheduleOne(ctx, targetMs, pi)
                    scheduled.add(code.toString())
                    detail.append("\n  [${title}] 提前${offset}min @ ${java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault()).format(java.util.Date(targetMs))}")
                }

                if (dueMs >= now) {
                    val code = requestCode(id, "due")
                    val pi = pendingIntent(ctx, code, id, -1, dueMs, title)
                    scheduleOne(ctx, dueMs, pi)
                    scheduled.add(code.toString())
                    detail.append("\n  [${title}] 到期 @ ${dueStr}")
                }
            }
        } catch (e: Exception) {
            lastScheduleLog = "调度异常: ${e.message}"
            Log.e(TAG, "调度失败: ${e.message}", e)
            return
        }

        ReminderStore.setScheduledCodes(ctx, scheduled)
        lastScheduleLog = "设了 ${scheduled.size} 个闹钟 | 可解析任务 $parsedTasks | setAlarmClock(系统闹钟) | 跳过无时间/过期 $skippedNoTime/$skippedPast" + detail
        Log.d(TAG, "调度完成: ${scheduled.size} 个闹钟, 任务=$parsedTasks$detail")
    }

    /** 调试用：设一个 delayMs 后触发的系统闹钟，验证 AlarmManager→Receiver 链路 */
    fun scheduleTestAlarm(ctx: Context, delayMs: Long) {
        val triggerAt = System.currentTimeMillis() + delayMs
        val pi = PendingIntent.getBroadcast(
            ctx, 0x0F00F00, // 固定测试 code
            Intent(ctx, ReminderReceiver::class.java)
                .putExtra("taskId", "__test__")
                .putExtra("offset", -2) // -2 表示测试闹钟
                .putExtra("dueMs", triggerAt)
                .putExtra("title", "测试闹钟"),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        try {
            scheduleOne(ctx, triggerAt, pi)
            lastScheduleLog = "测试闹钟已设，${delayMs / 1000} 秒后触发"
        } catch (e: Exception) {
            lastScheduleLog = "测试闹钟设置失败: ${e.message}"
            Log.e(TAG, "测试闹钟失败: ${e.message}", e)
        }
    }

    private fun pendingIntent(ctx: Context, code: Int, taskId: String, offset: Int, dueMs: Long, title: String): PendingIntent {
        val intent = Intent(ctx, ReminderReceiver::class.java)
            .putExtra("taskId", taskId)
            .putExtra("offset", offset) // -1 表示到期
            .putExtra("dueMs", dueMs)
            .putExtra("title", title)
        return PendingIntent.getBroadcast(
            ctx, code, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    /**
     * 用 setAlarmClock 调度：系统级闹钟，ColorOS/realme 不会冻结，
     * 且不需要 SCHEDULE_EXACT_ALARM 权限，后台/锁屏也能准点触发。
     */
    private fun scheduleOne(ctx: Context, triggerAt: Long, pi: PendingIntent) {
        val alarm = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val showIntent = PendingIntent.getActivity(
            ctx, 0,
            Intent(ctx, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        try {
            AlarmManagerCompat.setAlarmClock(alarm, triggerAt, showIntent, pi)
            Log.d(TAG, "setAlarmClock 已设 @ ${java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date(triggerAt))}")
        } catch (e: Exception) {
            Log.e(TAG, "setAlarmClock 失败: ${e.message}", e)
        }
    }

    fun cancelAll(ctx: Context) {
        val alarm = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        for (code in ReminderStore.scheduledCodes(ctx)) {
            try {
                val pi = PendingIntent.getBroadcast(
                    ctx, code.toIntOrNull() ?: continue,
                    Intent(ctx, ReminderReceiver::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                alarm.cancel(pi)
            } catch (e: Exception) {
                // 忽略单个取消失败
            }
        }
        ReminderStore.setScheduledCodes(ctx, emptySet())
    }

    /**
     * App 打开时补发一次"已到提醒时间但未提醒过"的最紧急档位。
     * 覆盖闹钟因设备重启/系统清理丢失的场景；每任务只发一条，不刷屏。
     */
    fun catchUpMissed(ctx: Context) {
        if (!ReminderStore.getEnabled(ctx)) return
        val offsets = parseOffsets(ReminderStore.getOffsetsRaw(ctx))
        if (offsets.isEmpty()) return
        val tasksJson = ReminderStore.getTasks(ctx) ?: return
        val now = System.currentTimeMillis()
        val notified = ReminderStore.notifiedKeys(ctx)

        try {
            val tasks = JSONArray(tasksJson)
            for (i in 0 until tasks.length()) {
                val task = tasks.getJSONObject(i)
                if (task.optBoolean("completed", false)) continue
                val due = task.optString("dueDate", "")
                if (due.isEmpty()) continue
                val dueMs = parseDate(due) ?: continue
                val id = task.optString("id", "")
                if (id.isEmpty()) continue
                val title = task.optString("title", "任务")
                val remainMs = dueMs - now

                if (remainMs <= 0) {
                    // 到期已错过：只补发"过去较短时间内"的到期提醒，避免刷屏历史任务
                    if (remainMs >= -60 * 60 * 1000L) {
                        val dueKey = id + "_due"
                        if (dueKey !in notified) {
                            if (ReminderNotifier.send(ctx, title, 0, isDue = true)) {
                                ReminderStore.addNotified(ctx, dueKey)
                            }
                        }
                    }
                    continue
                }

                // 提前提醒：找最紧急"已到时间且未发"档位，发"剩 X 分钟"
                val remainMin = remainMs / 60000.0
                for (offset in offsets) {
                    val targetMs = dueMs - offset * 60_000L
                    if (now < targetMs) continue
                    val key = id + "_" + offset
                    if (key in notified) break
                    val showMin = Math.round(remainMin).toInt().coerceAtLeast(1)
                    if (ReminderNotifier.send(ctx, title, showMin)) {
                        ReminderStore.addNotified(ctx, key)
                    }
                    break
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "补发失败: ${e.message}")
        }
    }
}

object ReminderNotifier {
    private const val TAG = "TodoReminder"
    private const val CHANNEL_ID = "todo_reminder"
    private const val NOTIFICATION_PERMISSION = 1001

    fun ensureChannel(ctx: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "任务提醒", NotificationManager.IMPORTANCE_DEFAULT).apply {
                description = "任务开始前与到期的提醒"
            }
            val manager = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    fun hasPermission(ctx: Context): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
    }

    /** minutes<=0 表示到期提醒；返回是否真正发送 */
    fun send(ctx: Context, title: String, minutes: Int, isDue: Boolean = false, isTest: Boolean = false): Boolean {
        ensureChannel(ctx)
        val notifTitle = when {
            isTest -> "🔔 测试通知"
            isDue -> "✅ 任务开始时间到了"
            else -> "📝 任务即将开始"
        }
        val notifText = when {
            isTest -> "通知通道正常（测试：$title）"
            isDue -> "任务「$title」开始时间已到，现在开始吧！"
            else -> "任务「$title」将在 $minutes 分钟后开始"
        }

        if (!hasPermission(ctx)) {
            Log.e(TAG, "通知未发送: POST_NOTIFICATIONS 权限未授予！请在系统设置中允许 TodoList 通知")
            return false
        }
        val notification = NotificationCompat.Builder(ctx, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(notifTitle)
            .setContentText(notifText)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()
        return try {
            val id = when {
                isTest -> 999999
                isDue -> (title.hashCode() and 0xFFFFFF) xor 0x111111
                else -> title.hashCode() and 0xFFFFFF
            }
            NotificationManagerCompat.from(ctx).notify(id, notification)
            Log.d(TAG, "通知已发送: $notifTitle / $notifText (id=$id)")
            true
        } catch (e: SecurityException) {
            Log.e(TAG, "通知发送失败(SecurityException): ${e.message}")
            false
        }
    }
}

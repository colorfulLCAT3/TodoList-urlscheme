package com.pywebview.todos.todolist

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import org.json.JSONArray

/**
 * 前台服务兜底：闹钟因权限/系统冻结未触发时，服务每 30s 读镜像补发提醒。
 * 与闹钟共用 notified_keys，避免重复。
 */
class ReminderService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private val poll = object : Runnable {
        override fun run() {
            pollReminders()
            handler.postDelayed(this, 30_000L)
        }
    }

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIF_ID, buildOngoingNotification())
        Log.d("TodoService", "提醒兜底服务已启动")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIF_ID, buildOngoingNotification())
        handler.removeCallbacks(poll)
        handler.post(poll)
        return START_STICKY
    }

    override fun onDestroy() {
        handler.removeCallbacks(poll)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun pollReminders() {
        try {
            if (!ReminderStore.getEnabled(this)) return
            val offsets = ReminderAlarm.parseOffsets(ReminderStore.getOffsetsRaw(this))
            if (offsets.isEmpty()) return
            val tasksJson = ReminderStore.getTasks(this) ?: return
            val now = System.currentTimeMillis()
            val notified = ReminderStore.notifiedKeys(this)

            val tasks = JSONArray(tasksJson)
            for (i in 0 until tasks.length()) {
                val task = tasks.getJSONObject(i)
                if (task.optBoolean("completed", false)) continue
                val due = task.optString("dueDate", "")
                if (due.isEmpty()) continue
                val dueMs = ReminderAlarm.parseDate(due) ?: continue
                val id = task.optString("id", "")
                if (id.isEmpty()) continue
                val title = task.optString("title", "任务")
                val remainMs = dueMs - now

                if (remainMs <= 0) {
                    // 到期兜底
                    val dueKey = id + "_due"
                    if (dueKey !in notified) {
                        if (ReminderNotifier.send(this, title, 0, isDue = true)) {
                            ReminderStore.addNotified(this, dueKey)
                        }
                    }
                    continue
                }

                val remainMin = remainMs / 60000.0
                for (offset in offsets) {
                    val targetMs = dueMs - offset * 60_000L
                    if (now < targetMs) continue // 该档位未到
                    val key = id + "_" + offset
                    if (key in notified) break // 最紧急已到时间档已发 → 停止
                    val showMin = Math.round(remainMin).toInt().coerceAtLeast(1)
                    if (ReminderNotifier.send(this, title, showMin)) {
                        ReminderStore.addNotified(this, key)
                    }
                    break
                }
            }
        } catch (e: Exception) {
            Log.e("TodoService", "兜底轮询失败: ${e.message}")
        }
    }

    private fun buildOngoingNotification(): Notification {
        val channelId = "todo_reminder_service"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            val channel = NotificationChannel(channelId, "提醒服务", NotificationManager.IMPORTANCE_LOW).apply {
                description = "保持任务提醒在后台运行"
            }
            manager.createNotificationChannel(channel)
        }
        val intent = Intent(this, MainActivity::class.java)
        val pi = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return Notification.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_popup_sync)
            .setContentTitle("TodoList 提醒服务")
            .setContentText("正在后台保持任务提醒")
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val NOTIF_ID = 1000
    }
}

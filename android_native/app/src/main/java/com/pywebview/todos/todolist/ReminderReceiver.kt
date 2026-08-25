package com.pywebview.todos.todolist

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * 精确闹钟到点后触发：读镜像发通知，并与兜底服务共用 notified_keys 去重。
 */
class ReminderReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        Log.d("TodoAlarm", "闹钟触发: ${intent.getStringExtra("title")} offset=${intent.getIntExtra("offset", -1)}")

        if (!ReminderStore.getEnabled(context)) {
            Log.d("TodoAlarm", "提醒已关闭，跳过")
            return
        }

        val taskId = intent.getStringExtra("taskId") ?: return
        val offset = intent.getIntExtra("offset", -1)
        val dueMs = intent.getLongExtra("dueMs", 0L)
        val title = intent.getStringExtra("title") ?: "任务"

        // 校验任务仍未完成且未被删除（读镜像里当前任务状态）
        val tasksJson = ReminderStore.getTasks(context)
        var valid = false
        var completed = true
        try {
            val tasks = org.json.JSONArray(tasksJson)
            for (i in 0 until tasks.length()) {
                val t = tasks.getJSONObject(i)
                if (t.optString("id", "") == taskId) {
                    valid = true
                    completed = t.optBoolean("completed", false)
                    break
                }
            }
        } catch (e: Exception) {
            Log.e("TodoAlarm", "镜像解析失败: ${e.message}")
        }
        if (!valid || completed) {
            Log.d("TodoAlarm", "任务已删除/完成，不提醒")
            return
        }

        val isDue = offset <= 0
        val key = if (isDue) taskId + "_due" else taskId + "_" + offset
        val notified = ReminderStore.notifiedKeys(context)
        if (key in notified) {
            Log.d("TodoAlarm", "已提醒过，跳过: $key")
            return
        }

        val minutes = if (isDue) 0 else {
            // 文案显示实际剩余分钟（闹钟可能延迟，避免与真实时间不符）
            val remainMs = dueMs - System.currentTimeMillis()
            if (remainMs <= 0) {
                ReminderNotifier.send(context, title, 0, isDue = true) // 到点了改发到期
                ReminderStore.addNotified(context, taskId + "_due")
                return
            }
            Math.round(remainMs / 60000.0).toInt().coerceAtLeast(1)
        }

        if (ReminderNotifier.send(context, title, minutes, isDue)) {
            ReminderStore.addNotified(context, key)
        }
    }
}

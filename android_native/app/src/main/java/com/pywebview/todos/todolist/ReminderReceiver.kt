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
        val now = System.currentTimeMillis()
        val dueMs = intent.getLongExtra("dueMs", 0L)
        val title = intent.getStringExtra("title") ?: "任务"
        val offset = intent.getIntExtra("offset", -1)
        Log.d("TodoAlarm", "闹钟触发: title=$title offset=$offset dueMs=$dueMs now=$now remainMs=${dueMs - now}")

        // 测试闹钟：直接发一条测试通知，验证 AlarmManager→Receiver→通知 整条链路
        if (offset == -2) {
            ReminderNotifier.send(context, title, 5, isTest = true)
            Log.d("TodoAlarm", "测试闹钟已触发，测试通知已发")
            return
        }

        if (!ReminderStore.getEnabled(context)) {
            Log.d("TodoAlarm", "跳过: 提醒已关闭")
            return
        }

        val taskId = intent.getStringExtra("taskId")
        if (taskId == null) {
            Log.d("TodoAlarm", "跳过: taskId 为空")
            return
        }

        // 校验任务仍未完成且未被删除（读镜像里当前任务状态）
        val tasksJson = ReminderStore.getTasks(context)
        var valid = false
        var completed = true
        if (tasksJson == null) {
            Log.d("TodoAlarm", "跳过: 镜像无任务 tasksJson=null")
            return
        }
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
        if (!valid) {
            Log.d("TodoAlarm", "跳过: 任务不在镜像中 taskId=$taskId")
            return
        }
        if (completed) {
            Log.d("TodoAlarm", "跳过: 任务已完成 title=$title")
            return
        }

        val isDue = offset <= 0
        val key = if (isDue) taskId + "_due" else taskId + "_" + offset
        val notified = ReminderStore.notifiedKeys(context)
        if (key in notified) {
            Log.d("TodoAlarm", "跳过: 已提醒过 key=$key")
            return
        }

        if (isDue) {
            if (ReminderNotifier.send(context, title, 0, isDue = true, taskId = taskId)) {
                ReminderStore.addNotified(context, key)
                Log.d("TodoAlarm", "到期提醒已发: $title")
            }
            return
        }

        // 提前提醒：文案显示实际剩余分钟（闹钟可能延迟）
        val remainMs = dueMs - now
        val minutes = if (remainMs <= 0) {
            // 闹钟延迟到过期：改发到期提醒，并记录原档位 key 避免重发
            val sent = ReminderNotifier.send(context, title, 0, isDue = true, taskId = taskId)
            ReminderStore.addNotified(context, key)
            ReminderStore.addNotified(context, taskId + "_due")
            Log.d("TodoAlarm", "闹钟延迟已过期，改发到期: $title sent=$sent")
            return
        } else {
            Math.round(remainMs / 60000.0).toInt().coerceAtLeast(1)
        }

        if (ReminderNotifier.send(context, title, minutes, isDue = false, taskId = taskId)) {
            ReminderStore.addNotified(context, key)
            Log.d("TodoAlarm", "提前提醒已发: $title 剩${minutes}分钟 key=$key")
        }
    }
}

#!/usr/bin/env python3
"""
任务提醒功能模块
支持任务开始时间前提前提醒（30/10/5 分钟）与到期提醒
桌面端使用系统原生通知栏，Android 使用系统原生通知
"""
import os
import queue
import sys
import threading
import time
import asyncio
import platform
from datetime import datetime, timedelta
from queue import Queue
from backend.utils import utils
from backend.database.operations import TodoDatabase
from backend.utils.logger import LogManager

# 默认提前提醒档位（分钟）
DEFAULT_REMIND_OFFSETS = (30, 10, 5)

class TaskReminder(LogManager):
    """任务提醒器"""

    def __init__(self):
        super().__init__()
        self.running = False
        self.check_interval = 30  # 检查间隔(秒),默认30秒
        self.notification_queue = Queue()
        self.db = TodoDatabase()
        self.notified_tasks = set()  # 已提醒"到期"的任务ID集合
        self.reminded_offsets = set()  # 已提醒的提前档位集合 {(task_id, offset_minutes)}
        self.scheduled_tasks = {}  # 已安排提醒的任务 {task_id: due_datetime}
        self._prev_remaining = {}  # 各任务上次检查时的剩余分钟数 {task_id: minutes}
        self.check_thread = None
        self.asyncio_thread = None
        self.notify_thread = None
        self.system = platform.system()
        self.is_android = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ
        self.notifier = None
        self.loop = asyncio.new_event_loop()
        self.remind_enabled = True
        self.remind_offsets = DEFAULT_REMIND_OFFSETS

    def start(self, click_event):
        """启动提醒服务"""
        if self.running:
            return

        self.running = True
        self.notified_tasks.clear()
        self.scheduled_tasks.clear()
        self.reminded_offsets.clear()
        self._prev_remaining.clear()

        # 读取提醒配置
        self._load_remind_config()

        # 启动检查线程
        self.check_thread = threading.Thread(target=self._check_tasks, daemon=True)
        self.check_thread.start()

        if self.is_android:
            # Android 使用原生通知，无需 asyncio/desktop_notifier 线程
            self._ensure_android_channel()
            self._request_android_notification_permission()
            self.get_logger.info("任务提醒服务已启动（Android）")
            return

        # 专门负责运行 asyncio 循环的线程
        self.asyncio_thread = threading.Thread(target=self._run_asyncio, daemon=True)
        self.asyncio_thread.start()

        # 启动通知线程
        self.notify_thread = threading.Thread(target=self._process_notifications, daemon=True, args=(click_event,))
        self.notify_thread.start()

        self.get_logger.info("任务提醒服务已启动")

    def stop(self):
        if not self.running:
            return
        self.running = False

        # 停止事件循环
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # 等待 asyncio 线程结束
        if self.asyncio_thread and self.asyncio_thread.is_alive():
            self.asyncio_thread.join(timeout=3)

        # 关闭事件循环（释放 WinRT 相关资源）
        if self.loop and not self.loop.is_closed():
            self.loop.close()

        # 等待其他线程
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=1)
        if self.notify_thread and self.notify_thread.is_alive():
            self.notify_thread.join(timeout=1)

        self.get_logger.info("任务提醒服务已停止")

    def _load_remind_config(self):
        """从数据库读取提前提醒配置"""
        try:
            enabled = self.db.get_setting('remind_enabled', True)
            self.remind_enabled = utils.str_to_bool(enabled) if not isinstance(enabled, bool) else enabled

            raw_offsets = self.db.get_setting('remind_offsets', ','.join(map(str, DEFAULT_REMIND_OFFSETS)))
            offsets = []
            for part in str(raw_offsets).split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    offset = int(part)
                except (ValueError, TypeError):
                    continue
                if offset > 0:
                    offsets.append(offset)
            self.remind_offsets = tuple(sorted(set(offsets), reverse=True)) or DEFAULT_REMIND_OFFSETS
        except Exception as e:
            self.get_logger.warning(f"读取提醒配置失败，使用默认值: {e}")
            self.remind_enabled = True
            self.remind_offsets = DEFAULT_REMIND_OFFSETS
        
    def _check_tasks(self):
        """后台线程检查任务提前提醒与到期提醒"""
        while self.running:
            try:
                # 获取所有未完成的任务
                tasks = self.db.get_all_tasks()
                now = datetime.now()

                for task in tasks:
                    # 跳过已完成的任务
                    if task['completed']:
                        continue

                    # 跳过没有截止时间的任务
                    if not task.get('dueDate'):
                        continue

                    # 解析截止时间
                    try:
                        due_date = datetime.fromisoformat(task['dueDate'])
                    except (ValueError, TypeError):
                        continue

                    task_id = task['id']

                    # 提前提醒：任务未到期时，按档位提前通知
                    remaining = due_date - now
                    if remaining.total_seconds() > 0:
                        self._check_advance_reminders(task, task_id, due_date, remaining)
                        self.scheduled_tasks[task_id] = due_date
                        continue

                    # 到期提醒：任务已到期且未提醒过
                    if task_id not in self.notified_tasks:
                        self.notification_queue.put({
                            'kind': 'due',
                            'task_id': task_id,
                            'title': task['title'],
                            'due_date': due_date,
                            'priority': task.get('priority', 'none')
                        })
                        self.notified_tasks.add(task_id)

                # 清理已完成任务的提醒记录
                self._cleanup_completed_tasks(tasks)

            except Exception as e:
                self.get_logger.error(f"检查任务时出错: {e}")

            # 等待下一次检查
            time.sleep(self.check_interval)

    def _check_advance_reminders(self, task, task_id, due_date, remaining):
        """检查并触发提前提醒（任务开始前 30/10/5 分钟）

        规则：
        - 任务首次被检查时（_prev_remaining 无记录）：若剩余时间已进入
          最小档位窗口（剩余 <= min(offsets)），补发一次最小档位提醒；
          否则仅记录，不发（避免补发早已错过的更大档位）。
        - 之后每轮：剩余时间跨过某个档位边界（上次 > offset，本次 <= offset）
          时，发该档位提醒。每个档位每任务只发一次。
        """
        if not self.remind_enabled:
            return
        remaining_minutes = remaining.total_seconds() / 60
        prev_minutes = self._prev_remaining.get(task_id, None)

        if prev_minutes is None:
            # 首次见到该任务
            min_offset = min(self.remind_offsets)
            if remaining_minutes <= min_offset:
                self._put_advance(task, task_id, due_date, min_offset)
                self.reminded_offsets.add((task_id, min_offset))
        else:
            for offset in self.remind_offsets:  # 降序
                key = (task_id, offset)
                if key in self.reminded_offsets:
                    continue
                if remaining_minutes <= offset < prev_minutes:
                    self._put_advance(task, task_id, due_date, offset)
                    self.reminded_offsets.add(key)

        # 更新该任务上次剩余时间（每轮检查更新）
        self._prev_remaining[task_id] = remaining_minutes

    def _put_advance(self, task, task_id, due_date, offset):
        self.notification_queue.put({
            'kind': 'advance',
            'task_id': task_id,
            'title': task['title'],
            'due_date': due_date,
            'priority': task.get('priority', 'none'),
            'offset': offset
        })

    def _run_asyncio(self):
        # 专门负责运行 asyncio 循环的线程
        import asyncio
        asyncio.set_event_loop(self.loop)
        from desktop_notifier import DesktopNotifier, Icon

        self.notifier = DesktopNotifier(
            app_name="TodoList",
            app_icon=Icon(utils.get_app_icon()),
            notification_limit=5,
        )
        self.loop.run_forever()

    def _cleanup_completed_tasks(self, current_tasks):
        """清理已完成或已删除任务的记录"""
        current_task_ids = {task['id'] for task in current_tasks}

        # 清理已删除任务的通知记录
        to_remove = []
        for task_id in list(self.notified_tasks):
            if task_id not in current_task_ids:
                to_remove.append(task_id)

        for task_id in to_remove:
            self.notified_tasks.discard(task_id)
            self.scheduled_tasks.pop(task_id, None)
            self._prev_remaining.pop(task_id, None)

        # 清理提前提醒档位记录
        for key in [k for k in self.reminded_offsets if k[0] not in current_task_ids]:
            self.reminded_offsets.discard(key)
            
    def _process_notifications(self, click_event=None):
        """处理提醒通知"""
        while self.running:
            try:
                notification_msg = self.notification_queue.get(timeout=1)
                self._show_notification(notification_msg, click_event)
            except queue.Empty:
                pass
            except Exception as e:
                self.get_logger.error(f"处理通知时出错: {e}")
                pass  # 队列为空或超时

    def _build_notification(self, notification):
        task_title = notification['title']
        due_date = notification['due_date']
        priority = notification['priority']
        kind = notification.get('kind', 'due')

        if kind == 'advance':
            offset = notification.get('offset', 0)
            message = f"任务「{task_title}」将在 {offset} 分钟后开始"
            if priority == 'high':
                title = "⚠️ 高优先级任务即将开始"
            elif priority == 'medium':
                title = "📋 任务即将开始"
            else:
                title = "📝 任务即将开始"
            return title, message, priority

        # 到期提醒：计算过期时长
        now = datetime.now()
        overdue_duration = now - due_date

        if overdue_duration.days > 0:
            time_str = f"{overdue_duration.days}天前"
        elif overdue_duration.seconds >= 3600:
            hours = overdue_duration.seconds // 3600
            time_str = f"{hours}小时前"
        else:
            minutes = overdue_duration.seconds // 60
            time_str = f"{minutes}分钟前"

        # 构建通知消息
        message = f"任务「{task_title}」已于{time_str}到期"

        # 根据优先级设置提醒标题
        if priority == 'high':
            title = "⚠️ 高优先级任务到期提醒"
        elif priority == 'medium':
            title = "📋 任务到期提醒"
        else:
            title = "📝 任务到期提醒"
        return title, message, priority

    def _show_notification(self, notification, click_event):
        """显示通知：Android 走原生 jnius，桌面走 asyncio + desktop_notifier"""
        title, message, priority = self._build_notification(notification)

        if self.is_android:
            self._notify_android(title, message, notification.get('task_id', ''))
            return

        try:
            async def _send():
                from desktop_notifier import Urgency
                await self.notifier.send(
                    title=title,
                    message=message,
                    urgency=Urgency.Critical if priority == 'high' else Urgency.Normal,
                    on_clicked=click_event,
                    timeout=0  # 0表示通知常驻
                )
            asyncio.run_coroutine_threadsafe(_send(), self.loop)
        except Exception as e:
            self.get_logger.error(f"显示通知时出错: {e}")

    # ---------- Android 原生通知 ----------
    def _get_android_context(self):
        """获取 Android activity context"""
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        return PythonActivity.mActivity

    def _ensure_android_channel(self):
        """创建 Android 通知渠道（API 26+ 必需）"""
        try:
            from jnius import autoclass
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            activity = self._get_android_context()
            manager = activity.getSystemService(activity.NOTIFICATION_SERVICE)
            channel = NotificationChannel('todo_reminder', '任务提醒', NotificationManager.IMPORTANCE_DEFAULT)
            channel.setDescription('任务开始前与到期的提醒')
            manager.createNotificationChannel(channel)
            self.get_logger.info("[提醒] Android 通知渠道已创建")
        except Exception as e:
            self.get_logger.error(f"[提醒] 创建 Android 通知渠道失败: {e}")

    def _request_android_notification_permission(self):
        """Android 13+ 请求通知运行时权限 POST_NOTIFICATIONS"""
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            if Build.VERSION.SDK_INT >= 33:
                activity = self._get_android_context()
                permission = 'android.permission.POST_NOTIFICATIONS'
                if activity.checkSelfPermission(permission) != 0:
                    activity.requestPermissions([permission], 1001)
                    self.get_logger.info("[提醒] 已请求 Android 通知权限")
        except Exception as e:
            self.get_logger.warning(f"[提醒] 请求 Android 通知权限失败: {e}")

    def _notify_android(self, title, message, task_id=''):
        """通过 jnius 发送 Android 原生通知"""
        try:
            from jnius import autoclass
            NotificationManager = autoclass('android.app.NotificationManager')
            Builder = autoclass('android.app.Notification$Builder')
            activity = self._get_android_context()
            manager = activity.getSystemService(activity.NOTIFICATION_SERVICE)

            builder = Builder(activity, 'todo_reminder')
            builder.setContentTitle(title)
            builder.setContentText(message)
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setAutoCancel(True)

            # 通知 id 用任务 id 哈希，保证可覆盖
            notify_id = abs(hash(task_id)) % 100000 if task_id else abs(hash(title)) % 100000
            manager.notify(notify_id, builder.build())
            self.get_logger.info(f"[提醒] Android 通知已发送: {title}")
        except Exception as e:
            self.get_logger.error(f"[提醒] Android 通知发送失败: {e}")

    def reset_notified_tasks(self):
        """重置已提醒任务列表(用于测试或重新提醒)"""
        self.notified_tasks.clear()
        self.reminded_offsets.clear()
        self.get_logger.info("已重置已提醒任务列表")
    
    def get_pending_tasks_count(self):
        """获取待提醒的任务数量"""
        return len(self.scheduled_tasks) - len(self.notified_tasks)


# 全局提醒器实例
_reminder = None

def get_reminder():
    """获取提醒器单例"""
    global _reminder
    if _reminder is None:
        _reminder = TaskReminder()
    return _reminder

def start_reminder(click_event=None):
    """启动提醒服务"""
    reminder = get_reminder()
    reminder.start(click_event)
    return reminder

def stop_reminder():
    """停止提醒服务"""
    reminder = get_reminder()
    reminder.stop()

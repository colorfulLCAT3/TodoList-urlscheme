# impl/mobile/android_impl.py
from backend.platforms.interface.service import PlatformService

class AndroidService(PlatformService):
    def force_kill_process_tree(self, pid):
        pass

    def get_log_directory(self):
        import sys
        from pathlib import Path

        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            exe_dir = Path(sys.executable).parent
        else:
            # 开发环境
            exe_dir = Path(__file__).parent.parent.parent

        log_dir = exe_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_app_icon(self, base_path):
        return base_path / 'todo_icon.ico'

    def is_ssl_enable(self):
        # 移动端需要开启ssl，避免在移动端使用报错存在安全问题
        return True

    def icon_exit(self):
        pass

    def start_prepare(self):
        pass

    def start_desktop_task_reminder(self, is_start, event=None):
        """启动/停止任务提醒服务（Android 使用系统原生通知）"""
        from backend.platforms.impl.desktop.common.task_reminder import start_reminder, stop_reminder
        if is_start:
            start_reminder(click_event=event)
        else:
            stop_reminder()

    def add_new_desktop_task_reminder(self):
        """重置提醒记录，确保新任务可以被提醒"""
        from backend.platforms.impl.desktop.common.task_reminder import get_reminder
        reminder = get_reminder()
        reminder.reset_notified_tasks()

    def check_calendar_permission(self):
        """校验日历使用权限的统一接口"""
        from backend.platforms.impl.mobile.common.calendar_manager import check_permission
        check_permission()

    def add_task_reminder_to_calendar(self, title, desc, start_time_ms):
        """添加任务提醒到日历的统一接口"""
        from backend.platforms.impl.mobile.common.calendar_manager import add_task_reminder_to_calendar
        add_task_reminder_to_calendar(title, desc, start_time_ms, self)

    def sync_reminder_to_calendar(self, sync_start_time, sync_end_time):
        """同步任务提醒到日历的统一接口"""
        from backend.platforms.impl.mobile.common.calendar_manager import sync_reminder_to_calendar
        sync_reminder_to_calendar(sync_start_time, sync_end_time, self)

    def register_url_scheme(self):
        """注册 URL scheme 的统一接口（Android 由 Manifest 声明，无需注册）"""
        return True

    def start_url_listener(self, callback):
        """监听 Android 冷启动 intent 与热启动 onNewIntent 传递的 URL"""
        import threading
        import time

        def poll():
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TodoActivity = autoclass('com.pywebview.todos.todolist.TodoListActivity')
                activity = PythonActivity.mActivity

                # 冷启动：读取初始 intent
                try:
                    intent = activity.getIntent()
                    if intent is not None:
                        data = intent.getDataString()
                        if data:
                            self.backend_logger().info(f"[URLScheme] 冷启动收到 URL: {data[:120]}")
                            callback(data)
                            intent.setData(None)
                except Exception as e:
                    self.backend_logger().warning(f"[URLScheme] 读取初始 intent 失败: {e}")

                # 热启动：轮询自定义 Activity 静态字段
                while True:
                    time.sleep(1)
                    last = TodoActivity.lastUrl
                    if last:
                        TodoActivity.lastUrl = None
                        self.backend_logger().info(f"[URLScheme] 热启动收到 URL: {last[:120]}")
                        callback(last)
            except Exception as e:
                self.backend_logger().error(f"[URLScheme] Android URL 监听异常: {e}")

        threading.Thread(target=poll, daemon=True).start()

    def dispatch_url_to_running_instance(self, url):
        """Android 无第二实例概念，热启动由 onNewIntent 直达"""
        return False

    def start_app(self):
        """启动应用的统一接口"""
        from backend import start
        # 先启动任务提醒服务（阻塞前）
        self.start_desktop_task_reminder(True)
        # 安卓端需要开启SSL，否则功能无法使用
        start.start_app(True, True)

    def frontend_logger(self):
        """前端日志的统一接口"""
        from backend.utils.logger import setup_logger
        # 创建默认的logger实例
        return setup_logger(self, 'frontend')

    def backend_logger(self):
        """后端日志的统一接口"""
        from backend.utils.logger import setup_logger
        # 创建默认的logger实例
        return setup_logger(self, 'backend')

    def export_tasks_excel(self, db = None, priority=None, status=None, year=None, month=None,
                           category_id=None, tag_ids=None):
        """后端数据导出的统一接口"""
        raise Exception(f'当前系统不支持')

# 用于给工厂注册的导出变量
ExportService = AndroidService

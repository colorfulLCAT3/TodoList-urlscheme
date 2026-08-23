# interfaces/service.py
from abc import ABC, abstractmethod

class PlatformService(ABC):
    @abstractmethod
    def force_kill_process_tree(self, pid):
        """强制结束当前进程及其所有子进程的统一接口"""
        pass

    @abstractmethod
    def get_log_directory(self):
        """返回可写的日志目录的统一接口"""
        pass

    @abstractmethod
    def get_app_icon(self, base_path):
        """获取应用图标的统一接口"""
        pass

    @abstractmethod
    def is_ssl_enable(self):
        """获取是否开启ssl的统一接口"""
        pass

    @abstractmethod
    def icon_exit(self):
        """图标注销消息的统一接口"""
        pass

    @abstractmethod
    def start_prepare(self):
        """应用启动前准备工作的统一接口"""
        pass

    @abstractmethod
    def start_desktop_task_reminder(self, is_start, event=None):
        """应用桌面端消息提醒的统一接口"""
        pass

    @abstractmethod
    def add_new_desktop_task_reminder(self):
        """应用桌面端新任务添加消息提醒的统一接口"""
        pass

    @abstractmethod
    def check_calendar_permission(self):
        """校验日历使用权限的统一接口"""
        pass

    @abstractmethod
    def add_task_reminder_to_calendar(self, title, desc, start_time_ms):
        """添加任务提醒到日历的统一接口"""
        pass

    @abstractmethod
    def sync_reminder_to_calendar(self, sync_start_time, sync_end_time):
        """同步任务提醒到日历的统一接口"""
        pass

    @abstractmethod
    def register_url_scheme(self):
        """注册应用 URL scheme 的统一接口"""
        pass

    @abstractmethod
    def start_url_listener(self, callback):
        """启动 URL 监听，收到 URL 时回调 callback(url) 的统一接口"""
        pass

    @abstractmethod
    def dispatch_url_to_running_instance(self, url):
        """把 URL 转发给已运行实例的统一接口，成功返回 True"""
        pass

    @abstractmethod
    def start_app(self):
        """启动应用的统一接口"""
        pass

    @abstractmethod
    def frontend_logger(self):
        """前端日志的统一接口"""
        pass

    @abstractmethod
    def backend_logger(self):
        """后端日志的统一接口"""
        pass

    @abstractmethod
    def export_tasks_excel(self, db = None, priority=None, status=None, year=None, month=None,
                           category_id=None, tag_ids=None):
        """后端数据导出的统一接口"""
        pass
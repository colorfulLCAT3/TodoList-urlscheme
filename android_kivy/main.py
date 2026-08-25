"""
TodoList Android Kivy 应用入口。

复用 backend 的 TodoDatabase / UrlSchemeManager / TaskReminder，
接收 todolist:// URL scheme 推送，启动提前提醒通知。
不依赖 pywebview（WebView 在 p4a 环境崩溃已验证）。
"""
import os
import sys
import threading


def log(msg):
    """输出 logcat 日志"""
    try:
        from jnius import autoclass
        Log = autoclass('android.util.Log')
        Log.i('TodoListKivy', str(msg))
    except Exception:
        try:
            print(f'[TodoListKivy] {msg}', flush=True)
        except Exception:
            pass


def setup_paths():
    """确保 backend 代码可导入"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Android 上工作目录是解压目录，切换到可写私有目录
    try:
        if hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            files_dir = PythonActivity.mActivity.getFilesDir().getAbsolutePath()
            os.chdir(files_dir)
            # 确保 backend/ 可写数据目录存在
            os.makedirs(files_dir, exist_ok=True)
    except Exception:
        pass
    return project_root


def setup_url_listener(app):
    """注册 URL scheme 接收：冷启动 intent + 热启动 on_new_intent"""
    try:
        from jnius import autoclass
        from android.activity import bind
        from backend.features.urlscheme.url_scheme import UrlSchemeManager

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        manager = UrlSchemeManager(app.db)

        # 冷启动：读取初始 intent
        try:
            intent = PythonActivity.mActivity.getIntent()
            if intent is not None and intent.getData() is not None:
                url = intent.getDataString()
                if url:
                    log(f'冷启动收到 URL: {url[:120]}')
                    result = manager.handle_url(url)
                    log(f'冷启动入库: {result}')
                    app.external_refresh()
        except Exception as e:
            log(f'冷启动 intent 处理失败: {e}')

        # 热启动：on_new_intent 回调
        def on_new_intent(intent):
            try:
                if intent is not None and intent.getData() is not None:
                    url = intent.getDataString()
                    if url:
                        log(f'热启动收到 URL: {url[:120]}')
                        result = manager.handle_url(url)
                        log(f'热启动入库: {result}')
                        app.external_refresh()
            except Exception as e:
                log(f'on_new_intent 处理失败: {e}')

        bind(on_new_intent=on_new_intent)
        log('URL 监听已注册')
    except Exception as e:
        log(f'URL 监听注册失败: {e}')


def setup_reminder(app):
    """启动任务提醒服务（Android 用 jnius 原生通知）"""
    try:
        from backend.platforms.impl.desktop.common.task_reminder import start_reminder
        start_reminder()
        log('任务提醒服务已启动')
    except Exception as e:
        log(f'任务提醒服务启动失败: {e}')


def main():
    log('TodoList Kivy 入口开始')
    setup_paths()

    from todolist_app import TodoListApp
    app = TodoListApp()

    # URL scheme 监听（应用实例就绪后）
    setup_url_listener(app)
    # 通知服务
    setup_reminder(app)

    log('启动 Kivy 应用')
    app.run()
    log('Kivy 应用退出')


if __name__ == '__main__':
    main()

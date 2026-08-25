"""Android logcat 日志辅助：用 jnius 直接调 android.util.Log，100% 进 logcat。

print() 在 Android 上不一定重定向到 logcat（取决于 p4a 配置），
用 jnius 调 android.util.Log 是最可靠的抓日志方式。
非 Android 环境自动降级为 print。
"""

TAG = 'TodoListDebug'


def log(msg):
    """输出一条 logcat 日志（tag: TodoListDebug）"""
    try:
        # 尝试用 jnius 调 android.util.Log.i
        from jnius import autoclass
        Log = autoclass('android.util.Log')
        Log.i(TAG, str(msg))
    except Exception:
        try:
            print(f'[{TAG}] {msg}', flush=True)
        except Exception:
            pass

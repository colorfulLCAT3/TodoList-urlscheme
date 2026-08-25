"""最小 pywebview 测试应用：不加载项目代码，只显示一行字。

用于二分定位：若此应用在两台手机正常，则崩溃在我们项目集成；
若也崩，则 pywebview + webview bootstrap 本身在这台设备有问题。
"""
import sys
import webview

def log(msg):
    try:
        from jnius import autoclass
        Log = autoclass('android.util.Log')
        Log.i('PWMinTest', str(msg))
    except Exception:
        print(f'[PWMinTest] {msg}', flush=True)

log('main.py 开始')
try:
    w = webview.create_window(
        'PWMinTest',
        html='<h1 style="text-align:center;margin-top:40vh;font-family:sans-serif;">pywebview OK</h1>',
    )
    log('create_window 完成')
    webview.start()
    log('webview.start 完成')
except Exception as e:
    log(f'异常: {e}')

"""
python-for-android 构建钩子。

1. jar 拷贝：webview bootstrap 的 Gradle 构建需要 pywebview-android.jar 位于
   dist 的 src/main/libs/，但 p4a 的 --add-jar 在 src/main/libs 目录
   不存在时静默失败，此 hook 手动拷贝。

2. 【实验】移除 bootstrap 自带的 WebView：webview bootstrap 的
   PythonActivity 会先创建一个 WebView 加载 _load.html，然后 pywebview
   又创建第二个 WebView 替换。同一进程两个 WebView 的渲染进程竞争
   GPU（snapalloc/Vulkan mutex）疑似触发高通驱动 bug 崩溃。
   此实验移除 bootstrap 自带的 WebView，只保留 Python 启动，让 pywebview
   独占 WebView。验证崩溃是否消除。
"""
import os
from pathlib import Path


def _copy_jar(src):
    """把 jar 拷贝到 dist 的 src/main/libs/"""
    libs_dir = Path('src/main/libs')
    libs_dir.mkdir(parents=True, exist_ok=True)
    dest = libs_dir / Path(src).name
    if not dest.exists():
        import shutil
        shutil.copy(src, dest)
        print(f'[p4a_hook] 已拷贝 {Path(src).name} 到 src/main/libs/')


def _patch_python_activity():
    """移除 PythonActivity.java 里 bootstrap 自带的 WebView 创建代码。

    把从 "// Set up the webview" 到 "setContentView(mLayout);" 的整段
    替换为空（保留 mLayout 定义以不破坏后续逻辑），并停用 WvThread。
    """
    path = Path('src/main/java/org/kivy/android/PythonActivity.java')
    if not path.exists():
        print('[p4a_hook] 未找到 PythonActivity.java，跳过单WebView补丁')
        return

    src = path.read_text(encoding='utf-8')
    original = src

    # 1. 移除 WebView 创建段（从 "// Set up the webview" 到 "setContentView(mLayout);"）
    start_marker = '            // Set up the webview'
    end_marker = '            setContentView(mLayout);'
    start = src.find(start_marker)
    end = src.find(end_marker)
    if start != -1 and end != -1 and end > start:
        block = src[start:end + len(end_marker)]
        # 替换为：仅创建一个空 layout 并 setContentView，不创建 WebView
        replacement = (
            '            // [p4a_hook] 已移除 bootstrap 自带的 WebView，'
            '由 pywebview 独占创建\n'
            '            mLayout = new AbsoluteLayout(PythonActivity.mActivity);\n'
            '            setContentView(mLayout);'
        )
        src = src[:start] + replacement + src[end + len(end_marker):]
        print('[p4a_hook] 已移除 bootstrap 自带的 WebView 创建段')
    else:
        print(f'[p4a_hook] 未找到 WebView 创建段 (start={start}, end={end})，跳过')

    # 2. 停用 WvThread（它 ping localhost:5000 空转，无意义）
    wv_start = '            final Thread wvThread = new Thread(new WebViewLoaderMain(), "WvThread");'
    wv_end = '            wvThread.start();'
    wvs = src.find(wv_start)
    wve = src.find(wv_end)
    if wvs != -1 and wve != -1 and wve > wvs:
        src = src[:wvs] + '            // [p4a_hook] WvThread 已停用' + src[wve + len(wv_end):]
        print('[p4a_hook] 已停用 WvThread')

    if src != original:
        path.write_text(src, encoding='utf-8')
    else:
        print('[p4a_hook] PythonActivity.java 无需修改')


def before_apk_build(ctx):
    """在 Gradle 构建前确保 jar 就位，并打单 WebView 补丁。"""
    candidates = [
        'lib/pywebview-android.jar',
        str(Path(__file__).resolve().parent.parent.parent / 'lib' / 'pywebview-android.jar'),
    ]
    for src in candidates:
        if os.path.exists(src):
            _copy_jar(src)
            break
    else:
        print('[p4a_hook] 未找到 pywebview-android.jar，跳过拷贝')

    _patch_python_activity()

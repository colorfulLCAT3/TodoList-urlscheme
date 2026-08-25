"""
python-for-android 构建钩子。

webview bootstrap 的 Gradle 构建需要 pywebview-android.jar 位于
dist 的 src/main/libs/，但 p4a 的 --add-jar 在 src/main/libs 目录
不存在时静默失败，导致 Gradle JetifyTransform 报
"input file does not exist"。此 hook 手动拷贝 jar。

注意：不要在此禁用 hardwareAccelerated！系统浏览器硬件加速正常，
强制 WebView 软件渲染会导致 tile memory limits exceeded 崩溃。
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


def before_apk_build(ctx):
    """在 Gradle 构建前确保 pywebview-android.jar 就位。"""
    candidates = [
        # 相对 dist 目录（cwd 是 dist）
        'lib/pywebview-android.jar',
        # 相对项目根（cwd 是项目根时的兜底）
        str(Path(__file__).resolve().parent.parent.parent / 'lib' / 'pywebview-android.jar'),
    ]
    for src in candidates:
        if os.path.exists(src):
            _copy_jar(src)
            return
    print('[p4a_hook] 未找到 pywebview-android.jar，跳过拷贝')

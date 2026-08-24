"""
python-for-android 构建钩子。

webview bootstrap 的 Gradle 构建需要 pywebview-android.jar 位于
dist 的 src/main/libs/ 目录，但 p4a 的 --add-jar 在 src/main/libs
目录不存在时静默失败，导致 Gradle JetifyTransform 报
"input file does not exist"。

此 hook 在 dist 构建阶段（before_apk_build，cwd 已是 dist 目录）
手动把 jar 拷贝到 src/main/libs/，确保 Gradle 能找到它。
"""
import glob
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
    """在 Gradle 构建前确保 pywebview-android.jar 就位。

    尝试多个可能的 jar 来源路径（相对 dist 目录或项目根）。
    """
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

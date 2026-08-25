"""
python-for-android 构建钩子。

1. jar 拷贝：webview bootstrap 的 Gradle 构建需要 pywebview-android.jar
   位于 dist 的 src/main/libs/，但 p4a 的 --add-jar 在目录不存在时静默失败，
   需手动拷贝（before_apk_build，cwd 已是 dist 目录）。

2. 禁用硬件加速：webview bootstrap 的 manifest 模板硬编码
   android:hardwareAccelerated="true"。在 Android 15 + 高通 Adreno 上，
   WebView 的 Chromium GPU 渲染线程（Chrome_InProcGp）会因
   Vulkan/gralloc 对已销毁 mutex 加锁而 SIGABRT 崩溃。
   把该属性改为 false，让 WebView 走软件渲染，消除 GPU 线程。
   （after_apk_build 时 manifest 已生成，cwd 是 dist 目录）
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


def _find_manifest():
    """在 dist 目录内查找 AndroidManifest.xml"""
    import glob
    candidates = [
        Path('src/main/AndroidManifest.xml'),
        Path('AndroidManifest.xml'),
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = glob.glob('**/AndroidManifest.xml', recursive=True)
    return Path(matches[0]) if matches else None


def _disable_hardware_acceleration():
    manifest_path = _find_manifest()
    if manifest_path is None:
        print('[p4a_hook] 未找到 AndroidManifest.xml，跳过硬件加速禁用')
        return

    content = manifest_path.read_text(encoding='utf-8')
    target = 'android:hardwareAccelerated="true"'
    replacement = 'android:hardwareAccelerated="false"'
    if target in content:
        content = content.replace(target, replacement)
        manifest_path.write_text(content, encoding='utf-8')
        print('[p4a_hook] 已禁用硬件加速（hardwareAccelerated=false）')
    else:
        print('[p4a_hook] 未找到 hardwareAccelerated 属性，跳过')


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


def after_apk_build(ctx):
    """manifest 已生成，禁用硬件加速消除 Chromium GPU 线程崩溃。"""
    _disable_hardware_acceleration()

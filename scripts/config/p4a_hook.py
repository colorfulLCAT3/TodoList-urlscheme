"""
python-for-android 构建钩子。

在 APK 构建前，把生成的 AndroidManifest.xml 里硬编码的
android:hardwareAccelerated="true" 替换为 "false"。

背景：pywebview 的 WebView 硬件渲染线程（hwuiTask）与 SDL2 bootstrap
的表面在 Android 14/15 上会因互斥锁竞争崩溃（
FORTIFY: pthread_mutex_lock called on a destroyed mutex / SIGABRT）。
禁用硬件加速让 WebView 走软件渲染，可绕过该崩溃。
"""


def _find_manifest():
    """在 dist 目录内查找 AndroidManifest.xml。

    p4a 调用 hook 时，当前工作目录是 dist 目录（dists/<name>），
    manifest 位于 src/main/AndroidManifest.xml，根目录也可能有一份副本。
    """
    from pathlib import Path
    import glob

    candidates = [
        Path('src/main/AndroidManifest.xml'),
        Path('AndroidManifest.xml'),
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = glob.glob('**/AndroidManifest.xml', recursive=True)
    return matches[0] if matches else None


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


def after_apk_build(ctx):
    """manifest 在此阶段已生成，cwd 是 dist 目录，可靠地禁用硬件加速。"""
    _disable_hardware_acceleration()

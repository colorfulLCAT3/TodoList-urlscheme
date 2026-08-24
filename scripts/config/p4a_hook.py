"""
python-for-android 构建钩子。

在 APK 构建前，把生成的 AndroidManifest.xml 里硬编码的
android:hardwareAccelerated="true" 替换为 "false"。

背景：pywebview 的 WebView 硬件渲染线程（hwuiTask）与 SDL2 bootstrap
的表面在 Android 14/15 上会因互斥锁竞争崩溃（
FORTIFY: pthread_mutex_lock called on a destroyed mutex / SIGABRT）。
禁用硬件加速让 WebView 走软件渲染，可绕过该崩溃。
"""


def before_apk_build(ctx):
    manifest_path = ctx.build_dir / 'android' / 'AndroidManifest.xml'
    if not manifest_path.exists():
        # 部分版本 manifest 在别处，尝试递归查找
        import glob
        matches = glob.glob(str(ctx.build_dir) + '/**/AndroidManifest.xml', recursive=True)
        if not matches:
            print('[p4a_hook] 未找到 AndroidManifest.xml，跳过硬件加速禁用')
            return
        manifest_path = matches[0]

    content = manifest_path.read_text(encoding='utf-8')
    target = 'android:hardwareAccelerated="true"'
    replacement = 'android:hardwareAccelerated="false"'
    if target in content:
        content = content.replace(target, replacement)
        manifest_path.write_text(content, encoding='utf-8')
        print('[p4a_hook] 已禁用硬件加速（hardwareAccelerated=false）')
    else:
        print('[p4a_hook] 未找到 hardwareAccelerated 属性，跳过')

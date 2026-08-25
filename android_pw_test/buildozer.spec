[app]

# (str) Title of your application
title = PWMinTest

# (str) Package name
package.name = pwtest

# (str) Package domain
package.domain = com.pywebview.todos

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
# 只有 pywebview，不加载任何项目代码
requirements = python3,pywebview,bottle,pyjnius,android

# (str) Presplash（省略）
# (str) Icon（省略）

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

fullscreen = 0

android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = android.permission.INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (int) Android NDK API (must match minapi)
android.ndk_api = 24

# (list) The Android archs
android.archs = arm64-v8a

# 关键：与主应用一致的 bootstrap
p4a.bootstrap = webview

# 排除 sdl2/sdl3
p4a.extra_args = --blacklist-requirements sdl2,sdl3

# 拷贝 pywebview jar（webview bootstrap 需要）
p4a.hook = ../scripts/config/p4a_hook.py

[buildozer]

log_level = 2

warn_on_root = 1

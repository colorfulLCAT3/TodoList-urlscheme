[app]

# (str) Title of your application
title = MinTest

# (str) Package name
package.name = mintest

# (str) Package domain
package.domain = com.pywebview.todos

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# 纯 Kivy，不含 pywebview
requirements = python3,kivy

# (str) Presplash of the application（省略，使用默认）
# (str) Icon of the application（省略，使用默认）

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color
android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = android.permission.INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 24

# (int) Android SDK version to use
#android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API (must match minapi)
android.ndk_api = 24

# (str) Android entry point
#android.entrypoint = org.kivy.android.PythonActivity

# (list) The Android archs to build for
android.archs = arm64-v8a

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1

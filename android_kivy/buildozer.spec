[app]

# (str) Title of your application
title = TodoList

# (str) Package name
package.name = todoList

# (str) Package domain
package.domain = com.pywebview.todos

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
# 复用项目根目录的 backend 代码（数据库/urlscheme/通知等）
source.include_patterns = android_kivy/*,backend/*,scripts/config/*,data/*

# (list) Source files to exclude
source.exclude_exts = spec

# (list) List of directory to exclude
source.exclude_dirs = bin,build,dist,docs,logs,tests,venv

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# 纯 Kivy，不含 pywebview（WebView 在 p4a 环境崩溃已验证）
requirements = python3,kivy,pyjnius,android,webdavclient3,lxml==6.0.2,python-dateutil==2.9.0.post0,Pillow

# (str) Presplash of the application
presplash.filename = ../todo_presplash.png

# (str) Icon of the application
icon.filename = ../todo_icon.png

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

fullscreen = 0

# (string) Presplash background color
android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = android.permission.INTERNET,android.permission.POST_NOTIFICATIONS,android.permission.READ_CALENDAR,android.permission.WRITE_CALENDAR

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

# (str) Android entry point (Kivy 默认 PythonActivity)
#android.entrypoint = org.kivy.android.PythonActivity

# (str) XML file to include as an intent filters in <activity> tag
# URL scheme: todolist://
android.manifest.intent_filters = ../scripts/config/url_scheme_intent_filter.xml

# (str) launchMode to set for the main activity
android.manifest.launch_mode = singleTask

# (list) The Android archs to build for
android.archs = arm64-v8a

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1

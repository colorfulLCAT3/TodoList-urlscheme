package com.pywebview.todos.todolist;

import android.content.Intent;
import android.os.Bundle;
import android.view.WindowManager;

import org.kivy.android.PythonActivity;

/**
 * 自定义 Activity，继承 PythonActivity。
 * 通过 onNewIntent 捕获 todolist:// URL scheme 的热启动链接，
 * 存入静态字段 lastUrl 供 Python 侧轮询读取。
 * 冷启动链接仍由 getIntent() 获取。
 *
 * 另外：SDLActivity 启动时会强制开启硬件加速（addFlags FLAG_HARDWARE_ACCELERATED），
 * 覆盖 manifest 的 android:hardwareAccelerated="false"，导致 Android 14/15 上
 * WebView 的 hwuiTask 渲染线程与 SDL 表面冲突崩溃
 * （FORTIFY: pthread_mutex_lock called on a destroyed mutex / SIGABRT）。
 * 这里在 SDL 设置后再清除该标志，强制窗口走软件渲染，绕过崩溃。
 */
public class TodoListActivity extends PythonActivity {
    public static String lastUrl = null;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // SDL 可能已在父类 onCreate 里加回硬件加速标志，这里清一次
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED);
        super.onCreate(savedInstanceState);
        // 父类执行后再清一次，确保 WebView 走软件渲染
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED);
    }

    @Override
    public void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent != null && intent.getData() != null) {
            lastUrl = intent.getDataString();
        }
    }
}

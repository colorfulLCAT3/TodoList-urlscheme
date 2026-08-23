package com.pywebview.todos.todolist;

import android.content.Intent;

import org.kivy.android.PythonActivity;

/**
 * 自定义 Activity，继承 PythonActivity。
 * 通过 onNewIntent 捕获 todolist:// URL scheme 的热启动链接，
 * 存入静态字段 lastUrl 供 Python 侧轮询读取。
 * 冷启动链接仍由 getIntent() 获取。
 */
public class TodoListActivity extends PythonActivity {
    public static String lastUrl = null;

    @Override
    public void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent != null && intent.getData() != null) {
            lastUrl = intent.getDataString();
        }
    }
}

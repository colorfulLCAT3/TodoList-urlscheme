"""
TodoList Android Kivy 应用主逻辑。

复用 backend 的 TodoDatabase / UrlSchemeManager / TaskReminder，
不依赖 pywebview（WebView 在 p4a 环境崩溃已验证）。
"""
import os
import sys
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, ListProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

# 复用后端数据库
from backend.database.operations import TodoDatabase

PRIORITY_COLORS = {
    'high': '#dc3545',
    'medium': '#ffc107',
    'low': '#28a745',
    'none': '#6c757d',
}
PRIORITY_LABELS = {
    'high': '高',
    'medium': '中',
    'low': '低',
    'none': '无',
}


class TaskItem(BoxLayout):
    """单条任务的可视化组件"""
    task_id = StringProperty('')
    task_title = StringProperty('')
    task_desc = StringProperty('')
    task_due = StringProperty('')
    task_priority = StringProperty('none')
    task_completed = BooleanProperty(False)
    category_name = StringProperty('')
    tags_text = StringProperty('')

    def __init__(self, task, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task.get('id', '')
        self.task_title = task.get('title', '')
        self.task_desc = task.get('description') or ''
        due = task.get('dueDate')
        self.task_due = self._fmt_due(due)
        self.task_priority = task.get('priority', 'none')
        self.task_completed = bool(task.get('completed'))
        self.category_name = ''
        self.tags_text = ''
        if task.get('tags'):
            self.tags_text = ' '.join('#' + t.get('name', '') for t in task['tags'])

    @staticmethod
    def _fmt_due(due):
        if not due:
            return ''
        try:
            dt = datetime.fromisoformat(due)
            return dt.strftime('%m-%d %H:%M')
        except Exception:
            return str(due)

    def on_toggle_complete(self, checkbox, value):
        app = App.get_running_app()
        if value is not None:
            app.toggle_task_complete(self.task_id, value)


class TaskListScreen(Screen):
    """任务列表主界面"""

    def on_enter(self, *args):
        app = App.get_running_app()
        app.refresh_tasks()


class TodoListApp(App):
    """TodoList Kivy 应用"""

    title = 'TodoList'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = TodoDatabase()
        self._tasks = []
        self._categories = []
        self._tag_map = {}

    def build(self):
        # 主题色初始
        self.set_theme('dark')
        self.refresh_categories()
        return self._build_ui()

    def _build_ui(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
        from kivy.metrics import dp

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))

        # 顶部：标题 + 操作按钮
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        title = Label(text='TodoList', bold=True, font_size=dp(20))
        add_btn = Button(text='+ 添加', size_hint_x=None, width=dp(80),
                         background_color=get_color_from_hex('#007bff'))
        add_btn.bind(on_release=lambda *a: self.open_add_task())
        header.add_widget(title)
        header.add_widget(add_btn)
        root.add_widget(header)

        # 分类切换行
        cat_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        all_btn = ToggleButton(text='全部', group='cat', state='down', size_hint_x=None, width=dp(60))
        all_btn.bind(on_release=lambda *a: self.filter_by_category(None))
        cat_bar.add_widget(all_btn)
        self.cat_bar = cat_bar
        self.all_cat_btn = all_btn
        root.add_widget(cat_bar)

        # 任务滚动列表
        self.task_container = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.task_container.bind(minimum_height=self.task_container.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.task_container)
        root.add_widget(scroll)

        self._root = root
        self.refresh_categories()
        self.refresh_tasks()
        return root

    # ---------- 主题 ----------
    def set_theme(self, theme):
        self.theme = theme
        from kivy.core.window import Window
        if theme == 'dark':
            Window.clearcolor = get_color_from_hex('#121212')
        else:
            Window.clearcolor = get_color_from_hex('#f5f5f5')

    # ---------- 分类 ----------
    def refresh_categories(self):
        try:
            self._categories = self.db.get_all_categories()
        except Exception:
            self._categories = []
        self._render_category_bar()

    def _render_category_bar(self):
        # 清空旧分类按钮（保留"全部"）
        if not hasattr(self, 'cat_bar'):
            return
        to_remove = [w for w in self.cat_bar.children if w is not self.all_cat_btn]
        for w in to_remove:
            self.cat_bar.remove_widget(w)
        for cat in self._categories:
            btn = ToggleButton(text=cat['name'], group='cat', size_hint_x=None, width=dp(80))
            btn.cat_id = cat['id']
            btn.bind(on_release=lambda b: self.filter_by_category(b.cat_id))
            self.cat_bar.add_widget(btn)

    def filter_by_category(self, category_id):
        self._active_category = category_id
        self.refresh_tasks()

    # ---------- 任务 ----------
    def refresh_tasks(self):
        try:
            if getattr(self, '_active_category', None):
                tasks = self.db.get_tasks_paginated(
                    page=1, page_size=500, category_id=self._active_category
                ).get('tasks', [])
            else:
                tasks = self.db.get_all_tasks()
        except Exception:
            tasks = self.db.get_all_tasks()
        self._tasks = tasks
        self._render_tasks()

    def _render_tasks(self):
        self.task_container.clear_widgets()
        if not self._tasks:
            empty = Label(text='暂无任务\n点击右上角 + 添加', halign='center', valign='middle')
            self.task_container.add_widget(empty)
            return

        cat_map = {c['id']: c['name'] for c in self._categories}
        for task in self._tasks:
            cat_name = cat_map.get(task.get('categoryId'), '')
            item = self._build_task_item(task, cat_name)
            self.task_container.add_widget(item)

    def _build_task_item(self, task, cat_name):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.checkbox import CheckBox
        from kivy.uix.stacklayout import StackLayout
        from kivy.metrics import dp

        box = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(4))
        row1 = BoxLayout(orientation='horizontal', spacing=dp(6))
        cb = CheckBox(active=bool(task.get('completed')), size_hint_x=None, width=dp(40))
        cb.task_id = task.get('id', '')
        cb.bind(active=self._on_complete_change)
        title_lbl = Label(text=task.get('title', ''), bold=True,
                          halign='left', valign='middle', text_size=(None, None))
        title_lbl.bind(size=lambda *a: setattr(title_lbl, 'text_size',
                                               (title_lbl.width, None)))
        if task.get('completed'):
            title_lbl.text = '[s]' + task.get('title', '') + '[/s]'
            title_lbl.markup = True
        row1.add_widget(cb)
        row1.add_widget(title_lbl)

        box.add_widget(row1)

        # 备注
        desc = task.get('description')
        if desc:
            desc_lbl = Label(text=desc, halign='left', valign='top',
                             color=get_color_from_hex('#aaaaaa'), font_size=dp(12))
            desc_lbl.bind(size=lambda *a: setattr(desc_lbl, 'text_size',
                                                  (desc_lbl.width, None)))
            box.add_widget(desc_lbl)

        # 元信息行
        meta = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(22))
        prio = task.get('priority', 'none')
        prio_color = PRIORITY_COLORS.get(prio, '#6c757d')
        meta_lbl = Label(text='', font_size=dp(12), color=get_color_from_hex(prio_color))
        parts = []
        if prio != 'none':
            parts.append('[' + PRIORITY_LABELS.get(prio, prio) + ']')
        if task.get('dueDate'):
            try:
                d = datetime.fromisoformat(task['dueDate'])
                parts.append(d.strftime('%m-%d %H:%M'))
            except Exception:
                pass
        if cat_name:
            parts.append(cat_name)
        if task.get('tags'):
            tag_text = ' '.join('#' + t.get('name', '') for t in task['tags'])
            parts.append(tag_text)
        meta_lbl.text = '  '.join(parts)
        meta.add_widget(meta_lbl)
        box.add_widget(meta)

        # 操作按钮
        ops = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(34))
        edit_btn = Button(text='编辑', size_hint_x=None, width=dp(60))
        edit_btn.task_id = task.get('id', '')
        edit_btn.bind(on_release=lambda b: self.open_edit_task(b.task_id))
        del_btn = Button(text='删除', size_hint_x=None, width=dp(60),
                         background_color=get_color_from_hex('#dc3545'))
        del_btn.task_id = task.get('id', '')
        del_btn.bind(on_release=lambda b: self.confirm_delete_task(b.task_id))
        ops.add_widget(Label())
        ops.add_widget(edit_btn)
        ops.add_widget(del_btn)
        box.add_widget(ops)

        return box

    def _on_complete_change(self, checkbox, value):
        if value is None:
            return
        self.toggle_task_complete(checkbox.task_id, value)

    def toggle_task_complete(self, task_id, completed):
        try:
            self.db.update_task(task_id, {'completed': bool(completed)})
        except Exception:
            pass
        self.refresh_tasks()

    def confirm_delete_task(self, task_id):
        from kivy.uix.popup import Popup
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text='确定删除该任务？'))
        btns = BoxLayout(orientation='horizontal', spacing=dp(8))
        cancel = Button(text='取消')
        ok = Button(text='删除', background_color=get_color_from_hex('#dc3545'))
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content.add_widget(btns)
        popup = Popup(title='删除任务', content=content, size_hint=(0.8, 0.4))
        cancel.bind(on_release=popup.dismiss)
        ok.bind(on_release=lambda *a: (self._do_delete(task_id), popup.dismiss()))
        popup.open()

    def _do_delete(self, task_id):
        try:
            self.db.delete_task(task_id)
        except Exception:
            pass
        self.refresh_tasks()

    # ---------- 添加/编辑任务 ----------
    def open_add_task(self):
        self._open_task_modal(None)

    def open_edit_task(self, task_id):
        task = self.db.get_task(task_id)
        if task:
            self._open_task_modal(task)

    def _open_task_modal(self, task):
        from kivy.uix.popup import Popup
        from kivy.uix.spinner import Spinner
        from kivy.uix.textinput import TextInput
        from kivy.metrics import dp

        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        title_input = TextInput(hint_text='任务标题', text=(task or {}).get('title', ''))
        content.add_widget(title_input)

        desc_input = TextInput(hint_text='备注（可选）', text=(task or {}).get('description', ''),
                               multiline=True, height=dp(70))
        content.add_widget(desc_input)

        # 优先级
        prio_row = BoxLayout(orientation='horizontal', spacing=dp(8))
        prio_row.add_widget(Label(text='优先级', size_hint_x=None, width=dp(60)))
        prio_spinner = Spinner(
            text=(task or {}).get('priority', 'none'),
            values=['none', 'low', 'medium', 'high'],
            size_hint_x=1.0,
        )
        prio_row.add_widget(prio_spinner)
        content.add_widget(prio_row)

        # 分类
        cat_row = BoxLayout(orientation='horizontal', spacing=dp(8))
        cat_row.add_widget(Label(text='分类', size_hint_x=None, width=dp(60)))
        cat_names = ['无'] + [c['name'] for c in self._categories]
        cat_spinner = Spinner(text='无', values=cat_names, size_hint_x=1.0)
        current_cat = (task or {}).get('categoryId')
        if current_cat:
            for c in self._categories:
                if c['id'] == current_cat:
                    cat_spinner.text = c['name']
                    break
        cat_row.add_widget(cat_spinner)
        content.add_widget(cat_row)

        # 截止时间（简单文本输入，格式 YYYY-MM-DD HH:MM）
        due_row = BoxLayout(orientation='horizontal', spacing=dp(8))
        due_row.add_widget(Label(text='开始时间', size_hint_x=None, width=dp(60)))
        due_input = TextInput(hint_text='YYYY-MM-DD HH:MM（可留空）')
        due = (task or {}).get('dueDate')
        if due:
            try:
                due_input.text = datetime.fromisoformat(due).strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass
        due_row.add_widget(due_input)
        content.add_widget(due_row)

        # 按钮
        btns = BoxLayout(orientation='horizontal', spacing=dp(8))
        cancel = Button(text='取消')
        save = Button(text='保存', background_color=get_color_from_hex('#007bff'))
        btns.add_widget(cancel)
        btns.add_widget(save)
        content.add_widget(btns)

        popup = Popup(title='编辑任务' if task else '添加任务', content=content,
                      size_hint=(0.9, 0.7))
        cancel.bind(on_release=popup.dismiss)

        def _save(*a):
            cat_id = None
            for c in self._categories:
                if c['name'] == cat_spinner.text:
                    cat_id = c['id']
                    break
            data = {
                'title': title_input.text.strip(),
                'description': desc_input.text.strip(),
                'priority': prio_spinner.text,
                'categoryId': cat_id,
                'completed': bool((task or {}).get('completed', False)),
            }
            if due_input.text.strip():
                data['dueDate'] = due_input.text.strip()
            if task:
                self.db.update_task(task['id'], data)
            else:
                self.db.add_task(data)
            self.refresh_tasks()
            popup.dismiss()

        save.bind(on_release=_save)
        popup.open()

    # ---------- 供外部（URL/通知）调用的刷新 ----------
    def external_refresh(self):
        """URL scheme 收到数据后刷新列表"""
        self.refresh_categories()
        self.refresh_tasks()

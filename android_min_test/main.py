"""
纯 Kivy 最小测试应用（不含 pywebview）。

用途：二分定位 Android 14/15 启动闪退。
- 若此应用在真机上不闪退 -> 崩溃由 pywebview/WebView 叠加 SDL 引起
- 若此应用也闪退       -> 崩溃是 Kivy/SDL bootstrap 与 Android 14/15 的通用问题
"""
from kivy.app import App
from kivy.uix.label import Label


class MinTestApp(App):
    def build(self):
        return Label(
            text='Minimal Kivy Test\nIf you see this, Kivy/SDL is fine',
            font_size='24sp',
            halign='center',
            valign='middle',
        )


if __name__ == '__main__':
    MinTestApp().run()

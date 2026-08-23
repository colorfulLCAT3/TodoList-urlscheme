# backend/api/mixins/urlscheme_mixin.py
import json

import backend.globals
from backend.features.urlscheme.url_scheme import UrlSchemeManager

class UrlSchemeMixin:
    """URL scheme 接收待办 Mixin"""

    def start_url_scheme_listener(self):
        """启动平台 URL 监听，收到 URL 后入库并刷新前端"""
        try:
            self.service.start_url_listener(self._handle_incoming_url)
            self.get_logger.info("[URLScheme] 已启动 URL 监听")
        except Exception as e:
            self.get_logger.error(f"[URLScheme] 启动 URL 监听失败: {e}")

    def _handle_incoming_url(self, url: str):
        """处理收到的 URL：入库 + 显示主窗口 + 通知前端刷新"""
        try:
            result = self._url_scheme_manager.handle_url(url)
            self._show_main_window()
            self._notify_frontend(result)
        except Exception as e:
            self.get_logger.error(f"[URLScheme] 处理 URL 异常: {e}")

    def _show_main_window(self):
        """唤起时显示主窗口：隐藏时显示，最小化时还原"""
        try:
            window = backend.globals.window
            if not window:
                return
            try:
                window.restore()
            except Exception:
                pass
            window.show()
            self.get_logger.info("[URLScheme] 已唤起主窗口")
        except Exception as e:
            self.get_logger.warning(f"[URLScheme] 显示主窗口失败: {e}")

    def _notify_frontend(self, result: dict):
        """通过 JS 通知前端刷新任务列表并提示"""
        try:
            window = backend.globals.window
            if not window:
                return
            added = result.get('added', 0)
            skipped = result.get('skipped', 0)
            if added > 0:
                message = f"已通过链接添加 {added} 个待办"
                if skipped > 0:
                    message += f"，跳过 {skipped} 条无效数据"
            else:
                message = "链接中没有有效的待办数据" if skipped else "链接解析失败"
            js_message = json.dumps(message, ensure_ascii=False)
            js_str = f"""
                if (window.todoManager) {{ window.todoManager.loadTasks(); }}
                if (window.Utils) {{ window.Utils.showToast({js_message}, 'success'); }}
            """
            window.evaluate_js(js_str)
        except Exception as e:
            self.get_logger.error(f"[URLScheme] 通知前端失败: {e}")

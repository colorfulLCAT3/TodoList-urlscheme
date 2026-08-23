# impl/desktop/mac_impl.py

import sys
from pathlib import Path
from backend.platforms.impl.desktop.common.common_impl import DesktopCommonService

class MacService(DesktopCommonService):
    def force_kill_process_tree(self, pid):
        """强制结束当前进程及其所有子进程的统一接口"""
        import subprocess
        import time
        # 优雅终止 (SIGTERM)
        subprocess.run(['kill', '-TERM', str(pid)])
        time.sleep(2)
        # 强制终止 (SIGKILL)
        subprocess.run(['kill', '-KILL', str(pid)])
        # 强制终止所有子进程，使用 pgrep -P 查找并传递给 kill -9[reference:5]
        subprocess.run(f'pgrep -P {pid} | xargs kill -9', shell=True)

    def get_log_directory(self):
        """返回可写的日志目录的统一接口"""
        # macOS: 使用 ~/Library/Logs/TodoList
        home = Path.home()
        log_dir = home / 'Library' / 'Logs' / 'TodoList'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_app_icon(self, base_path):
        """获取应用图标的统一接口"""
        return base_path / 'todo_icon.icns'

    def is_ssl_enable(self):
        """获取是否开启ssl的统一接口"""
        # MacOS端开启后存在不影响使用的warning
        return False

    def start_prepare(self):
        """应用启动前准备工作的统一接口"""
        # 强制在主线程预热 TIS API，防止后台线程后续并发调用导致崩溃
        import ctypes
        import ctypes.util

        try:
            # 加载 Carbon 框架并调用一次获取当前输入源
            carbon = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Carbon.framework/Carbon')
            carbon.TISCopyCurrentKeyboardInputSource()
        except Exception:
            pass

    def _enable_auto_start_impl(self) -> bool:
        """macOS平台启用自启动"""
        from backend.utils import utils
        app_path = utils.get_app_path(self)
        try:
            # LaunchAgents目录
            launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
            launch_agents_dir.mkdir(parents=True, exist_ok=True)

            # plist文件路径
            plist_file = launch_agents_dir / f"com.{self.APP_NAME.lower()}.plist"

            # 日志目录
            log_dir = Path.home() / '.local' / 'var' / 'log'
            log_dir.mkdir(parents=True, exist_ok=True)

            # 直接启动应用
            # plist文件内容
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
    <key>Label</key>
    <string>com.{self.APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{log_dir}/{self.APP_NAME}.out.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/{self.APP_NAME}.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>{Path(app_path).parent}</string>
    <key>StartInterval</key>
    <integer>0</integer>
    <key>LaunchOnlyOnce</key>
    <true/>
    </dict>
    </plist>
    """

            with open(plist_file, 'w', encoding='utf-8') as f:
                f.write(plist_content)

            self.backend_logger().info(f"macOS开机自启动已启用: {plist_file}")
            return True

        except Exception as e:
            self.backend_logger().error(f"macOS启用自启动失败: {e}")
            return False

    def _disable_auto_start_impl(self) -> bool:
        """macOS平台禁用自启动"""
        try:
            # LaunchAgents目录
            launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
            plist_file = launch_agents_dir / f"com.{self.APP_NAME.lower()}.plist"

            if plist_file.exists():
                # 删除plist文件
                plist_file.unlink()

            # 删除启动脚本
            script_file = Path.home() / '.local' / 'bin' / f"{self.APP_NAME}_start.sh"
            if script_file.exists():
                script_file.unlink()

            self.backend_logger().info("macOS开机自启动已禁用")
            return True

        except Exception as e:
            self.backend_logger().error(f"macOS禁用自启动失败: {e}")
            return False

    def start_app(self):
        """启动应用的统一接口"""
        from backend.platforms.impl.desktop.common.system_tray import SystemTrayManager
        manager = SystemTrayManager()
        manager.start_app(False) # Mac端开启SSL存在warning告警

# 用于给工厂注册的导出变量
ExportService = MacService

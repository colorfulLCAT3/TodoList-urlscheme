# impl/desktop/win_impl.py
import os
from pathlib import Path
from backend.platforms.impl.desktop.common.common_impl import DesktopCommonService

class WindowsService(DesktopCommonService):
    def force_kill_process_tree(self, pid):
        """强制结束当前进程及其所有子进程的统一接口"""
        import subprocess
        import time
        # --- Windows ---
        # 优雅终止 (SIGTERM)
        subprocess.run(f'taskkill /PID {pid} /T', shell=True)
        time.sleep(2)
        # 强制终止 (SIGKILL)
        subprocess.run(f'taskkill /F /T /PID {pid}', shell=True, capture_output=True)

    def get_log_directory(self):
        """返回可写的日志目录的统一接口"""
        import sys
        # Windows: exe 同级目录（用户通常有写权限）
        exe_dir = Path(sys.executable).parent
        log_dir = exe_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_app_icon(self, base_path):
        """获取应用图标的统一接口"""
        return base_path / 'todo_icon.ico'

    def start_prepare(self):
        """应用启动前准备工作的统一接口"""
        pass

    def _enable_auto_start_impl(self) -> bool:
        """启用开机自启动"""
        from backend.utils import utils
        app_path = utils.get_app_path(self)

        try:
            import winreg

            # 启动命令
            launch_cmd = utils.get_launch_command(self)

            # 注册表路径
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            # 打开注册表键
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                # 设置注册表值
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, launch_cmd)

            self.backend_logger().info(f"Windows开机自启动已启用: {launch_cmd}")
            return True

        except ImportError:
            # 备用方案：使用启动文件夹
            startup_folder = Path(
                os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
            startup_folder.mkdir(parents=True, exist_ok=True)

            # 创建快捷方式
            shortcut_path = startup_folder / f"{self.APP_NAME}.lnk"

            # 使用Python创建快捷方式
            import pythoncom
            from win32com.client import Dispatch

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortcut(str(shortcut_path))
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = str(Path(app_path).parent)

            shortcut.save()

            self.backend_logger().warning(f"Windows启动文件夹快捷方式已创建: {shortcut_path}")

            return True
        except Exception as e:
            self.backend_logger().error(f"启用开机自启动失败: {e}")
            return False

    def _disable_auto_start_impl(self) -> bool:
        """禁用开机自启动"""
        try:
            import winreg

            # 注册表路径
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            # 尝试删除注册表项
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.DeleteValue(key, self.APP_NAME)
            except FileNotFoundError:
                # 注册表项不存在，继续检查启动文件夹
                pass

            # 删除启动文件夹中的快捷方式和批处理文件
            startup_folder = Path(
                os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'

            # 删除快捷方式
            shortcut_path = startup_folder / f"{self.APP_NAME}.lnk"
            if shortcut_path.exists():
                shortcut_path.unlink()

            # 删除批处理文件
            bat_path = startup_folder / f"{self.APP_NAME}.bat"
            if bat_path.exists():
                bat_path.unlink()

            self.backend_logger().info("Windows开机自启动已禁用")
            return True

        except Exception as e:
            self.backend_logger().error(f"Windows禁用自启动失败: {e}")
            return False

    def register_url_scheme(self):
        """注册 todolist:// URL scheme 到当前用户"""
        from backend.features.urlscheme.url_scheme import URL_SCHEME
        from backend.utils import utils
        import winreg

        try:
            launch_cmd = utils.get_launch_command(self) + f' --url "%1"'

            # HKCU\Software\Classes\todolist
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                    rf"Software\Classes\{URL_SCHEME}",
                                    0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"URL:{URL_SCHEME} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

            # HKCU\Software\Classes\todolist\shell\open\command
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                    rf"Software\Classes\{URL_SCHEME}\shell\open\command",
                                    0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, launch_cmd)

            self.backend_logger().info(f"URL scheme {URL_SCHEME}:// 已注册: {launch_cmd}")
            return True
        except Exception as e:
            self.backend_logger().error(f"注册 URL scheme 失败: {e}")
            return False

    def start_url_listener(self, callback):
        """监听本机 URL scheme 转发端口，收到 URL 时回调 callback(url)"""
        from backend.features.urlscheme.url_scheme import LISTENER_PORT
        import socket
        import struct
        import threading

        def receive_all(sock, length):
            data = bytearray()
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data.extend(chunk)
            return bytes(data)

        def handle_client(sock):
            try:
                length_data = receive_all(sock, 4)
                if not length_data:
                    return
                length = struct.unpack('!I', length_data)[0]
                if length <= 0 or length > 10 * 1024 * 1024:
                    return
                data_bytes = receive_all(sock, length)
                if not data_bytes:
                    return
                url = data_bytes.decode('utf-8')
                self.backend_logger().info(f"收到 URL scheme 转发: {url[:120]}")
                try:
                    callback(url)
                except Exception as e:
                    self.backend_logger().error(f"处理 URL 回调异常: {e}")
            except Exception as e:
                self.backend_logger().error(f"URL 监听处理连接异常: {e}")
            finally:
                try:
                    sock.close()
                except Exception:
                    pass

        def listen_loop():
            import time
            server_socket = None
            while True:
                try:
                    if server_socket is None:
                        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        server_socket.bind(('127.0.0.1', LISTENER_PORT))
                        server_socket.listen(5)
                        self.backend_logger().info(f"URL 监听已启动: 127.0.0.1:{LISTENER_PORT}")
                    server_socket.settimeout(1.0)
                    client_socket, _ = server_socket.accept()
                    thread = threading.Thread(target=handle_client, args=(client_socket,), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except OSError as e:
                    self.backend_logger().warning(f"URL 监听启动失败（可能已有实例在监听）: {e}")
                    server_socket = None
                    time.sleep(5)
                except Exception as e:
                    self.backend_logger().error(f"URL 监听异常: {e}")
                    server_socket = None
                    time.sleep(5)

        threading.Thread(target=listen_loop, daemon=True).start()

    def dispatch_url_to_running_instance(self, url):
        """把 URL 转发给已运行实例，成功返回 True"""
        from backend.features.urlscheme.url_scheme import LISTENER_PORT
        import socket
        import struct

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(('127.0.0.1', LISTENER_PORT))
            data_bytes = url.encode('utf-8')
            sock.sendall(struct.pack('!I', len(data_bytes)) + data_bytes)
            sock.close()
            self.backend_logger().info(f"已转发 URL 到运行中的实例")
            return True
        except Exception as e:
            self.backend_logger().info(f"无运行中实例，由本进程接管: {e}")
            return False

    def start_app(self):
        """启动应用的统一接口"""
        from backend.platforms.impl.desktop.common.system_tray import SystemTrayManager
        manager = SystemTrayManager()
        manager.start_app(True)

# 用于给工厂注册的导出变量
ExportService = WindowsService

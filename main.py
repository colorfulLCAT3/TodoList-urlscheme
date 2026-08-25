#!/usr/bin/env python3
"""
TodoList桌面应用启动脚本
"""

import sys
import os
import time
from pathlib import Path

# 1. 代码根目录（只读）与数据存储目录（可写）分离
project_root = Path(__file__).parent

# 检查是否在打包环境（AppImage / PyInstaller 单文件模式）下运行
if hasattr(sys, '_MEIPASS'):
    # 如果是打包环境，将可写目录指向用户家目录下的 .todolist 文件夹
    data_dir = Path.home() / '.todolist'
else:
    # 如果是本地开发环境，依然保存在项目根目录下
    data_dir = project_root

# 2. 在安全的可写路径下创建 backend 文件夹
backend_dir = data_dir / 'backend'
Path(backend_dir).mkdir(parents=True, exist_ok=True)  # 此时不会再报只读错误

# 3. 将【代码】的 backend 目录添加到 Python 路径（依然从解压后的只读路径读取代码）
code_backend_dir = project_root / 'backend'
if str(code_backend_dir) not in sys.path:
    sys.path.insert(0, str(code_backend_dir))

# 4. 切换到可写的工作目录
os.chdir(str(data_dir))

from backend.platforms.core.factory import get_platform_service
service = get_platform_service()
backend_logger = service.backend_logger()
service.start_prepare()

def handle_startup_url():
    """解析 --url 参数：已运行则转发后退出，否则交由本进程处理"""
    import backend.globals

    url = None
    args = sys.argv[1:]
    if '--url' in args:
        idx = args.index('--url')
        if idx + 1 < len(args):
            url = args[idx + 1]
    if not url:
        return

    # 尝试转发给已运行实例（主实例可能尚未启动监听，短暂重试）
    for _ in range(5):
        if service.dispatch_url_to_running_instance(url):
            backend_logger.info("URL 已转发给运行中的实例，退出本进程")
            sys.exit(0)
        time.sleep(0.4)

    backend_logger.info("无运行中的实例，URL 由本进程处理")
    backend.globals.pending_url = url

if __name__ == '__main__':
    # Android logcat 抓取用标记：优先用 jnius android.util.Log（100%进logcat）
    from backend.utils.android_log import log as _android_log
    _android_log("main.py __main__ 开始执行 (Python 已启动)")
    print("[MAIN-DEBUG] main.py __main__ 开始执行", flush=True)
    try:
        from backend import start

        _android_log("backend.start 导入成功")
        print("[MAIN-DEBUG] backend.start 导入成功", flush=True)
        backend_logger.info("=" * 60)
        backend_logger.info("从 main.py 启动 TodoList 应用")
        backend_logger.info("=" * 60)

        handle_startup_url()
        print("[MAIN-DEBUG] handle_startup_url 完成，准备 service.start_app()", flush=True)
        service.start_app()
        print("[MAIN-DEBUG] service.start_app() 返回（不应到达，Android 上应阻塞）", flush=True)

    except ImportError as e:
        print(f"[MAIN-DEBUG] 导入错误: {e}", flush=True)
        print(f"导入错误: {e}")
        print("请检查Python环境是否正确安装了依赖：pip install pywebview")
        sys.exit(1)
    except Exception as e:
        print(f"[MAIN-DEBUG] 启动应用失败: {e}", flush=True)
        print(f"启动应用失败: {e}")
        sys.exit(1)
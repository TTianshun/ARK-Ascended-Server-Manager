"""
ARK: Survival Ascended Server Manager 主程序入口
"""
import os
import sys
import tkinter as tk
import subprocess
from pathlib import Path

# 确保可以找到模块 (支持从任何地方运行)
_current_dir = Path(__file__).parent.parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from ark_asa_manager.ui import ServerManagerApp, configure_theme
from ark_asa_manager.utils import setup_logger, get_logger
from ark_asa_manager.utils.constants import (
    APP_NAME,
    APPDATA_DIR_NAME,
    LOG_DIR_NAME,
    LOG_FILE_NAME,
)


def get_app_base_dir() -> Path:
    """获取应用基目录"""
    if os.name == 'nt':
        # Windows: %APPDATA%
        appdata = Path(os.environ.get('APPDATA', Path.home()))
        return appdata / APPDATA_DIR_NAME
    else:
        # Linux/Mac: ~/.config
        return Path.home() / '.config' / APPDATA_DIR_NAME.lower()


def _is_windows_admin() -> bool:
    """Check whether current process has admin rights on Windows."""
    if os.name != "nt":
        return True
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin() -> bool:
    """Relaunch current app with admin rights on Windows."""
    if os.name != "nt":
        return False

    try:
        import ctypes

        if getattr(sys, "frozen", False):
            executable = sys.executable
            params = subprocess.list2cmdline(sys.argv[1:])
        else:
            executable = sys.executable
            params = subprocess.list2cmdline([str(Path(__file__).resolve())] + sys.argv[1:])

        rc = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            params,
            None,
            1,
        )
        return rc > 32
    except Exception:
        return False


def ensure_admin_or_exit() -> None:
    """Ensure admin privileges on Windows; relaunch elevated and exit current process."""
    if os.name != "nt":
        return

    if _is_windows_admin():
        return

    if _relaunch_as_admin():
        sys.exit(0)

    print("需要管理员权限才能启动应用。请允许 UAC 提权后重试。")
    sys.exit(1)


def launch() -> None:
    """直接启动应用"""
    ensure_admin_or_exit()

    # 初始化
    app_base = get_app_base_dir()
    log_dir = app_base / LOG_DIR_NAME
    setup_logger(log_dir, LOG_FILE_NAME)
    
    logger = get_logger(__name__)
    logger.info(f"{APP_NAME} 启动")
    
    # 创建GUI
    root = tk.Tk()
    configure_theme(root)
    ServerManagerApp(root, app_base)
    
    # 启动
    root.mainloop()


if __name__ == "__main__":
    launch()
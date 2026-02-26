"""
ARK: Survival Ascended Server Manager 主程序入口
"""
import os
import sys
import tkinter as tk
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


def launch() -> None:
    """直接启动应用"""
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
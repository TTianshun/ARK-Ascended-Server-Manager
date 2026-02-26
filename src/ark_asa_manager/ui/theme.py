"""
UI主题和样式配置
"""
import tkinter as tk
from pathlib import Path
from tkinter import ttk


def configure_theme(root: tk.Tk) -> None:
    """配置现代主题"""
    style = ttk.Style()
    
    # 设置主题
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    
    # 定义颜色
    colors = {
        'bg': '#f0f0f0',
        'fg': '#333333',
        'accent': '#0078d4',
        'success': '#107c10',
        'warning': '#ffb900',
        'error': '#d13438',
    }
    
    # 配置样式
    style.configure('TButton', font=('Segoe UI', 9))
    style.configure('TLabel', font=('Segoe UI', 9))
    style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
    
    root.configure(bg=colors['bg'])


def apply_window_icon(root: tk.Tk, icon_path: str = "") -> None:
    """设置窗口图标"""
    try:
        if icon_path and Path(icon_path).exists():
            root.iconbitmap(default=icon_path)
    except Exception:
        pass
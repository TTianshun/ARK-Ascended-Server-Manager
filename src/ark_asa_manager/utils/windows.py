"""
Windows系统操作
"""
import os
import subprocess
import subprocess as sp
from typing import Optional
from pathlib import Path


def is_admin() -> bool:
    """检查是否以管理员身份运行"""
    try:
        import ctypes
        return ctypes.windll.shell.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """以管理员身份重新启动"""
    try:
        import ctypes
        ctypes.windll.shell.ShellExecuteEx(
            lpVerb='runas',
            lpFile=__file__,
            nShow=1
        )
        return True
    except Exception:
        return False


def run_process(
    cmd: list,
    capture_output: bool = False,
    shell: bool = False,
    cwd: Optional[Path] = None
) -> sp.CompletedProcess:
    """运行进程"""
    kwargs = {
        "shell": shell,
    }
    if cwd:
        kwargs["cwd"] = str(cwd)
    if capture_output:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    
    # Windows下隐藏控制台窗口
    if os.name == 'nt':
        kwargs["creationflags"] = sp.CREATE_NO_WINDOW
    
    return sp.run(cmd, **kwargs)


def get_process_info(pid: int) -> dict:
    """获取进程信息"""
    try:
        import psutil
        p = psutil.Process(pid)
        return {
            "pid": p.pid,
            "name": p.name(),
            "status": p.status(),
            "memory_mb": p.memory_info().rss / 1024 / 1024,
            "cpu_percent": p.cpu_percent(),
        }
    except Exception:
        return {}

"""ARK: Survival Ascended Server Manager 主程序入口"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".write_test_{os.getpid()}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)  # type: ignore[arg-type]
        return True
    except Exception:
        return False


def _portable_base_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except Exception:
        return Path.cwd()


def _programdata_base() -> Path:
    from ark_asa_manager.utils.constants import APPDATA_DIR_NAME
    return Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / APPDATA_DIR_NAME


def _appdata_base() -> Path:
    from ark_asa_manager.utils.constants import APPDATA_DIR_NAME
    return Path(os.environ.get("APPDATA", str(Path.home()))) / APPDATA_DIR_NAME


def get_app_base_dir() -> Path:
    """获取应用基目录（与 legacy 逻辑对齐）。"""
    if os.name != "nt":
        return _appdata_base()

    shared = _programdata_base()
    if _is_writable_dir(shared):
        return shared

    user = _appdata_base()
    if _is_writable_dir(user):
        return user

    portable = _portable_base_dir() / "ARK-Ascended-Server-Manager"
    portable.mkdir(parents=True, exist_ok=True)
    return portable


def _migrate_user_appdata_to_target_if_needed(target_base: Path) -> None:
    """
    一次性迁移：当目标目录还没有配置时，从 APPDATA 位置复制旧配置。
    """
    try:
        from ark_asa_manager.utils.constants import GLOBAL_CONFIG_NAME, SERVERS_DIR_NAME

        target_global = target_base / GLOBAL_CONFIG_NAME
        if target_global.exists():
            return

        source_base = _appdata_base()
        source_global = source_base / GLOBAL_CONFIG_NAME
        if not source_global.exists() or source_base.resolve() == target_base.resolve():
            return

        target_base.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_global, target_global)

        source_servers = source_base / SERVERS_DIR_NAME
        target_servers = target_base / SERVERS_DIR_NAME
        if source_servers.exists() and not target_servers.exists():
            shutil.copytree(source_servers, target_servers, dirs_exist_ok=True)
    except Exception:
        pass


def _is_windows_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin() -> bool:
    if os.name != "nt":
        return False

    try:
        import ctypes

        if getattr(sys, "frozen", False):
            executable = sys.executable
            params = subprocess.list2cmdline(sys.argv[1:])
        else:
            executable = sys.executable
            # src layout 下直接执行 __main__.py 会丢失包导入路径，
            # 因此提权后统一通过项目根目录 RUN.py 入口启动。
            run_py = Path(__file__).resolve().parents[2] / "RUN.py"
            params = subprocess.list2cmdline([str(run_py)] + sys.argv[1:])

        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        return rc > 32
    except Exception:
        return False


def ensure_admin_or_exit() -> None:
    if os.name != "nt":
        return
    if _is_windows_admin():
        return
    if _relaunch_as_admin():
        sys.exit(0)
    print("需要管理员权限才能启动应用。请允许 UAC 提权后重试。")
    sys.exit(1)


def _launch_modular_fallback() -> None:
    from ark_asa_manager.ui import ServerManagerApp, configure_theme
    from ark_asa_manager.utils import setup_logger, get_logger
    from ark_asa_manager.utils.constants import APP_NAME, LOG_DIR_NAME, LOG_FILE_NAME

    ensure_admin_or_exit()

    app_base = get_app_base_dir()
    _migrate_user_appdata_to_target_if_needed(app_base)
    log_dir = app_base / LOG_DIR_NAME
    setup_logger(log_dir, LOG_FILE_NAME)

    logger = get_logger(__name__)
    logger.info(f"{APP_NAME} 启动")

    root = tk.Tk()
    configure_theme(root)
    ServerManagerApp(root, app_base)
    root.mainloop()


def launch() -> None:
    _launch_modular_fallback()


if __name__ == "__main__":
    launch()
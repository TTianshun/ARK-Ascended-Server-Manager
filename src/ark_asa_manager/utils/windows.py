"""
Windows 系统操作工具集
"""
import logging
import os
import re
import subprocess
import ssl
import sys
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from urllib.request import Request, urlopen

from .constants import (
    AMAZON_R2M02_URL,
    AMAZON_ROOT_CA1_URL,
    DIRECTX_LEGACY_DLLS,
    DOWNLOAD_TIMEOUT_SEC,
    DXWEBSETUP_URL,
    VC_REDIST_X64_URL,
)

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

try:
    import winreg  # type: ignore
except ImportError:
    winreg = None  # type: ignore


# ---------------------------------------------------------------------------
# 管理员检查
# ---------------------------------------------------------------------------

def is_admin() -> bool:
    """检查当前进程是否以管理员身份运行"""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """以管理员身份重新启动当前程序"""
    if os.name != "nt":
        return False
    if is_admin():
        return True
    try:
        import ctypes
        exe = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return int(rc) > 32
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 进程输出流式读取（实时写入 logger）
# ---------------------------------------------------------------------------

def stream_process_output(
    cmd: List[str],
    logger: logging.Logger,
    cwd: Optional[Path] = None,
    timeout_s: int = 0,
    log_prefix: str = "",
) -> Tuple[int, str]:
    """
    启动子进程，将 stdout/stderr 实时输出到 logger，
    同时返回 (returncode, 全部输出文本)。
    """
    logger.info(" ".join(cmd))
    p = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        creationflags=_CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    assert p.stdout is not None

    start = time.time()
    buf = b""
    collected: List[str] = []
    last_line = ""
    last_emit_t = 0.0

    def emit(line: str) -> None:
        nonlocal last_line, last_emit_t
        s = line.strip("\r\n")
        if not s:
            return
        now = time.time()
        # 轻度节流：高频进度行相同内容不超过 0.25s 重复
        if s == last_line and (now - last_emit_t) < 0.25:
            return
        last_line = s
        last_emit_t = now
        msg = f"{log_prefix}{s}" if log_prefix else s
        collected.append(msg)
        logger.info(msg)

    while True:
        if timeout_s > 0 and (time.time() - start) > timeout_s:
            try:
                p.kill()
            except Exception:
                pass
            emit("进程超时，已强制终止")
            break

        chunk = p.stdout.read(4096)
        if not chunk:
            break

        buf += chunk
        while True:
            m = re.search(rb"[\r\n]", buf)
            if not m:
                break
            idx = m.start()
            line = buf[:idx]
            sep = buf[idx : idx + 1]
            buf = buf[idx + 1 :]
            try:
                emit(line.decode("utf-8", errors="replace"))
            except Exception:
                pass
            if sep == b"\r":
                continue

    if buf:
        try:
            emit(buf.decode("utf-8", errors="replace"))
        except Exception:
            pass

    code = p.wait()
    return code, "\n".join(collected)


def run_quiet(
    cmd: List[str], cwd: Optional[Path] = None
) -> Tuple[int, str]:
    """安静地运行命令，返回 (returncode, 合并后输出)"""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            creationflags=_CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return p.returncode, out.strip()
    except Exception as e:
        return 1, str(e)


# ---------------------------------------------------------------------------
# SSL 安全下载
# ---------------------------------------------------------------------------

def download_file(
    url: str,
    dest: Path,
    logger: logging.Logger,
    timeout: int = DOWNLOAD_TIMEOUT_SEC,
) -> None:
    """下载文件并原子写入，使用 certifi SSL 证书（若已安装）"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"下载: {url}")

    ctx = ssl.create_default_context()
    try:
        import certifi  # type: ignore
        ctx.load_verify_locations(cafile=certifi.where())
    except Exception:
        pass

    req = Request(url, headers={"User-Agent": "ARK-ASA-Manager/1.0"})
    with urlopen(req, timeout=timeout, context=ctx) as r:
        data = r.read()

    if not data:
        raise RuntimeError("下载响应为空")

    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    logger.info(f"已保存: {dest}")


# ---------------------------------------------------------------------------
# PowerShell 查找
# ---------------------------------------------------------------------------

def _find_powershell() -> Optional[str]:
    if os.name != "nt":
        return None
    for c in ["powershell.exe", "powershell", "pwsh.exe", "pwsh"]:
        try:
            p = subprocess.run(
                ["where", c],
                capture_output=True,
                text=True,
                creationflags=_CREATE_NO_WINDOW,
            )
            if p.returncode == 0:
                return c
        except Exception:
            continue
    return "powershell.exe"


# ---------------------------------------------------------------------------
# Windows 注册表辅助
# ---------------------------------------------------------------------------

def _reg_open_key_64(hive, path: str):
    """打开 64 位注册表视图"""
    if winreg is None:
        raise ImportError("winreg not available")
    return winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)


# ---------------------------------------------------------------------------
# VC++ / DirectX 检测与安装
# ---------------------------------------------------------------------------

def vc14_x64_version() -> Optional[str]:
    """返回已安装的 VC++ 14 x64 版本号，未安装则返回 None"""
    if winreg is None:
        return None
    try:
        key_path = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
        with _reg_open_key_64(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            installed, _ = winreg.QueryValueEx(key, "Installed")
            version, _ = winreg.QueryValueEx(key, "Version")
            if int(installed) == 1:
                return str(version)
            return None
    except Exception:
        return None


def directx_registry_present() -> bool:
    """检查 DirectX 注册表项是否存在"""
    if winreg is None:
        return False
    try:
        with _reg_open_key_64(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectX"):
            return True
    except Exception:
        return False


def has_directx_legacy(min_hits: int = 1) -> bool:
    """检查 DirectX 遗留 DLL 是否存在"""
    if os.name != "nt":
        return False
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates = [Path(windir) / "System32", Path(windir) / "SysWOW64"]
    hits = 0
    for folder in candidates:
        for dll in DIRECTX_LEGACY_DLLS:
            if (folder / dll).exists():
                hits += 1
    return hits >= min_hits


def install_vcredist(logger: logging.Logger) -> None:
    """下载并静默安装 VC++ Redistributable x64"""
    temp = Path(os.environ.get("TEMP", str(Path.home() / "AppData/Local/Temp")))
    exe = temp / "vc_redist.x64.exe"
    download_file(VC_REDIST_X64_URL, exe, logger)
    code, _ = stream_process_output(
        [str(exe), "/install", "/passive", "/norestart"], logger
    )
    logger.info(f"VC++ 安装程序退出码: {code}")


def install_directx_web(logger: logging.Logger) -> None:
    """下载并静默安装 DirectX Web Setup"""
    temp = Path(os.environ.get("TEMP", str(Path.home() / "AppData/Local/Temp")))
    exe = temp / "dxwebsetup.exe"
    download_file(DXWEBSETUP_URL, exe, logger)
    code, _ = stream_process_output([str(exe), "/Q"], logger)
    logger.info(f"DirectX Web 安装程序退出码: {code}")


def install_asa_certificates(logger: logging.Logger) -> None:
    """
    下载 Amazon 根证书（AmazonRootCA1 + r2m02）并导入 Windows 证书存储。
    使用 PowerShell Import-Certificate（对 Defender 更友好）。
    """
    if os.name != "nt":
        logger.info("证书安装已跳过：仅支持 Windows。")
        return

    ps_exe = _find_powershell()
    if not ps_exe:
        raise RuntimeError("未找到 PowerShell，无法导入证书。")

    temp = Path(os.environ.get("TEMP", str(Path.home() / "AppData/Local/Temp")))
    root_path = temp / f"AmazonRootCA1_{os.getpid()}.cer"
    r2m02_path = temp / f"r2m02_{os.getpid()}.cer"

    download_file(AMAZON_ROOT_CA1_URL, root_path, logger)
    download_file(AMAZON_R2M02_URL, r2m02_path, logger)

    if is_admin():
        root_store = r"Cert:\LocalMachine\Root"
        ca_store = r"Cert:\LocalMachine\CA"
        logger.info("证书导入：LocalMachine 存储区（管理员模式）。")
    else:
        root_store = r"Cert:\CurrentUser\Root"
        ca_store = r"Cert:\CurrentUser\CA"
        logger.info("证书导入：CurrentUser 存储区（非管理员模式）。")

    def import_cert(cer_path: Path, store: str) -> None:
        ps = (
            f"Import-Certificate -FilePath '{cer_path}'"
            f" -CertStoreLocation '{store}' | Out-Null"
        )
        code, out = run_quiet(
            [ps_exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps]
        )
        if code != 0:
            msg = out.splitlines()[-1].strip() if out else "Import-Certificate 失败"
            raise RuntimeError(f"证书导入失败 {cer_path.name} → {store}: {msg}")

    logger.info("正在安装证书：AmazonRootCA1 → Root，r2m02 → CA")
    import_cert(root_path, root_store)
    import_cert(r2m02_path, ca_store)
    logger.info("证书安装/更新成功。")

    for p in (root_path, r2m02_path):
        try:
            p.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


def ensure_dependencies(logger: logging.Logger) -> None:
    """
    检测并安装 ASA 服务器所需的运行时依赖（VC++、DirectX）。
    在首次安装流程中调用。
    """
    v = vc14_x64_version()
    if v:
        logger.info(f"VC++ v14 x64 已就绪 (Version={v})")
    else:
        logger.info("VC++ v14 x64 未安装 → 正在安装...")
        install_vcredist(logger)

    dx_reg = directx_registry_present()
    dx_legacy = has_directx_legacy()

    if dx_reg and dx_legacy:
        logger.info("DirectX 遗留库已就绪（注册表 + 遗留 DLL 均已检测到）")
    else:
        logger.info(
            f"DirectX 检查：registry={dx_reg} legacy_dlls={dx_legacy} → 正在安装 DirectX..."
        )
        install_directx_web(logger)
        if has_directx_legacy():
            logger.info("DirectX 遗留库安装后已就绪")
        else:
            logger.info("DirectX 遗留 DLL 安装后仍未检测到（部分系统属正常现象）。")

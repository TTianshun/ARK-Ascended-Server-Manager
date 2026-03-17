"""
SteamCMD 管理：下载、安装、更新 ASA 服务器。
"""
import logging
import os
import re
import shutil
import stat
import tempfile
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from ..utils.constants import ARK_ASA_APP_ID, LOCKS_DIR_NAME, STEAMCMD_ZIP_URL
from ..utils.windows import download_file, stream_process_output

_CREATE_NO_WINDOW = getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0)


# ---------------------------------------------------------------------------
# 文件锁（Windows msvcrt）
# ---------------------------------------------------------------------------

@contextmanager
def exclusive_file_lock(lock_path: Path, timeout_s: int = 900, poll_s: float = 0.25):
    """跨进程互斥文件锁，用于防止多个 SteamCMD 实例并发运行"""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "a+", encoding="utf-8")
    start = time.time()

    if os.name == "nt":
        import msvcrt  # type: ignore

        while True:
            try:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.time() - start > timeout_s:
                    fh.close()
                    raise TimeoutError(f"等待锁超时: {lock_path}")
                time.sleep(poll_s)
        try:
            yield
        finally:
            try:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                fh.close()
    else:
        try:
            yield
        finally:
            fh.close()


# ---------------------------------------------------------------------------
# SteamCMD 路径
# ---------------------------------------------------------------------------

def resolve_steamcmd_exe(steamcmd_root: str) -> Path:
    """在可能的子目录中查找 steamcmd.exe"""
    root = Path(steamcmd_root)
    candidates = [
        root / "steamcmd.exe",
        root / "SteamCMD" / "steamcmd.exe",
        root / "steamcmd" / "steamcmd.exe",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]  # 未找到时返回默认路径


def _safe_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """安全解压 ZIP 文件，防止路径穿越攻击"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_real = dest_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zf:
        for zi in zf.infolist():
            if zi.is_dir():
                continue
            target = (dest_dir / zi.filename).resolve()
            if not str(target).startswith(str(dest_real)):
                raise RuntimeError(f"拦截了不安全的 ZIP 路径: {zi.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(zi, "r") as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)


# ---------------------------------------------------------------------------
# SteamCMD 安装/验证
# ---------------------------------------------------------------------------

def ensure_steamcmd(steamcmd_root: str, logger: logging.Logger) -> Path:
    """
    确保 SteamCMD 可用。若已安装则校验可启动；否则下载解压并做一次引导启动。
    返回 steamcmd.exe 的路径。
    """
    exe = resolve_steamcmd_exe(steamcmd_root)
    root = exe.parent
    root.mkdir(parents=True, exist_ok=True)

    if exe.is_file():
        code, _ = stream_process_output(
            [str(exe), "+quit"], logger, cwd=root, log_prefix="[SteamCMD] "
        )
        if code in (0, 7, 8):
            if code != 0:
                logger.warning("[SteamCMD] 启动退出码 %s（自引导/自更新）。", code)
            return exe
        logger.warning(
            "[SteamCMD] steamcmd.exe 存在但启动退出码 %s → 重新安装", code
        )

    zip_path = root / "steamcmd.zip"
    try:
        if zip_path.exists():
            zip_path.unlink()
    except Exception:
        pass

    download_file(STEAMCMD_ZIP_URL, zip_path, logger)
    _safe_extract_zip(zip_path, root)
    try:
        zip_path.unlink()
    except Exception:
        pass

    exe = resolve_steamcmd_exe(str(root))
    if not exe.is_file():
        raise FileNotFoundError(f"SteamCMD 解压失败：{root} 中未找到 steamcmd.exe")

    code, _ = stream_process_output(
        [str(exe), "+quit"], logger, cwd=root, log_prefix="[SteamCMD] "
    )
    if code != 0:
        logger.warning(
            "[SteamCMD] 新安装后首次启动退出码 %s（自引导/自更新），继续...", code
        )

    return exe


# ---------------------------------------------------------------------------
# SteamCMD 输出分析
# ---------------------------------------------------------------------------

def _steamcmd_has_fatal(out: str) -> bool:
    """检查 SteamCMD 输出是否包含致命错误标记（exit=0 但实际失败）"""
    if not out:
        return False
    fatal_patterns = [
        r"\bERROR!\b",
        r"\bFAILED\b",
        r"Failed to install app",
        r"Invalid Password",
        r"No subscription",
        r"Login Failure",
        r"Timed out",
        r"Disk write failure",
        r"Missing file privileges",
    ]
    for pat in fatal_patterns:
        if re.search(pat, out, re.IGNORECASE):
            return True
    return False


def _steamcmd_verify_install(install_dir: Path, app_id: int) -> bool:
    """简单验证安装是否产生了有效的制品"""
    manifest = install_dir / "steamapps" / f"appmanifest_{app_id}.acf"
    exe = install_dir / "ShooterGame" / "Binaries" / "Win64" / "ArkAscendedServer.exe"
    return manifest.exists() or exe.exists()


def _unstick_install_dir(
    install_dir: Path, app_id: int, logger: logging.Logger
) -> bool:
    """清理可能导致 SteamCMD 卡死的残留文件"""
    steamapps = install_dir / "steamapps"
    manifest = steamapps / f"appmanifest_{app_id}.acf"
    downloading = steamapps / "downloading" / str(app_id)
    tempdir = steamapps / "temp"

    changed = False
    if manifest.exists():
        backup = steamapps / "_repair_backup"
        backup.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        target = backup / f"appmanifest_{app_id}.acf.{ts}.bak"
        try:
            os.chmod(manifest, stat.S_IWRITE)
        except Exception:
            pass
        shutil.move(str(manifest), str(target))
        logger.warning("[SteamCMD] 已移动残留 manifest → %s", target)
        changed = True

    for p in [downloading, tempdir]:
        if p.exists():
            try:
                shutil.rmtree(p, ignore_errors=True)
                logger.warning("[SteamCMD] 已删除残留目录 → %s", p)
                changed = True
            except Exception:
                pass

    return changed


# ---------------------------------------------------------------------------
# SteamCMD app_update
# ---------------------------------------------------------------------------

def steamcmd_app_update(
    logger: logging.Logger,
    steamcmd_exe: Path,
    install_dir: Path,
    app_id: int,
    validate: bool,
    lock_root: Path,
    retries: int = 2,
) -> None:
    """
    运行 SteamCMD app_update，自动重试并处理常见故障。

    Args:
        logger: 日志记录器（实时输出到 UI 控制台）
        steamcmd_exe: steamcmd.exe 路径
        install_dir: 服务器安装目录
        app_id: Steam AppID（ASA 为 2430930）
        validate: 是否在更新时进行文件校验
        lock_root: 锁文件根目录（防并发）
        retries: 最大重试次数
    """
    install_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / LOCKS_DIR_NAME / "steamcmd.lock"

    with exclusive_file_lock(lock_path):
        # 预热：让 SteamCMD 自我更新
        stream_process_output(
            [str(steamcmd_exe), "+quit"],
            logger,
            cwd=steamcmd_exe.parent,
            log_prefix="[SteamCMD] ",
        )

        for attempt in range(1, retries + 2):
            script_lines = [
                "@ShutdownOnFailedCommand 1",
                "@NoPromptForPassword 1",
                f'force_install_dir "{install_dir}"',
                "login anonymous",
                f"app_update {app_id}" + (" validate" if validate else ""),
                "quit",
                "",
            ]
            with tempfile.NamedTemporaryFile(
                "w", delete=False, suffix=".txt", encoding="utf-8"
            ) as tf:
                tf.write("\n".join(script_lines))
                script_path = Path(tf.name)

            try:
                code, out = stream_process_output(
                    [str(steamcmd_exe), "+runscript", str(script_path)],
                    logger,
                    cwd=steamcmd_exe.parent,
                    log_prefix="[SteamCMD] ",
                )
            finally:
                try:
                    script_path.unlink()
                except Exception:
                    pass

            # ---- 退出码 0：主要成功信号 ----
            if code == 0:
                if _steamcmd_has_fatal(out) and not _steamcmd_verify_install(
                    install_dir, app_id
                ):
                    logger.warning(
                        "[SteamCMD] exit=0 但检测到致命标记且未验证安装 → 重试"
                    )
                else:
                    if _steamcmd_verify_install(install_dir, app_id):
                        logger.info("[SteamCMD] app_update 成功（已验证）。")
                        return

                    logger.warning("[SteamCMD] exit=0 但安装未验证 → 短暂等待后重检")
                    time.sleep(2.0)
                    if _steamcmd_verify_install(install_dir, app_id):
                        logger.info("[SteamCMD] app_update 成功（延迟验证）。")
                        return

                    if attempt < (retries + 1):
                        logger.warning(
                            "[SteamCMD] 仍未验证 → 重试 (%s/%s)", attempt, retries + 1
                        )
                        time.sleep(2.0 * attempt)
                        continue

                    raise RuntimeError(
                        "SteamCMD exit=0 但安装无法验证（未找到 manifest/exe）。"
                    )

            # ---- 可重试失败 ----
            retryable = False
            if code in (7, 8) or re.search(
                r"state is 0x6 after update job", out or "", re.IGNORECASE
            ):
                retryable = True
                changed = _unstick_install_dir(install_dir, app_id, logger)
                logger.warning(
                    "[SteamCMD] 可重试失败 (exit=%s) 自愈 changed=%s，尝试 %s/%s",
                    code,
                    changed,
                    attempt,
                    retries + 1,
                )

            if code == 3221225477:
                retryable = True
                logger.warning("[SteamCMD] 崩溃 (3221225477) → 重新安装 SteamCMD 后重试")
                ensure_steamcmd(str(steamcmd_exe.parent), logger)

            if retryable and attempt <= retries:
                time.sleep(3.0 * attempt)
                continue

            # ---- 硬失败 ----
            tail = "\n".join((out or "").splitlines()[-35:])
            raise RuntimeError(f"SteamCMD 失败 (exit={code})。最后输出:\n{tail}")


# ---------------------------------------------------------------------------
# 对外高层接口（向后兼容）
# ---------------------------------------------------------------------------

class SteamManager:
    """SteamCMD 高层管理器"""

    def __init__(self, steamcmd_dir: Path):
        self.steamcmd_dir = steamcmd_dir

    def is_installed(self) -> bool:
        """检查 SteamCMD 是否已安装"""
        return resolve_steamcmd_exe(str(self.steamcmd_dir)).is_file()

    def ensure(self, logger: logging.Logger) -> Path:
        """确保 SteamCMD 可用，返回 exe 路径"""
        return ensure_steamcmd(str(self.steamcmd_dir), logger)

    def update_app(
        self,
        install_dir: Path,
        logger: logging.Logger,
        app_id: int = ARK_ASA_APP_ID,
        validate: bool = False,
        lock_root: Optional[Path] = None,
        retries: int = 2,
    ) -> None:
        """更新指定 App（默认为 ASA Dedicated Server）"""
        exe = self.ensure(logger)
        steamcmd_app_update(
            logger=logger,
            steamcmd_exe=exe,
            install_dir=install_dir,
            app_id=app_id,
            validate=validate,
            lock_root=lock_root or self.steamcmd_dir,
            retries=retries,
        )

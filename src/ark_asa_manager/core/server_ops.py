"""
服务器操作辅助函数：命令构建、INI staging、备份。
"""
import logging
import shlex
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ini.parser import INIParser
from ..utils.constants import (
    BACKUP_DIR_NAME,
    BASELINE_DIR_NAME,
    DEFAULT_SERVER_NAME,
    GAME_INI_REL,
    GAMEUSERSETTINGS_REL,
    SERVERS_DIR_NAME,
    STAGING_DIR_NAME,
)

# ---------------------------------------------------------------------------
# 路径辅助
# ---------------------------------------------------------------------------

def ark_server_exe(server_dir: Path) -> Path:
    """返回 ASA 服务器 EXE 路径"""
    return server_dir / "ShooterGame" / "Binaries" / "Win64" / "ArkAscendedServer.exe"


def server_saved_dir(server_dir: Path) -> Path:
    return server_dir / "ShooterGame" / "Saved"


def server_config_dir(server_dir: Path) -> Path:
    return server_dir / "ShooterGame" / "Saved" / "Config" / "WindowsServer"


def server_root(app_base: Path, server_id: str) -> Path:
    return app_base / SERVERS_DIR_NAME / server_id


def staging_paths(app_base: Path, server_id: str):
    """返回 (staging_gus_path, staging_game_path)"""
    root = server_root(app_base, server_id) / STAGING_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root / "GameUserSettings.ini", root / "Game.ini"


# ---------------------------------------------------------------------------
# 启动命令构建
# ---------------------------------------------------------------------------

def _split_custom_args(raw: str) -> List[str]:
    cleaned = (raw or "").strip()
    if not cleaned:
        return []
    try:
        parts = shlex.split(cleaned, posix=False)
    except ValueError:
        parts = cleaned.split()
    return [p for p in parts if p]


def _normalized_mods(mods_raw: str) -> str:
    raw = (mods_raw or "").strip()
    if not raw:
        return ""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return ",".join(parts)


def build_server_command(cfg: Dict[str, Any]) -> List[str]:
    """
    根据 server_cfg 字典构建完整的 ASA 服务器启动命令列表。
    """
    server_dir = Path(cfg["server_dir"])
    exe = ark_server_exe(server_dir)

    map_name = (cfg.get("map_name") or "").strip()
    if not map_name:
        raise ValueError("地图名称（map_name）是必填项")

    session = (cfg.get("server_name") or "").replace('"', "").strip() or DEFAULT_SERVER_NAME

    url_parts = [
        f"{map_name}?listen",
        f"SessionName={session}",
        f"Port={int(cfg.get('port', 7777))}",
        f"QueryPort={int(cfg.get('query_port', 27015))}",
    ]

    server_platform = ""
    if cfg.get("server_platform_crossplay"):
        server_platform = "PC+XSX+WINGDK"
    if cfg.get("server_platform", "").strip():
        server_platform = cfg["server_platform"].strip()
    if server_platform:
        url_parts.append(f"ServerPlatform={server_platform}")

    alt_save = (cfg.get("alt_save_directory_name") or "").strip()
    if alt_save:
        url_parts.append(f"AltSaveDirectoryName={alt_save}")

    url = "?".join(url_parts)

    flags: List[str] = []
    flags.append("-UseBattlEye" if cfg.get("enable_battleye") else "-NoBattlEye")

    if cfg.get("automanaged_mods"):
        flags.append("-automanagedmods")

    mods = _normalized_mods(cfg.get("mods", ""))
    if mods:
        flags.append(f"-mods={mods}")

    flags.append(f"-WinLiveMaxPlayers={int(cfg.get('max_players', 70))}")

    if cfg.get("cluster_enable"):
        cid = (cfg.get("cluster_id") or "").strip()
        if not cid:
            raise ValueError("启用集群（cluster_enable）需要填写集群 ID（cluster_id）。")
        flags.append(f"-clusterid={cid}")

    if cfg.get("cluster_custom_path_enable"):
        p = (cfg.get("cluster_dir_override") or "").strip()
        if not p:
            raise ValueError("启用集群自定义路径需要填写 cluster_dir_override。")
        flags.append(f"-ClusterDirOverride={p}")

    if cfg.get("no_transfer_from_filtering"):
        flags.append("-NoTransferFromFiltering")

    dino_mode = (cfg.get("dino_mode") or "").strip()
    if dino_mode:
        flags.append(f"-{dino_mode}")

    if cfg.get("log_servergamelog"):
        flags.append("-servergamelog")
    if cfg.get("log_servergamelogincludetribelogs"):
        flags.append("-servergamelogincludetribelogs")
    if cfg.get("log_serverrconoutputtribelogs"):
        flags.append("-ServerRCONOutputTribeLogs")

    mech_map = {
        "mech_disablecustomcosmetics": "-DisableCustomCosmetics",
        "mech_autodestroystructures": "-AutoDestroyStructures",
        "mech_forcerespawndinos": "-ForceRespawnDinos",
        "mech_nowildbabies": "-NoWildBabies",
        "mech_forceallowcaveflyers": "-ForceAllowCaveFlyers",
        "mech_disabledinonetrangescaling": "-disabledinonetrangescaling",
        "mech_unstasisdinoobstructioncheck": "-UnstasisDinoObstructionCheck",
        "mech_alwaystickdedicatedskeletalmeshes": "-AlwaysTickDedicatedSkeletalMeshes",
        "mech_disablecharactertracker": "-disableCharacterTracker",
        "mech_useservernetspeedcheck": "-UseServerNetSpeedCheck",
        "mech_stasiskeepcontrollers": "-StasisKeepControllers",
        "mech_ignoredupeditems": "-ignoredupeditems",
    }
    for key, flag in mech_map.items():
        if cfg.get(key):
            flags.append(flag)

    flags.extend(_split_custom_args(cfg.get("custom_start_args", "")))

    return [str(exe), url, *flags]


# ---------------------------------------------------------------------------
# Baseline / Staging 工作流
# ---------------------------------------------------------------------------

def ensure_baseline(
    app_base: Path,
    server_id: str,
    server_dir: Path,
    logger: logging.Logger,
    refresh: bool = True,
) -> Path:
    """
    将服务器当前 INI 文件复制到 baseline 目录（用于停止后恢复）。

    Args:
        refresh: True 表示总是覆盖；False 表示仅在 baseline 不存在时初始化。
    Returns:
        baseline 目录路径。
    """
    base = server_root(app_base, server_id) / BASELINE_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)

    src_gus = server_dir / GAMEUSERSETTINGS_REL
    src_game = server_dir / GAME_INI_REL
    dst_gus = base / "GameUserSettings.ini"
    dst_game = base / "Game.ini"

    if src_gus.exists() and (refresh or not dst_gus.exists()):
        shutil.copy2(src_gus, dst_gus)
        logger.info("Baseline 已更新: GameUserSettings.ini")
    if src_game.exists() and (refresh or not dst_game.exists()):
        shutil.copy2(src_game, dst_game)
        logger.info("Baseline 已更新: Game.ini")

    return base


def apply_staging_to_server(
    app_base: Path,
    server_id: str,
    server_dir: Path,
    logger: logging.Logger,
) -> None:
    """将 staging 目录中的 INI 文件覆盖到服务器实际目录"""
    stage_gus, stage_game = staging_paths(app_base, server_id)
    dest_gus = server_dir / GAMEUSERSETTINGS_REL
    dest_game = server_dir / GAME_INI_REL

    if stage_gus.exists():
        dest_gus.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage_gus, dest_gus)
        logger.info("已应用 staging: GameUserSettings.ini")

    if stage_game.exists():
        dest_game.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage_game, dest_game)
        logger.info("已应用 staging: Game.ini")


def restore_baseline_to_server(
    app_base: Path,
    server_id: str,
    server_dir: Path,
    logger: logging.Logger,
) -> None:
    """服务器停止后，将 baseline 文件还原到服务器实际目录"""
    base_root = server_root(app_base, server_id) / BASELINE_DIR_NAME
    src_gus = base_root / "GameUserSettings.ini"
    src_game = base_root / "Game.ini"
    dest_gus = server_dir / GAMEUSERSETTINGS_REL
    dest_game = server_dir / GAME_INI_REL

    if src_gus.exists():
        dest_gus.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_gus, dest_gus)
        logger.info("Baseline 已还原: GameUserSettings.ini")
    if src_game.exists():
        dest_game.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_game, dest_game)
        logger.info("Baseline 已还原: Game.ini")


def ensure_required_server_settings(
    cfg: Dict[str, Any],
    app_base: Path,
    server_id: str,
    server_dir: Path,
    logger: logging.Logger,
) -> None:
    """
    在 staging 目录的 INI 文件中写入必要的服务器设置：
    管理员密码、加入密码、RCON 端口、会话名称、最大玩家数。
    """
    stage_gus, stage_game = staging_paths(app_base, server_id)

    # ---------- GameUserSettings.ini ----------
    # 若 staging 不存在则从服务器实际文件初始化（或创建空文件）
    if not stage_gus.exists():
        live_gus = server_dir / GAMEUSERSETTINGS_REL
        if live_gus.exists():
            stage_gus.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live_gus, stage_gus)
            logger.info("Staging 初始化自服务器: GameUserSettings.ini")
        else:
            stage_gus.parent.mkdir(parents=True, exist_ok=True)
            stage_gus.write_text("", encoding="utf-8")

    parser_gus = INIParser()
    parser_gus.parse_file(stage_gus)

    admin_pw = (cfg.get("admin_password") or "").strip()
    join_pw = (cfg.get("join_password") or "").strip()
    rcon_port = int(cfg.get("rcon_port", 27020))
    session_name = (cfg.get("server_name") or DEFAULT_SERVER_NAME).strip()
    max_players = int(cfg.get("max_players", 70))
    enable_rcon = bool(cfg.get("enable_rcon", True))

    sec_srv = "ServerSettings"
    parser_gus.set(sec_srv, "ServerAdminPassword", admin_pw)
    parser_gus.set(sec_srv, "ServerPassword", join_pw)
    if enable_rcon:
        parser_gus.set(sec_srv, "RCONEnabled", "True")
        parser_gus.set(sec_srv, "RCONPort", str(rcon_port))
    else:
        parser_gus.set(sec_srv, "RCONEnabled", "False")

    sec_session = "/Script/Engine.GameSession"
    parser_gus.set(sec_session, "SessionName", session_name)
    parser_gus.set(sec_session, "MaxPlayers", str(max_players))

    parser_gus.save_file(stage_gus)
    logger.info("Staging GameUserSettings.ini 已更新（密码/RCON/会话/玩家数）。")

    # ---------- Game.ini ----------
    if not stage_game.exists():
        live_game = server_dir / GAME_INI_REL
        if live_game.exists():
            stage_game.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live_game, stage_game)
            logger.info("Staging 初始化自服务器: Game.ini")
        else:
            stage_game.parent.mkdir(parents=True, exist_ok=True)
            stage_game.write_text("", encoding="utf-8")

    parser_game = INIParser()
    parser_game.parse_file(stage_game)
    parser_game.set("/Script/Engine.GameSession", "MaxPlayers", str(max_players))
    parser_game.save_file(stage_game)
    logger.info("Staging Game.ini 已更新（MaxPlayers）。")


# ---------------------------------------------------------------------------
# 备份
# ---------------------------------------------------------------------------

def _now_ts() -> str:
    return time.strftime("%Y-%m-%d_%H-%M-%S")


def backup_server(
    cfg: Dict[str, Any],
    app_base: Path,
    logger: logging.Logger,
) -> Optional[Path]:
    """
    将服务器 Saved 目录和配置文件打包为 ZIP 备份。
    按 backup_retention 保留最新 N 份，自动删除旧备份。

    Returns:
        生成的备份 ZIP 路径，若跳过则返回 None。
    """
    server_dir = Path(cfg["server_dir"])
    saved = server_saved_dir(server_dir)
    if not saved.exists():
        logger.info("备份已跳过：Saved 目录不存在。")
        return None

    backup_dir_cfg = (cfg.get("backup_dir") or "").strip()
    target_dir = Path(backup_dir_cfg) if backup_dir_cfg else (app_base / BACKUP_DIR_NAME)
    target_dir.mkdir(parents=True, exist_ok=True)

    out_zip = target_dir / f"ASA_Backup_{_now_ts()}.zip"
    include_roots = [saved, server_config_dir(server_dir)]

    logger.info(f"正在创建备份: {out_zip}")
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root in include_roots:
            root = root.resolve()
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_dir():
                    continue
                arc = path.relative_to(server_dir.resolve())
                z.write(path, arcname=str(arc))

    logger.info("备份完成。")

    try:
        keep = max(1, int(cfg.get("backup_retention", 20)))
        zips = sorted(
            target_dir.glob("ASA_Backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in zips[keep:]:
            try:
                old.unlink()
                logger.info(f"保留策略：已删除旧备份 {old.name}")
            except Exception:
                pass
    except Exception:
        pass

    return out_zip

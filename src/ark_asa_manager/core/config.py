"""
配置管理
"""
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict

from ..utils.constants import (
    DEFAULT_MAP,
    DEFAULT_MAX_PLAYERS,
    DEFAULT_PORT,
    DEFAULT_QUERY_PORT,
    DEFAULT_RCON_HOST,
    DEFAULT_RCON_PORT,
    DEFAULT_SCHEDULE_TIME,
    DEFAULT_SERVER_DIR,
    DEFAULT_SERVER_NAME,
    DEFAULT_STEAMCMD_DIR,
    GLOBAL_CONFIG_NAME,
    LEGACY_CONFIG_NAME,
    SERVER_CONFIG_NAME,
    SERVERS_DIR_NAME,
)

_logger = logging.getLogger(__name__)


class ConfigManager:
    """配置文件管理"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.global_config_path = config_dir / GLOBAL_CONFIG_NAME
        self.legacy_config_path = config_dir / LEGACY_CONFIG_NAME
        # 保护所有 JSON 读写操作，避免并发时数据损坏
        self._lock = threading.RLock()
    
    def _read_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if not path.exists():
                return dict(default)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
                _logger.warning("配置文件格式错误（非 dict）: %s", path)
            except json.JSONDecodeError as e:
                _logger.error("JSON 解析错误 %s: %s", path, e)
            except OSError as e:
                _logger.error("读取配置文件失败 %s: %s", path, e)
            except Exception as e:
                _logger.error("读取配置文件时发生未知错误 %s: %s", path, e)
            return dict(default)

    def _write_json(self, path: Path, data: Dict[str, Any]) -> bool:
        with self._lock:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                # 先写临时文件再原子替换，避免写入中途崩溃导致文件损坏
                tmp = path.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                tmp.replace(path)
                return True
            except OSError as e:
                _logger.error("写入配置文件失败 %s: %s", path, e)
                return False
            except Exception as e:
                _logger.error("写入配置文件时发生未知错误 %s: %s", path, e)
                return False

    def get_servers_root(self) -> Path:
        return self.config_dir / SERVERS_DIR_NAME

    def get_server_root(self, server_id: str) -> Path:
        return self.get_servers_root() / server_id

    def get_server_config_path(self, server_id: str) -> Path:
        return self.get_server_root(server_id) / SERVER_CONFIG_NAME

    def default_global_config(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "steamcmd_dir": DEFAULT_STEAMCMD_DIR,
            "last_selected_server_id": "",
            "start_on_startup": False,
            "servers": [],
            # ---- 跨服聊天 (LACC) ----
            "chat_enable": False,
            "chat_ws_port": 8000,
            "chat_token": "",
            "chat_cluster_key": "",
            "chat_auto_start": False,
        }

    def default_server_config(self) -> Dict[str, Any]:
        return {
            # ---- 基础设置 ----
            "schema_version": 12,
            "server_dir": DEFAULT_SERVER_DIR,
            "map_name": DEFAULT_MAP,
            "server_name": DEFAULT_SERVER_NAME,
            "port": DEFAULT_PORT,
            "query_port": DEFAULT_QUERY_PORT,
            "max_players": DEFAULT_MAX_PLAYERS,
            "join_password": "",
            "admin_password": "AdminPassword",
            "enable_battleye": False,
            "enable_rcon": True,
            "rcon_host": DEFAULT_RCON_HOST,
            "rcon_port": DEFAULT_RCON_PORT,
            "automanaged_mods": True,
            "mods": "",
            "validate_on_update": False,
            "backup_on_stop": True,
            "backup_dir": "",
            "backup_retention": 20,
            "auto_update_restart": False,
            "auto_update_time": DEFAULT_SCHEDULE_TIME,
            "update_on_startup": False,
            "hide_gameanalytics_console_logs": True,
            "custom_start_args": "",
            # ---- 集群设置 ----
            "cluster_enable": False,
            "cluster_id": "",
            "cluster_custom_path_enable": False,
            "cluster_dir_override": "",
            "no_transfer_from_filtering": False,
            "alt_save_directory_name": "",
            # ---- 平台 ----
            "server_platform_crossplay": False,
            "server_platform": "",
            # ---- 恐龙模式 ----
            "dino_mode": "",
            # ---- 日志 ----
            "log_servergamelog": False,
            "log_servergamelogincludetribelogs": False,
            "log_serverrconoutputtribelogs": False,
            # ---- 力学/性能 ----
            "mech_disablecustomcosmetics": False,
            "mech_autodestroystructures": False,
            "mech_forcerespawndinos": False,
            "mech_nowildbabies": False,
            "mech_forceallowcaveflyers": False,
            "mech_disabledinonetrangescaling": False,
            "mech_unstasisdinoobstructioncheck": False,
            "mech_alwaystickdedicatedskeletalmeshes": False,
            "mech_disablecharactertracker": False,
            "mech_useservernetspeedcheck": False,
            "mech_stasiskeepcontrollers": False,
            "mech_ignoredupeditems": False,
        }

    def load_global_config(self) -> Dict[str, Any]:
        data = self._read_json(self.global_config_path, self.default_global_config())
        if not isinstance(data.get("servers"), list):
            data["servers"] = []
        return data

    def save_global_config(self, data: Dict[str, Any]) -> bool:
        merged = self.default_global_config()
        merged.update(data or {})
        if not isinstance(merged.get("servers"), list):
            merged["servers"] = []
        return self._write_json(self.global_config_path, merged)

    def load_server_config(self, server_id: str) -> Dict[str, Any]:
        path = self.get_server_config_path(server_id)
        data = self._read_json(path, self.default_server_config())
        merged = self.default_server_config()
        merged.update(data)
        return merged

    def save_server_config(self, server_id: str, data: Dict[str, Any]) -> bool:
        path = self.get_server_config_path(server_id)
        merged = self.default_server_config()
        merged.update(data or {})
        return self._write_json(path, merged)

    def migrate_legacy_if_needed(self) -> None:
        if self.global_config_path.exists() or not self.legacy_config_path.exists():
            return

        legacy = self._read_json(self.legacy_config_path, {})
        if not legacy:
            return

        migrated_global = self.default_global_config()
        migrated_global["steamcmd_dir"] = str(legacy.get("steamcmd_dir") or DEFAULT_STEAMCMD_DIR)
        self.save_global_config(migrated_global)
    
    def bootstrap_defaults(self, server_id: str, display_name: str = "Server 1") -> None:
        global_cfg = self.load_global_config()
        servers = global_cfg.get("servers", [])
        if not any(isinstance(s, dict) and s.get("id") == server_id for s in servers):
            servers.append(
                {
                    "id": server_id,
                    "display_name": display_name,
                    "server_dir": DEFAULT_SERVER_DIR,
                }
            )
            global_cfg["servers"] = servers
        if not global_cfg.get("last_selected_server_id"):
            global_cfg["last_selected_server_id"] = server_id
        self.save_global_config(global_cfg)
        self.save_server_config(server_id, self.default_server_config())

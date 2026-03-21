"""
Refactored Server Manager UI - Main application window with modular tabs.

This is the main entry point for the GUI, coordinating all tabs and managers.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
import logging
import json
import uuid

import os
import subprocess
import time

from ..core import ConfigManager, StorageManager, ProcessManager
from ..core.server_ops import (
    ark_server_exe,
    apply_staging_to_server,
    backup_server,
    build_server_command,
    ensure_baseline,
    ensure_required_server_settings,
    inject_lacc_to_server_config,
    restore_baseline_to_server,
    staging_paths,
)
from ..ini.parser import INIParser
from ..models import ServerConfig
from ..steam.manager import SteamManager
from ..utils import get_logger
from ..utils.constants import (
    AUTO_RESTART_DELAY_SEC,
    AUTO_RESTART_EXIT_CODES,
    ARK_ASA_APP_ID,
    AUTOSAVE_DEBOUNCE_MS,
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
    GAMEUSERSETTINGS_REL,
    GAME_INI_REL,
    MAP_PRESETS,
    MAP_CUSTOM_SENTINEL,
)
from .tabs import (
    BaseTab,
    ServerTab,
    AdvancedTab,
    RconTab,
    DiscordTab,
    IniEditorTab,
    ChatTab,
)
from ..chat import LACCWebSocketServer
from ..chat.server import LACC_MOD_ID


# Theme colors - migrated from original
THEME_COLORS = {
    "bg":               "#1e1e1e",
    "surface":          "#2d2d2d",
    "surface_light":    "#3a3a3a",
    "border":           "#444444",
    "text":             "#e8e8e8",
    "muted":            "#888888",
    "accent":           "#0e639c",
    "accent_light":     "#1177bb",
    "success":          "#00aa00",
    "warning":          "#ffcc00",
    "error":            "#ff0000",
}


class ServerManagerApp:
    """
    Main application window for ARK: Survival Ascended Server Manager.
    
    Coordinates all UI components, managers, and configuration state.
    """
    
    def __init__(self, root: tk.Tk, app_base: Path):
        """
        Initialize the main application.
        
        Args:
            root: The root tkinter window
            app_base: Base directory for application data
        """
        self.root = root
        self.app_base = app_base
        self.theme_colors = THEME_COLORS
        
        # Initialize managers
        self.storage = StorageManager(app_base)
        self.config_manager = ConfigManager(app_base)
        self.process_manager = ProcessManager()
        
        self.logger = get_logger(__name__)
        
        # Configure the root window
        self.root.title("ARK：生存进化 服务器管理器")
        self.root.geometry("1220x780")
        self.root.minsize(1000, 700)
        
        # Apply theme
        self._apply_theme()
        
        # Initialize state
        self._init_state()
        
        # Initialize variables
        self._init_variables()
        
        # Build UI
        self._create_ui()

        # Load/create legacy-aligned persisted config state
        self._load_profile_state_from_disk()

        # Hook debounced autosave after initial values are loaded
        self._setup_autosave_hooks()

        # Ensure config is flushed on window close
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        # 启动所有已配置自动更新的服务器的调度器
        self._init_all_auto_update_schedulers()
        
        self.logger.info("Server Manager UI initialized")
    
    def _apply_theme(self) -> None:
        """Apply dark theme to the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for dark theme
        style.configure(
            "TFrame",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TLabel",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TLabelframe",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TLabelframe.Label",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TButton",
            background=THEME_COLORS["surface"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TCheckbutton",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TRadiobutton",
            background=THEME_COLORS["bg"],
            foreground=THEME_COLORS["text"]
        )
        style.configure(
            "TEntry",
            fieldbackground=THEME_COLORS["surface"],
            foreground=THEME_COLORS["text"],
            borderwidth=1
        )
        style.configure(
            "TCombobox",
            fieldbackground=THEME_COLORS["surface"],
            foreground=THEME_COLORS["text"],
            borderwidth=1
        )
        style.configure(
            "Treeview",
            background=THEME_COLORS["surface"],
            foreground=THEME_COLORS["text"],
            fieldbackground=THEME_COLORS["surface"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=THEME_COLORS["surface_light"],
            foreground=THEME_COLORS["text"]
        )
        
        self.root.configure(bg=THEME_COLORS["bg"])
    
    def _init_state(self) -> None:
        """Initialize application state."""
        self.active_server_id = ""
        self.current_config: Optional[ServerConfig] = None
        self.tabs: Dict[str, BaseTab] = {}
        self.global_cfg: Dict[str, Any] = {}
        self.server_cfg: Dict[str, Any] = {}
        self._server_profile_ids: List[str] = []
        self._server_profile_labels: List[str] = []
        self._autosave_after_id: Optional[str] = None
        self._autosave_guard = False
        self._busy_servers: set = set()
        self._async_thread: Optional[threading.Thread] = None

        # 多服务器进程管理（每个 server_id 独立）
        # server_id -> subprocess.Popen
        self._server_procs: Dict[str, subprocess.Popen] = {}
        self._server_procs_lock = threading.Lock()
        # server_id -> threading.Event (日志读取停止标志)
        self._stop_log_readers: Dict[str, threading.Event] = {}
        # server_id -> threading.Event (用户主动停止标志)
        self._stop_requested_flags: Dict[str, threading.Event] = {}
        # server_id -> 服务器配置快照（启动时记录，用于停止/备份）
        self._running_server_configs: Dict[str, Dict[str, Any]] = {}

        # 自动更新调度（每个 server_id 独立）
        # server_id -> threading.Thread
        self._auto_update_threads: Dict[str, threading.Thread] = {}
        # server_id -> threading.Event
        self._auto_update_stops: Dict[str, threading.Event] = {}

        # 每服务器独立的控制台日志缓冲区
        self._console_buffers: Dict[str, List[str]] = {}
        self._console_buffers_lock = threading.Lock()

        # LACC 跨服聊天 WebSocket 服务器
        self._chat_server: Optional[LACCWebSocketServer] = None

        # INI 编辑器状态
        self._ini_parser: Optional[INIParser] = None
        self._ini_loaded_path: Optional[Path] = None
        self._ini_loaded_name: str = ""
    
    def _init_variables(self) -> None:
        """Initialize all tkinter variables."""
        # Server profile management
        self.var_server_profile = tk.StringVar(master=self.root)
        self.var_steamcmd_dir = tk.StringVar(master=self.root, value=DEFAULT_STEAMCMD_DIR)
        self.var_server_dir = tk.StringVar(master=self.root, value=DEFAULT_SERVER_DIR)
        
        # Server settings (basic)
        self.var_map_preset = tk.StringVar(master=self.root, value=DEFAULT_MAP)
        self.var_map_custom = tk.StringVar(master=self.root)
        self.var_server_name = tk.StringVar(master=self.root, value=DEFAULT_SERVER_NAME)
        self.var_port = tk.StringVar(master=self.root, value=str(DEFAULT_PORT))
        self.var_query_port = tk.StringVar(master=self.root, value=str(DEFAULT_QUERY_PORT))
        self.var_max_players = tk.StringVar(master=self.root, value=str(DEFAULT_MAX_PLAYERS))
        self.var_join_password = tk.StringVar(master=self.root)
        self.var_admin_password = tk.StringVar(master=self.root, value="AdminPassword")
        
        # Server settings (advanced)
        self.var_server_platform_crossplay = tk.BooleanVar(master=self.root)
        self.var_enable_battleye = tk.BooleanVar(master=self.root)
        self.var_automanaged_mods = tk.BooleanVar(master=self.root, value=True)
        self.var_validate_on_update = tk.BooleanVar(master=self.root)
        self.var_custom_start_args = tk.StringVar(master=self.root)
        
        # Cluster settings
        self.var_cluster_enable = tk.BooleanVar(master=self.root)
        self.var_cluster_id = tk.StringVar(master=self.root)
        self.var_cluster_custom_path_enable = tk.BooleanVar(master=self.root)
        self.var_cluster_dir_override = tk.StringVar(master=self.root)
        self.var_no_transfer_from_filtering = tk.BooleanVar(master=self.root)
        self.var_alt_save_directory_name = tk.StringVar(master=self.root)
        
        # Dino and log settings
        self.var_dino_mode = tk.StringVar(master=self.root)
        self.var_log_servergamelog = tk.BooleanVar(master=self.root)
        self.var_log_servergamelogincludetribelogs = tk.BooleanVar(master=self.root)
        self.var_log_serverrconoutputtribelogs = tk.BooleanVar(master=self.root)
        
        # Mechanics
        self.var_m_disablecustomcosmetics = tk.BooleanVar(master=self.root)
        self.var_m_autodestroystructures = tk.BooleanVar(master=self.root)
        self.var_m_forcerespawndinos = tk.BooleanVar(master=self.root)
        self.var_m_nowildbabies = tk.BooleanVar(master=self.root)
        self.var_m_forceallowcaveflyers = tk.BooleanVar(master=self.root)
        self.var_m_disabledinonetrangescaling = tk.BooleanVar(master=self.root)
        self.var_m_unstasisdinoobstructioncheck = tk.BooleanVar(master=self.root)
        self.var_m_alwaystickdedicatedskeletalmeshes = tk.BooleanVar(master=self.root)
        self.var_m_disablecharactertracker = tk.BooleanVar(master=self.root)
        self.var_m_useservernetspeedcheck = tk.BooleanVar(master=self.root)
        self.var_m_stasiskeepcontrollers = tk.BooleanVar(master=self.root)
        self.var_m_ignoredupeditems = tk.BooleanVar(master=self.root)
        
        # RCON settings
        self.var_enable_rcon = tk.BooleanVar(master=self.root, value=True)
        self.var_rcon_host = tk.StringVar(master=self.root, value=DEFAULT_RCON_HOST)
        self.var_rcon_port = tk.StringVar(master=self.root, value=str(DEFAULT_RCON_PORT))
        self.var_rcon_cmd = tk.StringVar(master=self.root)
        self.var_rcon_saved = tk.StringVar(master=self.root)
        
        # Discord settings
        self.var_discord_enable = tk.BooleanVar(master=self.root)
        self.var_discord_webhook_url = tk.StringVar(master=self.root)
        self.var_discord_poll_interval_min = tk.StringVar(master=self.root, value="5")
        self.var_discord_notify_start = tk.BooleanVar(master=self.root, value=True)
        self.var_discord_notify_stop = tk.BooleanVar(master=self.root, value=True)
        self.var_discord_notify_join = tk.BooleanVar(master=self.root, value=True)
        self.var_discord_notify_leave = tk.BooleanVar(master=self.root)
        self.var_discord_notify_crash = tk.BooleanVar(master=self.root, value=True)
        self.var_discord_include_player_id = tk.BooleanVar(master=self.root)
        self.var_discord_mention_mode = tk.StringVar(master=self.root, value="name")
        self.var_discord_mention_map_json = tk.StringVar(master=self.root)
        
        # Backup settings
        self.var_backup_on_stop = tk.BooleanVar(master=self.root, value=True)
        self.var_backup_dir = tk.StringVar(master=self.root)
        self.var_backup_retention = tk.StringVar(master=self.root, value="20")
        
        # Auto-update settings
        self.var_auto_update_restart = tk.BooleanVar(master=self.root)
        self.var_auto_start_on_launch = tk.BooleanVar(master=self.root)
        self.var_auto_update_time = tk.StringVar(master=self.root, value=DEFAULT_SCHEDULE_TIME)
        self.var_update_on_startup = tk.BooleanVar(master=self.root)
        
        # Misc
        self.var_hide_gameanalytics_console_logs = tk.BooleanVar(master=self.root, value=True)
        self.var_status = tk.StringVar(master=self.root, value="就绪")
        
        # 跨服聊天 (LACC)
        self.var_chat_ws_port = tk.StringVar(master=self.root, value="8000")
        self.var_chat_token = tk.StringVar(master=self.root)
        self.var_chat_cluster_key = tk.StringVar(master=self.root)
        self.var_chat_auto_start = tk.BooleanVar(master=self.root)

        # INI editor
        self.var_ini_filter = tk.StringVar(master=self.root)
        self.var_ini_section = tk.StringVar(master=self.root)
        self.var_ini_key = tk.StringVar(master=self.root)
        self.var_ini_value = tk.StringVar(master=self.root)
        self.var_ini_add_section = tk.StringVar(master=self.root)
        self.var_ini_add_key = tk.StringVar(master=self.root)
        self.var_ini_add_value = tk.StringVar(master=self.root)
    
    def _create_ui(self) -> None:
        """Create the main UI structure with tabs."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create notebook (tab widget)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Create tab frames
        tab_server_frame = ttk.Frame(self.notebook, padding=10)
        tab_adv_frame = ttk.Frame(self.notebook, padding=10)
        tab_rcon_frame = ttk.Frame(self.notebook, padding=10)
        tab_discord_frame = ttk.Frame(self.notebook, padding=10)
        tab_ini_frame = ttk.Frame(self.notebook, padding=10)
        tab_chat_frame = ttk.Frame(self.notebook, padding=10)
        
        # Add tabs to notebook
        self.notebook.add(tab_server_frame, text="服务器")
        self.notebook.add(tab_adv_frame, text="高级设置")
        self.notebook.add(tab_rcon_frame, text="RCON")
        self.notebook.add(tab_discord_frame, text="Discord")
        self.notebook.add(tab_ini_frame, text="INI编辑器")
        self.notebook.add(tab_chat_frame, text="跨服聊天")
        
        # Initialize tab components
        self.tabs["server"] = ServerTab(tab_server_frame, self)
        self.tabs["advanced"] = AdvancedTab(tab_adv_frame, self)
        self.tabs["rcon"] = RconTab(tab_rcon_frame, self)
        self.tabs["discord"] = DiscordTab(tab_discord_frame, self)
        self.tabs["ini"] = IniEditorTab(tab_ini_frame, self)
        self.tabs["chat"] = ChatTab(tab_chat_frame, self)
        
        # Build all tabs
        for tab in self.tabs.values():
            tab.build()

        # Apply initial map UI mode
        self._sync_map_mode()
        
        # Console output area at bottom
        self._create_console_area(main_frame)
    
    def _create_console_area(self, parent: ttk.Frame) -> None:
        """Create the console output area at the bottom of the window."""
        self._console_label_frame = console_frame = ttk.LabelFrame(parent, text="控制台输出", padding=5)
        console_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        parent.rowconfigure(1, weight=0)  # Console takes minimal space
        
        # Text widget for console output
        self.txt_log = tk.Text(
            console_frame,
            height=8,
            background=THEME_COLORS["surface"],
            foreground=THEME_COLORS["text"],
            insertbackground=THEME_COLORS["text"],
            selectbackground=THEME_COLORS["accent_light"],
            highlightthickness=1,
            highlightbackground=THEME_COLORS["border"],
            highlightcolor=THEME_COLORS["accent"],
        )
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        self.txt_log.configure(state="disabled")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.txt_log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.txt_log.configure(yscrollcommand=scrollbar.set)

    def _load_profile_state_from_disk(self) -> None:
        self.config_manager.migrate_legacy_if_needed()
        self.global_cfg = self.config_manager.load_global_config()

        servers = self.global_cfg.get("servers") or []
        if not servers:
            server_id = str(uuid.uuid4())
            self.config_manager.bootstrap_defaults(server_id, display_name="Server 1")
            self.global_cfg = self.config_manager.load_global_config()
            servers = self.global_cfg.get("servers") or []

        selected_id = str(self.global_cfg.get("last_selected_server_id") or "")
        server_ids = [str(s.get("id")) for s in servers if isinstance(s, dict) and s.get("id")]
        if selected_id not in server_ids and server_ids:
            selected_id = server_ids[0]

        if not selected_id:
            return

        self.active_server_id = selected_id
        self._ensure_server_workspace(selected_id)
        self.server_cfg = self.config_manager.load_server_config(selected_id)

        self._apply_global_config_to_vars(self.global_cfg)
        self._apply_server_config_to_vars(self.server_cfg)
        self._refresh_server_profile_selector()
        self._sync_map_mode()
        self._switch_console_to(selected_id)
        self._update_button_states()

    def _ensure_server_workspace(self, server_id: str) -> None:
        if not server_id:
            return
        try:
            self.storage.get_server_dir(server_id)
            self.storage.get_staging_dir(server_id)
            self.storage.get_baseline_dir(server_id)
            self.storage.get_backup_dir(server_id)
            self.storage.get_server_locks_dir(server_id)
        except Exception as e:
            self.logger.debug(f"Failed to initialize server workspace for {server_id}: {e}")

    def _apply_global_config_to_vars(self, cfg: Dict[str, Any]) -> None:
        steamcmd_dir = str(cfg.get("steamcmd_dir") or DEFAULT_STEAMCMD_DIR)
        self.var_steamcmd_dir.set(steamcmd_dir)
        self.var_auto_start_on_launch.set(bool(cfg.get("start_on_startup", False)))

        # 跨服聊天
        self.var_chat_ws_port.set(str(cfg.get("chat_ws_port", 8000)))
        self.var_chat_token.set(str(cfg.get("chat_token") or ""))
        self.var_chat_cluster_key.set(str(cfg.get("chat_cluster_key") or ""))
        self.var_chat_auto_start.set(bool(cfg.get("chat_auto_start", False)))

        if cfg.get("chat_auto_start"):
            self.root.after(500, self._start_chat_server)

    def _apply_server_config_to_vars(self, cfg: Dict[str, Any]) -> None:
        self._autosave_guard = True
        self.var_server_dir.set(str(cfg.get("server_dir") or DEFAULT_SERVER_DIR))

        map_name = str(cfg.get("map_name") or DEFAULT_MAP)
        if map_name in MAP_PRESETS:
            self.var_map_preset.set(map_name)
            self.var_map_custom.set(map_name)
        else:
            self.var_map_preset.set(MAP_CUSTOM_SENTINEL)
            self.var_map_custom.set(map_name)

        self.var_server_name.set(str(cfg.get("server_name") or DEFAULT_SERVER_NAME))
        self.var_port.set(str(cfg.get("port", DEFAULT_PORT)))
        self.var_query_port.set(str(cfg.get("query_port", DEFAULT_QUERY_PORT)))
        self.var_max_players.set(str(cfg.get("max_players", DEFAULT_MAX_PLAYERS)))
        self.var_join_password.set(str(cfg.get("join_password") or ""))
        self.var_admin_password.set(str(cfg.get("admin_password") or "AdminPassword"))
        self.var_enable_battleye.set(bool(cfg.get("enable_battleye", False)))
        self.var_automanaged_mods.set(bool(cfg.get("automanaged_mods", True)))
        self.var_validate_on_update.set(bool(cfg.get("validate_on_update", False)))
        self.var_enable_rcon.set(bool(cfg.get("enable_rcon", True)))
        self.var_rcon_host.set(str(cfg.get("rcon_host") or DEFAULT_RCON_HOST))
        self.var_rcon_port.set(str(cfg.get("rcon_port", DEFAULT_RCON_PORT)))
        self.var_custom_start_args.set(str(cfg.get("custom_start_args") or ""))
        self.var_backup_on_stop.set(bool(cfg.get("backup_on_stop", True)))
        self.var_backup_dir.set(str(cfg.get("backup_dir") or ""))
        self.var_backup_retention.set(str(cfg.get("backup_retention", 20)))
        self.var_auto_update_restart.set(bool(cfg.get("auto_update_restart", False)))
        self.var_auto_update_time.set(str(cfg.get("auto_update_time") or DEFAULT_SCHEDULE_TIME))
        self.var_update_on_startup.set(bool(cfg.get("update_on_startup", False)))
        self.var_hide_gameanalytics_console_logs.set(bool(cfg.get("hide_gameanalytics_console_logs", True)))

        server_tab = self.tabs.get("server")
        mods_editor = getattr(server_tab, "txt_mods", None) if server_tab else None
        if mods_editor is not None:
            try:
                mods_editor.delete("1.0", "end")
                mods_editor.insert("1.0", str(cfg.get("mods") or ""))
            except Exception:
                pass

        # ---- 高级设置 ----
        self.var_cluster_enable.set(bool(cfg.get("cluster_enable", False)))
        self.var_cluster_id.set(str(cfg.get("cluster_id") or ""))
        self.var_cluster_custom_path_enable.set(bool(cfg.get("cluster_custom_path_enable", False)))
        self.var_cluster_dir_override.set(str(cfg.get("cluster_dir_override") or ""))
        self.var_no_transfer_from_filtering.set(bool(cfg.get("no_transfer_from_filtering", False)))
        self.var_alt_save_directory_name.set(str(cfg.get("alt_save_directory_name") or ""))
        self.var_server_platform_crossplay.set(bool(cfg.get("server_platform_crossplay", False)))
        self.var_dino_mode.set(str(cfg.get("dino_mode") or ""))
        self.var_log_servergamelog.set(bool(cfg.get("log_servergamelog", False)))
        self.var_log_servergamelogincludetribelogs.set(bool(cfg.get("log_servergamelogincludetribelogs", False)))
        self.var_log_serverrconoutputtribelogs.set(bool(cfg.get("log_serverrconoutputtribelogs", False)))
        self.var_m_disablecustomcosmetics.set(bool(cfg.get("mech_disablecustomcosmetics", False)))
        self.var_m_autodestroystructures.set(bool(cfg.get("mech_autodestroystructures", False)))
        self.var_m_forcerespawndinos.set(bool(cfg.get("mech_forcerespawndinos", False)))
        self.var_m_nowildbabies.set(bool(cfg.get("mech_nowildbabies", False)))
        self.var_m_forceallowcaveflyers.set(bool(cfg.get("mech_forceallowcaveflyers", False)))
        self.var_m_disabledinonetrangescaling.set(bool(cfg.get("mech_disabledinonetrangescaling", False)))
        self.var_m_unstasisdinoobstructioncheck.set(bool(cfg.get("mech_unstasisdinoobstructioncheck", False)))
        self.var_m_alwaystickdedicatedskeletalmeshes.set(bool(cfg.get("mech_alwaystickdedicatedskeletalmeshes", False)))
        self.var_m_disablecharactertracker.set(bool(cfg.get("mech_disablecharactertracker", False)))
        self.var_m_useservernetspeedcheck.set(bool(cfg.get("mech_useservernetspeedcheck", False)))
        self.var_m_stasiskeepcontrollers.set(bool(cfg.get("mech_stasiskeepcontrollers", False)))
        self.var_m_ignoredupeditems.set(bool(cfg.get("mech_ignoredupeditems", False)))

        self._autosave_guard = False

    def _refresh_server_profile_selector(self) -> None:
        servers = self.global_cfg.get("servers") or []
        ids: List[str] = []
        labels: List[str] = []
        for s in servers:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("id") or "").strip()
            if not sid:
                continue
            ids.append(sid)
            labels.append(str(s.get("display_name") or sid))

        self._server_profile_ids = ids
        self._server_profile_labels = labels

        server_tab = self.tabs.get("server")
        combo = getattr(server_tab, "cmb_server_profile", None) if server_tab else None
        if combo is None:
            return

        try:
            combo.configure(values=labels)
        except Exception:
            return

        if self.active_server_id in ids:
            idx = ids.index(self.active_server_id)
            if 0 <= idx < len(labels):
                self.var_server_profile.set(labels[idx])

    def _collect_vars_to_server_config(self) -> Dict[str, Any]:
        def parse_int(value: str, default: int) -> int:
            try:
                return int(str(value).strip())
            except Exception:
                return default

        map_choice = (self.var_map_preset.get() or "").strip()
        custom_map = (self.var_map_custom.get() or "").strip()
        map_name = custom_map if map_choice == MAP_CUSTOM_SENTINEL else (map_choice or DEFAULT_MAP)

        server_tab = self.tabs.get("server")
        mods_editor = getattr(server_tab, "txt_mods", None) if server_tab else None
        mods_text = ""
        if mods_editor is not None:
            try:
                mods_text = mods_editor.get("1.0", "end-1c")
            except Exception:
                mods_text = ""

        cfg = self.config_manager.default_server_config()
        cfg.update(
            {
                # ---- 基础设置 ----
                "server_dir": self.var_server_dir.get().strip() or DEFAULT_SERVER_DIR,
                "map_name": map_name,
                "server_name": self.var_server_name.get().strip() or DEFAULT_SERVER_NAME,
                "port": parse_int(self.var_port.get(), DEFAULT_PORT),
                "query_port": parse_int(self.var_query_port.get(), DEFAULT_QUERY_PORT),
                "max_players": parse_int(self.var_max_players.get(), DEFAULT_MAX_PLAYERS),
                "join_password": self.var_join_password.get(),
                "admin_password": self.var_admin_password.get() or "AdminPassword",
                "enable_battleye": self.var_enable_battleye.get(),
                "automanaged_mods": self.var_automanaged_mods.get(),
                "validate_on_update": self.var_validate_on_update.get(),
                "enable_rcon": self.var_enable_rcon.get(),
                "rcon_host": self.var_rcon_host.get().strip() or DEFAULT_RCON_HOST,
                "rcon_port": parse_int(self.var_rcon_port.get(), DEFAULT_RCON_PORT),
                "custom_start_args": self.var_custom_start_args.get(),
                "mods": mods_text.strip(),
                "backup_on_stop": self.var_backup_on_stop.get(),
                "backup_dir": self.var_backup_dir.get().strip(),
                "backup_retention": parse_int(self.var_backup_retention.get(), 20),
                "auto_update_restart": self.var_auto_update_restart.get(),
                "auto_update_time": self.var_auto_update_time.get().strip() or DEFAULT_SCHEDULE_TIME,
                "update_on_startup": self.var_update_on_startup.get(),
                "hide_gameanalytics_console_logs": self.var_hide_gameanalytics_console_logs.get(),
                # ---- 集群设置 ----
                "cluster_enable": self.var_cluster_enable.get(),
                "cluster_id": self.var_cluster_id.get().strip(),
                "cluster_custom_path_enable": self.var_cluster_custom_path_enable.get(),
                "cluster_dir_override": self.var_cluster_dir_override.get().strip(),
                "no_transfer_from_filtering": self.var_no_transfer_from_filtering.get(),
                "alt_save_directory_name": self.var_alt_save_directory_name.get().strip(),
                # ---- 平台 ----
                "server_platform_crossplay": self.var_server_platform_crossplay.get(),
                # ---- 恐龙/日志 ----
                "dino_mode": self.var_dino_mode.get(),
                "log_servergamelog": self.var_log_servergamelog.get(),
                "log_servergamelogincludetribelogs": self.var_log_servergamelogincludetribelogs.get(),
                "log_serverrconoutputtribelogs": self.var_log_serverrconoutputtribelogs.get(),
                # ---- 力学/性能 ----
                "mech_disablecustomcosmetics": self.var_m_disablecustomcosmetics.get(),
                "mech_autodestroystructures": self.var_m_autodestroystructures.get(),
                "mech_forcerespawndinos": self.var_m_forcerespawndinos.get(),
                "mech_nowildbabies": self.var_m_nowildbabies.get(),
                "mech_forceallowcaveflyers": self.var_m_forceallowcaveflyers.get(),
                "mech_disabledinonetrangescaling": self.var_m_disabledinonetrangescaling.get(),
                "mech_unstasisdinoobstructioncheck": self.var_m_unstasisdinoobstructioncheck.get(),
                "mech_alwaystickdedicatedskeletalmeshes": self.var_m_alwaystickdedicatedskeletalmeshes.get(),
                "mech_disablecharactertracker": self.var_m_disablecharactertracker.get(),
                "mech_useservernetspeedcheck": self.var_m_useservernetspeedcheck.get(),
                "mech_stasiskeepcontrollers": self.var_m_stasiskeepcontrollers.get(),
                "mech_ignoredupeditems": self.var_m_ignoredupeditems.get(),
            }
        )
        return cfg

    def _iter_other_profiles(self, exclude_id: Optional[str] = None) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for server in self.global_cfg.get("servers", []):
            if not isinstance(server, dict):
                continue
            sid = str(server.get("id") or "").strip()
            if not sid or sid == exclude_id:
                continue
            result.append(server)
        return result

    def _server_dir_conflict(self, server_dir: str, exclude_id: Optional[str] = None) -> Optional[str]:
        target = str(Path(server_dir).resolve())
        for server in self._iter_other_profiles(exclude_id):
            other_dir = str(server.get("server_dir") or "").strip()
            if not other_dir:
                continue
            try:
                if str(Path(other_dir).resolve()) == target:
                    return str(server.get("display_name") or server.get("id") or "unknown")
            except Exception:
                if other_dir == target:
                    return str(server.get("display_name") or server.get("id") or "unknown")
        return None

    def _ports_conflict(self, cfg: Dict[str, Any], exclude_id: Optional[str] = None) -> Optional[str]:
        current_ports = {
            int(cfg.get("port", DEFAULT_PORT)),
            int(cfg.get("query_port", DEFAULT_QUERY_PORT)),
            int(cfg.get("rcon_port", DEFAULT_RCON_PORT)),
        }
        for server in self._iter_other_profiles(exclude_id):
            sid = str(server.get("id") or "").strip()
            if not sid:
                continue
            other_cfg = self.config_manager.load_server_config(sid)
            other_ports = {
                int(other_cfg.get("port", DEFAULT_PORT)),
                int(other_cfg.get("query_port", DEFAULT_QUERY_PORT)),
                int(other_cfg.get("rcon_port", DEFAULT_RCON_PORT)),
            }
            if current_ports & other_ports:
                return str(server.get("display_name") or sid)
        return None

    def _find_free_port_block(self, base_port: int, base_query_port: int, base_rcon_port: int) -> Dict[str, int]:
        used: set[int] = set()
        for server in self._iter_other_profiles(None):
            sid = str(server.get("id") or "").strip()
            if not sid:
                continue
            cfg = self.config_manager.load_server_config(sid)
            used.update(
                {
                    int(cfg.get("port", DEFAULT_PORT)),
                    int(cfg.get("query_port", DEFAULT_QUERY_PORT)),
                    int(cfg.get("rcon_port", DEFAULT_RCON_PORT)),
                }
            )

        stride = 10
        for n in range(0, 200):
            p = base_port + n * stride
            q = base_query_port + n * stride
            r = base_rcon_port + n * stride
            if p in used or q in used or r in used:
                continue
            if not (1 <= p <= 65535 and 1 <= q <= 65535 and 1 <= r <= 65535):
                continue
            return {"port": p, "query_port": q, "rcon_port": r}

        return {
            "port": base_port,
            "query_port": base_query_port,
            "rcon_port": base_rcon_port,
        }

    def _validate_config_conflicts(self, cfg: Dict[str, Any], interactive: bool = False) -> bool:
        try:
            port = int(cfg.get("port", DEFAULT_PORT))
            query_port = int(cfg.get("query_port", DEFAULT_QUERY_PORT))
            rcon_port = int(cfg.get("rcon_port", DEFAULT_RCON_PORT))
        except Exception:
            if interactive:
                messagebox.showwarning("配置无效", "端口必须是数字。")
            return False

        if not (1 <= port <= 65535 and 1 <= query_port <= 65535 and 1 <= rcon_port <= 65535):
            if interactive:
                messagebox.showwarning("配置无效", "端口范围必须在 1-65535。")
            return False

        if len({port, query_port, rcon_port}) < 3:
            if interactive:
                messagebox.showwarning("配置冲突", "游戏端口/查询端口/RCON 端口不能重复。")
            return False

        conflict_dir_profile = self._server_dir_conflict(str(cfg.get("server_dir") or ""), exclude_id=self.active_server_id)
        if conflict_dir_profile:
            if interactive:
                messagebox.showwarning("配置冲突", f"服务器目录已被配置文件 '{conflict_dir_profile}' 使用。")
            return False

        conflict_port_profile = self._ports_conflict(cfg, exclude_id=self.active_server_id)
        if conflict_port_profile:
            if interactive:
                messagebox.showwarning("配置冲突", f"端口与配置文件 '{conflict_port_profile}' 冲突。")
            return False

        return True

    def _save_active_server_config(self, interactive: bool = False) -> bool:
        if not self.active_server_id:
            return True
        self._ensure_server_workspace(self.active_server_id)
        next_cfg = self._collect_vars_to_server_config()
        if not self._validate_config_conflicts(next_cfg, interactive=interactive):
            return False
        self.server_cfg = next_cfg
        self.config_manager.save_server_config(self.active_server_id, self.server_cfg)

        for server in self.global_cfg.get("servers", []):
            if isinstance(server, dict) and str(server.get("id")) == self.active_server_id:
                server["server_dir"] = self.server_cfg.get("server_dir", DEFAULT_SERVER_DIR)
                break

        self.global_cfg["steamcmd_dir"] = self.var_steamcmd_dir.get().strip() or DEFAULT_STEAMCMD_DIR
        self.global_cfg["start_on_startup"] = self.var_auto_start_on_launch.get()

        # 跨服聊天配置
        try:
            self.global_cfg["chat_ws_port"] = int(self.var_chat_ws_port.get().strip() or "8000")
        except ValueError:
            self.global_cfg["chat_ws_port"] = 8000
        self.global_cfg["chat_token"] = self.var_chat_token.get().strip()
        self.global_cfg["chat_cluster_key"] = self.var_chat_cluster_key.get().strip()
        self.global_cfg["chat_auto_start"] = self.var_chat_auto_start.get()

        self.config_manager.save_global_config(self.global_cfg)
        return True

    def _setup_autosave_hooks(self) -> None:
        tracked_vars = [
            self.var_steamcmd_dir,
            self.var_server_dir,
            self.var_map_preset,
            self.var_map_custom,
            self.var_server_name,
            self.var_port,
            self.var_query_port,
            self.var_max_players,
            self.var_join_password,
            self.var_admin_password,
            self.var_enable_battleye,
            self.var_automanaged_mods,
            self.var_validate_on_update,
            self.var_enable_rcon,
            self.var_rcon_host,
            self.var_rcon_port,
            self.var_custom_start_args,
            self.var_backup_on_stop,
            self.var_backup_dir,
            self.var_backup_retention,
            self.var_auto_update_restart,
            self.var_auto_update_time,
            self.var_auto_start_on_launch,
            self.var_update_on_startup,
            self.var_hide_gameanalytics_console_logs,
            self.var_chat_ws_port,
            self.var_chat_token,
            self.var_chat_cluster_key,
            self.var_chat_auto_start,
        ]

        def traced(*_args: Any) -> None:
            if self._autosave_guard:
                return
            self._schedule_autosave()

        for var in tracked_vars:
            try:
                var.trace_add("write", traced)
            except Exception:
                pass

        server_tab = self.tabs.get("server")
        mods_editor = getattr(server_tab, "txt_mods", None) if server_tab else None
        if mods_editor is not None:
            try:
                mods_editor.bind("<KeyRelease>", lambda _e: self._schedule_autosave(), add="+")
                mods_editor.bind("<<Paste>>", lambda _e: self._schedule_autosave(), add="+")
                mods_editor.bind("<<Cut>>", lambda _e: self._schedule_autosave(), add="+")
            except Exception:
                pass

    def _schedule_autosave(self) -> None:
        if self._autosave_guard:
            return
        if self._autosave_after_id:
            try:
                self.root.after_cancel(self._autosave_after_id)
            except Exception:
                pass
        self._autosave_after_id = self.root.after(AUTOSAVE_DEBOUNCE_MS, self._autosave_now)

    def _autosave_now(self) -> None:
        self._autosave_after_id = None
        if self._autosave_guard:
            return
        try:
            self._save_active_server_config()
        except Exception as e:
            self.logger.debug(f"Autosave skipped: {e}")
    
    # =========================================================================
    # Event Handlers & Methods (Stubs)
    # =========================================================================
    
    def _on_server_profile_selected(self) -> None:
        """Handle server profile selection change."""
        selected_label = (self.var_server_profile.get() or "").strip()
        if not selected_label or selected_label not in self._server_profile_labels:
            return

        idx = self._server_profile_labels.index(selected_label)
        if idx < 0 or idx >= len(self._server_profile_ids):
            return

        selected_id = self._server_profile_ids[idx]
        if selected_id == self.active_server_id:
            return

        # 保存当前配置后再切换（允许在任何服务器运行时切换）
        if not self._save_active_server_config(interactive=True):
            # Keep selection on current profile when validation fails
            self._refresh_server_profile_selector()
            return
        self.active_server_id = selected_id
        self.global_cfg["last_selected_server_id"] = selected_id
        self.config_manager.save_global_config(self.global_cfg)

        self._ensure_server_workspace(selected_id)
        self.server_cfg = self.config_manager.load_server_config(selected_id)
        self._apply_server_config_to_vars(self.server_cfg)
        self._sync_map_mode()
        self._switch_console_to(selected_id)
        self._refresh_buttons()
        self.logger.debug("Server profile selected")
    
    def _add_server_profile(self) -> None:
        """Add a new server profile."""
        name = simpledialog.askstring("新建服务器", "显示名称：")
        if not name:
            return

        if not self._save_active_server_config(interactive=True):
            return

        chosen_dir = filedialog.askdirectory(
            title="选择该新配置文件对应的服务器安装目录",
            mustexist=False,
        )
        if not chosen_dir:
            return
        chosen_dir = str(Path(chosen_dir).resolve())
        conflict = self._server_dir_conflict(chosen_dir, exclude_id=None)
        if conflict:
            messagebox.showwarning("目录冲突", f"该目录已被配置文件 '{conflict}' 使用。")
            return

        new_id = str(uuid.uuid4())
        self._ensure_server_workspace(new_id)
        new_cfg = self.config_manager.default_server_config()
        new_cfg["server_name"] = name.strip() or DEFAULT_SERVER_NAME
        new_cfg["server_dir"] = chosen_dir
        new_cfg.update(
            self._find_free_port_block(
                int(new_cfg.get("port", DEFAULT_PORT)),
                int(new_cfg.get("query_port", DEFAULT_QUERY_PORT)),
                int(new_cfg.get("rcon_port", DEFAULT_RCON_PORT)),
            )
        )
        self.config_manager.save_server_config(new_id, new_cfg)

        servers = self.global_cfg.get("servers") or []
        servers.append(
            {
                "id": new_id,
                "display_name": name.strip() or "New Server",
                "server_dir": chosen_dir,
            }
        )
        self.global_cfg["servers"] = servers
        self.global_cfg["last_selected_server_id"] = new_id
        self.config_manager.save_global_config(self.global_cfg)

        self.active_server_id = new_id
        self.server_cfg = new_cfg
        self._apply_server_config_to_vars(new_cfg)
        self.var_server_name.set(name.strip() or DEFAULT_SERVER_NAME)
        self._refresh_server_profile_selector()
        self._sync_map_mode()
        self.logger.info(f"Adding server profile: {name}")
    
    def _rename_server_profile(self) -> None:
        """Rename the current server profile."""
        if not self.active_server_id:
            return
        current_label = self.var_server_profile.get() or "当前服务器"
        new_name = simpledialog.askstring("重命名服务器", "显示名称：", initialvalue=current_label)
        if not new_name:
            return

        for server in self.global_cfg.get("servers", []):
            if isinstance(server, dict) and str(server.get("id")) == self.active_server_id:
                server["display_name"] = new_name.strip()
                break

        self.config_manager.save_global_config(self.global_cfg)
        self._refresh_server_profile_selector()
        self.logger.info("Renaming server profile")
    
    def _remove_server_profile(self) -> None:
        """Remove the current server profile."""
        # 若该配置的服务器正在运行，禁止删除
        if self._is_server_running_for(self.active_server_id):
            messagebox.showwarning(
                "无法删除",
                "该服务器正在运行，请先停止服务器再删除配置文件。"
            )
            return

        servers = [s for s in (self.global_cfg.get("servers") or []) if isinstance(s, dict)]
        if len(servers) <= 1:
            messagebox.showwarning("提示", "至少需要保留一个服务器配置。")
            return

        if not messagebox.askyesno("删除服务器", "确认删除当前服务器配置文件？（仅删除配置，不删除游戏文件）"):
            return

        remaining = [s for s in servers if str(s.get("id")) != self.active_server_id]
        self.global_cfg["servers"] = remaining

        next_id = str(remaining[0].get("id"))
        self.active_server_id = next_id
        self.global_cfg["last_selected_server_id"] = next_id
        self.config_manager.save_global_config(self.global_cfg)

        self._ensure_server_workspace(next_id)
        self.server_cfg = self.config_manager.load_server_config(next_id)
        self._apply_server_config_to_vars(self.server_cfg)
        self._refresh_server_profile_selector()
        self._sync_map_mode()
        self.logger.info("Removing server profile")
    
    def _browse_steamcmd(self) -> None:
        """Browse for SteamCMD directory."""
        path = filedialog.askdirectory(title="选择SteamCMD目录")
        if path:
            self.var_steamcmd_dir.set(path)
            self.global_cfg["steamcmd_dir"] = path
            self.config_manager.save_global_config(self.global_cfg)
    
    def _browse_server_dir(self) -> None:
        """Browse for server installation directory."""
        path = filedialog.askdirectory(title="选择服务器安装目录")
        if path:
            selected = str(Path(path).resolve())
            conflict = self._server_dir_conflict(selected, exclude_id=self.active_server_id)
            if conflict:
                messagebox.showwarning("目录冲突", f"该目录已被配置文件 '{conflict}' 使用。")
                return
            self.var_server_dir.set(selected)
            self._save_active_server_config(interactive=True)
    
    def _browse_backup_dir(self) -> None:
        """Browse for backup directory."""
        path = filedialog.askdirectory(title="选择备份目录")
        if path:
            self.var_backup_dir.set(path)
    
    def _browse_cluster_dir(self) -> None:
        """Browse for cluster directory override."""
        path = filedialog.askdirectory(title="选择集群目录")
        if path:
            self.var_cluster_dir_override.set(path)
    
    def _sync_map_mode(self) -> None:
        """Synchronize map selection mode."""
        selected = (self.var_map_preset.get() or "").strip()
        if not selected:
            selected = DEFAULT_MAP
            self.var_map_preset.set(selected)

        is_custom = selected == MAP_CUSTOM_SENTINEL

        server_tab = self.tabs.get("server")
        custom_entry = getattr(server_tab, "ent_map_custom", None) if server_tab else None

        if is_custom:
            if not (self.var_map_custom.get() or "").strip():
                self.var_map_custom.set(DEFAULT_MAP)
            if custom_entry is not None:
                try:
                    custom_entry.configure(state="normal")
                except Exception:
                    pass
        else:
            self.var_map_custom.set(selected)
            if custom_entry is not None:
                try:
                    custom_entry.configure(state="disabled")
                except Exception:
                    pass

        self.logger.debug("Syncing map mode")
    
    def _sync_backup_label_texts(self) -> None:
        """Update backup-related UI elements."""
        self.logger.debug("Syncing backup labels")
    
    def _sync_console_log_filter_state(self) -> None:
        """Update console logging filter state."""
        self.logger.debug("Syncing console filter")
    
    
    def _validate_digits(self, value: str) -> bool:
        """Validate that input contains only digits."""
        return value == "" or value.isdigit()

    # ------------------------------------------------------------------
    # 异步执行工具
    # ------------------------------------------------------------------

    def _is_busy(self, server_id: str = "") -> bool:
        """检查指定服务器是否有操作正在进行"""
        sid = server_id or self.active_server_id
        return sid in self._busy_servers

    def _set_busy(self, server_id: str, busy: bool) -> None:
        """更新指定服务器的忙碌状态，并刷新按钮。"""
        if busy:
            self._busy_servers.add(server_id)
        else:
            self._busy_servers.discard(server_id)
        self._update_button_states()

    def _run_async(self, task_fn, *, label: str = "操作", server_id: str = "") -> None:
        """
        在守护线程中执行 task_fn，期间锁定该服务器的操作按钮防止重复点击。
        不同服务器的操作可以并行执行。
        """
        sid = server_id or self.active_server_id
        if sid in self._busy_servers:
            self.logger.warning("该服务器已有操作正在进行，忽略新请求: %s", label)
            return

        def _worker() -> None:
            try:
                task_fn()
            except Exception as e:
                self.logger.error("%s 执行异常: %s", label, e)
                self.root.after(0, lambda msg=str(e): messagebox.showerror(label, msg))
            finally:
                self.root.after(0, lambda: self._set_busy(sid, False))

        self._set_busy(sid, True)
        t = threading.Thread(target=_worker, daemon=True, name=label)
        t.start()

    def _log_console(self, message: str, server_id: str = "") -> None:
        """线程安全地向指定服务器的控制台缓冲区追加一行，
        如果是当前激活的服务器则同时显示到 UI。"""
        sid = server_id or self.active_server_id
        if sid:
            with self._console_buffers_lock:
                buf = self._console_buffers.setdefault(sid, [])
                buf.append(message)

        def _append() -> None:
            if sid and sid != self.active_server_id:
                return
            try:
                self.txt_log.configure(state="normal")
                self.txt_log.insert("end", message + "\n")
                self.txt_log.see("end")
                self.txt_log.configure(state="disabled")
            except Exception:
                pass
        self.root.after(0, _append)

    def _switch_console_to(self, server_id: str) -> None:
        """切换控制台显示到指定服务器的日志缓冲区"""
        try:
            # 更新标题以显示当前服务器名称
            display_name = ""
            for s in self.global_cfg.get("servers", []):
                if isinstance(s, dict) and str(s.get("id")) == server_id:
                    display_name = str(s.get("display_name") or "")
                    break
            label = f"控制台输出 - {display_name}" if display_name else "控制台输出"
            self._console_label_frame.configure(text=label)

            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            with self._console_buffers_lock:
                lines = self._console_buffers.get(server_id, [])
                if lines:
                    self.txt_log.insert("end", "\n".join(lines) + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 多服务器进程状态辅助
    # ------------------------------------------------------------------

    def _is_server_running(self) -> bool:
        """检查当前选中配置的服务器是否正在运行"""
        return self._is_server_running_for(self.active_server_id)

    def _is_server_running_for(self, server_id: str) -> bool:
        """检查指定 server_id 的服务器是否正在运行"""
        if not server_id:
            return False
        with self._server_procs_lock:
            p = self._server_procs.get(server_id)
        return p is not None and p.poll() is None

    def _get_running_server_ids(self) -> List[str]:
        """获取所有正在运行的 server_id 列表"""
        with self._server_procs_lock:
            ids = list(self._server_procs.keys())
        return [sid for sid in ids if self._is_server_running_for(sid)]

    def _refresh_buttons(self) -> None:
        """刷新操作按钮状态（在 UI 线程中调用）"""
        self._update_button_states()

    def _update_button_states(self) -> None:
        """根据当前服务器运行状态和忙碌状态刷新所有操作按钮。"""
        server_tab = self.tabs.get("server")
        if server_tab is None:
            return

        running = self._is_server_running()
        busy = self._is_busy()

        try:
            if busy:
                server_tab.btn_first_install.configure(state="disabled")
                server_tab.btn_start.configure(state="disabled")
                server_tab.btn_stop.configure(state="disabled")
                server_tab.btn_update_validate.configure(state="disabled")
                server_tab.btn_update_restart.configure(state="disabled")
                server_tab.btn_backup_now.configure(state="disabled")
            elif running:
                server_tab.btn_first_install.configure(state="disabled")
                server_tab.btn_start.configure(state="disabled")
                server_tab.btn_stop.configure(state="normal")
                server_tab.btn_update_validate.configure(state="disabled")
                server_tab.btn_update_restart.configure(state="normal")
                server_tab.btn_backup_now.configure(state="normal")
            else:
                server_tab.btn_first_install.configure(state="normal")
                server_tab.btn_start.configure(state="normal")
                server_tab.btn_stop.configure(state="disabled")
                server_tab.btn_update_validate.configure(state="normal")
                server_tab.btn_update_restart.configure(state="normal")
                server_tab.btn_backup_now.configure(state="normal")
        except Exception:
            pass

    def _server_log_reader_for(self, server_id: str) -> None:
        """后台线程：将指定服务器进程的 stdout 实时写入该服务器的控制台缓冲区"""
        with self._server_procs_lock:
            p = self._server_procs.get(server_id)
        if not p or not p.stdout:
            return

        stop_event = self._stop_log_readers.get(server_id)
        cfg = self._running_server_configs.get(server_id, {})
        hide_ga = cfg.get("hide_gameanalytics_console_logs", True)

        try:
            for line in p.stdout:
                if stop_event and stop_event.is_set():
                    break
                stripped = line.rstrip()
                if hide_ga and "gameanalytics" in stripped.lower():
                    continue
                self._log_console(stripped, server_id=server_id)
        except Exception as e:
            self._log_console(f"日志读取器停止: {e}", server_id=server_id)
        finally:
            code: Optional[int] = None
            try:
                code = p.poll()
                if code is not None:
                    self._log_console(
                        f"服务器已退出，退出码: {code}", server_id=server_id
                    )
            except Exception:
                pass

            with self._server_procs_lock:
                if self._server_procs.get(server_id) is p:
                    self._server_procs.pop(server_id, None)
                self._stop_log_readers.pop(server_id, None)
                self._running_server_configs.pop(server_id, None)

            self.root.after(0, self._refresh_buttons)
            self._maybe_auto_restart_for(server_id, code)

    def _maybe_auto_restart_for(self, server_id: str, exit_code: Optional[int]) -> None:
        """若退出码符合自动重启条件，在延迟后重新启动指定服务器"""
        if exit_code is None:
            return
        if exit_code not in AUTO_RESTART_EXIT_CODES:
            return
        stop_flag = self._stop_requested_flags.get(server_id)
        if stop_flag and stop_flag.is_set():
            return
        if self._is_busy(server_id):
            return

        self._log_console(
            f"服务器以代码 {exit_code} 退出 → {AUTO_RESTART_DELAY_SEC}s 后自动重启...",
            server_id=server_id,
        )

        def _delayed_restart() -> None:
            time.sleep(AUTO_RESTART_DELAY_SEC)
            try:
                cfg = self.config_manager.load_server_config(server_id)
                self._start_server_for(server_id, cfg)
            except Exception as e:
                self._log_console(f"自动重启失败: {e}", server_id=server_id)

        threading.Thread(target=_delayed_restart, daemon=True).start()

    # ------------------------------------------------------------------
    # 服务器操作 — 公共方法（后台线程执行）
    # ------------------------------------------------------------------

    def first_install(self) -> None:
        """首次安装：安装依赖 + 证书 + SteamCMD + ASA 服务器"""
        server_id = self.active_server_id

        def _task() -> None:
            self._save_active_server_config()
            cfg = self.server_cfg
            steamcmd_dir = self.var_steamcmd_dir.get().strip() or DEFAULT_STEAMCMD_DIR

            from ..utils.windows import ensure_dependencies, install_asa_certificates, is_admin
            if not is_admin():
                self._log_console("警告：未以管理员身份运行，安装可能失败。", server_id=server_id)

            self._log_console("正在安装依赖...", server_id=server_id)
            ensure_dependencies(self.logger)
            install_asa_certificates(self.logger)

            self._log_console("正在通过 SteamCMD 安装服务器...", server_id=server_id)
            steam = SteamManager(Path(steamcmd_dir))
            steam.update_app(
                install_dir=Path(cfg["server_dir"]),
                logger=self.logger,
                app_id=ARK_ASA_APP_ID,
                validate=False,
                lock_root=self.app_base,
            )

            exe = ark_server_exe(Path(cfg["server_dir"]))
            self._log_console(
                f"服务器 EXE: {exe}  ({'存在' if exe.exists() else '未找到'})",
                server_id=server_id,
            )

        self._run_async(_task, label="首次安装")

    def start_server(self) -> None:
        """启动当前选中的服务器"""
        server_id = self.active_server_id

        def _task() -> None:
            self._save_active_server_config()
            cfg = dict(self.server_cfg)
            steamcmd_dir = self.var_steamcmd_dir.get().strip() or DEFAULT_STEAMCMD_DIR

            if cfg.get("update_on_startup"):
                self._log_console("启动时更新已开启 → 正在更新服务器...", server_id=server_id)
                self._update_server_install(cfg, steamcmd_dir, validate=None)

            if self._is_server_running_for(server_id):
                raise RuntimeError("该服务器已在运行中。")

            self._start_server_for(server_id, cfg)

        self._run_async(_task, label="启动服务器")

    def stop_server_safe(self) -> None:
        """安全停止当前选中的服务器"""
        server_id = self.active_server_id

        def _task() -> None:
            self._save_active_server_config()
            stop_flag = self._stop_requested_flags.setdefault(server_id, threading.Event())
            stop_flag.set()
            self._stop_server_for(server_id)

        self._run_async(_task, label="停止服务器")

    def update_validate(self) -> None:
        """更新并验证服务器文件"""
        def _task() -> None:
            self._save_active_server_config()
            cfg = self.server_cfg
            steamcmd_dir = self.var_steamcmd_dir.get().strip() or DEFAULT_STEAMCMD_DIR
            validate = bool(cfg.get("validate_on_update", False))
            self._update_server_install(cfg, steamcmd_dir, validate=validate)

        self._run_async(_task, label="更新/验证")

    def update_and_restart_safe(self) -> None:
        """安全停止 → 更新 → 重新启动"""
        server_id = self.active_server_id

        def _task() -> None:
            self._save_active_server_config()
            cfg = dict(self.server_cfg)
            steamcmd_dir = self.var_steamcmd_dir.get().strip() or DEFAULT_STEAMCMD_DIR

            if self._is_server_running_for(server_id):
                self._log_console("服务器运行中 → 安全停止后更新...", server_id=server_id)
                stop_flag = self._stop_requested_flags.setdefault(server_id, threading.Event())
                stop_flag.set()
                self._stop_server_for(server_id)

            self._log_console("正在更新服务器...", server_id=server_id)
            self._update_server_install(cfg, steamcmd_dir, validate=None)

            self._log_console("更新完成 → 正在重新启动服务器...", server_id=server_id)
            self._start_server_for(server_id, cfg)

        self._run_async(_task, label="更新并重启")

    def backup_now(self) -> None:
        """立即创建备份"""
        def _task() -> None:
            self._save_active_server_config()
            path = backup_server(self.server_cfg, self.app_base, self.logger)
            if path:
                self.root.after(
                    0, lambda p=path: messagebox.showinfo("备份完成", f"备份已保存到:\n{p}")
                )

        self._run_async(_task, label="立即备份")

    def auto_update_test(self) -> None:
        """手动触发自动更新流程（测试用）"""
        if self._is_busy():
            messagebox.showwarning("忙碌", "该服务器有操作正在进行，请稍后再试。")
            return
        self.logger.info("手动触发 → 更新并重启（安全）。")
        self.update_and_restart_safe()

    # ------------------------------------------------------------------
    # 服务器操作内部实现（支持多服务器隔离）
    # ------------------------------------------------------------------

    def _start_server_for(self, server_id: str, cfg: Dict[str, Any]) -> None:
        """启动指定 server_id 的服务器（可从任意线程调用）"""
        server_dir = Path(cfg["server_dir"])
        exe = ark_server_exe(server_dir)

        if not exe.exists():
            raise FileNotFoundError(f"服务器 EXE 不存在: {exe}")

        if cfg.get("enable_rcon") and not (cfg.get("admin_password") or "").strip():
            raise RuntimeError("管理员密码为空。启用 RCON 前必须设置管理员密码。")

        ensure_baseline(self.app_base, server_id, server_dir, self.logger, refresh=True)
        ensure_required_server_settings(cfg, self.app_base, server_id, server_dir, self.logger)
        apply_staging_to_server(self.app_base, server_id, server_dir, self.logger)

        self._reinject_lacc_to_server(server_id, server_dir)

        stop_flag = self._stop_requested_flags.setdefault(server_id, threading.Event())
        stop_flag.clear()

        cmd = build_server_command(cfg)
        self._log_console(f"启动服务器命令:", server_id=server_id)
        self._log_console(" ".join(cmd), server_id=server_id)

        _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with self._server_procs_lock:
            existing = self._server_procs.get(server_id)
            if existing and existing.poll() is None:
                raise RuntimeError("该服务器已在运行中。")

            stop_log = threading.Event()
            self._stop_log_readers[server_id] = stop_log

            proc = subprocess.Popen(
                cmd,
                cwd=str(exe.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=_CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            self._server_procs[server_id] = proc
            self._running_server_configs[server_id] = dict(cfg)

        threading.Thread(
            target=self._server_log_reader_for, args=(server_id,), daemon=True
        ).start()
        self.root.after(0, self._refresh_buttons)

    def _stop_server_for(self, server_id: str) -> None:
        """停止指定 server_id 的服务器进程"""
        with self._server_procs_lock:
            p = self._server_procs.get(server_id)

        if not p or p.poll() is not None:
            self._log_console("服务器未运行。", server_id=server_id)
            return

        cfg = self._running_server_configs.get(server_id) or self.config_manager.load_server_config(server_id)

        if cfg.get("enable_rcon"):
            for rcon_cmd in ("SaveWorld", "DoExit"):
                try:
                    self._log_console(f"RCON: {rcon_cmd}", server_id=server_id)
                    self._rcon_exec_for(cfg, rcon_cmd, timeout=6.0)
                except Exception as e:
                    self._log_console(f"RCON {rcon_cmd} 失败: {e}", server_id=server_id)

        t_end = time.time() + 20
        while time.time() < t_end and p.poll() is None:
            time.sleep(0.5)

        if p.poll() is None:
            self._log_console("正在强制终止服务器进程...", server_id=server_id)
            stop_log = self._stop_log_readers.get(server_id)
            if stop_log:
                stop_log.set()
            p.terminate()
            try:
                p.wait(timeout=12)
            except subprocess.TimeoutExpired:
                self._log_console("terminate() 超时，执行 kill()...", server_id=server_id)
                p.kill()
                p.wait(timeout=5)

        with self._server_procs_lock:
            self._server_procs.pop(server_id, None)
            self._running_server_configs.pop(server_id, None)
            self._stop_log_readers.pop(server_id, None)

        self._log_console("服务器已停止。", server_id=server_id)

        if cfg.get("backup_on_stop"):
            path = backup_server(cfg, self.app_base, self.logger)
            if path:
                self._log_console(f"停止时备份已完成: {path}", server_id=server_id)

        restore_baseline_to_server(self.app_base, server_id, Path(cfg["server_dir"]), self.logger)
        self.root.after(0, self._refresh_buttons)

    def _update_server_install(
        self,
        cfg: Dict[str, Any],
        steamcmd_dir: str,
        validate: Optional[bool],
    ) -> None:
        """运行 SteamCMD app_update"""
        if validate is None:
            validate = bool(cfg.get("validate_on_update", False))
        steam = SteamManager(Path(steamcmd_dir))
        steam.update_app(
            install_dir=Path(cfg["server_dir"]),
            logger=self.logger,
            app_id=ARK_ASA_APP_ID,
            validate=validate,
            lock_root=self.app_base,
        )

    # ------------------------------------------------------------------
    # RCON 运行时快照
    # 防止用户在 GUI 中修改密码/端口后，RCON 用了与运行中服务器不一致的参数
    # ------------------------------------------------------------------

    def _current_rcon_cfg(self, server_id: str = "") -> Dict[str, Any]:
        """获取 RCON 连接参数：服务器运行中时使用启动时的快照，否则使用当前配置。"""
        sid = server_id or self.active_server_id
        if self._is_server_running_for(sid):
            runtime_cfg = self._running_server_configs.get(sid)
            if runtime_cfg:
                return runtime_cfg
        return self.server_cfg

    def _rcon_exec(self, cmd: str, timeout: float = 4.0) -> str:
        """发送 RCON 命令到当前选中的服务器（自动选择运行时快照或当前配置）"""
        cfg = self._current_rcon_cfg()
        return self._rcon_exec_for(cfg, cmd, timeout)

    def _rcon_exec_for(self, cfg: Dict[str, Any], cmd: str, timeout: float = 4.0) -> str:
        """发送一条 RCON 命令到指定配置的服务器"""
        from ..rcon.protocol import RCONProtocol

        host = (cfg.get("rcon_host") or DEFAULT_RCON_HOST).strip()
        port = int(cfg.get("rcon_port", DEFAULT_RCON_PORT))
        password = (cfg.get("admin_password") or "").strip()

        if not password:
            raise RuntimeError("管理员密码为空，无法进行 RCON 认证。")

        proto = RCONProtocol(host, port)
        if not proto.connect(timeout=int(max(timeout, 1))):
            raise RuntimeError(f"RCON 连接失败 ({host}:{port})，服务器是否在运行？")
        try:
            if not proto.authenticate(password):
                raise RuntimeError(f"RCON 认证失败 ({host}:{port})，请检查管理员密码。")
            response = proto.execute_command(cmd)
        finally:
            proto.disconnect()
        return (response or "").strip()

    # ------------------------------------------------------------------
    # 自动更新调度器（每服务器独立）
    # ------------------------------------------------------------------

    def _init_all_auto_update_schedulers(self) -> None:
        """应用启动时，为所有已启用自动更新的服务器启动调度器"""
        servers = self.global_cfg.get("servers") or []
        for server in servers:
            if not isinstance(server, dict):
                continue
            server_id = str(server.get("id") or "").strip()
            if not server_id:
                continue
            cfg = self.config_manager.load_server_config(server_id)
            if cfg.get("auto_update_restart", False):
                self._start_auto_update_scheduler_for(server_id, cfg)

    def _start_auto_update_scheduler_for(self, server_id: str, cfg: Dict[str, Any]) -> None:
        """为指定服务器启动自动更新调度线程"""
        old_stop = self._auto_update_stops.get(server_id)
        if old_stop:
            old_stop.set()

        new_stop = threading.Event()
        self._auto_update_stops[server_id] = new_stop
        t = threading.Thread(
            target=self._auto_update_loop_for,
            args=(server_id, new_stop),
            daemon=True,
            name=f"AutoUpdate-{server_id[:8]}",
        )
        self._auto_update_threads[server_id] = t
        t.start()

        schedule_time = cfg.get("auto_update_time") or "03:00"
        self.logger.info(f"[{server_id[:8]}] 自动更新调度器已启动 (计划时间: {schedule_time})。")

    def _stop_auto_update_scheduler_for(self, server_id: str) -> None:
        """停止指定服务器的自动更新调度线程"""
        old_stop = self._auto_update_stops.get(server_id)
        if old_stop:
            old_stop.set()
            self.logger.info(f"[{server_id[:8]}] 自动更新调度器已停止。")

    def _sync_auto_update_scheduler(self) -> None:
        """根据当前配置启动或停止该服务器的自动更新调度线程"""
        try:
            self._save_active_server_config()
        except Exception:
            return

        server_id = self.active_server_id
        if not server_id:
            return

        enabled = bool(self.server_cfg.get("auto_update_restart", False))

        if enabled:
            self._start_auto_update_scheduler_for(server_id, self.server_cfg)
        else:
            self._stop_auto_update_scheduler_for(server_id)

    def _auto_update_loop_for(self, server_id: str, stop_event: threading.Event) -> None:
        """后台线程：等待到计划时间后触发指定服务器的更新重启"""
        import re as _re
        from datetime import datetime, time as dt_time, timedelta

        def _parse_hhmm(value: str):
            clean = (value or "").strip()
            if _re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", clean):
                h, m = clean.split(":")
                return dt_time(int(h), int(m))
            return dt_time(3, 0)

        while not stop_event.is_set():
            cfg = self.config_manager.load_server_config(server_id)
            schedule_time = _parse_hhmm(cfg.get("auto_update_time") or "03:00")
            now = datetime.now()
            candidate = now.replace(
                hour=schedule_time.hour, minute=schedule_time.minute, second=0, microsecond=0
            )
            if candidate <= now:
                candidate += timedelta(days=1)
            wait_sec = max(1.0, (candidate - now).total_seconds())

            if stop_event.wait(timeout=wait_sec):
                return
            if stop_event.is_set():
                return
            if self._is_busy(server_id):
                self.logger.info(f"[{server_id[:8]}] 自动更新已跳过：该服务器正忙。")
                continue

            self.logger.info(f"[{server_id[:8]}] 自动更新触发 → 更新并重启（安全）。")

            def _do_update(sid=server_id):
                cfg_now = self.config_manager.load_server_config(sid)
                steamcmd_dir = self.global_cfg.get("steamcmd_dir") or DEFAULT_STEAMCMD_DIR
                if self._is_server_running_for(sid):
                    stop_flag = self._stop_requested_flags.setdefault(sid, threading.Event())
                    stop_flag.set()
                    self._stop_server_for(sid)
                self._update_server_install(cfg_now, steamcmd_dir, validate=None)
                self._start_server_for(sid, cfg_now)

            self._run_async(_do_update, label=f"自动更新-{server_id[:8]}", server_id=server_id)
    
    def send_rcon(self) -> None:
        """Send RCON command."""
        cmd = self.var_rcon_cmd.get().strip()
        if not cmd:
            return
        server_id = self.active_server_id

        def _task() -> None:
            self._save_active_server_config()
            self._log_console(f"RCON> {cmd}", server_id=server_id)
            try:
                out = self._rcon_exec(cmd, timeout=5.0)
                self._log_console(out if out else "(无响应)", server_id=server_id)
            except Exception as e:
                self._log_console(f"RCON 错误: {e}", server_id=server_id)
            self.root.after(0, lambda: self.var_rcon_cmd.set(""))

        self._run_async(_task, label="RCON")
    
    def _rcon_save_current(self) -> None:
        """Save the current RCON command to saved list."""
        self.logger.debug("Saving RCON command")
    
    def _rcon_remove_selected(self) -> None:
        """Remove selected RCON command from saved list."""
        self.logger.debug("Removing RCON command")
    
    def _discord_send_test(self) -> None:
        """Send a test Discord webhook."""
        self.logger.info("Sending Discord test message")
    
    def _discord_open_state_folder(self) -> None:
        """Open the Discord state folder."""
        self.logger.debug("Opening Discord state folder")
    
    def load_gameusersettings(self) -> None:
        """Load GameUserSettings.ini for editing."""
        if not self.active_server_id:
            messagebox.showwarning("提示", "请先选择一个服务器配置。")
            return
        stage_gus, _ = staging_paths(self.app_base, self.active_server_id)
        if not stage_gus.exists():
            server_dir = Path(self.var_server_dir.get().strip())
            live = server_dir / GAMEUSERSETTINGS_REL
            if live.exists():
                stage_gus.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(live, stage_gus)
            else:
                stage_gus.parent.mkdir(parents=True, exist_ok=True)
                stage_gus.write_text("", encoding="utf-8")
        self._ini_load_file(stage_gus, "GameUserSettings.ini")

    def load_game_ini(self) -> None:
        """Load Game.ini for editing."""
        if not self.active_server_id:
            messagebox.showwarning("提示", "请先选择一个服务器配置。")
            return
        _, stage_game = staging_paths(self.app_base, self.active_server_id)
        if not stage_game.exists():
            server_dir = Path(self.var_server_dir.get().strip())
            live = server_dir / GAME_INI_REL
            if live.exists():
                stage_game.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(live, stage_game)
            else:
                stage_game.parent.mkdir(parents=True, exist_ok=True)
                stage_game.write_text("", encoding="utf-8")
        self._ini_load_file(stage_game, "Game.ini")

    def _ini_load_file(self, path: Path, display_name: str) -> None:
        """Load and parse an INI file, then refresh the tree view."""
        parser = INIParser()
        if not parser.parse_file(path):
            messagebox.showerror("加载失败", f"无法解析 INI 文件:\n{path}")
            return
        self._ini_parser = parser
        self._ini_loaded_path = path
        self._ini_loaded_name = display_name

        ini_tab = self.tabs.get("ini")
        if ini_tab:
            ini_tab.lbl_ini_target.configure(text=f"{display_name}  ({path})")

        self.var_ini_section.set("")
        self.var_ini_key.set("")
        self.var_ini_value.set("")
        self._ini_refresh_tree()
        self.logger.info("已加载 INI 文件: %s", path)

    def open_loaded_ini(self) -> None:
        """Open the currently loaded INI file in the default text editor."""
        if not self._ini_loaded_path or not self._ini_loaded_path.exists():
            messagebox.showwarning("提示", "尚未加载任何 INI 文件。")
            return
        try:
            if os.name == "nt":
                os.startfile(str(self._ini_loaded_path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(self._ini_loaded_path)])
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件: {e}")

    def _ini_resync_from_upstream(self) -> None:
        """Copy the server's actual INI files to staging and reload the current one."""
        if not self.active_server_id:
            messagebox.showwarning("提示", "请先选择一个服务器配置。")
            return
        server_dir = Path(self.var_server_dir.get().strip())
        stage_gus, stage_game = staging_paths(self.app_base, self.active_server_id)
        import shutil

        live_gus = server_dir / GAMEUSERSETTINGS_REL
        if live_gus.exists():
            stage_gus.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live_gus, stage_gus)

        live_game = server_dir / GAME_INI_REL
        if live_game.exists():
            stage_game.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live_game, stage_game)

        if self._ini_loaded_path and self._ini_loaded_path.exists():
            self._ini_load_file(self._ini_loaded_path, self._ini_loaded_name)
            messagebox.showinfo("同步完成", "已从上游重新整合 INI 文件。")
        else:
            messagebox.showinfo("同步完成", "已从服务器目录复制 INI 到 staging。\n请点击加载按钮查看。")

    def _ini_refresh_tree(self) -> None:
        """Refresh the INI tree view based on current parser data and filter."""
        ini_tab = self.tabs.get("ini")
        if not ini_tab or not self._ini_parser:
            return

        tree = ini_tab.tree_ini
        tree.delete(*tree.get_children())

        filter_text = (self.var_ini_filter.get() or "").strip().lower()

        for section, keys in self._ini_parser.sections.items():
            section_matches = not filter_text or filter_text in section.lower()
            child_items = []
            for key, value in keys.items():
                if filter_text and not section_matches:
                    if filter_text not in key.lower() and filter_text not in value.lower():
                        continue
                child_items.append((key, value))

            if not child_items and not section_matches:
                continue

            section_id = tree.insert(
                "", "end",
                text=f"[{section}]",
                values=(section, "", ""),
                open=bool(filter_text),
            )
            for key, value in child_items:
                tree.insert(
                    section_id, "end",
                    text=key,
                    values=(section, key, value),
                )

    def _ini_tree_select(self) -> None:
        """Handle INI tree selection — populate the edit panel."""
        ini_tab = self.tabs.get("ini")
        if not ini_tab:
            return
        tree = ini_tab.tree_ini
        selection = tree.selection()
        if not selection:
            return
        item = selection[0]
        values = tree.item(item, "values")
        if not values or len(values) < 3:
            return
        section, key, value = values[0], values[1], values[2]
        self.var_ini_section.set(section)
        self.var_ini_key.set(key)
        self.var_ini_value.set(value)

    def _ini_update_value(self) -> None:
        """Update the selected INI value."""
        if not self._ini_parser:
            messagebox.showwarning("提示", "请先加载一个 INI 文件。")
            return
        section = self.var_ini_section.get().strip()
        key = self.var_ini_key.get().strip()
        value = self.var_ini_value.get()
        if not section or not key:
            messagebox.showwarning("提示", "请在左侧树中选择一个键值条目。")
            return
        self._ini_parser.set(section, key, value)
        self._ini_refresh_tree()
        self.logger.info("INI 值已更新: [%s] %s = %s", section, key, value)

    def _ini_delete_entry(self) -> None:
        """Delete the selected INI entry."""
        if not self._ini_parser:
            messagebox.showwarning("提示", "请先加载一个 INI 文件。")
            return
        section = self.var_ini_section.get().strip()
        key = self.var_ini_key.get().strip()
        if not section or not key:
            messagebox.showwarning("提示", "请在左侧树中选择一个键值条目。")
            return
        if not self._ini_parser.delete(section, key):
            messagebox.showwarning("提示", f"未找到条目: [{section}] {key}")
            return
        self.var_ini_section.set("")
        self.var_ini_key.set("")
        self.var_ini_value.set("")
        self._ini_refresh_tree()
        self.logger.info("INI 条目已删除: [%s] %s", section, key)

    def _ini_add_entry(self) -> None:
        """Add a new INI entry."""
        if not self._ini_parser:
            messagebox.showwarning("提示", "请先加载一个 INI 文件。")
            return
        section = self.var_ini_add_section.get().strip()
        key = self.var_ini_add_key.get().strip()
        value = self.var_ini_add_value.get()
        if not section or not key:
            messagebox.showwarning("提示", "部分和键不能为空。")
            return
        self._ini_parser.set(section, key, value)
        self.var_ini_add_section.set("")
        self.var_ini_add_key.set("")
        self.var_ini_add_value.set("")
        self._ini_refresh_tree()
        self.logger.info("INI 条目已添加: [%s] %s = %s", section, key, value)

    def _ini_save_changes(self) -> None:
        """Save all INI changes to the staging file."""
        if not self._ini_parser or not self._ini_loaded_path:
            messagebox.showwarning("提示", "请先加载一个 INI 文件。")
            return
        if self._ini_parser.save_file(self._ini_loaded_path):
            messagebox.showinfo("保存成功", f"INI 更改已保存到:\n{self._ini_loaded_path}")
            self.logger.info("INI 文件已保存: %s", self._ini_loaded_path)
        else:
            messagebox.showerror("保存失败", f"无法保存 INI 文件:\n{self._ini_loaded_path}")
    
    def open_server_config_dir(self) -> None:
        """Open the server configuration directory."""
        path = self.app_base
        if self.active_server_id:
            path = self.config_manager.get_server_root(self.active_server_id)
        self.open_folder(path)
        self.logger.debug("Opening server config directory")
    
    def open_folder(self, path: Path) -> None:
        """Open a folder in file explorer."""
        try:
            import os
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
        except Exception as e:
            self.logger.error(f"Failed to open folder: {e}")
    
    # ------------------------------------------------------------------
    # 跨服聊天 (LACC WebSocket)
    # ------------------------------------------------------------------

    def _start_chat_server(self) -> None:
        """启动 LACC WebSocket 中继服务器"""
        if self._chat_server and self._chat_server.is_running:
            self.logger.info("LACC WebSocket 服务器已在运行中")
            return

        try:
            port = int(self.var_chat_ws_port.get().strip() or "8000")
        except ValueError:
            messagebox.showwarning("配置错误", "WebSocket 端口必须是数字。")
            return

        token = self.var_chat_token.get().strip()
        cluster_key = self.var_chat_cluster_key.get().strip()

        self._chat_server = LACCWebSocketServer(
            host="0.0.0.0",
            port=port,
            token=token,
            cluster_key=cluster_key,
            on_message=self._on_chat_message,
            on_connect=self._on_chat_client_connect,
            on_disconnect=self._on_chat_client_disconnect,
        )
        self._chat_server.start()

        chat_tab = self.tabs.get("chat")
        if chat_tab:
            self.root.after(0, lambda: chat_tab.update_server_status(True))
            self.root.after(0, lambda: chat_tab.append_system_message(
                f"WebSocket 中继服务器已启动 (端口: {port})"
            ))

        self.logger.info("LACC WebSocket 服务器已启动 (端口: %d)", port)
        self._save_active_server_config()

    def _stop_chat_server(self) -> None:
        """停止 LACC WebSocket 中继服务器"""
        if not self._chat_server or not self._chat_server.is_running:
            return

        self._chat_server.stop()
        self._chat_server = None

        chat_tab = self.tabs.get("chat")
        if chat_tab:
            self.root.after(0, lambda: chat_tab.update_server_status(False))
            self.root.after(0, lambda: chat_tab.append_system_message(
                "WebSocket 中继服务器已停止"
            ))

        self.logger.info("LACC WebSocket 服务器已停止")

    def _send_chat_message(self) -> None:
        """从管理器向所有已连接服务器广播消息"""
        chat_tab = self.tabs.get("chat")
        if not chat_tab:
            return

        text = chat_tab.var_chat_input.get().strip()
        if not text:
            return

        if not self._chat_server or not self._chat_server.is_running:
            messagebox.showwarning("未启动", "WebSocket 中继服务器未运行，请先启动。")
            return

        self._chat_server.send_admin_message(text)
        chat_tab.var_chat_input.set("")

    def _on_chat_message(self, msg) -> None:
        """收到聊天消息时的回调（从 WebSocket 线程调用）"""
        chat_tab = self.tabs.get("chat")
        if chat_tab:
            self.root.after(0, lambda m=msg: chat_tab.append_chat_message(m))

    def _on_chat_client_connect(self, name: str) -> None:
        """客户端连接时的回调"""
        chat_tab = self.tabs.get("chat")
        if chat_tab and self._chat_server:
            clients = self._chat_server.get_connected_clients()
            self.root.after(0, lambda: chat_tab.refresh_client_list(clients))
            self.root.after(0, lambda: chat_tab.append_system_message(
                f"服务器 [{name}] 已连接"
            ))

    def _on_chat_client_disconnect(self, name: str) -> None:
        """客户端断开时的回调"""
        chat_tab = self.tabs.get("chat")
        if chat_tab and self._chat_server:
            clients = self._chat_server.get_connected_clients()
            self.root.after(0, lambda: chat_tab.refresh_client_list(clients))
            self.root.after(0, lambda: chat_tab.append_system_message(
                f"服务器 [{name}] 已断开"
            ))

    def _reinject_lacc_to_server(self, server_id: str, server_dir: Path) -> None:
        """在 apply_staging_to_server 之后，用原始文本直接将 LACC 配置
        注入到服务器的 GameUserSettings.ini 中，避免 UE5 INI 解析器
        将 URL 中的 :// 截断。"""
        stage_gus, _ = staging_paths(self.app_base, server_id)
        if not stage_gus.exists():
            return

        import re
        content = stage_gus.read_text(encoding="utf-8-sig")
        match = re.search(r"\[LACC\]\s*\n((?:[^\[]*\n?)*)", content)
        if not match:
            return

        lacc_body = match.group(1)
        kv: Dict[str, str] = {}
        for line in lacc_body.splitlines():
            stripped = line.strip()
            if "=" in stripped:
                k, v = stripped.split("=", 1)
                kv[k.strip()] = v.strip()

        ws_url = kv.get("URL", "").strip('"')
        token = kv.get("Token", "")
        name = kv.get("Name", "").strip('"')

        if not ws_url:
            return

        inject_lacc_to_server_config(
            server_dir, ws_url, token, name, self.logger
        )

    def _auto_configure_lacc(self) -> None:
        """自动为所有服务器配置 LACC mod"""
        servers = self.global_cfg.get("servers") or []
        if not servers:
            messagebox.showwarning("无服务器", "没有可配置的服务器。")
            return

        try:
            ws_port = int(self.var_chat_ws_port.get().strip() or "8000")
        except ValueError:
            messagebox.showwarning("配置错误", "WebSocket 端口必须是数字。")
            return

        token = self.var_chat_token.get().strip()
        cluster_key = self.var_chat_cluster_key.get().strip()

        ws_url = f"ws://127.0.0.1:{ws_port}"

        configured_count = 0
        for server in servers:
            if not isinstance(server, dict):
                continue
            sid = str(server.get("id") or "").strip()
            if not sid:
                continue

            display_name = str(server.get("display_name") or sid)
            cfg = self.config_manager.load_server_config(sid)

            # 添加 LACC mod ID 到 mods 列表
            mods_raw = str(cfg.get("mods") or "")
            mod_ids = [m.strip() for m in mods_raw.split(",") if m.strip()]
            if LACC_MOD_ID not in mod_ids:
                mod_ids.append(LACC_MOD_ID)
                cfg["mods"] = ",".join(mod_ids)
                self.config_manager.save_server_config(sid, cfg)

            # 写入 LACC INI 配置到 staging 目录
            server_dir = Path(str(cfg.get("server_dir") or ""))
            self._inject_lacc_ini(
                sid, server_dir, ws_url, token, display_name
            )

            configured_count += 1

        # 刷新当前 UI 显示的 mods
        if self.active_server_id:
            self.server_cfg = self.config_manager.load_server_config(self.active_server_id)
            server_tab = self.tabs.get("server")
            mods_editor = getattr(server_tab, "txt_mods", None) if server_tab else None
            if mods_editor is not None:
                try:
                    mods_editor.delete("1.0", "end")
                    mods_editor.insert("1.0", str(self.server_cfg.get("mods") or ""))
                except Exception:
                    pass

        messagebox.showinfo(
            "LACC 配置完成",
            f"已为 {configured_count} 个服务器配置 LACC mod (ID: {LACC_MOD_ID})。\n"
            f"WebSocket URL: {ws_url}\n\n"
            f"配置已写入各服务器的 GameUserSettings.ini (staging)。\n"
            f"下次启动服务器时将生效。"
        )

    def _inject_lacc_ini(
        self,
        server_id: str,
        server_dir: Path,
        ws_url: str,
        token: str,
        map_name: str,
    ) -> None:
        """将 LACC 配置写入服务器的 GameUserSettings.ini (staging 目录)"""
        staging_dir = self.storage.get_staging_dir(server_id)
        ini_path = staging_dir / "GameUserSettings.ini"

        lacc_section = (
            f"\n[LACC]\n"
            f'URL="{ws_url}"\n'
            f"Token={token}\n"
            f'Name="{map_name}"\n'
            f"GlobalChatMode=2\n"
        )

        try:
            if ini_path.exists():
                content = ini_path.read_text(encoding="utf-8-sig")
            else:
                content = ""

            if "[LACC]" in content:
                import re
                content = re.sub(
                    r"\[LACC\][^\[]*",
                    lacc_section.lstrip("\n") + "\n",
                    content,
                    count=1,
                )
            else:
                content = content.rstrip() + "\n" + lacc_section

            ini_path.parent.mkdir(parents=True, exist_ok=True)
            ini_path.write_text(content, encoding="utf-8")
            self.logger.info(
                "[%s] LACC INI 配置已写入: %s", server_id[:8], ini_path
            )
        except Exception as e:
            self.logger.error(
                "[%s] 写入 LACC INI 配置失败: %s", server_id[:8], e
            )

    def close(self) -> None:
        """Close the application."""
        try:
            self._autosave_now()
        except Exception:
            pass
        if self._chat_server and self._chat_server.is_running:
            try:
                self._chat_server.stop()
            except Exception:
                pass
        self.logger.info("Closing application")
        self.root.destroy()
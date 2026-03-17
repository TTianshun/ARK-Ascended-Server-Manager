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

from ..core import ConfigManager, StorageManager, ProcessManager
from ..models import ServerConfig
from ..utils import get_logger
from ..utils.constants import (
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
)


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
        self._busy = False
        self._async_thread: Optional[threading.Thread] = None
    
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
        
        # Add tabs to notebook
        self.notebook.add(tab_server_frame, text="服务器")
        self.notebook.add(tab_adv_frame, text="高级设置")
        self.notebook.add(tab_rcon_frame, text="RCON")
        self.notebook.add(tab_discord_frame, text="Discord")
        self.notebook.add(tab_ini_frame, text="INI编辑器")
        
        # Initialize tab components
        self.tabs["server"] = ServerTab(tab_server_frame, self)
        self.tabs["advanced"] = AdvancedTab(tab_adv_frame, self)
        self.tabs["rcon"] = RconTab(tab_rcon_frame, self)
        self.tabs["discord"] = DiscordTab(tab_discord_frame, self)
        self.tabs["ini"] = IniEditorTab(tab_ini_frame, self)
        
        # Build all tabs
        for tab in self.tabs.values():
            tab.build()

        # Apply initial map UI mode
        self._sync_map_mode()
        
        # Console output area at bottom
        self._create_console_area(main_frame)
    
    def _create_console_area(self, parent: ttk.Frame) -> None:
        """Create the console output area at the bottom of the window."""
        console_frame = ttk.LabelFrame(parent, text="控制台输出", padding=5)
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
    
    def _sync_auto_update_scheduler(self) -> None:
        """Update auto-update scheduler."""
        self.logger.debug("Syncing auto-update scheduler")
    
    def _validate_digits(self, value: str) -> bool:
        """Validate that input contains only digits."""
        return value == "" or value.isdigit()

    # ------------------------------------------------------------------
    # 异步执行工具
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        """在 UI 线程中更新忙碌状态，并同步刷新操作按钮。"""
        self._busy = busy
        server_tab = self.tabs.get("server")
        if server_tab is not None:
            try:
                server_tab.refresh_button_states()  # type: ignore[attr-defined]
            except Exception:
                pass

    def _run_async(self, task_fn, *, label: str = "操作") -> None:
        """
        在守护线程中执行 task_fn，期间锁定操作按钮防止重复点击。

        task_fn 签名：() -> None
        执行完成（无论成功或失败）后在 UI 线程中恢复按钮状态。
        """
        if self._busy:
            self.logger.warning("已有操作正在进行，忽略新请求: %s", label)
            return

        def _worker() -> None:
            try:
                task_fn()
            except Exception as e:
                self.logger.error("%s 执行异常: %s", label, e)
            finally:
                # 必须通过 root.after 在 UI 线程中修改 UI 状态
                self.root.after(0, lambda: self._set_busy(False))

        self._set_busy(True)
        self._async_thread = threading.Thread(target=_worker, daemon=True, name=label)
        self._async_thread.start()

    def _log_console(self, message: str) -> None:
        """线程安全地向控制台输出区追加一行文字。"""
        def _append() -> None:
            try:
                self.txt_log.configure(state="normal")
                self.txt_log.insert("end", message + "\n")
                self.txt_log.see("end")
                self.txt_log.configure(state="disabled")
            except Exception:
                pass
        self.root.after(0, _append)

    # ------------------------------------------------------------------
    # 服务器操作（均通过 _run_async 在后台线程中执行）
    # ------------------------------------------------------------------

    def first_install(self) -> None:
        """Install server for the first time."""
        def _task() -> None:
            self.logger.info("Starting first install")
            self._log_console("首次安装：功能待实现")
        self._run_async(_task, label="首次安装")
    
    def start_server(self) -> None:
        """Start the server."""
        def _task() -> None:
            self.logger.info("Starting server")
            self._log_console("启动服务器：功能待实现")
        self._run_async(_task, label="启动服务器")
    
    def stop_server_safe(self) -> None:
        """Stop the server safely."""
        def _task() -> None:
            self.logger.info("Stopping server safely")
            self._log_console("停止服务器：功能待实现")
        self._run_async(_task, label="停止服务器")
    
    def update_validate(self) -> None:
        """Update and validate server files."""
        def _task() -> None:
            self.logger.info("Updating and validating server")
            self._log_console("更新并验证：功能待实现")
        self._run_async(_task, label="更新验证")
    
    def update_and_restart_safe(self) -> None:
        """Update and restart server safely."""
        def _task() -> None:
            self.logger.info("Updating and restarting server")
            self._log_console("更新并重启：功能待实现")
        self._run_async(_task, label="更新重启")
    
    def backup_now(self) -> None:
        """Create a backup now."""
        def _task() -> None:
            self.logger.info("Creating backup")
            self._log_console("立即备份：功能待实现")
        self._run_async(_task, label="立即备份")
    
    def auto_update_test(self) -> None:
        """Test the auto-update scheduler."""
        def _task() -> None:
            self.logger.info("Testing auto-update scheduler")
            self._log_console("测试自动更新：功能待实现")
        self._run_async(_task, label="测试自动更新")
    
    def send_rcon(self) -> None:
        """Send RCON command."""
        cmd = self.var_rcon_cmd.get()
        self.logger.info(f"Sending RCON command: {cmd}")
    
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
        self.logger.info("Loading GameUserSettings.ini")
    
    def load_game_ini(self) -> None:
        """Load Game.ini for editing."""
        self.logger.info("Loading Game.ini")
    
    def open_loaded_ini(self) -> None:
        """Open the currently loaded INI file."""
        self.logger.debug("Opening loaded INI file")
    
    def _ini_resync_from_upstream(self) -> None:
        """Resync INI staging from upstream."""
        self.logger.debug("Resyncing INI from upstream")
    
    def _ini_refresh_tree(self) -> None:
        """Refresh the INI tree view based on filter."""
        self.logger.debug("Refreshing INI tree")
    
    def _ini_tree_select(self) -> None:
        """Handle INI tree selection."""
        self.logger.debug("INI tree item selected")
    
    def _ini_update_value(self) -> None:
        """Update the selected INI value."""
        self.logger.debug("Updating INI value")
    
    def _ini_delete_entry(self) -> None:
        """Delete the selected INI entry."""
        self.logger.debug("Deleting INI entry")
    
    def _ini_add_entry(self) -> None:
        """Add a new INI entry."""
        self.logger.debug("Adding INI entry")
    
    def _ini_save_changes(self) -> None:
        """Save all INI changes."""
        self.logger.info("Saving INI changes")
    
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
    
    def close(self) -> None:
        """Close the application."""
        try:
            self._autosave_now()
        except Exception:
            pass
        self.logger.info("Closing application")
        self.root.destroy()
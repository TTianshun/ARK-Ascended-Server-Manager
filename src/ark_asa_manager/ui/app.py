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

from ..core import ConfigManager, StorageManager, ProcessManager
from ..models import ServerConfig
from ..utils import get_logger
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
        self.root.title("ARK: Survival Ascended Server Manager")
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
        self._busy = False
    
    def _init_variables(self) -> None:
        """Initialize all tkinter variables."""
        # Server profile management
        self.var_server_profile = tk.StringVar(master=self.root)
        self.var_steamcmd_dir = tk.StringVar(master=self.root)
        self.var_server_dir = tk.StringVar(master=self.root)
        
        # Server settings (basic)
        self.var_map_preset = tk.StringVar(master=self.root)
        self.var_map_custom = tk.StringVar(master=self.root)
        self.var_server_name = tk.StringVar(master=self.root)
        self.var_port = tk.StringVar(master=self.root)
        self.var_query_port = tk.StringVar(master=self.root)
        self.var_max_players = tk.StringVar(master=self.root)
        self.var_join_password = tk.StringVar(master=self.root)
        self.var_admin_password = tk.StringVar(master=self.root)
        
        # Server settings (advanced)
        self.var_server_platform_crossplay = tk.BooleanVar(master=self.root)
        self.var_enable_battleye = tk.BooleanVar(master=self.root)
        self.var_automanaged_mods = tk.BooleanVar(master=self.root)
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
        self.var_enable_rcon = tk.BooleanVar(master=self.root)
        self.var_rcon_host = tk.StringVar(master=self.root)
        self.var_rcon_port = tk.StringVar(master=self.root)
        self.var_rcon_cmd = tk.StringVar(master=self.root)
        self.var_rcon_saved = tk.StringVar(master=self.root)
        
        # Discord settings
        self.var_discord_enable = tk.BooleanVar(master=self.root)
        self.var_discord_webhook_url = tk.StringVar(master=self.root)
        self.var_discord_poll_interval_min = tk.StringVar(master=self.root)
        self.var_discord_notify_start = tk.BooleanVar(master=self.root)
        self.var_discord_notify_stop = tk.BooleanVar(master=self.root)
        self.var_discord_notify_join = tk.BooleanVar(master=self.root)
        self.var_discord_notify_leave = tk.BooleanVar(master=self.root)
        self.var_discord_notify_crash = tk.BooleanVar(master=self.root)
        self.var_discord_include_player_id = tk.BooleanVar(master=self.root)
        self.var_discord_mention_mode = tk.StringVar(master=self.root)
        self.var_discord_mention_map_json = tk.StringVar(master=self.root)
        
        # Backup settings
        self.var_backup_on_stop = tk.BooleanVar(master=self.root)
        self.var_backup_dir = tk.StringVar(master=self.root)
        self.var_backup_retention = tk.StringVar(master=self.root)
        
        # Auto-update settings
        self.var_auto_update_restart = tk.BooleanVar(master=self.root)
        self.var_auto_start_on_launch = tk.BooleanVar(master=self.root)
        self.var_auto_update_time = tk.StringVar(master=self.root)
        self.var_update_on_startup = tk.BooleanVar(master=self.root)
        
        # Misc
        self.var_hide_gameanalytics_console_logs = tk.BooleanVar(master=self.root)
        self.var_status = tk.StringVar(master=self.root, value="Ready")
        
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
        self.notebook.add(tab_server_frame, text="Server")
        self.notebook.add(tab_adv_frame, text="Advanced")
        self.notebook.add(tab_rcon_frame, text="RCON")
        self.notebook.add(tab_discord_frame, text="Discord")
        self.notebook.add(tab_ini_frame, text="INI Editor")
        
        # Initialize tab components
        self.tabs["server"] = ServerTab(tab_server_frame, self)
        self.tabs["advanced"] = AdvancedTab(tab_adv_frame, self)
        self.tabs["rcon"] = RconTab(tab_rcon_frame, self)
        self.tabs["discord"] = DiscordTab(tab_discord_frame, self)
        self.tabs["ini"] = IniEditorTab(tab_ini_frame, self)
        
        # Build all tabs
        for tab in self.tabs.values():
            tab.build()
        
        # Console output area at bottom
        self._create_console_area(main_frame)
    
    def _create_console_area(self, parent: ttk.Frame) -> None:
        """Create the console output area at the bottom of the window."""
        console_frame = ttk.LabelFrame(parent, text="Console Output", padding=5)
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
    
    # =========================================================================
    # Event Handlers & Methods (Stubs)
    # =========================================================================
    
    def _on_server_profile_selected(self) -> None:
        """Handle server profile selection change."""
        self.logger.debug("Server profile selected")
    
    def _add_server_profile(self) -> None:
        """Add a new server profile."""
        name = simpledialog.askstring("New Server", "Display name:")
        if name:
            self.logger.info(f"Adding server profile: {name}")
    
    def _rename_server_profile(self) -> None:
        """Rename the current server profile."""
        self.logger.info("Renaming server profile")
    
    def _remove_server_profile(self) -> None:
        """Remove the current server profile."""
        self.logger.info("Removing server profile")
    
    def _browse_steamcmd(self) -> None:
        """Browse for SteamCMD directory."""
        path = filedialog.askdirectory(title="Select SteamCMD Directory")
        if path:
            self.var_steamcmd_dir.set(path)
    
    def _browse_server_dir(self) -> None:
        """Browse for server installation directory."""
        path = filedialog.askdirectory(title="Select Server Install Directory")
        if path:
            self.var_server_dir.set(path)
    
    def _browse_backup_dir(self) -> None:
        """Browse for backup directory."""
        path = filedialog.askdirectory(title="Select Backup Directory")
        if path:
            self.var_backup_dir.set(path)
    
    def _browse_cluster_dir(self) -> None:
        """Browse for cluster directory override."""
        path = filedialog.askdirectory(title="Select Cluster Directory")
        if path:
            self.var_cluster_dir_override.set(path)
    
    def _sync_map_mode(self) -> None:
        """Synchronize map selection mode."""
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
    
    def first_install(self) -> None:
        """Install server for the first time."""
        self.logger.info("Starting first install")
    
    def start_server(self) -> None:
        """Start the server."""
        self.logger.info("Starting server")
    
    def stop_server_safe(self) -> None:
        """Stop the server safely."""
        self.logger.info("Stopping server safely")
    
    def update_validate(self) -> None:
        """Update and validate server files."""
        self.logger.info("Updating and validating server")
    
    def update_and_restart_safe(self) -> None:
        """Update and restart server safely."""
        self.logger.info("Updating and restarting server")
    
    def backup_now(self) -> None:
        """Create a backup now."""
        self.logger.info("Creating backup")
    
    def auto_update_test(self) -> None:
        """Test the auto-update scheduler."""
        self.logger.info("Testing auto-update scheduler")
    
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
        self.logger.info("Closing application")
        self.root.destroy()
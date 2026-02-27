"""
Modern Server Manager App - CustomTkinter version with professional UI

Uses CustomTkinter for modern, beautiful UI components with automatic dark/light theme support.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict, List
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from ..core import ConfigManager, StorageManager, ProcessManager
from ..models import ServerConfig
from ..utils import get_logger
from .modern_theme import get_theme, apply_ctk_theme, get_font, BUTTON_STYLES, ENTRY_STYLES, LABEL_FRAME_STYLES


class ModernServerManagerApp:
    """
    Modern Server Manager Application using CustomTkinter.
    
    Features:
    - Professional dark/light theme with automatic system detection
    - Modern card-based layout
    - Smooth animations and hover effects
    - Responsive grid-based design
    - Keyboard shortcuts integration
    """
    
    def __init__(self, root: ctk.CTk, app_base: Path):
        """
        Initialize the modern application.
        
        Args:
            root: CustomTkinter root window
            app_base: Base directory for application data
        """
        self.root = root
        self.app_base = app_base
        
        # Apply modern appearance
        apply_ctk_theme("system")  # Auto-detects system theme
        
        # Initialize managers
        self.storage = StorageManager(app_base)
        self.config_manager = ConfigManager(app_base)
        self.process_manager = ProcessManager()
        
        self.logger = get_logger(__name__)
        
        # Configure root window
        self.root.title("ARK: Survival Ascended Server Manager")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize state
        self.tabs: Dict[str, ctk.CTkFrame] = {}
        self.active_tab = "server"
        
        # Initialize tkinter variables
        self._init_variables()
        
        # Build UI
        self._create_modern_ui()
        
        self.logger.info("Modern Server Manager UI initialized")
    
    def _init_variables(self) -> None:
        """Initialize all tkinter variables."""
        # Profile management
        self.var_server_profile = tk.StringVar(master=self.root)
        self.var_status = tk.StringVar(master=self.root, value="Ready")
        
        # Server settings
        self.var_server_name = tk.StringVar(master=self.root)
        self.var_server_dir = tk.StringVar(master=self.root)
        self.var_steamcmd_dir = tk.StringVar(master=self.root)
        self.var_map_preset = tk.StringVar(master=self.root)
        self.var_port = tk.StringVar(master=self.root)
        self.var_max_players = tk.StringVar(master=self.root)
        
        # Advanced settings
        self.var_cluster_enable = tk.BooleanVar(master=self.root)
        self.var_enable_rcon = tk.BooleanVar(master=self.root)
        self.var_enable_battleye = tk.BooleanVar(master=self.root)
        
        # Discord
        self.var_discord_enable = tk.BooleanVar(master=self.root)
        self.var_discord_webhook_url = tk.StringVar(master=self.root)
        
        # Backup
        self.var_backup_on_stop = tk.BooleanVar(master=self.root)
        self.var_backup_dir = tk.StringVar(master=self.root)
        
        # Auto-update
        self.var_auto_update_restart = tk.BooleanVar(master=self.root)
    
    def _create_modern_ui(self) -> None:
        """Create modern UI with CustomTkinter components."""
        # Main container with padding
        main_container = ctk.CTkFrame(self.root, corner_radius=0)
        main_container.pack(fill="both", expand=True)
        
        # Header bar
        self._create_header(main_container)
        
        # Content area with tabs and panels
        content_frame = ctk.CTkFrame(main_container, corner_radius=0)
        content_frame.pack(fill="both", expand=True, padx=0, pady=0)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Sidebar with tabs
        self._create_sidebar(content_frame)
        
        # Main content area
        main_content = ctk.CTkFrame(content_frame, corner_radius=0)
        main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(1, weight=1)
        
        # Tab content
        self._create_tab_views(main_content)
        
        # Status bar
        self._create_statusbar(main_container)
    
    def _create_header(self, parent: ctk.CTkFrame) -> None:
        """Create modern header bar with title and controls."""
        header = ctk.CTkFrame(parent)
        header.pack(fill="x", padx=20, pady=15)
        header.columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="🎮 ARK: Survival Ascended Server Manager",
            font=get_font(size=24, weight="bold"),
            text_color="white"
        )
        title.pack(side="left", anchor="w")
        
        # Quick action buttons
        btn_frame = ctk.CTkFrame(header)
        btn_frame.pack(side="right", anchor="e")
        
        ctk.CTkButton(
            btn_frame,
            text="▶ Start",
            width=90,
            fg_color="#10B981",
            hover_color="#059669",
            font=get_font(size=11, weight="bold"),
            command=self._start_server
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="⏹ Stop",
            width=90,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=get_font(size=11, weight="bold"),
            command=self._stop_server
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Update",
            width=90,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=get_font(size=11, weight="bold"),
            command=self._update_server
        ).pack(side="left", padx=5)
    
    def _create_sidebar(self, parent: ctk.CTkFrame) -> None:
        """Create sidebar with navigation tabs."""
        sidebar = ctk.CTkFrame(parent, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        sidebar.grid_propagate(False)
        
        # Sidebar title
        ctk.CTkLabel(
            sidebar,
            text="Navigation",
            font=get_font(size=13, weight="bold"),
            text_color="white"
        ).pack(pady=(0, 20), anchor="w")
        
        # Navigation items
        nav_items = [
            ("📊 Server", "server"),
            ("⚙️ Advanced", "advanced"),
            ("📡 RCON", "rcon"),
            ("💬 Discord", "discord"),
            ("📝 INI Editor", "ini"),
            ("ℹ️ About", "about"),
        ]
        
        for label, tab_id in nav_items:
            self._create_nav_button(sidebar, label, tab_id)
    
    def _create_nav_button(self, parent: ctk.CTkFrame, label: str, tab_id: str) -> None:
        """Create a navigation button."""
        btn = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            text_color="white",
            fg_color=("#3B82F6", "#2563EB") if tab_id == "server" else ("gray", "gray20"),
            hover_color=("#2563EB", "#1D4ED8") if tab_id == "server" else ("gray20", "gray30"),
            font=get_font(size=11),
            corner_radius=8,
            command=lambda: self._switch_tab(tab_id)
        )
        btn.pack(fill="x", pady=8)
    
    def _create_tab_views(self, parent: ctk.CTkFrame) -> None:
        """Create tab content areas."""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Server Configuration",
            font=get_font(size=18, weight="bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Tab content
        content = ctk.CTkScrollableFrame(parent, corner_radius=12)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        
        # Create tab cards
        self._create_server_card(content)
        self._create_execution_card(content)
        self._create_backup_card(content)
        self._create_advanced_card(content)
    
    def _create_server_card(self, parent: ctk.CTkScrollableFrame) -> None:
        """Create server configuration card."""
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("white", "#27272A"), border_width=1, border_color=("lightgray", "#3F3F46"))
        card.pack(fill="x", pady=10, padx=0)
        card.columnconfigure(1, weight=1)
        
        # Card title
        title = ctk.CTkLabel(card, text="Server Profile", font=get_font(size=13, weight="bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))
        
        # Server name
        ctk.CTkLabel(card, text="Server Name:", font=get_font(size=10)).grid(row=1, column=0, sticky="w", padx=20)
        entry = ctk.CTkEntry(card, placeholder_text="Enter server name", height=36, corner_radius=8)
        entry.grid(row=1, column=1, sticky="ew", padx=(10, 20), pady=5)
        
        # Server directory
        ctk.CTkLabel(card, text="Install Directory:", font=get_font(size=10)).grid(row=2, column=0, sticky="w", padx=20)
        entry_dir = ctk.CTkEntry(card, placeholder_text="Path to server installation", height=36, corner_radius=8)
        entry_dir.grid(row=2, column=1, sticky="ew", padx=(10, 10), pady=5)
        ctk.CTkButton(card, text="Browse", width=70, height=36).grid(row=2, column=2, padx=(0, 20), pady=5)
        
        # Port configuration
        ctk.CTkLabel(card, text="Game Port:", font=get_font(size=10)).grid(row=3, column=0, sticky="w", padx=20)
        entry_port = ctk.CTkEntry(card, placeholder_text="7777", height=36, corner_radius=8, width=80)
        entry_port.grid(row=3, column=1, sticky="w", padx=(10, 20), pady=5)
        
        # Padding bottom
        ctk.CTkLabel(card, text="").grid(row=4, column=0, pady=10)
    
    def _create_execution_card(self, parent: ctk.CTkScrollableFrame) -> None:
        """Create server execution card with action buttons."""
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("white", "#27272A"), border_width=1, border_color=("lightgray", "#3F3F46"))
        card.pack(fill="x", pady=10, padx=0)
        card.columnconfigure(5, weight=1)
        
        # Card title
        title = ctk.CTkLabel(card, text="Server Control", font=get_font(size=13, weight="bold"))
        title.grid(row=0, column=0, columnspan=6, sticky="w", padx=20, pady=(15, 10))
        
        # Action buttons with better styling
        btn_start = ctk.CTkButton(
            card,
            text="▶ Start Server",
            font=get_font(size=11, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=40,
            corner_radius=8,
            command=self._start_server
        )
        btn_start.grid(row=1, column=0, padx=(20, 5), pady=15, sticky="ew")
        
        btn_stop = ctk.CTkButton(
            card,
            text="⏹ Stop Server",
            font=get_font(size=11, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            height=40,
            corner_radius=8,
            command=self._stop_server
        )
        btn_stop.grid(row=1, column=1, padx=5, pady=15, sticky="ew")
        
        btn_update = ctk.CTkButton(
            card,
            text="🔄 Update",
            font=get_font(size=11, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=40,
            corner_radius=8,
            command=self._update_server
        )
        btn_update.grid(row=1, column=2, padx=5, pady=15, sticky="ew")
        
        btn_install = ctk.CTkButton(
            card,
            text="📥 First Install",
            font=get_font(size=11, weight="bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            height=40,
            corner_radius=8,
            command=self._first_install
        )
        btn_install.grid(row=1, column=3, padx=5, pady=15, sticky="ew")
        
        # Spacer
        ctk.CTkLabel(card, text="").grid(row=1, column=4, padx=5)
        
        # Status indicator
        status_frame = ctk.CTkFrame(card, corner_radius=8, fg_color=("lightgray", "#3F3F46"))
        status_frame.grid(row=1, column=5, padx=(5, 20), pady=15, sticky="ew")
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="● Server: Stopped",
            text_color=("#EF4444", "#EF4444"),
            font=get_font(size=10, weight="bold")
        )
        status_label.pack(pady=10, padx=15)
    
    def _create_backup_card(self, parent: ctk.CTkScrollableFrame) -> None:
        """Create backup configuration card."""
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("white", "#27272A"), border_width=1, border_color=("lightgray", "#3F3F46"))
        card.pack(fill="x", pady=10, padx=0)
        
        # Card title
        title = ctk.CTkLabel(card, text="Backup Settings", font=get_font(size=13, weight="bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))
        
        # Backup on stop checkbox
        checkbox = ctk.CTkCheckBox(
            card,
            text="Backup on server stop",
            font=get_font(size=10),
            onvalue=True,
            offvalue=False,
            corner_radius=6
        )
        checkbox.grid(row=1, column=0, columnspan=3, sticky="w", padx=20, pady=5)
        
        # Backup directory
        ctk.CTkLabel(card, text="Backup Directory:", font=get_font(size=10)).grid(row=2, column=0, sticky="w", padx=20)
        entry_backup = ctk.CTkEntry(card, placeholder_text="Path to backup folder", height=36, corner_radius=8)
        entry_backup.grid(row=2, column=1, sticky="ew", padx=(10, 10), pady=5)
        ctk.CTkButton(card, text="Browse", width=70, height=36).grid(row=2, column=2, padx=(0, 20), pady=5)
        
        # Padding bottom
        ctk.CTkLabel(card, text="").grid(row=3, column=0, pady=10)
    
    def _create_advanced_card(self, parent: ctk.CTkScrollableFrame) -> None:
        """Create advanced settings card."""
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("white", "#27272A"), border_width=1, border_color=("lightgray", "#3F3F46"))
        card.pack(fill="x", pady=10, padx=0)
        card.columnconfigure(1, weight=1)
        
        # Card title
        title = ctk.CTkLabel(card, text="Advanced Settings", font=get_font(size=13, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        
        # Settings items
        settings = [
            ("Enable RCON", "RCON allows remote console commands"),
            ("Enable BattlEye", "Anti-cheat system for the server"),
            ("Enable Clustering", "Join multiple servers in a cluster"),
            ("Discord Notifications", "Receive server events in Discord"),
        ]
        
        for i, (setting, description) in enumerate(settings):
            # Checkbox with description
            container = ctk.CTkFrame(card, fg_color="transparent")
            container.grid(row=i+1, column=0, columnspan=2, sticky="ew", padx=20, pady=8)
            container.columnconfigure(1, weight=1)
            
            checkbox = ctk.CTkCheckBox(card, text=setting, font=get_font(size=10), corner_radius=6)
            checkbox.grid(row=i+1, column=0, sticky="w", padx=20)
            
            desc = ctk.CTkLabel(card, text=description, font=get_font(size=9), text_color="gray")
            desc.grid(row=i+1, column=1, sticky="ew", padx=20)
        
        # Padding bottom
        ctk.CTkLabel(card, text="").grid(row=len(settings)+1, column=0, pady=10)
    
    def _create_statusbar(self, parent: ctk.CTkFrame) -> None:
        """Create status bar at bottom."""
        statusbar = ctk.CTkFrame(parent, corner_radius=0)
        statusbar.pack(fill="x", padx=0, pady=0)
        statusbar.columnconfigure(0, weight=1)
        
        status_label = ctk.CTkLabel(
            statusbar,
            text="✓ Ready",
            font=get_font(size=9),
            text_color="green"
        )
        status_label.pack(side="left", padx=20, pady=10)
    
    def _switch_tab(self, tab_id: str) -> None:
        """Switch to a different tab."""
        self.active_tab = tab_id
        self.logger.info(f"Switched to {tab_id} tab")
    
    def _start_server(self) -> None:
        """Start the server."""
        self.logger.info("Starting server...")
    
    def _stop_server(self) -> None:
        """Stop the server."""
        self.logger.info("Stopping server...")
    
    def _update_server(self) -> None:
        """Update the server."""
        self.logger.info("Updating server...")
    
    def _first_install(self) -> None:
        """First time installation."""
        self.logger.info("Starting first install...")
    
    def close(self) -> None:
        """Close the application."""
        self.logger.info("Closing application")
        self.root.destroy()


def launch_modern() -> None:
    """Launch modern CustomTkinter application."""
    from ..utils import setup_logger, get_logger
    from ..utils.constants import APP_NAME, APPDATA_DIR_NAME, LOG_DIR_NAME, LOG_FILE_NAME
    import os
    
    # Setup paths
    if os.name == 'nt':
        appdata = Path(os.environ.get('APPDATA', Path.home()))
        app_base = appdata / APPDATA_DIR_NAME
    else:
        app_base = Path.home() / '.config' / APPDATA_DIR_NAME.lower()
    
    # Setup logging
    log_dir = app_base / LOG_DIR_NAME
    setup_logger(log_dir, LOG_FILE_NAME)
    logger = get_logger(__name__)
    logger.info(f"{APP_NAME} Modern UI started")
    
    # Create and launch app
    root = ctk.CTk()
    root.protocol("WM_DELETE_WINDOW", lambda: (ModernServerManagerApp.close(app) if isinstance(app, ModernServerManagerApp) else None) or root.destroy())
    app = ModernServerManagerApp(root, app_base)
    root.mainloop()


if __name__ == "__main__":
    launch_modern()

"""
Advanced tab - Advanced server configuration and mechanics.
"""

import tkinter as tk
from tkinter import ttk, filedialog

from .base import BaseTab


class AdvancedTab(BaseTab):
    """Advanced configuration tab for server mechanics and start args."""
    
    def build(self) -> None:
        """Build the Advanced tab UI."""
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        
        # Cluster configuration
        self._build_cluster_section()
        
        # Platform and mechanics (right side)
        self._build_platform_section()
        self._build_dinos_section()
        self._build_mechanics_section()
        
        # Logs and runtime options
        self._build_logs_section()
        self._build_runtime_section()
        
        # Tools/folders
        self._build_tools_section()
    
    def _build_cluster_section(self) -> None:
        """Build cluster configuration section."""
        lf = ttk.LabelFrame(self.frame, text="Cluster Configuration", padding=10)
        lf.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf,
            text="Enable Cluster",
            variable=self.app.var_cluster_enable
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Label(lf, text="Cluster ID").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(lf, textvariable=self.app.var_cluster_id).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Checkbutton(
            lf,
            text="NoTransferFromFiltering",
            variable=self.app.var_no_transfer_from_filtering
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        
        ttk.Checkbutton(
            lf,
            text="Enable Cluster Custom Path",
            variable=self.app.var_cluster_custom_path_enable
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))
        
        ttk.Label(lf, text="ClusterDirOverride Path").grid(
            row=4, column=0, sticky="w", pady=(6, 0)
        )
        path_row = ttk.Frame(lf)
        path_row.grid(row=4, column=1, sticky="ew", padx=6, pady=(6, 0))
        path_row.columnconfigure(0, weight=1)
        
        ttk.Entry(path_row, textvariable=self.app.var_cluster_dir_override).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(
            path_row,
            text="Browse",
            command=self.app._browse_cluster_dir
        ).grid(row=0, column=1, padx=(6, 0))
        
        ttk.Label(
            lf,
            text="AltSaveDirectoryName (optional)"
        ).grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(
            lf,
            textvariable=self.app.var_alt_save_directory_name
        ).grid(row=5, column=1, sticky="ew", padx=6, pady=(8, 0))
    
    def _build_platform_section(self) -> None:
        """Build platform/crossplay section."""
        lf = ttk.LabelFrame(self.frame, text="Platform / Crossplay", padding=10)
        lf.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Checkbutton(
            lf,
            text="ServerPlatform: PC+XSX+WINGDK",
            variable=self.app.var_server_platform_crossplay
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="Enable BattlEye",
            variable=self.app.var_enable_battleye
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
    
    def _build_dinos_section(self) -> None:
        """Build dinosaur settings section."""
        lf = ttk.LabelFrame(
            self.frame,
            text="Dinosaur Settings (mutual exclusive)",
            padding=10
        )
        lf.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        dino_opts = [
            ("Default", ""),
            ("No Dinos", "NoDinos"),
            ("No Dinos Except Forced Spawn", "NoDinosExceptForcedSpawn"),
            ("No Dinos Except Streaming Spawn", "NoDinosExceptStreamingSpawn"),
            ("No Dinos Except Manual Spawn", "NoDinosExceptManualSpawn"),
            ("No Dinos Except Water Spawn", "NoDinosExceptWaterSpawn"),
        ]
        
        for i, (label, value) in enumerate(dino_opts):
            ttk.Radiobutton(
                lf,
                text=label,
                variable=self.app.var_dino_mode,
                value=value
            ).grid(row=i, column=0, sticky="w")
    
    def _build_logs_section(self) -> None:
        """Build logs section."""
        lf = ttk.LabelFrame(self.frame, text="Logs", padding=10)
        lf.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        ttk.Checkbutton(
            lf,
            text="servergamelog",
            variable=self.app.var_log_servergamelog
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="servergamelogincludetribelogs",
            variable=self.app.var_log_servergamelogincludetribelogs
        ).grid(row=1, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="ServerRCONOutputTribeLogs",
            variable=self.app.var_log_serverrconoutputtribelogs
        ).grid(row=2, column=0, sticky="w")
    
    def _build_mechanics_section(self) -> None:
        """Build server mechanics section."""
        lf = ttk.LabelFrame(self.frame, text="Mechanics / Performance", padding=10)
        lf.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        mech_items = [
            ("DisableCustomCosmetics", self.app.var_m_disablecustomcosmetics),
            ("AutoDestroyStructures", self.app.var_m_autodestroystructures),
            ("ForceRespawnDinos", self.app.var_m_forcerespawndinos),
            ("NoWildBabies", self.app.var_m_nowildbabies),
            ("ForceAllowCaveFlyers", self.app.var_m_forceallowcaveflyers),
            ("disabledinonetrangescaling", self.app.var_m_disabledinonetrangescaling),
            ("UnstasisDinoObstructionCheck", self.app.var_m_unstasisdinoobstructioncheck),
            ("AlwaysTickDedicatedSkeletalMeshes", self.app.var_m_alwaystickdedicatedskeletalmeshes),
            ("disableCharacterTracker", self.app.var_m_disablecharactertracker),
            ("UseServerNetSpeedCheck", self.app.var_m_useservernetspeedcheck),
            ("StasisKeepControllers", self.app.var_m_stasiskeepcontrollers),
            ("ignoredupeditems", self.app.var_m_ignoredupeditems),
        ]
        
        for i, (label, var) in enumerate(mech_items):
            ttk.Checkbutton(
                lf,
                text=label,
                variable=var
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 14), pady=2)
    
    def _build_runtime_section(self) -> None:
        """Build runtime and RCON section."""
        lf = ttk.LabelFrame(self.frame, text="Mods & RCON", padding=10)
        lf.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf,
            text="Automanaged Mods",
            variable=self.app.var_automanaged_mods
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="Enable RCON",
            variable=self.app.var_enable_rcon
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        
        ttk.Label(lf, text="RCON Host").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(lf, textvariable=self.app.var_rcon_host).grid(
            row=2, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Label(lf, text="RCON Port").grid(row=3, column=0, sticky="w", pady=(6, 0))
        vcmd = (self.app.root.register(self.app._validate_digits), "%P")
        ttk.Entry(
            lf,
            textvariable=self.app.var_rcon_port,
            validate="key",
            validatecommand=vcmd
        ).grid(row=3, column=1, sticky="ew", padx=6, pady=(6, 0))
    
    def _build_tools_section(self) -> None:
        """Build tools/folder access section."""
        lf = ttk.LabelFrame(self.frame, text="Folders", padding=10)
        lf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        lf.columnconfigure(0, weight=1)
        
        self.btn_open_app = ttk.Button(
            lf,
            text="Open App Folder",
            command=lambda: self.app.open_folder(self.app.app_base)
        )
        self.btn_open_app.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        self.btn_open_server_cfg = ttk.Button(
            lf,
            text="Open Server Config",
            command=self.app.open_server_config_dir
        )
        self.btn_open_server_cfg.grid(row=1, column=0, sticky="ew")
    
    def on_selected(self) -> None:
        """Called when tab is selected."""
        pass
    
    def on_deselected(self) -> None:
        """Called when tab is deselected."""
        pass
    
    def collect_from_ui(self) -> dict:
        """Collect advanced settings from UI."""
        return {
            "cluster_enable": self.app.var_cluster_enable.get(),
            "cluster_id": self.app.var_cluster_id.get(),
            "cluster_custom_path_enable": self.app.var_cluster_custom_path_enable.get(),
            "cluster_dir_override": self.app.var_cluster_dir_override.get(),
            "no_transfer_from_filtering": self.app.var_no_transfer_from_filtering.get(),
            "alt_save_directory_name": self.app.var_alt_save_directory_name.get(),
            "server_platform_crossplay": self.app.var_server_platform_crossplay.get(),
            "enable_battleye": self.app.var_enable_battleye.get(),
            "dino_mode": self.app.var_dino_mode.get(),
            "log_servergamelog": self.app.var_log_servergamelog.get(),
            "log_servergamelogincludetribelogs": self.app.var_log_servergamelogincludetribelogs.get(),
            "log_serverrconoutputtribelogs": self.app.var_log_serverrconoutputtribelogs.get(),
            "automanaged_mods": self.app.var_automanaged_mods.get(),
            "enable_rcon": self.app.var_enable_rcon.get(),
            "rcon_host": self.app.var_rcon_host.get(),
            "rcon_port": self.app.var_rcon_port.get(),
        }
    
    def apply_to_ui(self, data: dict) -> None:
        """Apply advanced settings to UI."""
        pass

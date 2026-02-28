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
        lf = ttk.LabelFrame(self.frame, text="集群配置", padding=10)
        lf.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf,
            text="启用集群",
            variable=self.app.var_cluster_enable
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Label(lf, text="集群ID").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(lf, textvariable=self.app.var_cluster_id).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Checkbutton(
            lf,
            text="禁用介麾转移筛选",
            variable=self.app.var_no_transfer_from_filtering
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        
        ttk.Checkbutton(
            lf,
            text="启用集群自定义路径",
            variable=self.app.var_cluster_custom_path_enable
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))
        
        ttk.Label(lf, text="集群路径覆盖").grid(
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
            text="浏覧",
            command=self.app._browse_cluster_dir
        ).grid(row=0, column=1, padx=(6, 0))
        
        ttk.Label(
            lf,
            text="替代保存程序名称（可选）"
        ).grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(
            lf,
            textvariable=self.app.var_alt_save_directory_name
        ).grid(row=5, column=1, sticky="ew", padx=6, pady=(8, 0))
    
    def _build_platform_section(self) -> None:
        """Build platform/crossplay section."""
        lf = ttk.LabelFrame(self.frame, text="平台 / 跨平台游戏", padding=10)
        lf.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Checkbutton(
            lf,
            text="服务器平台: PC+XSX+WINGDK",
            variable=self.app.var_server_platform_crossplay
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="启用BattlEye",
            variable=self.app.var_enable_battleye
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
    
    def _build_dinos_section(self) -> None:
        """Build dinosaur settings section."""
        lf = ttk.LabelFrame(
            self.frame,
            text="恐龙设置（互斥）",
            padding=10
        )
        lf.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        dino_opts = [
            ("默认", ""),
            ("不恐龙", "NoDinos"),
            ("除横出恐龙外不恐龙", "NoDinosExceptForcedSpawn"),
            ("除流渐恐龙外不恐龙", "NoDinosExceptStreamingSpawn"),
            ("除手威需恐龙外不恐龙", "NoDinosExceptManualSpawn"),
            ("除水攋恐龙外不恐龙", "NoDinosExceptWaterSpawn"),
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
        lf = ttk.LabelFrame(self.frame, text="日志", padding=10)
        lf.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        ttk.Checkbutton(
            lf,
            text="服务器游戏日志",
            variable=self.app.var_log_servergamelog
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="服务器游戏日志包含部落日志",
            variable=self.app.var_log_servergamelogincludetribelogs
        ).grid(row=1, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="服务器RCON输出部落日志",
            variable=self.app.var_log_serverrconoutputtribelogs
        ).grid(row=2, column=0, sticky="w")
    
    def _build_mechanics_section(self) -> None:
        """Build server mechanics section."""
        lf = ttk.LabelFrame(self.frame, text="力学 / 性能", padding=10)
        lf.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        mech_items = [
            ("禁用自定义旺旧事物", self.app.var_m_disablecustomcosmetics),
            ("自动销毁建筑", self.app.var_m_autodestroystructures),
            ("强制重换恐龙", self.app.var_m_forcerespawndinos),
            ("止止野生亯化", self.app.var_m_nowildbabies),
            ("强制允许洞窟飞行恐龙", self.app.var_m_forceallowcaveflyers),
            ("突准掩蔽恐龙网络范围缩放", self.app.var_m_disabledinonetrangescaling),
            ("离云状态恐龙阻挡检测", self.app.var_m_unstasisdinoobstructioncheck),
            ("总是按次渐进事药跟阺骨网格", self.app.var_m_alwaystickdedicatedskeletalmeshes),
            ("禁用角色追踪器", self.app.var_m_disablecharactertracker),
            ("使用服务器网络速度检查", self.app.var_m_useservernetspeedcheck),
            ("云状态保持控制器", self.app.var_m_stasiskeepcontrollers),
            ("忽略重复网格", self.app.var_m_ignoredupeditems),
        ]
        
        for i, (label, var) in enumerate(mech_items):
            ttk.Checkbutton(
                lf,
                text=label,
                variable=var
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 14), pady=2)
    
    def _build_runtime_section(self) -> None:
        """Build runtime and RCON section."""
        lf = ttk.LabelFrame(self.frame, text="MOD 和 RCON", padding=10)
        lf.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf,
            text="自动管理MOD",
            variable=self.app.var_automanaged_mods
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            lf,
            text="启用RCON",
            variable=self.app.var_enable_rcon
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        
        ttk.Label(lf, text="RCON主樋").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(lf, textvariable=self.app.var_rcon_host).grid(
            row=2, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Label(lf, text="RCON端口").grid(row=3, column=0, sticky="w", pady=(6, 0))
        vcmd = (self.app.root.register(self.app._validate_digits), "%P")
        ttk.Entry(
            lf,
            textvariable=self.app.var_rcon_port,
            validate="key",
            validatecommand=vcmd
        ).grid(row=3, column=1, sticky="ew", padx=6, pady=(6, 0))
    
    def _build_tools_section(self) -> None:
        """Build tools/folder access section."""
        lf = ttk.LabelFrame(self.frame, text="文件夹", padding=10)
        lf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        lf.columnconfigure(0, weight=1)
        
        self.btn_open_app = ttk.Button(
            lf,
            text="打开应用文件夹",
            command=lambda: self.app.open_folder(self.app.app_base)
        )
        self.btn_open_app.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        self.btn_open_server_cfg = ttk.Button(
            lf,
            text="打开服务器配置",
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

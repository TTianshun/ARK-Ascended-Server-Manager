"""
Server tab - Server configuration and control panel.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional
import os

from .base import BaseTab
from ...utils.constants import MAP_PRESETS, MAP_CUSTOM_SENTINEL


class ServerTab(BaseTab):
    """Server configuration and management tab."""
    
    def build(self) -> None:
        """Build the Server tab UI."""
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        
        # --- Server Profiles Section ---
        self._build_profiles_section()
        
        # --- Paths Section ---
        self._build_paths_section()
        
        # --- Server Settings and Operations (side-by-side) ---
        self._build_settings_and_ops_sections()
        
        # --- Update, Backup, and Auto-start Options ---
        self._build_options_frame()
    
    def _build_profiles_section(self) -> None:
        """Build the server profiles selector and management buttons."""
        lf = ttk.LabelFrame(self.frame, text="服务器配置文件", padding=10)
        lf.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Label(lf, text="活沁服务器").grid(row=0, column=0, sticky="w")
        
        self.cmb_server_profile = ttk.Combobox(
            lf,
            textvariable=self.app.var_server_profile,
            state="readonly",
            values=[],
        )
        self.cmb_server_profile.grid(row=0, column=1, sticky="ew", padx=6)
        self.cmb_server_profile.bind(
            "<<ComboboxSelected>>",
            lambda e: self.app._on_server_profile_selected()
        )
        
        # Profile action buttons
        profile_actions = ttk.Frame(lf)
        profile_actions.grid(row=0, column=2, sticky="e")
        
        ttk.Button(
            profile_actions,
            text="添加",
            command=self.app._add_server_profile
        ).grid(row=0, column=0, padx=(0, 6))
        
        ttk.Button(
            profile_actions,
            text="重新命名",
            command=self.app._rename_server_profile
        ).grid(row=0, column=1, padx=(0, 6))
        
        ttk.Button(
            profile_actions,
            text="删除",
            command=self.app._remove_server_profile
        ).grid(row=0, column=2)
    
    def _build_paths_section(self) -> None:
        """Build the paths configuration section (SteamCMD and Server directories)."""
        lf = ttk.LabelFrame(self.frame, text="路径", padding=10)
        lf.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        lf.columnconfigure(4, weight=1)
        
        ttk.Label(lf, text="SteamCMD目录").grid(row=0, column=0, sticky="w")
        ttk.Entry(lf, textvariable=self.app.var_steamcmd_dir).grid(
            row=0, column=1, sticky="ew", padx=6
        )
        ttk.Button(
            lf,
            text="浏覧",
            command=self.app._browse_steamcmd
        ).grid(row=0, column=2)
        
        ttk.Label(lf, text="服务器安装目录").grid(
            row=0, column=3, sticky="w", padx=(18, 0)
        )
        ttk.Entry(lf, textvariable=self.app.var_server_dir).grid(
            row=0, column=4, sticky="ew", padx=6
        )
        ttk.Button(
            lf,
            text="浏覧",
            command=self.app._browse_server_dir
        ).grid(row=0, column=5)
    
    def _build_settings_and_ops_sections(self) -> None:
        """Build the server settings (left) and operations (right) side-by-side sections."""
        # --- Server Settings (left column) ---
        lf_server = ttk.LabelFrame(self.frame, text="服务器设置", padding=10)
        lf_server.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        lf_server.columnconfigure(1, weight=1)
        lf_server.columnconfigure(2, weight=1)
        
        vcmd = (self.app.root.register(self.app._validate_digits), "%P")
        
        # Map Preset
        ttk.Label(lf_server, text="地图预设").grid(row=0, column=0, sticky="w")
        self.cmb_map = ttk.Combobox(
            lf_server,
            textvariable=self.app.var_map_preset,
            state="readonly",
            values=[*MAP_PRESETS, MAP_CUSTOM_SENTINEL],
        )
        self.cmb_map.grid(row=0, column=1, sticky="ew", padx=6)
        self.cmb_map.bind("<<ComboboxSelected>>", lambda e: self.app._sync_map_mode())
        ttk.Label(
            lf_server,
            text="从预设中选择地图；如果是自定义地图，请填写下一项",
        ).grid(row=0, column=2, sticky="w")
        
        # Custom Map Name
        ttk.Label(lf_server, text="自定义地图名称").grid(row=1, column=0, sticky="w")
        ttk.Entry(lf_server, textvariable=self.app.var_map_custom).grid(
            row=1, column=1, sticky="ew", padx=6
        )
        ttk.Label(
            lf_server,
            text="仅在地图预设选择 Custom... 时填写，例如：TheIsland_WP",
        ).grid(row=1, column=2, sticky="w")
        
        # Server Name
        ttk.Label(lf_server, text="服务器名称").grid(row=2, column=0, sticky="w")
        ttk.Entry(lf_server, textvariable=self.app.var_server_name).grid(
            row=2, column=1, sticky="ew", padx=6
        )
        ttk.Label(
            lf_server,
            text="将作为 SessionName 显示在服务器列表中",
        ).grid(row=2, column=2, sticky="w")
        
        # Port settings
        ttk.Label(lf_server, text="端口").grid(row=3, column=0, sticky="w")
        ttk.Entry(
            lf_server,
            textvariable=self.app.var_port,
            validate="key",
            validatecommand=vcmd
        ).grid(row=3, column=1, sticky="ew", padx=6)
        ttk.Label(lf_server, text="游戏端口（默认 7777，仅数字）").grid(row=3, column=2, sticky="w")
        
        ttk.Label(lf_server, text="查询端口").grid(row=4, column=0, sticky="w")
        ttk.Entry(
            lf_server,
            textvariable=self.app.var_query_port,
            validate="key",
            validatecommand=vcmd
        ).grid(row=4, column=1, sticky="ew", padx=6)
        ttk.Label(lf_server, text="查询端口（默认 27015，仅数字）").grid(row=4, column=2, sticky="w")
        
        ttk.Label(lf_server, text="最大玩家数").grid(row=5, column=0, sticky="w")
        ttk.Entry(
            lf_server,
            textvariable=self.app.var_max_players,
            validate="key",
            validatecommand=vcmd
        ).grid(row=5, column=1, sticky="ew", padx=6)
        ttk.Label(lf_server, text="推荐范围：1-200").grid(row=5, column=2, sticky="w")
        
        # Passwords
        ttk.Label(lf_server, text="横细庆密码").grid(row=6, column=0, sticky="w")
        ttk.Entry(lf_server, textvariable=self.app.var_join_password).grid(
            row=6, column=1, sticky="ew", padx=6
        )
        
        ttk.Label(lf_server, text="管理员密码 (RCON/管理)").grid(row=7, column=0, sticky="w")
        ttk.Entry(lf_server, textvariable=self.app.var_admin_password).grid(
            row=7, column=1, sticky="ew", padx=6
        )
        ttk.Label(lf_server, text="必填：用于管理员命令与 RCON").grid(row=7, column=2, sticky="w")
        
        # Mods
        ttk.Label(lf_server, text="MOD（用逗号分隔）").grid(
            row=8, column=0, sticky="nw", pady=(6, 0)
        )
        mods_frame = ttk.Frame(lf_server)
        mods_frame.grid(row=8, column=1, sticky="ew", padx=6, pady=(6, 0))
        mods_frame.columnconfigure(0, weight=1)
        
        self.txt_mods = tk.Text(
            mods_frame,
            height=4,
            wrap="none",
            background=self.app.theme_colors["surface"],
            foreground=self.app.theme_colors["text"],
            insertbackground=self.app.theme_colors["text"],
            selectbackground=self.app.theme_colors["accent_light"],
            highlightthickness=1,
            highlightbackground=self.app.theme_colors["border"],
            highlightcolor=self.app.theme_colors["accent"],
        )
        self.txt_mods.grid(row=0, column=0, sticky="ew")
        
        xscroll = ttk.Scrollbar(mods_frame, orient="horizontal", command=self.txt_mods.xview)
        xscroll.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.txt_mods.configure(xscrollcommand=xscroll.set)
        ttk.Label(
            mods_frame,
            text="示例：123456,987654（用英文逗号分隔）",
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))
        
        # Custom args
        ttk.Label(lf_server, text="自定义服务器参数（可选）").grid(
            row=9, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Entry(lf_server, textvariable=self.app.var_custom_start_args).grid(
            row=9, column=1, sticky="ew", padx=6, pady=(8, 0)
        )
        ttk.Label(
            lf_server,
            text="示例：-Parameter1 -Parameter2",
        ).grid(row=9, column=2, sticky="w", pady=(8, 0))
        
        # --- Operations (right column) ---
        lf_ops = ttk.LabelFrame(self.frame, text="操作", padding=10)
        lf_ops.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        lf_ops.columnconfigure(0, weight=1)
        lf_ops.columnconfigure(1, weight=1)
        lf_ops.columnconfigure(2, weight=1)
        
        # Control buttons
        actions = ttk.Frame(lf_ops, padding=(0, 0, 0, 10))
        actions.grid(row=0, column=0, columnspan=3, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)
        
        self.btn_first_install = ttk.Button(
            actions,
            text="首次安装",
            command=self.app.first_install
        )
        self.btn_stop = ttk.Button(
            actions,
            text="停止服务器（安全）",
            command=self.app.stop_server_safe
        )
        self.btn_start = ttk.Button(
            actions,
            text="启动服务器",
            command=self.app.start_server
        )
        
        self.btn_first_install.grid(row=0, column=0, padx=5, pady=(0, 6), sticky="ew")
        self.btn_stop.grid(row=0, column=1, padx=5, pady=(0, 6), sticky="ew")
        self.btn_start.grid(row=0, column=2, padx=5, pady=(0, 6), sticky="ew")
        
        self.btn_update_validate = ttk.Button(
            actions,
            text="更新 / 验证",
            command=self.app.update_validate
        )
        self.btn_update_restart = ttk.Button(
            actions,
            text="更新 / 重新启动（安全）",
            command=self.app.update_and_restart_safe
        )
        self.btn_backup_now = ttk.Button(
            actions,
            text="主动备份",
            command=self.app.backup_now
        )
        
        self.btn_update_validate.grid(row=1, column=0, padx=5, sticky="ew")
        self.btn_update_restart.grid(row=1, column=1, padx=5, sticky="ew")
        self.btn_backup_now.grid(row=1, column=2, padx=5, sticky="ew")
    
    def _build_options_frame(self) -> None:
        """Build the update, backup, and auto-start options."""
        options_frame = ttk.Frame(self.frame)
        options_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
        # Update frame (left)
        update_frame = ttk.LabelFrame(options_frame, text="更新选项", padding=8)
        update_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        update_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            update_frame,
            text="更新时验证",
            variable=self.app.var_validate_on_update
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Checkbutton(
            update_frame,
            text="启动时更新",
            variable=self.app.var_update_on_startup
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        
        self.chk_auto_update_restart = ttk.Checkbutton(
            update_frame,
            text="自动更新和重新启动",
            variable=self.app.var_auto_update_restart,
            command=self.app._sync_auto_update_scheduler
        )
        self.chk_auto_update_restart.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        
        ttk.Label(update_frame, text="计划时间 (HH:MM)").grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(update_frame, textvariable=self.app.var_auto_update_time).grid(
            row=3, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        self.btn_auto_update_test = ttk.Button(
            update_frame,
            text="测试",
            command=self.app.auto_update_test
        )
        self.btn_auto_update_test.grid(row=3, column=2, padx=(6, 0), pady=(6, 0))
        
        # Backup and misc (right)
        other_frame = ttk.LabelFrame(options_frame, text="备份和启动", padding=8)
        other_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        other_frame.columnconfigure(1, weight=1)
        
        self.chk_backup_on_stop = ttk.Checkbutton(
            other_frame,
            text="停止时备份",
            variable=self.app.var_backup_on_stop,
            command=self.app._sync_backup_label_texts
        )
        self.chk_backup_on_stop.grid(row=0, column=0, sticky="w")
        
        ttk.Label(other_frame, text="备份目录").grid(row=1, column=0, sticky="w")
        ttk.Entry(other_frame, textvariable=self.app.var_backup_dir).grid(
            row=1, column=1, sticky="ew", padx=6
        )
        ttk.Button(
            other_frame,
            text="浏覧",
            command=self.app._browse_backup_dir
        ).grid(row=1, column=2, padx=(6, 0))
        
        ttk.Label(other_frame, text="保留个数").grid(
            row=2, column=0, sticky="w"
        )
        vcmd = (self.app.root.register(self.app._validate_digits), "%P")
        ttk.Entry(
            other_frame,
            textvariable=self.app.var_backup_retention,
            validate="key",
            validatecommand=vcmd
        ).grid(row=2, column=1, sticky="ew", padx=6)
        
        ttk.Checkbutton(
            other_frame,
            text="应用启动时启动服务器",
            variable=self.app.var_auto_start_on_launch
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        
        ttk.Checkbutton(
            other_frame,
            text="隐藏GameAnalytics庞音",
            variable=self.app.var_hide_gameanalytics_console_logs,
            command=self.app._sync_console_log_filter_state
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
    
    def on_selected(self) -> None:
        """Called when tab is selected."""
        pass
    
    def on_deselected(self) -> None:
        """Called when tab is deselected."""
        pass
    
    def collect_from_ui(self) -> dict:
        """Collect server settings from UI."""
        return {
            "server_profile": self.app.var_server_profile.get(),
            "steamcmd_dir": self.app.var_steamcmd_dir.get(),
            "server_dir": self.app.var_server_dir.get(),
            "map_preset": self.app.var_map_preset.get(),
            "map_custom": self.app.var_map_custom.get(),
            "server_name": self.app.var_server_name.get(),
            "port": self.app.var_port.get(),
            "query_port": self.app.var_query_port.get(),
            "max_players": self.app.var_max_players.get(),
            "join_password": self.app.var_join_password.get(),
            "admin_password": self.app.var_admin_password.get(),
            "mods": self.txt_mods.get("1.0", "end-1c"),
            "custom_start_args": self.app.var_custom_start_args.get(),
            "validate_on_update": self.app.var_validate_on_update.get(),
            "update_on_startup": self.app.var_update_on_startup.get(),
            "auto_update_restart": self.app.var_auto_update_restart.get(),
            "auto_update_time": self.app.var_auto_update_time.get(),
            "backup_on_stop": self.app.var_backup_on_stop.get(),
            "backup_dir": self.app.var_backup_dir.get(),
            "backup_retention": self.app.var_backup_retention.get(),
            "auto_start_on_launch": self.app.var_auto_start_on_launch.get(),
            "hide_gameanalytics": self.app.var_hide_gameanalytics_console_logs.get(),
        }
    
    def apply_to_ui(self, data: dict) -> None:
        """Apply server settings to UI."""
        if "mods" in data:
            self.txt_mods.delete("1.0", "end")
            self.txt_mods.insert("1.0", data["mods"])

"""
Discord tab - Discord webhook notifications configuration.
"""

import tkinter as tk
from tkinter import ttk

from .base import BaseTab


class DiscordTab(BaseTab):
    """Discord webhook notifications configuration tab."""
    
    def build(self) -> None:
        """Build the Discord tab UI."""
        self.frame.columnconfigure(0, weight=1)
        
        # Discord webhooks configuration
        lf_discord = ttk.LabelFrame(self.frame, text="Discord接欺配置", padding=10)
        lf_discord.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        lf_discord.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf_discord,
            text="启用Discord通知",
            variable=self.app.var_discord_enable
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        
        ttk.Label(lf_discord, text="Webhook URL").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_discord, textvariable=self.app.var_discord_webhook_url).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Label(lf_discord, text="测释间隔（分鐘）").grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_discord, textvariable=self.app.var_discord_poll_interval_min).grid(
            row=2, column=1, sticky="w", padx=6, pady=(6, 0)
        )
        
        # Notifications options
        notify_frame = ttk.LabelFrame(self.frame, text="通知", padding=10)
        notify_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        notify_frame.columnconfigure(0, weight=1)
        notify_frame.columnconfigure(1, weight=1)
        notify_frame.columnconfigure(2, weight=1)
        
        ttk.Checkbutton(
            notify_frame,
            text="服务器启动",
            variable=self.app.var_discord_notify_start
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="服务器停止",
            variable=self.app.var_discord_notify_stop
        ).grid(row=0, column=1, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="服务器崩溃/退出",
            variable=self.app.var_discord_notify_crash
        ).grid(row=0, column=2, sticky="w")
        
        ttk.Checkbutton(
            notify_frame,
            text="玩家加入",
            variable=self.app.var_discord_notify_join
        ).grid(row=1, column=0, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="玩家离开",
            variable=self.app.var_discord_notify_leave
        ).grid(row=1, column=1, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="包括玩家ID（高级）",
            variable=self.app.var_discord_include_player_id
        ).grid(row=2, column=0, sticky="w", padx=(0, 14), pady=(6, 0))
        
        # Mentions configuration
        mention_frame = ttk.LabelFrame(self.frame, text="提及人民", padding=10)
        mention_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        mention_frame.columnconfigure(1, weight=1)
        
        ttk.Label(mention_frame, text="提及模式").grid(row=0, column=0, sticky="w")
        self.cmb_discord_mention_mode = ttk.Combobox(
            mention_frame,
            textvariable=self.app.var_discord_mention_mode,
            state="readonly",
            values=["name", "mapping", "none"],
            width=14
        )
        self.cmb_discord_mention_mode.grid(row=0, column=1, sticky="w", padx=6)
        
        ttk.Label(mention_frame, text="提及映射（JSON或文件路径）").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(mention_frame, textvariable=self.app.var_discord_mention_map_json).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        # Action buttons
        discord_btns = ttk.Frame(self.frame)
        discord_btns.grid(row=3, column=0, sticky="w", padx=5, pady=(5, 0))
        
        ttk.Button(
            discord_btns,
            text="发送测试",
            command=self.app._discord_send_test
        ).grid(row=0, column=0, padx=(0, 6))
        
        ttk.Button(
            discord_btns,
            text="打开控制状态文件夹",
            command=self.app._discord_open_state_folder
        ).grid(row=0, column=1)
    
    def on_selected(self) -> None:
        """Called when tab is selected."""
        pass
    
    def on_deselected(self) -> None:
        """Called when tab is deselected."""
        pass
    
    def collect_from_ui(self) -> dict:
        """Collect Discord settings from UI."""
        return {
            "discord_enable": self.app.var_discord_enable.get(),
            "discord_webhook_url": self.app.var_discord_webhook_url.get(),
            "discord_poll_interval_min": self.app.var_discord_poll_interval_min.get(),
            "discord_notify_start": self.app.var_discord_notify_start.get(),
            "discord_notify_stop": self.app.var_discord_notify_stop.get(),
            "discord_notify_join": self.app.var_discord_notify_join.get(),
            "discord_notify_leave": self.app.var_discord_notify_leave.get(),
            "discord_notify_crash": self.app.var_discord_notify_crash.get(),
            "discord_include_player_id": self.app.var_discord_include_player_id.get(),
            "discord_mention_mode": self.app.var_discord_mention_mode.get(),
            "discord_mention_map_json": self.app.var_discord_mention_map_json.get(),
        }
    
    def apply_to_ui(self, data: dict) -> None:
        """Apply Discord settings to UI."""
        pass

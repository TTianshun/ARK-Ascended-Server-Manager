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
        lf_discord = ttk.LabelFrame(self.frame, text="Discord Webhooks", padding=10)
        lf_discord.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        lf_discord.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            lf_discord,
            text="Enable Discord notifications",
            variable=self.app.var_discord_enable
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        
        ttk.Label(lf_discord, text="Webhook URL").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_discord, textvariable=self.app.var_discord_webhook_url).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Label(lf_discord, text="Poll interval (minutes)").grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_discord, textvariable=self.app.var_discord_poll_interval_min).grid(
            row=2, column=1, sticky="w", padx=6, pady=(6, 0)
        )
        
        # Notifications options
        notify_frame = ttk.LabelFrame(self.frame, text="Notifications", padding=10)
        notify_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        notify_frame.columnconfigure(0, weight=1)
        notify_frame.columnconfigure(1, weight=1)
        notify_frame.columnconfigure(2, weight=1)
        
        ttk.Checkbutton(
            notify_frame,
            text="Server start",
            variable=self.app.var_discord_notify_start
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="Server stop",
            variable=self.app.var_discord_notify_stop
        ).grid(row=0, column=1, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="Server crash/exit",
            variable=self.app.var_discord_notify_crash
        ).grid(row=0, column=2, sticky="w")
        
        ttk.Checkbutton(
            notify_frame,
            text="Player join",
            variable=self.app.var_discord_notify_join
        ).grid(row=1, column=0, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="Player leave",
            variable=self.app.var_discord_notify_leave
        ).grid(row=1, column=1, sticky="w", padx=(0, 14))
        
        ttk.Checkbutton(
            notify_frame,
            text="Include player IDs (advanced)",
            variable=self.app.var_discord_include_player_id
        ).grid(row=2, column=0, sticky="w", padx=(0, 14), pady=(6, 0))
        
        # Mentions configuration
        mention_frame = ttk.LabelFrame(self.frame, text="Mentions", padding=10)
        mention_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        mention_frame.columnconfigure(1, weight=1)
        
        ttk.Label(mention_frame, text="Mention mode").grid(row=0, column=0, sticky="w")
        self.cmb_discord_mention_mode = ttk.Combobox(
            mention_frame,
            textvariable=self.app.var_discord_mention_mode,
            state="readonly",
            values=["name", "mapping", "none"],
            width=14
        )
        self.cmb_discord_mention_mode.grid(row=0, column=1, sticky="w", padx=6)
        
        ttk.Label(mention_frame, text="Mention map (JSON or file path)").grid(
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
            text="Send Test",
            command=self.app._discord_send_test
        ).grid(row=0, column=0, padx=(0, 6))
        
        ttk.Button(
            discord_btns,
            text="Open State Folder",
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

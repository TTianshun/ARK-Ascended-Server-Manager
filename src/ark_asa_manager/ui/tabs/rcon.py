"""
RCON tab - Remote console command interface.
"""

import tkinter as tk
from tkinter import ttk

from .base import BaseTab


class RconTab(BaseTab):
    """RCON (Remote Console) command tab."""
    
    def build(self) -> None:
        """Build the RCON tab UI."""
        self.frame.columnconfigure(0, weight=1)
        
        # RCON command interface
        lf = ttk.LabelFrame(self.frame, text="RCON", padding=10)
        lf.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        lf.columnconfigure(1, weight=1)
        
        ttk.Label(lf, text="Saved Commands").grid(row=0, column=0, sticky="w")
        self.cmb_rcon_saved = ttk.Combobox(
            lf,
            textvariable=self.app.var_rcon_saved,
            state="readonly",
            values=[]
        )
        self.cmb_rcon_saved.grid(row=0, column=1, sticky="ew", padx=6)
        self.cmb_rcon_saved.bind(
            "<<ComboboxSelected>>",
            lambda e: self.app.var_rcon_cmd.set(self.app.var_rcon_saved.get())
        )
        
        ttk.Label(lf, text="Command").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ent_rcon_cmd = ttk.Entry(lf, textvariable=self.app.var_rcon_cmd)
        self.ent_rcon_cmd.grid(row=1, column=1, sticky="ew", padx=6, pady=(8, 0))
        self.ent_rcon_cmd.bind("<Return>", lambda e: self.app.send_rcon())
        
        self.btn_rcon_send = ttk.Button(
            lf,
            text="Send",
            command=self.app.send_rcon
        )
        self.btn_rcon_send.grid(row=1, column=2, pady=(8, 0))
        
        # Action buttons
        btn_row = ttk.Frame(lf)
        btn_row.grid(row=2, column=1, sticky="w", padx=6, pady=(10, 0))
        
        ttk.Button(
            btn_row,
            text="Save Command",
            command=self.app._rcon_save_current
        ).grid(row=0, column=0, padx=(0, 6))
        
        ttk.Button(
            btn_row,
            text="Remove Selected",
            command=self.app._rcon_remove_selected
        ).grid(row=0, column=1)
        
        # Info label
        ttk.Label(
            self.frame,
            text="Responses are written to the shared Console.",
            foreground=self.app.theme_colors.get("muted", "#888888")
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
    
    def on_selected(self) -> None:
        """Called when tab is selected."""
        # Update the saved commands list from config
        if hasattr(self.app, 'cfg') and self.app.cfg:
            saved_commands = self.app.cfg.rcon_saved_commands or []
            try:
                self.cmb_rcon_saved.configure(values=saved_commands)
            except Exception:
                pass
    
    def on_deselected(self) -> None:
        """Called when tab is deselected."""
        pass
    
    def collect_from_ui(self) -> dict:
        """Collect RCON settings from UI."""
        return {
            "rcon_cmd": self.app.var_rcon_cmd.get(),
            "rcon_saved": self.app.var_rcon_saved.get(),
        }
    
    def apply_to_ui(self, data: dict) -> None:
        """Apply RCON settings to UI."""
        pass

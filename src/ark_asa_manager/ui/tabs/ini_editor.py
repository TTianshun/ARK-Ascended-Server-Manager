"""
INI Editor tab - GameUserSettings.ini and Game.ini editor.
"""

import tkinter as tk
from tkinter import ttk

from .base import BaseTab


class IniEditorTab(BaseTab):
    """INI file editor tab for GameUserSettings.ini and Game.ini."""
    
    def build(self) -> None:
        """Build the INI Editor tab UI."""
        self.frame.columnconfigure(0, weight=2)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        # --- Top controls ---
        ini_top = ttk.Frame(self.frame)
        ini_top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ini_top.columnconfigure(1, weight=1)
        
        ttk.Label(ini_top, text="目标").grid(row=0, column=0, sticky="w")
        self.lbl_ini_target = ttk.Label(ini_top, text="（未加载）")
        self.lbl_ini_target.grid(row=0, column=1, sticky="w", padx=6)
        
        ttk.Button(
            ini_top,
            text="加载GameUserSettings.ini",
            command=self.app.load_gameusersettings
        ).grid(row=0, column=2, padx=4)
        
        ttk.Button(
            ini_top,
            text="加载Game.ini",
            command=self.app.load_game_ini
        ).grid(row=0, column=3, padx=4)
        
        ttk.Button(
            ini_top,
            text="打开流洋文档 + 上会模坻",
            command=self.app.open_loaded_ini
        ).grid(row=0, column=4, padx=4)
        
        ttk.Button(
            ini_top,
            text="从上游重新整合",
            command=self.app._ini_resync_from_upstream
        ).grid(row=0, column=5, padx=4)
        
        ttk.Label(ini_top, text="筛选").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ent_filter = ttk.Entry(ini_top, textvariable=self.app.var_ini_filter)
        ent_filter.grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        ent_filter.bind("<KeyRelease>", lambda e: self.app._ini_refresh_tree())
        
        # --- INI tree view (left side) ---
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(5, 2), pady=(0, 5))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        ttk.Label(tree_frame, text="INI条目").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        
        self.tree_ini = ttk.Treeview(
            tree_frame,
            columns=("Section", "Key", "Value"),
            height=20
        )
        self.tree_ini.heading("#0", text="条目")
        self.tree_ini.heading("Section", text="部分")
        self.tree_ini.heading("Key", text="键")
        self.tree_ini.heading("Value", text="值")
        self.tree_ini.column("#0", width=150)
        self.tree_ini.column("Section", width=150)
        self.tree_ini.column("Key", width=150)
        self.tree_ini.column("Value", width=200)
        
        self.tree_ini.grid(row=1, column=0, sticky="nsew")
        self.tree_ini.bind("<<TreeviewSelect>>", lambda e: self.app._ini_tree_select())
        
        # Scrollbar
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ini.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.tree_ini.configure(yscrollcommand=scroll.set)
        
        # --- Edit panel (right side) ---
        edit_frame = ttk.LabelFrame(self.frame, text="编辑条目", padding=10)
        edit_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 5), pady=(0, 5))
        edit_frame.columnconfigure(1, weight=1)
        
        ttk.Label(edit_frame, text="部分").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            edit_frame,
            textvariable=self.app.var_ini_section,
            state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=6)
        
        ttk.Label(edit_frame, text="关锫").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(
            edit_frame,
            textvariable=self.app.var_ini_key,
            state="readonly"
        ).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        
        ttk.Label(edit_frame, text="值").grid(row=2, column=0, sticky="nw", pady=(6, 0))
        self.ent_ini_value = ttk.Entry(edit_frame, textvariable=self.app.var_ini_value)
        self.ent_ini_value.grid(row=2, column=1, sticky="ew", padx=6, pady=(6, 0))
        
        # Edit buttons
        edit_btns = ttk.Frame(edit_frame)
        edit_btns.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(
            edit_btns,
            text="更新",
            command=self.app._ini_update_value
        ).grid(row=0, column=0, padx=(0, 6))
        
        ttk.Button(
            edit_btns,
            text="删除",
            command=self.app._ini_delete_entry
        ).grid(row=0, column=1)
        
        # --- Add entry panel (right side, bottom) ---
        add_frame = ttk.LabelFrame(self.frame, text="添加条目", padding=10)
        add_frame.grid(row=2, column=1, sticky="nsew", padx=(2, 5), pady=(0, 5))
        add_frame.columnconfigure(1, weight=1)
        
        ttk.Label(add_frame, text="部分").grid(row=0, column=0, sticky="w")
        ttk.Entry(add_frame, textvariable=self.app.var_ini_add_section).grid(
            row=0, column=1, sticky="ew", padx=6
        )
        
        ttk.Label(add_frame, text="关锫").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(add_frame, textvariable=self.app.var_ini_add_key).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        ttk.Label(add_frame, text="值").grid(row=2, column=0, sticky="nw", pady=(6, 0))
        ttk.Entry(add_frame, textvariable=self.app.var_ini_add_value).grid(
            row=2, column=1, sticky="ew", padx=6, pady=(6, 0)
        )
        
        add_btn = ttk.Button(
            add_frame,
            text="添加条目",
            command=self.app._ini_add_entry
        )
        add_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Save changes button
        save_frame = ttk.Frame(self.frame)
        save_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        save_frame.columnconfigure(0, weight=1)
        
        self.btn_ini_save = ttk.Button(
            save_frame,
            text="保存更改",
            command=self.app._ini_save_changes
        )
        self.btn_ini_save.grid(row=0, column=0, sticky="ew")
    
    def on_selected(self) -> None:
        """Called when tab is selected."""
        pass
    
    def on_deselected(self) -> None:
        """Called when tab is deselected."""
        pass
    
    def collect_from_ui(self) -> dict:
        """Collect INI editor state from UI."""
        return {
            "ini_filter": self.app.var_ini_filter.get(),
            "ini_section": self.app.var_ini_section.get(),
            "ini_key": self.app.var_ini_key.get(),
            "ini_value": self.app.var_ini_value.get(),
        }
    
    def apply_to_ui(self, data: dict) -> None:
        """Apply INI editor state to UI."""
        pass

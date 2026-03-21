"""
跨服聊天标签页 - LACC WebSocket 中继服务器管理与聊天界面
"""

import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from .base import BaseTab

THEME_COLORS = {
    "bg": "#1e1e1e",
    "surface": "#2d2d2d",
    "surface_light": "#3a3a3a",
    "border": "#444444",
    "text": "#e8e8e8",
    "muted": "#888888",
    "accent": "#0e639c",
    "accent_light": "#1177bb",
    "success": "#00aa00",
    "warning": "#ffcc00",
    "error": "#ff0000",
}


class ChatTab(BaseTab):
    """LACC 跨服聊天标签页"""

    def build(self) -> None:
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        colors = getattr(self.app, "theme_colors", THEME_COLORS)

        # ---- 配置区 ----
        lf_config = ttk.LabelFrame(self.frame, text="WebSocket 中继服务器配置", padding=10)
        lf_config.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        lf_config.columnconfigure(1, weight=1)

        ttk.Label(lf_config, text="监听端口").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            lf_config, textvariable=self.app.var_chat_ws_port, width=10
        ).grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(lf_config, text="认证 Token").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_config, textvariable=self.app.var_chat_token).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(6, 0)
        )

        ttk.Label(lf_config, text="Cluster Key").grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(lf_config, textvariable=self.app.var_chat_cluster_key).grid(
            row=2, column=1, sticky="ew", padx=6, pady=(6, 0)
        )

        ttk.Checkbutton(
            lf_config,
            text="随管理器启动时自动启动",
            variable=self.app.var_chat_auto_start,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # ---- 控制区 + 连接状态 ----
        ctrl_frame = ttk.Frame(self.frame)
        ctrl_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        ctrl_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(ctrl_frame)
        btn_frame.grid(row=0, column=0, sticky="w")

        self.btn_start = ttk.Button(
            btn_frame, text="启动服务器", command=self.app._start_chat_server
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 6))

        self.btn_stop = ttk.Button(
            btn_frame, text="停止服务器", command=self.app._stop_chat_server
        )
        self.btn_stop.grid(row=0, column=1, padx=(0, 6))

        self.btn_auto_config = ttk.Button(
            btn_frame, text="自动配置 LACC", command=self.app._auto_configure_lacc
        )
        self.btn_auto_config.grid(row=0, column=2, padx=(0, 6))

        self.lbl_status = ttk.Label(
            btn_frame, text="已停止", foreground=colors.get("muted", "#888888")
        )
        self.lbl_status.grid(row=0, column=3, padx=(6, 0))

        # 已连接的服务器列表
        lf_clients = ttk.LabelFrame(ctrl_frame, text="已连接的服务器", padding=5)
        lf_clients.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        lf_clients.columnconfigure(0, weight=1)

        self.tree_clients = ttk.Treeview(
            lf_clients,
            columns=("name", "cluster", "connected"),
            show="headings",
            height=3,
        )
        self.tree_clients.heading("name", text="服务器名称")
        self.tree_clients.heading("cluster", text="Cluster")
        self.tree_clients.heading("connected", text="连接时间")
        self.tree_clients.column("name", width=140)
        self.tree_clients.column("cluster", width=100)
        self.tree_clients.column("connected", width=140)
        self.tree_clients.grid(row=0, column=0, sticky="ew")

        # ---- 聊天记录区 ----
        lf_chat = ttk.LabelFrame(self.frame, text="跨服聊天记录", padding=5)
        lf_chat.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        lf_chat.columnconfigure(0, weight=1)
        lf_chat.rowconfigure(0, weight=1)

        self.txt_chat = tk.Text(
            lf_chat,
            wrap="word",
            state="disabled",
            background=colors.get("surface", "#2d2d2d"),
            foreground=colors.get("text", "#e8e8e8"),
            insertbackground=colors.get("text", "#e8e8e8"),
            selectbackground=colors.get("accent_light", "#1177bb"),
            highlightthickness=1,
            highlightbackground=colors.get("border", "#444444"),
            highlightcolor=colors.get("accent", "#0e639c"),
            font=("Consolas", 10),
        )
        self.txt_chat.grid(row=0, column=0, sticky="nsew")

        chat_scroll = ttk.Scrollbar(
            lf_chat, orient="vertical", command=self.txt_chat.yview
        )
        chat_scroll.grid(row=0, column=1, sticky="ns")
        self.txt_chat.configure(yscrollcommand=chat_scroll.set)

        # 聊天颜色标签
        self.txt_chat.tag_configure(
            "timestamp", foreground=colors.get("muted", "#888888")
        )
        self.txt_chat.tag_configure(
            "map_name", foreground="#5dade2"
        )
        self.txt_chat.tag_configure(
            "sender", foreground="#f5b041"
        )
        self.txt_chat.tag_configure(
            "admin_sender", foreground="#ff6b6b"
        )
        self.txt_chat.tag_configure(
            "message_text", foreground=colors.get("text", "#e8e8e8")
        )
        self.txt_chat.tag_configure(
            "system", foreground=colors.get("success", "#00aa00")
        )
        self.txt_chat.tag_configure(
            "raw_json", foreground="#666666", font=("Consolas", 8)
        )

        # ---- 消息发送区 ----
        send_frame = ttk.Frame(self.frame)
        send_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
        send_frame.columnconfigure(0, weight=1)

        self.var_chat_input = tk.StringVar(master=self.app.root)
        self.ent_chat_input = ttk.Entry(
            send_frame, textvariable=self.var_chat_input
        )
        self.ent_chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.ent_chat_input.bind("<Return>", lambda e: self.app._send_chat_message())

        self.btn_send = ttk.Button(
            send_frame, text="发送消息", command=self.app._send_chat_message
        )
        self.btn_send.grid(row=0, column=1)

        ttk.Label(
            send_frame,
            text="以管理员身份向所有已连接的 ARK 服务器广播消息",
            foreground=colors.get("muted", "#888888"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def append_chat_message(self, msg) -> None:
        """向聊天记录区追加一条 ChatMessage（线程安全，通过 root.after 调用）"""
        ts = datetime.fromtimestamp(msg.time_received).strftime("%H:%M:%S")
        sender_tag = "admin_sender" if msg.is_admin else "sender"

        map_name = msg.map_name or "未知地图"
        sender_name = msg.sender_name or msg.platform_player_name or "未知玩家"
        message_text = msg.message or "(空消息)"

        tribe_info = ""
        if msg.sender_tribe_name:
            tribe_info = f" <{msg.sender_tribe_name}>"

        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", f"[{ts}] ", "timestamp")
        self.txt_chat.insert("end", f"[{map_name}] ", "map_name")
        self.txt_chat.insert("end", f"{sender_name}{tribe_info}: ", sender_tag)
        self.txt_chat.insert("end", f"{message_text}\n", "message_text")

        if hasattr(msg, "raw_json") and msg.raw_json and not msg.is_admin:
            self.txt_chat.insert("end", f"  [RAW] {msg.raw_json}\n", "raw_json")

        self.txt_chat.see("end")
        self.txt_chat.configure(state="disabled")

    def append_system_message(self, text: str) -> None:
        """向聊天记录区追加系统信息"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", f"[{ts}] ", "timestamp")
        self.txt_chat.insert("end", f"[系统] {text}\n", "system")
        self.txt_chat.see("end")
        self.txt_chat.configure(state="disabled")

    def update_server_status(self, running: bool) -> None:
        colors = getattr(self.app, "theme_colors", THEME_COLORS)
        if running:
            self.lbl_status.configure(
                text="运行中", foreground=colors.get("success", "#00aa00")
            )
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        else:
            self.lbl_status.configure(
                text="已停止", foreground=colors.get("muted", "#888888")
            )
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    def refresh_client_list(self, clients) -> None:
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        for c in clients:
            t = datetime.fromtimestamp(c["connected_at"]).strftime("%Y-%m-%d %H:%M:%S")
            self.tree_clients.insert("", "end", values=(c["name"], c["cluster_key"], t))

    # ------------------------------------------------------------------
    # BaseTab interface
    # ------------------------------------------------------------------

    def on_selected(self) -> None:
        chat_server = getattr(self.app, "_chat_server", None)
        if chat_server and chat_server.is_running:
            self.update_server_status(True)
            self.refresh_client_list(chat_server.get_connected_clients())
        else:
            self.update_server_status(False)

    def on_deselected(self) -> None:
        pass

    def collect_from_ui(self) -> dict:
        return {
            "chat_ws_port": self.app.var_chat_ws_port.get(),
            "chat_token": self.app.var_chat_token.get(),
            "chat_cluster_key": self.app.var_chat_cluster_key.get(),
            "chat_auto_start": self.app.var_chat_auto_start.get(),
        }

    def apply_to_ui(self, data: dict) -> None:
        pass

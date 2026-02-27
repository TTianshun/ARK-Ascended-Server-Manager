"""
Modern UI Components - Reusable CustomTkinter widget components

这个模块提供现代化的CTk组件，用于快速构建专业的UI。
"""

import customtkinter as ctk
from typing import Callable, Optional, Any
from .modern_theme import get_font


class ModernCard(ctk.CTkFrame):
    """
    Modern card container with rounded corners and shadow effect.
    适用于分组相关的设置或信息。
    """
    
    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(
            parent,
            corner_radius=12,
            fg_color=("white", "#27272A"),
            border_width=1,
            border_color=("lightgray", "#3F3F46"),
            **kwargs
        )
        
        self.columnconfigure(0, weight=1)
        
        # Title if provided
        if title:
            title_label = ctk.CTkLabel(
                self,
                text=title,
                font=get_font(size=13, weight="bold"),
                text_color=("black", "white")
            )
            title_label.pack(padx=20, pady=(15, 10), anchor="w", fill="x")
        
        # Content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=(10, 15))
        self.content.columnconfigure(0, weight=1)


class ModernButton(ctk.CTkButton):
    """
    Modern button with customizable style.
    支持primary, secondary, danger, success等预定义样式。
    """
    
    STYLES = {
        "primary": {
            "fg_color": ("#3B82F6", "#2563EB"),
            "hover_color": ("#2563EB", "#1D4ED8"),
            "text_color": "white",
        },
        "secondary": {
            "fg_color": ("#E5E7EB", "#3F3F46"),
            "hover_color": ("#D1D5DB", "#525256"),
            "text_color": ("#111827", "#FAFAFA"),
        },
        "danger": {
            "fg_color": ("#EF4444", "#DC2626"),
            "hover_color": ("#DC2626", "#BA1B1B"),
            "text_color": "white",
        },
        "success": {
            "fg_color": ("#10B981", "#059669"),
            "hover_color": ("#059669", "#047857"),
            "text_color": "white",
        },
        "warning": {
            "fg_color": ("#F59E0B", "#D97706"),
            "hover_color": ("#D97706", "#B45309"),
            "text_color": "white",
        },
    }
    
    def __init__(self, parent, text: str = "", style: str = "primary", **kwargs):
        style_config = self.STYLES.get(style, self.STYLES["primary"])
        super().__init__(
            parent,
            text=text,
            corner_radius=8,
            **{**style_config, **kwargs}
        )


class ModernInputField(ctk.CTkFrame):
    """
    Modern input field with label and optional helper text.
    包含标签、输入框和可选的助手文本。
    """
    
    def __init__(
        self,
        parent,
        label: str = "",
        placeholder: str = "",
        helper_text: str = "",
        is_password: bool = False,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        
        # Label
        if label:
            lbl = ctk.CTkLabel(
                self,
                text=label,
                font=get_font(size=10),
                text_color=("black", "white")
            )
            lbl.pack(anchor="w", pady=(0, 5))
        
        # Input field
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            height=36,
            corner_radius=8,
            show="•" if is_password else ""
        )
        self.entry.pack(fill="x")
        
        # Helper text
        if helper_text:
            helper = ctk.CTkLabel(
                self,
                text=helper_text,
                font=get_font(size=8),
                text_color="gray"
            )
            helper.pack(anchor="w", pady=(5, 0))
    
    def get(self) -> str:
        """Get input value."""
        return self.entry.get()
    
    def set(self, value: str) -> None:
        """Set input value."""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)


class ModernComboBox(ctk.CTkFrame):
    """
    Modern combobox with label and optional helper text.
    """
    
    def __init__(
        self,
        parent,
        label: str = "",
        values: list = None,
        helper_text: str = "",
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        
        # Label
        if label:
            lbl = ctk.CTkLabel(
                self,
                text=label,
                font=get_font(size=10),
                text_color=("black", "white")
            )
            lbl.pack(anchor="w", pady=(0, 5))
        
        # Combobox
        self.combo = ctk.CTkComboBox(
            self,
            values=values or [],
            height=36,
            corner_radius=8
        )
        self.combo.pack(fill="x")
        
        # Helper text
        if helper_text:
            helper = ctk.CTkLabel(
                self,
                text=helper_text,
                font=get_font(size=8),
                text_color="gray"
            )
            helper.pack(anchor="w", pady=(5, 0))
    
    def get(self) -> str:
        """Get selected value."""
        return self.combo.get()
    
    def set(self, value: str) -> None:
        """Set selected value."""
        self.combo.set(value)


class ModernCheckBox(ctk.CTkCheckBox):
    """
    Modern checkbox with enhanced styling.
    """
    
    def __init__(self, parent, text: str = "", **kwargs):
        super().__init__(
            parent,
            text=text,
            corner_radius=6,
            checkbox_height=20,
            checkbox_width=20,
            font=get_font(size=10),
            **kwargs
        )


class ModernToggle(ctk.CTkSwitch):
    """
    Modern toggle switch for boolean settings.
    """
    
    def __init__(self, parent, text: str = "", **kwargs):
        super().__init__(
            parent,
            text=text,
            font=get_font(size=10),
            **kwargs
        )


class ModernSection(ctk.CTkFrame):
    """
    Section container for grouping related controls with header.
    用于在卡片内进一步组织内容。
    """
    
    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        
        if title:
            header = ctk.CTkLabel(
                self,
                text=title,
                font=get_font(size=11, weight="bold"),
                text_color=("black", "white")
            )
            header.pack(anchor="w", pady=(10, 8))
        
        # Content container
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        self.content.columnconfigure(0, weight=1)


class ModernStatusBadge(ctk.CTkFrame):
    """
    Status badge showing current server status.
    """
    
    def __init__(self, parent, status: str = "offline", **kwargs):
        super().__init__(
            parent,
            corner_radius=8,
            fg_color=("lightgray", "#3F3F46"),
            **kwargs
        )
        
        self.status = status
        self._update_display()
    
    def _update_display(self) -> None:
        """Update status display."""
        # Clear existing children
        for widget in self.winfo_children():
            widget.destroy()
        
        # Determine color and text
        if self.status == "running":
            color = "#10B981"
            symbol = "●"
            text = "Running"
        elif self.status == "stopping":
            color = "#F59E0B"
            symbol = "◐"
            text = "Stopping..."
        else:  # offline
            color = "#EF4444"
            symbol = "●"
            text = "Offline"
        
        label = ctk.CTkLabel(
            self,
            text=f"{symbol} {text}",
            text_color=color,
            font=get_font(size=11, weight="bold")
        )
        label.pack(padx=15, pady=10)
    
    def set_status(self, status: str) -> None:
        """Update status."""
        self.status = status
        self._update_display()


class ModernProgressBar(ctk.CTkProgressBar):
    """
    Modern progress bar with enhanced styling.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            corner_radius=8,
            height=8,
            fg_color=("lightgray", "#3F3F46"),
            progress_color="#3B82F6",
            **kwargs
        )

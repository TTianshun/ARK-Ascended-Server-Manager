"""
Modern theme for CustomTkinter UI - Professional dark/light themes
"""

# Modern Dark Theme (recommended)
DARK_THEME = {
    # Primary colors
    "bg": "#18181C",              # Main background
    "surface": "#27272A",         # Panel/widget background
    "surface_hover": "#3F3F46",   # Hover state
    "surface_active": "#4A4A52",  # Active state
    "border": "#3F3F46",          # Border color
    
    # Text colors
    "text": "#FAFAFA",            # Primary text
    "text_secondary": "#A1A1A6",  # Secondary text
    "text_muted": "#727277",      # Muted text
    
    # Accent colors
    "accent": "#3B82F6",          # Primary accent (blue)
    "accent_hover": "#2563EB",    # Accent hover
    "accent_light": "#60A5FA",    # Light accent
    
    # States
    "success": "#10B981",         # Success (green)
    "warning": "#F59E0B",         # Warning (amber)
    "error": "#EF4444",           # Error (red)
    "info": "#06B6D4",            # Info (cyan)
    
    # Special
    "console_bg": "#0F0F12",
    "console_fg": "#D1D3D8",
}

# Modern Light Theme
LIGHT_THEME = {
    # Primary colors
    "bg": "#FFFFFF",              # Main background
    "surface": "#F3F4F6",         # Panel/widget background
    "surface_hover": "#E5E7EB",   # Hover state
    "surface_active": "#D1D5DB",  # Active state
    "border": "#E5E7EB",          # Border color
    
    # Text colors
    "text": "#111827",            # Primary text
    "text_secondary": "#6B7280",  # Secondary text
    "text_muted": "#9CA3AF",      # Muted text
    
    # Accent colors
    "accent": "#3B82F6",          # Primary accent (blue)
    "accent_hover": "#2563EB",    # Accent hover
    "accent_light": "#60A5FA",    # Light accent
    
    # States
    "success": "#059669",         # Success (green)
    "warning": "#D97706",         # Warning (amber)
    "error": "#DC2626",           # Error (red)
    "info": "#0891B2",            # Info (cyan)
    
    # Special
    "console_bg": "#F9FAFB",
    "console_fg": "#111827",
}

# Component styling presets
BUTTON_STYLES = {
    "primary": {
        "fg_color": ("#3B82F6", "#2563EB"),      # light, dark
        "hover_color": ("#2563EB", "#1D4ED8"),
        "text_color": "white",
        "corner_radius": 8,
        "border_width": 0,
    },
    "secondary": {
        "fg_color": ("#E5E7EB", "#3F3F46"),      # light, dark
        "hover_color": ("#D1D5DB", "#525256"),
        "text_color": ("#111827", "#FAFAFA"),
        "corner_radius": 8,
        "border_width": 1,
        "border_color": ("#D1D5DB", "#525256"),
    },
    "danger": {
        "fg_color": ("#EF4444", "#DC2626"),      # light, dark
        "hover_color": ("#DC2626", "#BA1B1B"),
        "text_color": "white",
        "corner_radius": 8,
        "border_width": 0,
    },
    "success": {
        "fg_color": ("#10B981", "#059669"),      # light, dark
        "hover_color": ("#059669", "#047857"),
        "text_color": "white",
        "corner_radius": 8,
        "border_width": 0,
    },
}

ENTRY_STYLES = {
    "fg_color": ("#FFFFFF", "#27272A"),          # light, dark
    "text_color": ("#111827", "#FAFAFA"),
    "border_color": ("#D1D5DB", "#3F3F46"),
    "border_width": 1,
    "corner_radius": 6,
}

LABEL_FRAME_STYLES = {
    "fg_color": ("#F3F4F6", "#27272A"),
    "text_color": ("#111827", "#FAFAFA"),
    "border_color": ("#E5E7EB", "#3F3F46"),
    "border_width": 1,
}

def get_theme(mode: str = "dark") -> dict:
    """
    Get theme dictionary for specified mode.
    
    Args:
        mode: "dark" or "light"
        
    Returns:
        Theme color dictionary
    """
    return DARK_THEME if mode.lower() == "dark" else LIGHT_THEME


def apply_ctk_theme(mode: str = "dark") -> None:
    """
    Apply CustomTkinter theme mode.
    
    Args:
        mode: "dark" or "light" or "system"
    """
    import customtkinter as ctk
    if mode.lower() == "system":
        ctk.set_appearance_mode("System")
    elif mode.lower() == "light":
        ctk.set_appearance_mode("Light")
    else:
        ctk.set_appearance_mode("Dark")


def get_font_family() -> str:
    """Get platform-appropriate font family."""
    import sys
    if sys.platform == "darwin":  # macOS
        return "SF Pro Display"
    elif sys.platform == "win32":  # Windows
        return "Segoe UI"
    else:  # Linux
        return "Ubuntu"


def get_font(size: int = 10, weight: str = "normal") -> tuple:
    """
    Get font tuple for CustomTkinter.
    
    Args:
        size: Font size in pixels
        weight: "normal", "bold", or "italic"
        
    Returns:
        Tuple of (family, size, weight)
    """
    family = get_font_family()
    return (family, size, weight if weight != "normal" else "normal")

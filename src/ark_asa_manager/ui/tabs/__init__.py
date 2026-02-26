"""
UI Tabs - Modular tab components for the server manager GUI.
"""

from .base import BaseTab
from .server import ServerTab
from .advanced import AdvancedTab
from .rcon import RconTab
from .discord import DiscordTab
from .ini_editor import IniEditorTab

__all__ = [
    "BaseTab",
    "ServerTab",
    "AdvancedTab",
    "RconTab",
    "DiscordTab",
    "IniEditorTab",
]

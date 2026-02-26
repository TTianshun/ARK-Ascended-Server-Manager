"""
Base class for tab components.
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk


class BaseTab(ABC):
    """Base class for all tab components in the UI."""

    def __init__(self, parent: ttk.Frame, app: "ServerManagerApp"):
        """
        Initialize the tab component.
        
        Args:
            parent: The parent ttk.Frame that will contain this tab
            app: Reference to the main ServerManagerApp instance
        """
        self.parent = parent
        self.app = app
        self.frame = parent  # The tab content frame is the parent itself
        
    @abstractmethod
    def build(self) -> None:
        """Build the tab UI components."""
        pass
    
    @abstractmethod
    def on_selected(self) -> None:
        """Called when the tab is selected."""
        pass
    
    @abstractmethod
    def on_deselected(self) -> None:
        """Called when the tab is deselected."""
        pass
    
    @abstractmethod
    def collect_from_ui(self) -> dict:
        """
        Collect all form data from the UI.
        
        Returns:
            Dictionary of collected data
        """
        pass
    
    @abstractmethod
    def apply_to_ui(self, data: dict) -> None:
        """
        Apply data to the UI form.
        
        Args:
            data: Dictionary of data to apply
        """
        pass

"""
Window selector UI components for Priston Tale Potion Bot
--------------------------------------------------------
This module handles the UI for selecting the game window.
"""

import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from app.bar_selector import ScreenSelector
from app.bot.interfaces import WindowManager

logger = logging.getLogger('PristonBot')

class WindowSelectorUI(WindowManager):
    """Class for managing game window selection in the UI"""
    
    def __init__(self, root, main_frame, log_callback):
        """
        Initialize the window selector UI components
        
        Args:
            root: The tkinter root window
            main_frame: The main frame to add UI elements to
            log_callback: Function to log messages
        """
        self.root = root
        self.log_callback = log_callback
        
        # Create game window selection frame
        self.window_frame = ttk.LabelFrame(main_frame, text="Game Window", padding=10)
        self.window_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Game window selector
        self._game_window = ScreenSelector(root)
        
        # Game window preview
        self.window_preview_label = ttk.Label(self.window_frame, text="Not Selected")
        self.window_preview_label.pack(padx=5, pady=5)
        
        # Window selection button
        ttk.Button(self.window_frame, text="Select Game Window", 
                 command=self.start_window_selection).pack(fill=tk.X, pady=5)
    
    @property
    def game_window(self):
        """Get the game window selector"""
        return self._game_window
        
    def is_setup(self):
        """Check if the window is configured"""
        return self._game_window.is_setup()
        
    def start_window_selection(self):
        """Start the game window selection process"""
        self._game_window = ScreenSelector(self.root)  # Recreate for fresh selection
        self._game_window.start_selection(title="Game Window", color="yellow")
        # Schedule an update to check if the selection was completed
        self.root.after(1000, self.update_window_preview)
    
    def update_window_preview(self):
        """Update the preview of the game window"""
        if self._game_window.is_setup():
            if hasattr(self._game_window, 'preview_image') and self._game_window.preview_image is not None:
                try:
                    # Resize the image to fit in the label
                    preview_size = (150, 100)  # Width, height
                    resized_img = self._game_window.preview_image.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.window_preview_label.config(image=preview_photo, text="")
                    self.window_preview_label.image = preview_photo  # Keep a reference
                    
                    self.log_callback(f"Game window selected: ({self._game_window.x1},{self._game_window.y1}) to ({self._game_window.x2},{self._game_window.y2})")
                    
                except Exception as e:
                    logger.error(f"Error displaying window preview: {e}")
                    self.window_preview_label.config(text=f"Selected: ({self._game_window.x1},{self._game_window.y1}) to ({self._game_window.x2},{self._game_window.y2})")
            else:
                self.window_preview_label.config(text=f"Selected: ({self._game_window.x1},{self._game_window.y1}) to ({self._game_window.x2},{self._game_window.y2})")
        else:
            # Check again later
            self.root.after(1000, self.update_window_preview)
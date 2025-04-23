"""
Bar selection UI components for Priston Tale Potion Bot
------------------------------------------------------
This module handles the UI for selecting and previewing health, mana, and stamina bars.
"""

import os
import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab

from app.bar_selector import ScreenSelector
from app.bot.interfaces import BarManager

logger = logging.getLogger('PristonBot')

class BarAdapter(BarManager):
    """Adapter class to make ScreenSelector compatible with BarManager interface"""
    
    def __init__(self, screen_selector):
        """
        Initialize with a ScreenSelector
        
        Args:
            screen_selector: ScreenSelector instance
        """
        self.screen_selector = screen_selector
    
    def is_setup(self) -> bool:
        """Check if the bar is configured"""
        return self.screen_selector.is_setup()
    
    def get_current_screenshot_region(self):
        """Get a screenshot of the selected region"""
        return self.screen_selector.get_current_screenshot_region()
    
    def configure_from_saved(self, x1, y1, x2, y2):
        """Delegate to the screen_selector"""
        return self.screen_selector.configure_from_saved(x1, y1, x2, y2)
    
    # Forward attributes to the screen_selector
    def __getattr__(self, attr):
        return getattr(self.screen_selector, attr)
        
    @property
    def x1(self):
        return self.screen_selector.x1
        
    @property
    def y1(self):
        return self.screen_selector.y1
        
    @property
    def x2(self):
        return self.screen_selector.x2
        
    @property
    def y2(self):
        return self.screen_selector.y2

class BarSelectorUI:
    """Class for managing bar selection in the UI"""
    
    def __init__(self, root, main_frame, log_callback):
        """
        Initialize the bar selector UI components
        
        Args:
            root: The tkinter root window
            main_frame: The main frame to add UI elements to
            log_callback: Function to log messages
        """
        self.root = root
        self.log_callback = log_callback
        
        # Create bar selection frame
        self.bars_frame = ttk.LabelFrame(main_frame, text="Bar Selection", padding=10)
        self.bars_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create bar selectors
        self.hp_bar_selector = ScreenSelector(root)
        self.mp_bar_selector = ScreenSelector(root)
        self.sp_bar_selector = ScreenSelector(root)
        
        # Set titles for the bar selectors
        self.hp_bar_selector.title = "Health Bar"
        self.mp_bar_selector.title = "Mana Bar"
        self.sp_bar_selector.title = "Stamina Bar"
        
        # Create bar adapters (implementing BarManager)
        self.hp_bar = BarAdapter(self.hp_bar_selector)
        self.mp_bar = BarAdapter(self.mp_bar_selector)
        self.sp_bar = BarAdapter(self.sp_bar_selector)
        
        # Create preview area for each bar
        preview_frame = ttk.Frame(self.bars_frame)
        preview_frame.pack(fill=tk.X, pady=5)
        
        # Health bar preview
        hp_frame = ttk.LabelFrame(preview_frame, text="Health Bar")
        hp_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)
        self.hp_preview_label = ttk.Label(hp_frame, text="Not Selected")
        self.hp_preview_label.pack(padx=5, pady=5)
        
        # Mana bar preview
        mp_frame = ttk.LabelFrame(preview_frame, text="Mana Bar")
        mp_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.mp_preview_label = ttk.Label(mp_frame, text="Not Selected")
        self.mp_preview_label.pack(padx=5, pady=5)
        
        # Stamina bar preview
        sp_frame = ttk.LabelFrame(preview_frame, text="Stamina Bar")
        sp_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
        self.sp_preview_label = ttk.Label(sp_frame, text="Not Selected")
        self.sp_preview_label.pack(padx=5, pady=5)
        
        # Create bar selection buttons
        selection_buttons_frame = ttk.Frame(self.bars_frame)
        selection_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Health Bar", 
                 command=lambda: self.start_bar_selection("Health", "red")).pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Mana Bar", 
                 command=lambda: self.start_bar_selection("Mana", "blue")).pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Stamina Bar", 
                 command=lambda: self.start_bar_selection("Stamina", "green")).pack(fill=tk.X, pady=5)
        
        # Schedule initial preview updates - this is important for loading saved configurations
        self.root.after(1000, self.update_all_previews)
    
    def update_all_previews(self):
        """Update all preview images"""
        self.update_preview_image(self.hp_bar_selector, self.hp_preview_label)
        self.update_preview_image(self.mp_bar_selector, self.mp_preview_label)
        self.update_preview_image(self.sp_bar_selector, self.sp_preview_label)
    
    def start_bar_selection(self, bar_type, color):
        """Start the selection process for a specific bar"""
        if bar_type == "Health":
            # Re-initialize the bar selector to ensure fresh selection
            self.hp_bar_selector = ScreenSelector(self.root)
            self.hp_bar_selector.title = "Health Bar"
            self.hp_bar = BarAdapter(self.hp_bar_selector)
            self.hp_bar_selector.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.hp_bar_selector, self.hp_preview_label))
        elif bar_type == "Mana":
            # Re-initialize the bar selector to ensure fresh selection
            self.mp_bar_selector = ScreenSelector(self.root)
            self.mp_bar_selector.title = "Mana Bar"
            self.mp_bar = BarAdapter(self.mp_bar_selector)
            self.mp_bar_selector.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.mp_bar_selector, self.mp_preview_label))
        elif bar_type == "Stamina":
            # Re-initialize the bar selector to ensure fresh selection
            self.sp_bar_selector = ScreenSelector(self.root)
            self.sp_bar_selector.title = "Stamina Bar"
            self.sp_bar = BarAdapter(self.sp_bar_selector)
            self.sp_bar_selector.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.sp_bar_selector, self.sp_preview_label))
    
    def update_preview_image(self, selector, label):
        """Update the preview image for a bar"""
        if selector.is_setup():
            if hasattr(selector, 'preview_image') and selector.preview_image is not None:
                try:
                    # Check if we have a rotated preview for vertical bars
                    preview_img = selector.preview_image_rotated if hasattr(selector, 'preview_image_rotated') and selector.preview_image_rotated is not None else selector.preview_image
                    
                    # Resize the image to fit in the label
                    preview_size = (120, 30)  # Width, height
                    resized_img = preview_img.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    label.config(image=preview_photo, text="")
                    label.image = preview_photo  # Keep a reference
                    
                    # Log the selection
                    title = selector.title if hasattr(selector, 'title') else "Bar"
                    self.log_callback(f"{title} selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
                    
                except Exception as e:
                    # If resize fails, show coords
                    logger.error(f"Error displaying preview image: {e}")
                    title = selector.title if hasattr(selector, 'title') else "Bar"
                    label.config(text=f"Selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
            else:
                # If no preview image, try to capture one
                try:
                    # Try to capture a screenshot of the region
                    if all([selector.x1 is not None, selector.y1 is not None, 
                            selector.x2 is not None, selector.y2 is not None]):
                        current_screenshot = ImageGrab.grab(bbox=(selector.x1, selector.y1, selector.x2, selector.y2))
                        selector.preview_image = current_screenshot
                        
                        # Try to update the image again
                        self.root.after(100, lambda: self.update_preview_image(selector, label))
                        return
                except Exception as e:
                    logger.debug(f"Could not capture preview image: {e}")
                
                # If we couldn't get a preview image, just show coords
                title = selector.title if hasattr(selector, 'title') else "Bar"
                label.config(text=f"Selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
        else:
            label.config(text="Not Selected")
            
            # Check again later
            self.root.after(1000, lambda: self.update_preview_image(selector, label))
            
    def is_all_bars_setup(self):
        """Check if all bars are configured"""
        return (self.hp_bar.is_setup() and
                self.mp_bar.is_setup() and 
                self.sp_bar.is_setup())
                
    def get_configured_count(self):
        """Get the number of configured bars"""
        return sum([
            self.hp_bar.is_setup(),
            self.mp_bar.is_setup(),
            self.sp_bar.is_setup()
        ])
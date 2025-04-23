"""
Main GUI for the Priston Tale Potion Bot
---------------------------------------
This module contains the main GUI class that integrates all UI components.
"""

import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from app.ui.components import ScrollableFrame
from app.ui.bar_selector_ui import BarSelectorUI
from app.ui.settings_ui import SettingsUI
from app.ui.bot_controller import BotControllerUI
from app.ui.config_manager_ui import ConfigManagerUI

logger = logging.getLogger('PristonBot')

class PristonTaleBot:
    """Main application class for the Priston Tale Potion Bot"""
    
    def __init__(self, root):
        """
        Initialize the application
        
        Args:
            root: tkinter root window
        """
        logger.info("Initializing Priston Tale Potion Bot")
        self.root = root
        self.root.geometry("550x750")  # Base size
        self.root.minsize(550, 600)    # Minimum size
        
        # Create scrollable main frame
        scroll_container = ScrollableFrame(root)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # Use the scrollable frame as our main container
        main_frame = scroll_container.scrollable_frame
        
        # Create title label
        title_label = ttk.Label(main_frame, text="Priston Tale Potion Bot", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Create log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Log text - using scrolledtext for better handling
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=50, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, pady=5)
        
        # Initialize components
        # Bar selector UI
        self.bar_selector_ui = BarSelectorUI(main_frame, root, self.log)
        
        # Settings UI
        self.settings_ui = SettingsUI(main_frame, self.save_config)
        
        # Config manager
        self.config_manager = ConfigManagerUI(
            self.bar_selector_ui,
            self.settings_ui,
            self.log
        )
        
        # Bot controller
        self.bot_controller = BotControllerUI(
            main_frame, 
            root,
            self.bar_selector_ui.hp_bar_selector,
            self.bar_selector_ui.mp_bar_selector,
            self.bar_selector_ui.sp_bar_selector,
            self.settings_ui,
            self.log
        )
        
        # Initial log entry
        self.log("Bot GUI initialized successfully")
        
        # Try to load saved configuration
        if self.config_manager.load_bar_config():
            self.log("Loaded saved configuration")
        else:
            self.log("No saved configuration found or loading failed")
            self.log("Please select the Health, Mana, and Stamina bars to continue")
        
        # Check if bars are configured periodically
        self.check_bar_config()
        
        # Set up window close handler to save configuration
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Bot GUI initialized")
    
    def log(self, message):
        """Add a message to the log display"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        # Also log to the logger
        logger.info(message)
    
    def check_bar_config(self):
        """Check if all bars are configured and enable the start button if they are"""
        # Count configured bars
        configured = self.bar_selector_ui.get_configured_count()
        
        if configured > 0:
            self.bot_controller.set_status(f"{configured}/3 bars configured")
            
        # Enable start button if all bars are configured
        if configured == 3:
            self.bot_controller.enable_start_button()
            self.bot_controller.set_status("Ready to start")
            self.log("All bars configured! You can now start the bot.")
            logger.info("All bars configured, start button enabled")
        else:
            self.bot_controller.disable_start_button()
            
        # Check again later if not all configured yet
        if configured < 3:
            self.root.after(1000, self.check_bar_config)
    
    def save_config(self):
        """Save the configuration"""
        self.config_manager.save_bar_config()
    
    def on_closing(self):
        """Handle window closing event"""
        try:
            # Stop the bot if running
            if self.bot_controller.running:
                self.bot_controller.stop_bot()
                
            # Save configuration before exiting
            self.save_config()
            logger.info("Configuration saved on exit")
            
            # Destroy the window
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error on closing: {e}", exc_info=True)
            self.root.destroy()
"""
Main GUI for the Priston Tale Potion Bot
---------------------------------------
This module contains the main GUI class that integrates all components.
"""

import os
import time
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from app.ui.scrollable_frame import ScrollableFrame
from app.ui.window_selector_ui import WindowSelectorUI
from app.ui.bar_selector_ui import BarSelectorUI
from app.ui.settings_ui import SettingsUI
from app.bot.potion_bot import PotionBot
from app.bot.config_manager import ConfigManager
from app.window_utils import test_click_methods, find_game_window

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
        self.root.geometry("800x600")  # Wider base size for horizontal layout
        self.root.minsize(750, 500)    # Adjusted minimum size
        
        # Create main container frame
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left column for game window and bar selection
        left_column = ttk.Frame(main_container)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create right column for settings and controls
        right_column = ttk.Frame(main_container)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create title label
        title_label = ttk.Label(left_column, text="Priston Tale Potion Bot", font=("Arial", 16, "bold"))
        title_label.pack(pady=5)
        
        # Initialize UI components
        self.window_selector_ui = WindowSelectorUI(root, left_column, self.log)
        self.bar_selector_ui = BarSelectorUI(root, left_column, self.log)
        
        # Settings in right column
        self.settings_ui = SettingsUI(right_column)
        
        # Add Save Configuration button
        save_config_btn = ttk.Button(
            self.settings_ui.settings_frame, 
            text="Save Configuration", 
            command=self.save_config
        )
        save_config_btn.pack(fill=tk.X, pady=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(right_column, text="Status", padding=5)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to configure")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10))
        self.status_label.pack(fill=tk.X, pady=2)
        
        # Control buttons
        control_frame = ttk.Frame(right_column)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Create buttons with normal styling to ensure text visibility
        self.start_button = tk.Button(
            control_frame, 
            text="START BOT",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",  # Green
            fg="white",
            command=self.start_bot, 
            state=tk.DISABLED,
            height=1
        )
        self.start_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.stop_button = tk.Button(
            control_frame, 
            text="STOP BOT",
            font=("Arial", 11, "bold"),
            bg="#F44336",  # Red
            fg="white",
            command=self.stop_bot, 
            state=tk.DISABLED,
            height=1
        )
        self.stop_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        # Test tools frame
        test_frame = ttk.LabelFrame(right_column, text="Testing Tools", padding=5)
        test_frame.pack(fill=tk.X, padx=5, pady=5)

        # Test click methods button
        test_click_button = ttk.Button(
            test_frame,
            text="Test Click Methods",
            command=self.test_click_methods
        )
        test_click_button.pack(fill=tk.X, padx=2, pady=2)
        
        # Log frame at the bottom spanning both columns
        log_frame = ttk.LabelFrame(main_container, text="Log",height=408, width=840)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)
        
        # Log text - using scrolledtext for better handling
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Store a reference to bar_selector_ui for config_manager to use
        main_container.bar_selector_ui = self.bar_selector_ui
        
        # Initialize bot and config manager
        self.potion_bot = PotionBot(
            self.bar_selector_ui.hp_bar,
            self.bar_selector_ui.mp_bar,
            self.bar_selector_ui.sp_bar,
            self.settings_ui,
            self.log
        )
        
        self.config_manager = ConfigManager(
            self.settings_ui, 
            self.bar_selector_ui.hp_bar,
            self.bar_selector_ui.mp_bar,
            self.bar_selector_ui.sp_bar,
            self.window_selector_ui, 
            self.log
        )
        
        # Initial log entry
        self.log("Bot GUI initialized successfully")
        
        # Try to load saved configuration
        if self.config_manager.load_bar_config():
            self.log("Loaded saved configuration")
            # Force update of all bar previews
            self.bar_selector_ui.update_all_previews()
            # Force update of window preview
            if hasattr(self.window_selector_ui, 'update_window_preview'):
                self.window_selector_ui.update_window_preview()
        else:
            self.log("No saved configuration found or loading failed")
            self.log("Please select the Health, Mana, and Stamina bars to continue")
        
        # Check if bars are configured periodically
        self.check_bar_config()
        
        # Set up window close handler to save configuration
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Bot GUI initialized")
    
    def test_click_methods(self):
        """Test click methods and log results"""
        self.log("Testing click methods...")
        
        # Try to get game window handle
        window_handle = None
        if self.window_selector_ui.is_setup():
            # Try to find the game window
            window_handle = find_game_window()
            if window_handle:
                self.log(f"Found game window with handle: {window_handle}")
            else:
                self.log("Game window not found, testing global methods only")
        
        # Run the tests
        results = test_click_methods(window_handle)
        
        # Log the results
        self.log("Click method test results:")
        for method, result in results.items():
            self.log(f"  {method}: {result}")
        
        self.log("Testing completed. Check the logs for detailed information.")
        
    def on_closing(self):
        """Handle window closing event"""
        try:
            # Stop the bot if running
            if self.potion_bot.running:
                self.stop_bot()
                
            # Save configuration before exiting
            self.save_config()
            logger.info("Configuration saved on exit")
            
            # Destroy the window
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error on closing: {e}", exc_info=True)
            self.root.destroy()
            
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
            self.status_var.set(f"{configured}/3 bars configured")
            
        # Enable start button if all bars are configured
        if configured == 3:
            self.start_button.config(state=tk.NORMAL)
            self.status_var.set("Ready to start")
            self.log("All bars configured! You can now start the bot.")
            logger.info("All bars configured, start button enabled")
        
        # Check again later if not all configured yet
        if configured < 3:
            self.root.after(1000, self.check_bar_config)
            
    def save_config(self):
        """Save the current configuration"""
        if self.config_manager.save_bar_config():
            self.log("Configuration saved successfully")
        else:
            self.log("Failed to save configuration")
    
    def start_bot(self):
        """Start the bot"""
        # Save current settings before starting
        self.save_config()
        
        if self.potion_bot.start_bot():
            self.status_var.set("Bot is running")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
    
    def stop_bot(self):
        """Stop the bot"""
        if self.potion_bot.stop_bot():
            self.status_var.set("Bot is stopped")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # Save settings after stopping the bot
            self.save_config()
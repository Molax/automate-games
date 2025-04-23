"""
Scrollable GUI for the Priston Tale Potion Bot
---------------------------------------
This module contains a scrollable GUI to ensure all components are visible.
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
import numpy as np
from PIL import Image, ImageTk, ImageGrab

# Import our simplified screen selector and bar detector
from app.bar_selector import ScreenSelector, BarDetector
from app.bar_selector import HEALTH_COLOR_RANGE, MANA_COLOR_RANGE, STAMINA_COLOR_RANGE
from app.window_utils import press_key, press_right_mouse
from app.config import load_config, save_config, DEFAULT_CONFIG

logger = logging.getLogger('PristonBot')

class ScrollableFrame(ttk.Frame):
    """A scrollable frame container"""
    
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # Create a window inside the canvas containing the scrollable frame
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to scroll
        self.bind_mousewheel()
        
    def bind_mousewheel(self):
        """Bind mousewheel to scroll canvas"""
        def _on_mousewheel(event):
            # Scroll direction depends on platform
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")
                
        # Bind mousewheel events
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and macOS
        self.canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
        self.canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down

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
        
        # Create game window selection frame
        window_frame = ttk.LabelFrame(main_frame, text="Game Window", padding=10)
        window_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Game window selector
        self.game_window = ScreenSelector(root)
        
        # Game window preview
        self.window_preview_label = ttk.Label(window_frame, text="Not Selected")
        self.window_preview_label.pack(padx=5, pady=5)
        
        # Window selection button
        ttk.Button(window_frame, text="Select Game Window", 
                 command=self.start_window_selection).pack(fill=tk.X, pady=5)
                 
        # Create bar selection frame
        bars_frame = ttk.LabelFrame(main_frame, text="Bar Selection", padding=10)
        bars_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create bar selectors
        self.hp_bar = ScreenSelector(root)
        self.mp_bar = ScreenSelector(root)
        self.sp_bar = ScreenSelector(root)
        
        # Create bar detectors
        self.hp_detector = BarDetector("Health", HEALTH_COLOR_RANGE)
        self.mp_detector = BarDetector("Mana", MANA_COLOR_RANGE)
        self.sp_detector = BarDetector("Stamina", STAMINA_COLOR_RANGE)
        
        # Create preview area for each bar
        preview_frame = ttk.Frame(bars_frame)
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
        selection_buttons_frame = ttk.Frame(bars_frame)
        selection_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Health Bar", 
                 command=lambda: self.start_bar_selection("Health", "red")).pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Mana Bar", 
                 command=lambda: self.start_bar_selection("Mana", "blue")).pack(fill=tk.X, pady=5)
        
        ttk.Button(selection_buttons_frame, text="Select Stamina Bar", 
                 command=lambda: self.start_bar_selection("Stamina", "green")).pack(fill=tk.X, pady=5)
        
        # Create settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create percentage thresholds
        thresholds_frame = ttk.Frame(settings_frame)
        thresholds_frame.pack(fill=tk.X, pady=5)
        
        # HP threshold
        ttk.Label(thresholds_frame, text="Health %:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.hp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.hp_threshold.set(50)
        self.hp_threshold.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # MP threshold
        ttk.Label(thresholds_frame, text="Mana %:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.mp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.mp_threshold.set(30)
        self.mp_threshold.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # SP threshold
        ttk.Label(thresholds_frame, text="Stamina %:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.sp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.sp_threshold.set(40)
        self.sp_threshold.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Keys frame
        keys_frame = ttk.Frame(settings_frame)
        keys_frame.pack(fill=tk.X, pady=5)
        
        # HP key
        ttk.Label(keys_frame, text="Health Potion Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.hp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.hp_key.set("1")
        self.hp_key.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # MP key
        ttk.Label(keys_frame, text="Mana Potion Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.mp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.mp_key.set("3")
        self.mp_key.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # SP key
        ttk.Label(keys_frame, text="Stamina Potion Key:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.sp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.sp_key.set("2")
        self.sp_key.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # NEW: Spellcasting frame
        spellcast_frame = ttk.LabelFrame(settings_frame, text="Spellcasting", padding=10)
        spellcast_frame.pack(fill=tk.X, pady=5)
        
        # NEW: Enable spellcasting checkbox
        self.spellcast_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            spellcast_frame, 
            text="Enable Auto Spellcasting", 
            variable=self.spellcast_enabled
        ).pack(anchor=tk.W, pady=5)
        
        # NEW: Spell key selection
        spell_key_frame = ttk.Frame(spellcast_frame)
        spell_key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(spell_key_frame, text="Spell Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.spell_key = ttk.Combobox(
            spell_key_frame, 
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"], 
            width=5
        )
        self.spell_key.set("F5")
        self.spell_key.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # NEW: Spellcasting interval
        ttk.Label(spell_key_frame, text="Cast Interval (sec):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.spell_interval = ttk.Spinbox(spell_key_frame, from_=0.5, to=10.0, increment=0.5, width=5)
        self.spell_interval.set(3.0)
        self.spell_interval.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Advanced settings
        adv_frame = ttk.Frame(settings_frame)
        adv_frame.pack(fill=tk.X, pady=5)
        
        # Scan interval
        ttk.Label(adv_frame, text="Scan Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.scan_interval = ttk.Spinbox(adv_frame, from_=0.1, to=5.0, increment=0.1, width=5)
        self.scan_interval.set(0.5)
        self.scan_interval.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Debug mode checkbox
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Enable Debug Mode", variable=self.debug_var).pack(anchor=tk.W, pady=5)
        
        # Add Save Configuration button
        save_config_btn = ttk.Button(
            settings_frame, 
            text="Save Configuration", 
            command=self.save_bar_config
        )
        save_config_btn.pack(fill=tk.X, pady=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to configure")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10))
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Create buttons with normal styling to ensure text visibility
        self.start_button = tk.Button(
            control_frame, 
            text="START BOT",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",  # Green
            fg="white",
            command=self.start_bot, 
            state=tk.DISABLED,
            height=2
        )
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.stop_button = tk.Button(
            control_frame, 
            text="STOP BOT",
            font=("Arial", 12, "bold"),
            bg="#F44336",  # Red
            fg="white",
            command=self.stop_bot, 
            state=tk.DISABLED,
            height=2
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Log text - using scrolledtext for better handling
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=50, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, pady=5)
        
        # Bot variables
        self.running = False
        self.bot_thread = None
        
        # Initial log entry
        self.log("Bot GUI initialized successfully")
        
        # Try to load saved configuration
        if self.load_bar_config():
            self.log("Loaded saved configuration")
        else:
            self.log("No saved configuration found or loading failed")
            self.log("Please select the Health, Mana, and Stamina bars to continue")
        
        # Check if bars are configured periodically
        self.check_bar_config()
        
        # Set up window close handler to save configuration
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Bot GUI initialized")
        
    def on_closing(self):
        """Handle window closing event"""
        try:
            # Stop the bot if running
            if self.running:
                self.stop_bot()
                
            # Save configuration before exiting
            self.save_bar_config()
            logger.info("Configuration saved on exit")
            
            # Destroy the window
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error on closing: {e}", exc_info=True)
            self.root.destroy()
        
    def start_window_selection(self):
        """Start the game window selection process"""
        self.game_window = ScreenSelector(self.root)  # Recreate for fresh selection
        self.game_window.start_selection(title="Game Window", color="yellow")
        # Schedule an update to check if the selection was completed
        self.root.after(1000, self.update_window_preview)
    
    def update_window_preview(self):
        """Update the preview of the game window"""
        if self.game_window.is_setup():
            if hasattr(self.game_window, 'preview_image') and self.game_window.preview_image is not None:
                try:
                    # Resize the image to fit in the label
                    preview_size = (150, 100)  # Width, height
                    resized_img = self.game_window.preview_image.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.window_preview_label.config(image=preview_photo, text="")
                    self.window_preview_label.image = preview_photo  # Keep a reference
                    
                    self.log(f"Game window selected: ({self.game_window.x1},{self.game_window.y1}) to ({self.game_window.x2},{self.game_window.y2})")
                    
                    # Save the configuration automatically after selection
                    self.save_bar_config()
                except Exception as e:
                    logger.error(f"Error displaying window preview: {e}")
                    self.window_preview_label.config(text=f"Selected: ({self.game_window.x1},{self.game_window.y1}) to ({self.game_window.x2},{self.game_window.y2})")
            else:
                self.window_preview_label.config(text=f"Selected: ({self.game_window.x1},{self.game_window.y1}) to ({self.game_window.x2},{self.game_window.y2})")
        else:
            # Check again later
            self.root.after(1000, self.update_window_preview)
    
    def start_bar_selection(self, bar_type, color):
        """Start the selection process for a specific bar"""
        if bar_type == "Health":
            # Re-initialize the bar selector to ensure fresh selection
            self.hp_bar = ScreenSelector(self.root)
            self.hp_bar.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.hp_bar, self.hp_preview_label))
        elif bar_type == "Mana":
            # Re-initialize the bar selector to ensure fresh selection
            self.mp_bar = ScreenSelector(self.root)
            self.mp_bar.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.mp_bar, self.mp_preview_label))
        elif bar_type == "Stamina":
            # Re-initialize the bar selector to ensure fresh selection
            self.sp_bar = ScreenSelector(self.root)
            self.sp_bar.start_selection(title=f"{bar_type} Bar", color=color)
            # Schedule an update to check if the selection was completed
            self.root.after(1000, lambda: self.update_preview_image(self.sp_bar, self.sp_preview_label))
    
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
                    self.log(f"{selector.title} selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
                    
                    # Save the configuration automatically after selection
                    self.save_bar_config()
                    
                except Exception as e:
                    # If resize fails, show coords
                    logger.error(f"Error displaying preview image: {e}")
                    label.config(text=f"Selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
            else:
                # If no preview image yet, show coords
                label.config(text=f"Selected: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
        else:
            label.config(text="Not Selected")
            
            # Check again later
            self.root.after(1000, lambda: self.update_preview_image(selector, label))
    
    def check_bar_config(self):
        """Check if all bars are configured and enable the start button if they are"""
        # Count configured bars
        configured = sum([
            self.hp_bar.is_setup(),
            self.mp_bar.is_setup(),
            self.sp_bar.is_setup()
        ])
        
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
    
    def log(self, message):
        """Add a message to the log display"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        # Also log to the logger
        logger.info(message)
    
    def bot_loop(self):
        """Main bot loop that checks bars and uses potions"""
        last_hp_potion = 0
        last_mp_potion = 0
        last_sp_potion = 0
        last_spell_cast = 0
        potion_cooldown = 3.0  # seconds
        loop_count = 0
        
        self.log("Bot started")
        self.status_var.set("Bot is running")
        logger.info("Bot loop started")
        
        # NEW: Check if spellcasting is enabled and log it
        if self.spellcast_enabled.get():
            self.log(f"Auto spellcasting enabled with key {self.spell_key.get()} at {self.spell_interval.get()}s interval")
            logger.info(f"Spellcasting enabled: Key={self.spell_key.get()}, Interval={self.spell_interval.get()}s")
        
        while self.running:
            try:
                loop_count += 1
                logger.debug(f"Bot loop iteration {loop_count}")
                
                # Get current time for potion cooldowns
                current_time = time.time()
                
                # Initialize status values
                hp_percent = 100.0
                mp_percent = 100.0
                sp_percent = 100.0
                hp_threshold = float(self.hp_threshold.get())
                mp_threshold = float(self.mp_threshold.get())
                sp_threshold = float(self.sp_threshold.get())
                
                # Check HP bar
                if self.hp_bar.is_setup():
                    hp_image = self.hp_bar.get_current_screenshot_region()
                    if hp_image:
                        hp_percent = self.hp_detector.detect_percentage(hp_image)
                
                # Check MP bar
                if self.mp_bar.is_setup():
                    mp_image = self.mp_bar.get_current_screenshot_region()
                    if mp_image:
                        mp_percent = self.mp_detector.detect_percentage(mp_image)
                
                # Check SP bar
                if self.sp_bar.is_setup():
                    sp_image = self.sp_bar.get_current_screenshot_region()
                    if sp_image:
                        sp_percent = self.sp_detector.detect_percentage(sp_image)
                
                # Log all percentages in a single line
                status_message = f"Health: {hp_percent:.1f}% (Thrs: {hp_threshold}%) | Mana: {mp_percent:.1f}% (Thrs: {mp_threshold}%) | Stamina: {sp_percent:.1f}% (Thrs: {sp_threshold}%)"
                self.log(status_message)
                logger.debug(status_message)
                
                # Use Health potion if needed
                if hp_percent < hp_threshold and current_time - last_hp_potion > potion_cooldown:
                    self.log(f"Health low ({hp_percent:.1f}%), using health potion (key {self.hp_key.get()})")
                    logger.info(f"Using health potion - HP: {hp_percent:.1f}% < {hp_threshold}%")
                    press_key(None, self.hp_key.get())
                    last_hp_potion = current_time
                
                # Use Mana potion if needed
                if mp_percent < mp_threshold and current_time - last_mp_potion > potion_cooldown:
                    self.log(f"Mana low ({mp_percent:.1f}%), using mana potion (key {self.mp_key.get()})")
                    logger.info(f"Using mana potion - MP: {mp_percent:.1f}% < {mp_threshold}%")
                    press_key(None, self.mp_key.get())
                    last_mp_potion = current_time
                
                # Use Stamina potion if needed
                if sp_percent < sp_threshold and current_time - last_sp_potion > potion_cooldown:
                    self.log(f"Stamina low ({sp_percent:.1f}%), using stamina potion (key {self.sp_key.get()})")
                    logger.info(f"Using stamina potion - SP: {sp_percent:.1f}% < {sp_threshold}%")
                    press_key(None, self.sp_key.get())
                    last_sp_potion = current_time
                
                # NEW: Check if spellcasting is enabled and it's time to cast
                if self.spellcast_enabled.get():
                    spell_interval = float(self.spell_interval.get())
                    if current_time - last_spell_cast > spell_interval:
                        spell_key = self.spell_key.get()
                        self.log(f"Casting spell ({spell_key})")
                        logger.info(f"Casting spell with key {spell_key}")
                        
                        # Press the spell key
                        press_key(None, spell_key)
                        
                        # Small delay before right-clicking
                        time.sleep(0.1)
                        
                        # Press right mouse button
                        logger.debug("Calling press_right_mouse(None) for spellcasting")
                        press_right_mouse(None)
                        
                        last_spell_cast = current_time
                
                # Wait for next scan
                scan_interval = float(self.scan_interval.get())
                time.sleep(scan_interval)
                
            except Exception as e:
                self.log(f"Error in bot loop: {e}")
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(1)
        
        self.log("Bot stopped")
        self.status_var.set("Bot is stopped")
        logger.info("Bot loop stopped")
    
    def start_bot(self):
        """Start the bot"""
        if self.running:
            logger.info("Start button clicked, but bot is already running")
            return
        
        # Save current settings before starting
        self.save_bar_config()
        
        self.log("Starting bot...")
        self.running = True
        self.bot_thread = threading.Thread(target=self.bot_loop)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        logger.info("Bot thread started")
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
    
    def stop_bot(self):
        """Stop the bot"""
        if not self.running:
            logger.info("Stop button clicked, but bot is not running")
            return
        
        self.log("Stopping bot...")
        self.running = False
        if self.bot_thread:
            self.bot_thread.join(1.0)
            logger.info("Bot thread joined")
        
        # Save settings after stopping the bot
        self.save_bar_config()
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def save_bar_config(self):
        """Save bar configuration to config file"""
        try:
            # Load current config
            config = load_config()
            
            # Save game window coordinates
            if self.game_window.is_setup():
                config["bars"]["game_window"]["x1"] = self.game_window.x1
                config["bars"]["game_window"]["y1"] = self.game_window.y1
                config["bars"]["game_window"]["x2"] = self.game_window.x2
                config["bars"]["game_window"]["y2"] = self.game_window.y2
                config["bars"]["game_window"]["configured"] = True
                logger.info("Saved game window configuration")
            
            # Save health bar coordinates
            if self.hp_bar.is_setup():
                config["bars"]["health_bar"]["x1"] = self.hp_bar.x1
                config["bars"]["health_bar"]["y1"] = self.hp_bar.y1
                config["bars"]["health_bar"]["x2"] = self.hp_bar.x2
                config["bars"]["health_bar"]["y2"] = self.hp_bar.y2
                config["bars"]["health_bar"]["configured"] = True
                logger.info("Saved health bar configuration")
            
            # Save mana bar coordinates
            if self.mp_bar.is_setup():
                config["bars"]["mana_bar"]["x1"] = self.mp_bar.x1
                config["bars"]["mana_bar"]["y1"] = self.mp_bar.y1
                config["bars"]["mana_bar"]["x2"] = self.mp_bar.x2
                config["bars"]["mana_bar"]["y2"] = self.mp_bar.y2
                config["bars"]["mana_bar"]["configured"] = True
                logger.info("Saved mana bar configuration")
            
            # Save stamina bar coordinates
            if self.sp_bar.is_setup():
                config["bars"]["stamina_bar"]["x1"] = self.sp_bar.x1
                config["bars"]["stamina_bar"]["y1"] = self.sp_bar.y1
                config["bars"]["stamina_bar"]["x2"] = self.sp_bar.x2
                config["bars"]["stamina_bar"]["y2"] = self.sp_bar.y2
                config["bars"]["stamina_bar"]["configured"] = True
                logger.info("Saved stamina bar configuration")
            
            # Save potion key settings
            config["potion_keys"]["health"] = self.hp_key.get()
            config["potion_keys"]["mana"] = self.mp_key.get()
            config["potion_keys"]["stamina"] = self.sp_key.get()
            
            # Save threshold settings
            config["thresholds"]["health"] = float(self.hp_threshold.get())
            config["thresholds"]["mana"] = float(self.mp_threshold.get())
            config["thresholds"]["stamina"] = float(self.sp_threshold.get())
            
            # Save scan interval
            config["scan_interval"] = float(self.scan_interval.get())
            
            # Save debug mode
            config["debug_enabled"] = self.debug_var.get()
            
            # Save spellcasting settings
            config["spellcasting"]["enabled"] = self.spellcast_enabled.get()
            config["spellcasting"]["spell_key"] = self.spell_key.get()
            config["spellcasting"]["spell_interval"] = float(self.spell_interval.get())
            
            # Save the config
            save_config(config)
            self.log("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            self.log(f"Error saving configuration: {e}")
    
    def load_bar_config(self):
        """Load bar configuration from config file"""
        try:
            # Load config
            config = load_config()
            bars_config = config.get("bars", {})
            
            # Check if there's a saved configuration
            if not bars_config:
                logger.info("No saved bar configuration found")
                return False
            
            bars_configured = 0
            
            # Load game window
            game_window_config = bars_config.get("game_window", {})
            if game_window_config.get("configured", False):
                self.game_window.configure_from_saved(
                    game_window_config.get("x1"),
                    game_window_config.get("y1"),
                    game_window_config.get("x2"),
                    game_window_config.get("y2")
                )
                
                # Try to update preview
                try:
                    # Create a screenshot for the preview
                    screenshot = ImageGrab.grab(bbox=(
                        self.game_window.x1, 
                        self.game_window.y1, 
                        self.game_window.x2, 
                        self.game_window.y2
                    ))
                    self.game_window.preview_image = screenshot
                    
                    # Resize for display
                    preview_size = (150, 100)
                    resized_img = screenshot.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.window_preview_label.config(image=preview_photo, text="")
                    self.window_preview_label.image = preview_photo
                    
                    self.log(f"Loaded game window: ({self.game_window.x1},{self.game_window.y1}) to ({self.game_window.x2},{self.game_window.y2})")
                except Exception as e:
                    logger.error(f"Error loading game window preview: {e}")
                    self.window_preview_label.config(text=f"Loaded: ({self.game_window.x1},{self.game_window.y1}) to ({self.game_window.x2},{self.game_window.y2})")
            
            # Load health bar
            hp_config = bars_config.get("health_bar", {})
            if hp_config.get("configured", False):
                self.hp_bar.configure_from_saved(
                    hp_config.get("x1"),
                    hp_config.get("y1"),
                    hp_config.get("x2"),
                    hp_config.get("y2")
                )
                bars_configured += 1
                
                # Try to update preview
                try:
                    # Create a screenshot for the preview
                    screenshot = ImageGrab.grab(bbox=(
                        self.hp_bar.x1, 
                        self.hp_bar.y1, 
                        self.hp_bar.x2, 
                        self.hp_bar.y2
                    ))
                    self.hp_bar.preview_image = screenshot
                    
                    # Resize for display
                    preview_size = (120, 30)
                    resized_img = screenshot.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.hp_preview_label.config(image=preview_photo, text="")
                    self.hp_preview_label.image = preview_photo
                    
                    self.log(f"Loaded health bar: ({self.hp_bar.x1},{self.hp_bar.y1}) to ({self.hp_bar.x2},{self.hp_bar.y2})")
                except Exception as e:
                    logger.error(f"Error loading health bar preview: {e}")
                    self.hp_preview_label.config(text=f"Loaded: ({self.hp_bar.x1},{self.hp_bar.y1}) to ({self.hp_bar.x2},{self.hp_bar.y2})")
            
            # Load mana bar
            mp_config = bars_config.get("mana_bar", {})
            if mp_config.get("configured", False):
                self.mp_bar.configure_from_saved(
                    mp_config.get("x1"),
                    mp_config.get("y1"),
                    mp_config.get("x2"),
                    mp_config.get("y2")
                )
                bars_configured += 1
                
                # Try to update preview
                try:
                    # Create a screenshot for the preview
                    screenshot = ImageGrab.grab(bbox=(
                        self.mp_bar.x1, 
                        self.mp_bar.y1, 
                        self.mp_bar.x2, 
                        self.mp_bar.y2
                    ))
                    self.mp_bar.preview_image = screenshot
                    
                    # Resize for display
                    preview_size = (120, 30)
                    resized_img = screenshot.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.mp_preview_label.config(image=preview_photo, text="")
                    self.mp_preview_label.image = preview_photo
                    
                    self.log(f"Loaded mana bar: ({self.mp_bar.x1},{self.mp_bar.y1}) to ({self.mp_bar.x2},{self.mp_bar.y2})")
                except Exception as e:
                    logger.error(f"Error loading mana bar preview: {e}")
                    self.mp_preview_label.config(text=f"Loaded: ({self.mp_bar.x1},{self.mp_bar.y1}) to ({self.mp_bar.x2},{self.mp_bar.y2})")
            
            # Load stamina bar
            sp_config = bars_config.get("stamina_bar", {})
            if sp_config.get("configured", False):
                self.sp_bar.configure_from_saved(
                    sp_config.get("x1"),
                    sp_config.get("y1"),
                    sp_config.get("x2"),
                    sp_config.get("y2")
                )
                bars_configured += 1
                
                # Try to update preview
                try:
                    # Create a screenshot for the preview
                    screenshot = ImageGrab.grab(bbox=(
                        self.sp_bar.x1, 
                        self.sp_bar.y1, 
                        self.sp_bar.x2, 
                        self.sp_bar.y2
                    ))
                    self.sp_bar.preview_image = screenshot
                    
                    # Resize for display
                    preview_size = (120, 30)
                    resized_img = screenshot.resize(preview_size, Image.LANCZOS)
                    preview_photo = ImageTk.PhotoImage(resized_img)
                    self.sp_preview_label.config(image=preview_photo, text="")
                    self.sp_preview_label.image = preview_photo
                    
                    self.log(f"Loaded stamina bar: ({self.sp_bar.x1},{self.sp_bar.y1}) to ({self.sp_bar.x2},{self.sp_bar.y2})")
                except Exception as e:
                    logger.error(f"Error loading stamina bar preview: {e}")
                    self.sp_preview_label.config(text=f"Loaded: ({self.sp_bar.x1},{self.sp_bar.y1}) to ({self.sp_bar.x2},{self.sp_bar.y2})")
            
            # Load other settings
            # Potion keys
            potion_keys = config.get("potion_keys", {})
            self.hp_key.set(potion_keys.get("health", "1"))
            self.mp_key.set(potion_keys.get("mana", "3"))
            self.sp_key.set(potion_keys.get("stamina", "2"))
            
            # Thresholds
            thresholds = config.get("thresholds", {})
            self.hp_threshold.set(thresholds.get("health", 50))
            self.mp_threshold.set(thresholds.get("mana", 30))
            self.sp_threshold.set(thresholds.get("stamina", 40))
            
            # Scan interval
            self.scan_interval.set(config.get("scan_interval", 0.5))
            
            # Debug mode
            self.debug_var.set(config.get("debug_enabled", True))
            
            # Spellcasting settings
            spellcasting = config.get("spellcasting", {})
            self.spellcast_enabled.set(spellcasting.get("enabled", False))
            self.spell_key.set(spellcasting.get("spell_key", "F5"))
            self.spell_interval.set(spellcasting.get("spell_interval", 3.0))
            
            # Return success if any bars were configured
            if bars_configured > 0:
                self.log(f"Loaded {bars_configured}/3 bars from saved configuration")
                logger.info(f"Loaded {bars_configured}/3 bars from saved configuration")
                return True
            else:
                logger.info("No bar configurations loaded")
                return False
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.log(f"Error loading configuration: {e}")
            return False
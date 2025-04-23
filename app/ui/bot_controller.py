"""
Improved Bot Controller UI for the Priston Tale Potion Bot
-------------------------------------------------------
This module handles the bot control UI with better visibility
and practical monitoring features in a single window.
"""

import tkinter as tk
from tkinter import ttk
import logging
import threading
import time
from app.window_utils import press_key, press_right_mouse
from app.bar_selector import BarDetector, HEALTH_COLOR_RANGE, MANA_COLOR_RANGE, STAMINA_COLOR_RANGE

logger = logging.getLogger('PristonBot')

class BotControllerUI:
    """Class that handles the bot control UI and logic with improved visibility"""
    
    def __init__(self, parent, root, hp_bar, mp_bar, sp_bar, settings_ui, log_callback):
        """
        Initialize the bot controller UI
        
        Args:
            parent: Parent frame to place UI elements
            root: Tkinter root window
            hp_bar: Health bar selector
            mp_bar: Mana bar selector
            sp_bar: Stamina bar selector
            settings_ui: Settings UI instance
            log_callback: Function to call for logging
        """
        self.parent = parent
        self.root = root
        self.hp_bar = hp_bar
        self.mp_bar = mp_bar
        self.sp_bar = sp_bar
        self.settings_ui = settings_ui
        self.log_callback = log_callback
        
        # Create detectors
        self.hp_detector = BarDetector("Health", HEALTH_COLOR_RANGE)
        self.mp_detector = BarDetector("Mana", MANA_COLOR_RANGE)
        self.sp_detector = BarDetector("Stamina", STAMINA_COLOR_RANGE)
        
        # Bot state
        self.running = False
        self.bot_thread = None
        
        # Store previous bar values to detect changes
        self.prev_hp_percent = 100.0
        self.prev_mp_percent = 100.0
        self.prev_sp_percent = 100.0
        
        # Statistics
        self.hp_potions_used = 0
        self.mp_potions_used = 0
        self.sp_potions_used = 0
        self.spells_cast = 0
        self.start_time = None
        
        # Create the UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components with improved layout"""
        # Status section
        status_frame = ttk.Frame(self.parent)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to configure")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Current values section
        values_frame = ttk.Frame(self.parent)
        values_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Two-column layout for current values
        values_left = ttk.Frame(values_frame)
        values_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        values_right = ttk.Frame(values_frame)
        values_right.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # HP current value
        hp_frame = ttk.Frame(values_left)
        hp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(hp_frame, text="Health:", foreground="#e74c3c", width=10).pack(side=tk.LEFT)
        self.hp_value_var = tk.StringVar(value="100.0%")
        ttk.Label(hp_frame, textvariable=self.hp_value_var).pack(side=tk.LEFT)
        
        # MP current value
        mp_frame = ttk.Frame(values_left)
        mp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mp_frame, text="Mana:", foreground="#3498db", width=10).pack(side=tk.LEFT)
        self.mp_value_var = tk.StringVar(value="100.0%")
        ttk.Label(mp_frame, textvariable=self.mp_value_var).pack(side=tk.LEFT)
        
        # HP potions used
        hp_pot_frame = ttk.Frame(values_right)
        hp_pot_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(hp_pot_frame, text="HP Potions:", width=12).pack(side=tk.LEFT)
        self.hp_potions_var = tk.StringVar(value="0")
        ttk.Label(hp_pot_frame, textvariable=self.hp_potions_var).pack(side=tk.LEFT)
        
        # MP potions used
        mp_pot_frame = ttk.Frame(values_right)
        mp_pot_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mp_pot_frame, text="MP Potions:", width=12).pack(side=tk.LEFT)
        self.mp_potions_var = tk.StringVar(value="0")
        ttk.Label(mp_pot_frame, textvariable=self.mp_potions_var).pack(side=tk.LEFT)
        
        # SP current value
        sp_frame = ttk.Frame(values_left)
        sp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sp_frame, text="Stamina:", foreground="#2ecc71", width=10).pack(side=tk.LEFT)
        self.sp_value_var = tk.StringVar(value="100.0%")
        ttk.Label(sp_frame, textvariable=self.sp_value_var).pack(side=tk.LEFT)
        
        # Runtime display
        runtime_frame = ttk.Frame(values_left)
        runtime_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(runtime_frame, text="Runtime:", width=10).pack(side=tk.LEFT)
        self.runtime_var = tk.StringVar(value="00:00:00")
        ttk.Label(runtime_frame, textvariable=self.runtime_var).pack(side=tk.LEFT)
        
        # SP potions used
        sp_pot_frame = ttk.Frame(values_right)
        sp_pot_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sp_pot_frame, text="SP Potions:", width=12).pack(side=tk.LEFT)
        self.sp_potions_var = tk.StringVar(value="0")
        ttk.Label(sp_pot_frame, textvariable=self.sp_potions_var).pack(side=tk.LEFT)
        
        # Spells cast
        spell_frame = ttk.Frame(values_right)
        spell_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(spell_frame, text="Spells Cast:", width=12).pack(side=tk.LEFT)
        self.spells_var = tk.StringVar(value="0")
        ttk.Label(spell_frame, textvariable=self.spells_var).pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Create custom button styles with Tkinter for more control and visibility
        self.start_button = tk.Button(
            button_frame, 
            text="START BOT",
            command=self.start_bot, 
            bg="#4CAF50",  # Green background
            fg="black",    # Black text (more visible)
            font=("Arial", 12, "bold"),
            height=2,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stop_button = tk.Button(
            button_frame, 
            text="STOP BOT",
            command=self.stop_bot, 
            bg="#F44336",  # Red background
            fg="black",    # Black text (more visible)
            font=("Arial", 12, "bold"),
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def start_bot(self):
        """Start the bot"""
        if self.running:
            logger.info("Start button clicked, but bot is already running")
            return
        
        self.log_callback("Starting bot...")
        self.running = True
        
        # Reset statistics
        self.hp_potions_used = 0
        self.mp_potions_used = 0
        self.sp_potions_used = 0
        self.spells_cast = 0
        
        self.hp_potions_var.set("0")
        self.mp_potions_var.set("0")
        self.sp_potions_var.set("0")
        self.spells_var.set("0")
        
        # Store start time
        self.start_time = time.time()
        
        # Start runtime updater
        self._update_runtime()
        
        # Start the bot thread
        self.bot_thread = threading.Thread(target=self.bot_loop)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        logger.info("Bot thread started")
        
        # Update button states
        self.start_button.config(state=tk.DISABLED, bg="#a0a0a0")  # Gray out when disabled
        self.stop_button.config(state=tk.NORMAL, bg="#F44336")
        
        # Update status
        self.status_var.set("Bot is running")
    
    def stop_bot(self):
        """Stop the bot"""
        if not self.running:
            logger.info("Stop button clicked, but bot is not running")
            return
        
        self.log_callback("Stopping bot...")
        self.running = False
        if self.bot_thread:
            self.bot_thread.join(1.0)
            logger.info("Bot thread joined")
        
        # Update button states
        self.start_button.config(state=tk.NORMAL, bg="#4CAF50")
        self.stop_button.config(state=tk.DISABLED, bg="#a0a0a0")  # Gray out when disabled
        
        # Update status
        self.status_var.set("Bot is stopped")
    
    def _update_runtime(self):
        """Update the runtime display"""
        if self.running and self.start_time:
            # Calculate elapsed time
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            # Update display
            self.runtime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Schedule next update
            self.root.after(1000, self._update_runtime)
    
    def enable_start_button(self):
        """Enable the start button"""
        self.start_button.config(state=tk.NORMAL, bg="#4CAF50")
        self.status_var.set("Ready to start")
    
    def disable_start_button(self):
        """Disable the start button"""
        self.start_button.config(state=tk.DISABLED, bg="#a0a0a0")
    
    def set_status(self, message):
        """Set the status message"""
        self.status_var.set(message)
    
    def has_value_changed(self, prev_val, current_val, threshold=0.5):
        """
        Check if a value has changed beyond a threshold
        
        Args:
            prev_val: Previous value
            current_val: Current value
            threshold: Change threshold (default 0.5%)
            
        Returns:
            True if the value has changed beyond the threshold
        """
        return abs(prev_val - current_val) >= threshold
    
    def bot_loop(self):
        """Main bot loop that checks bars and uses potions"""
        last_hp_potion = 0
        last_mp_potion = 0
        last_sp_potion = 0
        last_spell_cast = 0
        potion_cooldown = 3.0  # seconds
        loop_count = 0
        
        self.log_callback("Bot started")
        logger.info("Bot loop started")
        
        # Get the settings
        settings = self.settings_ui.get_settings()
        
        # Check if spellcasting is enabled and log it
        if settings["spellcasting"]["enabled"]:
            self.log_callback(f"Auto spellcasting enabled with key {settings['spellcasting']['spell_key']} " + 
                             f"at {settings['spellcasting']['spell_interval']}s interval")
            logger.info(f"Spellcasting enabled: Key={settings['spellcasting']['spell_key']}, " + 
                        f"Interval={settings['spellcasting']['spell_interval']}s")
        
        # Log initial values
        status_message = (f"Health: {self.prev_hp_percent:.1f}% | " +
                         f"Mana: {self.prev_mp_percent:.1f}% | " +
                         f"Stamina: {self.prev_sp_percent:.1f}%")
        self.log_callback(status_message)
        
        while self.running:
            try:
                loop_count += 1
                logger.debug(f"Bot loop iteration {loop_count}")
                
                # Get current time for potion cooldowns
                current_time = time.time()
                
                # Get the latest settings
                settings = self.settings_ui.get_settings()
                
                # Initialize status values
                hp_percent = 100.0
                mp_percent = 100.0
                sp_percent = 100.0
                hp_threshold = settings["thresholds"]["health"]
                mp_threshold = settings["thresholds"]["mana"]
                sp_threshold = settings["thresholds"]["stamina"]
                
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
                
                # Check if any values have changed
                hp_changed = self.has_value_changed(self.prev_hp_percent, hp_percent)
                mp_changed = self.has_value_changed(self.prev_mp_percent, mp_percent)
                sp_changed = self.has_value_changed(self.prev_sp_percent, sp_percent)
                
                # Log all percentages in a single line if any have changed
                if hp_changed or mp_changed or sp_changed:
                    status_message = (f"Health: {hp_percent:.1f}% | " +
                                     f"Mana: {mp_percent:.1f}% | " +
                                     f"Stamina: {sp_percent:.1f}%")
                    self.log_callback(status_message)
                    logger.debug(status_message)
                    
                    # Update previous values
                    self.prev_hp_percent = hp_percent
                    self.prev_mp_percent = mp_percent
                    self.prev_sp_percent = sp_percent
                    
                    # Update UI values
                    self.hp_value_var.set(f"{hp_percent:.1f}%")
                    self.mp_value_var.set(f"{mp_percent:.1f}%")
                    self.sp_value_var.set(f"{sp_percent:.1f}%")
                
                # Use Health potion if needed
                if hp_percent < hp_threshold and current_time - last_hp_potion > potion_cooldown:
                    hp_key = settings["potion_keys"]["health"]
                    self.log_callback(f"Health low ({hp_percent:.1f}%), using health potion (key {hp_key})")
                    logger.info(f"Using health potion - HP: {hp_percent:.1f}% < {hp_threshold}%")
                    press_key(None, hp_key)
                    last_hp_potion = current_time
                    
                    # Update statistics
                    self.hp_potions_used += 1
                    self.hp_potions_var.set(str(self.hp_potions_used))
                
                # Use Mana potion if needed
                if mp_percent < mp_threshold and current_time - last_mp_potion > potion_cooldown:
                    mp_key = settings["potion_keys"]["mana"]
                    self.log_callback(f"Mana low ({mp_percent:.1f}%), using mana potion (key {mp_key})")
                    logger.info(f"Using mana potion - MP: {mp_percent:.1f}% < {mp_threshold}%")
                    press_key(None, mp_key)
                    last_mp_potion = current_time
                    
                    # Update statistics
                    self.mp_potions_used += 1
                    self.mp_potions_var.set(str(self.mp_potions_used))
                
                # Use Stamina potion if needed
                if sp_percent < sp_threshold and current_time - last_sp_potion > potion_cooldown:
                    sp_key = settings["potion_keys"]["stamina"]
                    self.log_callback(f"Stamina low ({sp_percent:.1f}%), using stamina potion (key {sp_key})")
                    logger.info(f"Using stamina potion - SP: {sp_percent:.1f}% < {sp_threshold}%")
                    press_key(None, sp_key)
                    last_sp_potion = current_time
                    
                    # Update statistics
                    self.sp_potions_used += 1
                    self.sp_potions_var.set(str(self.sp_potions_used))
                
                # Check if spellcasting is enabled and it's time to cast
                if settings["spellcasting"]["enabled"]:
                    spell_interval = settings["spellcasting"]["spell_interval"]
                    if current_time - last_spell_cast > spell_interval:
                        spell_key = settings["spellcasting"]["spell_key"]
                        self.log_callback(f"Casting spell ({spell_key})")
                        logger.info(f"Casting spell with key {spell_key}")
                        
                        # Press the spell key
                        press_key(None, spell_key)
                        
                        # Small delay before right-clicking
                        time.sleep(0.1)
                        
                        # Press right mouse button
                        logger.debug("Calling press_right_mouse(None) for spellcasting")
                        press_right_mouse(None)
                        
                        last_spell_cast = current_time
                        
                        # Update statistics
                        self.spells_cast += 1
                        self.spells_var.set(str(self.spells_cast))
                
                # Wait for next scan
                scan_interval = settings["scan_interval"]
                time.sleep(scan_interval)
                
            except Exception as e:
                self.log_callback(f"Error in bot loop: {e}")
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(1)
        
        self.log_callback("Bot stopped")
        logger.info("Bot loop stopped")
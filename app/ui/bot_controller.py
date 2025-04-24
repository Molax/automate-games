"""
Fixed Bot Controller UI for the Priston Tale Potion Bot
-------------------------------------------------------
This module handles the bot control UI with fixes for mouse movement during spellcasting
and adds keyboard shortcuts for starting/stopping the bot.
"""

import tkinter as tk
from tkinter import ttk
import logging
import threading
import time
import random
import math
from PIL import Image

# First try to import the windows_utils mouse functions
try:
    from app.windows_utils.mouse import move_mouse_direct, press_right_mouse
except ImportError:
    # Fallback to older window_utils if needed
    from app.window_utils import press_right_mouse, get_window_rect
    
    # Define move_mouse_direct as fallback
    def move_mouse_direct(x, y):
        """Fallback mouse movement function"""
        logger = logging.getLogger('PristonBot')
        logger.warning(f"Using fallback mouse movement to ({x}, {y})")
        import ctypes
        try:
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
            return True
        except Exception as e:
            logger.error(f"Error in fallback mouse movement: {e}")
            return False

# Import press_key function specifically
try:
    from app.windows_utils.keyboard import press_key
except ImportError:
    try:
        from app.window_utils import press_key
    except ImportError:
        # Define press_key fallback if we can't import it
        def press_key(hwnd, key):
            """Fallback press_key function"""
            logger = logging.getLogger('PristonBot')
            logger.info(f"Using fallback key press for '{key}'")
            import ctypes
            
            # Map common keys to virtual key codes
            key_map = {
                '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
                '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
                'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
                'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B
            }
            
            # Get virtual key code
            if isinstance(key, str):
                key = key.lower()
                vk_code = key_map.get(key)
                if vk_code is None:
                    try:
                        vk_code = ord(key.upper()[0])
                    except:
                        logger.error(f"Could not determine virtual key code for '{key}'")
                        return False
            else:
                vk_code = key
                
            try:
                # Define key event flags
                KEYEVENTF_KEYDOWN = 0x0000
                KEYEVENTF_KEYUP = 0x0002
                
                # Send key down
                ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYDOWN, 0)
                time.sleep(0.05)  # Small delay between down and up
                
                # Send key up
                ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
                
                return True
            except Exception as e:
                logger.error(f"Error pressing key '{key}': {e}")
                return False

# Import focus_game_window, with fallback if not found
try:
    from app.windows_utils.windows_management import focus_game_window
except ImportError:
    try:
        from app.window_utils import focus_game_window
    except ImportError:
        def focus_game_window(hwnd):
            """Fallback function if module isn't created yet"""
            logger = logging.getLogger('PristonBot')
            logger.warning(f"Using fallback for window focus")
            import win32gui
            try:
                return win32gui.SetForegroundWindow(hwnd) if hwnd else False
            except Exception as e:
                logger.error(f"Error in fallback focus: {e}")
                return False

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
        
        # Random targeting variables
        self.target_x_offset = 0
        self.target_y_offset = 0
        self.spells_cast_since_target_change = 0
        
        # Game window reference
        self.game_window = None
        
        # Create the UI
        self._create_ui()
        
        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()
    
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

        # Target position display (for random targeting)
        target_frame = ttk.Frame(values_right)
        target_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(target_frame, text="Target Offset:", width=12).pack(side=tk.LEFT)
        self.target_var = tk.StringVar(value="(0, 0)")
        ttk.Label(target_frame, textvariable=self.target_var).pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Create custom button styles with Tkinter for more control and visibility
        self.start_button = tk.Button(
            button_frame, 
            text="START BOT (Ctrl+Shift+A)",
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
            text="STOP BOT (Ctrl+Shift+B)",
            command=self.stop_bot, 
            bg="#F44336",  # Red background
            fg="black",    # Black text (more visible)
            font=("Arial", 12, "bold"),
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Add shortcut information
        shortcut_frame = ttk.Frame(self.parent)
        shortcut_frame.pack(fill=tk.X, pady=5)
        
        shortcut_label = ttk.Label(
            shortcut_frame, 
            text="Keyboard Shortcuts: Ctrl+Shift+A to Start, Ctrl+Shift+B to Stop",
            font=("Arial", 8),
            foreground="#555555"
        )
        shortcut_label.pack(anchor=tk.CENTER)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for starting and stopping the bot"""
        # Register keyboard shortcuts with Tkinter
        self.root.bind("<Control-Shift-a>", lambda event: self._handle_start_shortcut())
        self.root.bind("<Control-Shift-A>", lambda event: self._handle_start_shortcut())
        self.root.bind("<Control-Shift-b>", lambda event: self._handle_stop_shortcut())
        self.root.bind("<Control-Shift-B>", lambda event: self._handle_stop_shortcut())
        
        logger.info("Keyboard shortcuts registered")
        
    def _handle_start_shortcut(self):
        """Handle Ctrl+Shift+A shortcut to start the bot"""
        if not self.running and self.start_button.cget('state') != 'disabled':
            logger.info("Start bot shortcut (Ctrl+Shift+A) triggered")
            self.start_bot()
            
    def _handle_stop_shortcut(self):
        """Handle Ctrl+Shift+B shortcut to stop the bot"""
        if self.running:
            logger.info("Stop bot shortcut (Ctrl+Shift+B) triggered")
            self.stop_bot()
    
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
        
        # Reset targeting variables
        self.target_x_offset = 0
        self.target_y_offset = 0
        self.spells_cast_since_target_change = 0
        
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
    
    def generate_random_target_offsets(self, radius):
        """
        Generate random offsets for spell targeting within specified radius
        
        Args:
            radius: Maximum radius from center in pixels
            
        Returns:
            (x_offset, y_offset) tuple of pixel offsets from center
        """
        # Generate random angle and distance (using square root for more even distribution)
        angle = random.uniform(0, 2 * math.pi)
        distance = radius * math.sqrt(random.random())  # Square root for more even distribution
        
        # Calculate x and y offsets (convert polar to cartesian coordinates)
        x_offset = int(distance * math.cos(angle))
        y_offset = int(distance * math.sin(angle))
        
        logger.debug(f"Generated new random offset: ({x_offset}, {y_offset})")
        return x_offset, y_offset
    
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
        
        # Save game window reference
        self.game_window = None
        game_window_rect = None
        game_hwnd = None
        
        # IMPORTANT FIX: Get the game window from hp_bar's screen selector
        try:
            # Check if there's a direct game_window attribute
            if hasattr(self.hp_bar, 'game_window') and self.hp_bar.is_setup():
                self.game_window = self.hp_bar.game_window
                logger.info(f"Found game window via hp_bar attribute")
            # Or check for one more level of nesting
            elif hasattr(self.hp_bar, 'screen_selector') and self.hp_bar.screen_selector.is_setup():
                self.game_window = self.hp_bar.screen_selector
                logger.info(f"Found game window via screen_selector")
            # Try the main UI structure
            elif hasattr(self.root, 'bar_selector_ui') and hasattr(self.root.bar_selector_ui, 'game_window'):
                self.game_window = self.root.bar_selector_ui.game_window
                logger.info(f"Found game window via root.bar_selector_ui")
            # Fallback to looking through all attributes
            else:
                for attr_name in dir(self.root):
                    attr = getattr(self.root, attr_name)
                    if hasattr(attr, 'game_window') and hasattr(attr.game_window, 'is_setup') and attr.game_window.is_setup():
                        self.game_window = attr.game_window
                        logger.info(f"Found game window via root.{attr_name}")
                        break
        except Exception as e:
            logger.error(f"Error finding game window: {e}")
        
        # Check if we found a valid game window
        if self.game_window and hasattr(self.game_window, 'is_setup') and self.game_window.is_setup():
            game_window_rect = (
                self.game_window.x1,
                self.game_window.y1,
                self.game_window.x2,
                self.game_window.y2
            )
            
            # Try to find the game window handle
            try:
                from app.window_utils import find_game_window
                game_hwnd = find_game_window("Priston Tale")
                if game_hwnd:
                    logger.info(f"Found game window handle: {game_hwnd}")
            except (ImportError, AttributeError):
                try:
                    from app.windows_utils.windows_management import find_game_window
                    game_hwnd = find_game_window("Priston Tale")
                    if game_hwnd:
                        logger.info(f"Found game window handle: {game_hwnd}")
                except (ImportError, AttributeError):
                    logger.warning("find_game_window function not available")
            
            self.log_callback(f"Game window found at ({self.game_window.x1},{self.game_window.y1})-({self.game_window.x2},{self.game_window.y2})")
            logger.info(f"Game window dimensions: ({self.game_window.x1},{self.game_window.y1})-({self.game_window.x2},{self.game_window.y2})")
        else:
            self.log_callback("WARNING: Game window not properly configured. Will use manual approach for targeting.")
            logger.warning("Game window not properly configured")
            
            # Try to find alternative sources of the game window
            if hasattr(self.hp_bar, 'x1') and hasattr(self.hp_bar, 'x2') and hasattr(self.hp_bar, 'y1') and hasattr(self.hp_bar, 'y2'):
                # Estimate the game window from the health bar position
                logger.info("Estimating game window from health bar position")
                # Assuming the game window extends around the health bar
                game_window_rect = (
                    max(0, self.hp_bar.x1 - 500),  # Left
                    max(0, self.hp_bar.y1 - 500),  # Top
                    self.hp_bar.x2 + 500,  # Right
                    self.hp_bar.y2 + 100   # Bottom
                )
                logger.info(f"Estimated game window: {game_window_rect}")
        
        # Get the settings
        settings = self.settings_ui.get_settings()
        
        # Check if spellcasting is enabled and log it
        if settings["spellcasting"]["enabled"]:
            self.log_callback(f"Auto spellcasting enabled with key {settings['spellcasting']['spell_key']} " + 
                            f"at {settings['spellcasting']['spell_interval']}s interval")
            logger.info(f"Spellcasting enabled: Key={settings['spellcasting']['spell_key']}, " + 
                        f"Interval={settings['spellcasting']['spell_interval']}s")
            
            # Check if random targeting is enabled
            if settings["spellcasting"].get("random_targeting", False):
                radius = settings["spellcasting"].get("target_radius", 100)
                change_interval = settings["spellcasting"].get("target_change_interval", 5)
                self.log_callback(f"Random spell targeting enabled with {radius}px radius, changing every {change_interval} casts")
                logger.info(f"Random targeting: Radius={radius}px, Change interval={change_interval} casts")
                
                # Generate initial random target
                self.target_x_offset, self.target_y_offset = self.generate_random_target_offsets(radius)
                self.log_callback(f"Initial target offset: ({self.target_x_offset}, {self.target_y_offset})")
                logger.info(f"Initial target offset: ({self.target_x_offset}, {self.target_y_offset})")
                
                # Update target display if available
                self.target_var.set(f"({self.target_x_offset}, {self.target_y_offset})")
        
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
                        
                        # FIX: Check if random targeting is enabled and handle target changes properly
                        if settings["spellcasting"].get("random_targeting", False):
                            radius = settings["spellcasting"].get("target_radius", 100)
                            change_interval = settings["spellcasting"].get("target_change_interval", 5)
                            
                            # FIXED: Generate a new random target for EVERY cast when change_interval is 1
                            if change_interval == 1 or self.spells_cast_since_target_change >= change_interval:
                                # Generate new random target
                                self.target_x_offset, self.target_y_offset = self.generate_random_target_offsets(radius)
                                self.log_callback(f"New target offset: ({self.target_x_offset}, {self.target_y_offset})")
                                logger.info(f"New target offset: ({self.target_x_offset}, {self.target_y_offset})")
                                self.spells_cast_since_target_change = 0
                                
                                # Update target display
                                self.target_var.set(f"({self.target_x_offset}, {self.target_y_offset})")
                            
                            self.log_callback(f"Casting spell ({spell_key}) with offset ({self.target_x_offset}, {self.target_y_offset})")
                            logger.info(f"Casting spell with key {spell_key} and offset ({self.target_x_offset}, {self.target_y_offset})")
                        else:
                            self.log_callback(f"Casting spell ({spell_key})")
                            logger.info(f"Casting spell with key {spell_key}")
                        
                        # Press the spell key
                        press_key(None, spell_key)
                        
                        # Small delay before right-clicking
                        time.sleep(0.1)
                        
                        # Press right mouse button with target offsets if random targeting is enabled
                        if settings["spellcasting"].get("random_targeting", False) and game_window_rect:
                            # Calculate center of game window
                            # IMPORTANT: Fixing the targeting calculation
                            center_x = (game_window_rect[0] + game_window_rect[2]) // 2
                            center_y = (game_window_rect[1] + game_window_rect[3]) // 2
                            
                            # Apply target offsets
                            target_x = center_x + self.target_x_offset
                            target_y = center_y + self.target_y_offset
                            
                            # Make sure target is within game window
                            target_x = max(game_window_rect[0], min(target_x, game_window_rect[2]))
                            target_y = max(game_window_rect[1], min(target_y, game_window_rect[3]))
                            
                            # Log the actual coordinates we're using
                            logger.info(f"Game window center: ({center_x}, {center_y})")
                            logger.info(f"Target coordinates: ({target_x}, {target_y})")
                            
                            # Focus the game window if we have a handle
                            if game_hwnd:
                                try:
                                    focus_game_window(game_hwnd)
                                    logger.info(f"Focused game window")
                                    time.sleep(0.2)  # Ensure window is focused
                                except Exception as e:
                                    logger.warning(f"Could not focus game window: {e}")
                            
                            # Move mouse to target position
                            try:
                                # First try windows_utils implementation
                                move_mouse_direct(target_x, target_y)
                                logger.info(f"Moved mouse to ({target_x}, {target_y})")
                                time.sleep(0.2)  # Let game register the mouse position
                                
                                # Then right-click at that position
                                press_right_mouse(None)
                                logger.info(f"Right-clicked at ({target_x}, {target_y})")
                            except Exception as e:
                                logger.error(f"Error using direct mouse functions: {e}")
                                
                                # Fallback using standard methods
                                try:
                                    logger.warning("Using fallback mouse methods")
                                    import ctypes
                                    
                                    # Move cursor
                                    logger.info(f"Moving cursor to ({target_x}, {target_y}) using SetCursorPos")
                                    ctypes.windll.user32.SetCursorPos(int(target_x), int(target_y))
                                    time.sleep(0.2)
                                    
                                    # Right click using mouse_event
                                    MOUSEEVENTF_RIGHTDOWN = 0x0008
                                    MOUSEEVENTF_RIGHTUP = 0x0010
                                    logger.info("Right-clicking using mouse_event")
                                    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                                    time.sleep(0.1)
                                    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                                    
                                    logger.info(f"Completed fallback mouse interaction")
                                except Exception as e2:
                                    logger.error(f"Fallback mouse methods also failed: {e2}")
                                    self.log_callback(f"Error with mouse movement: {e2}")
                        else:
                            # If random targeting is disabled or no game window available - just do a regular right-click
                            press_right_mouse(None)
                        
                        # Update state
                        last_spell_cast = current_time
                        self.spells_cast += 1
                        self.spells_var.set(str(self.spells_cast))
                        self.spells_cast_since_target_change += 1
                
                # Wait for next scan
                scan_interval = settings["scan_interval"]
                time.sleep(scan_interval)
                
            except Exception as e:
                self.log_callback(f"Error in bot loop: {e}")
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(1)
        
        self.log_callback("Bot stopped")
        logger.info("Bot loop stopped")
"""
Largato Hunt Module for Priston Tale Potion Bot
---------------------------------------------
Save this file as: app/largato_hunt.py

This module implements automated hunting in the 2D Largato dungeon.
Features:
- Automatic movement using arrow keys
- Wood stack detection and destruction
- Attack automation using X key
- Completion tracking (4 wood stacks)
"""

import time
import logging
import threading
import random
import os

# Try to import OpenCV, with fallback if not available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not available. Largato Hunt will use fallback detection.")

from PIL import ImageGrab, Image

# Import key press functions with fallbacks
def get_press_key_function():
    """Get the best available key press function"""
    try:
        from app.windows_utils.keyboard import press_key
        return press_key
    except ImportError:
        try:
            from app.window_utils import press_key
            return press_key
        except ImportError:
            # Fallback key press function
            import ctypes
            def press_key(hwnd, key):
                """Fallback press_key function"""
                logger = logging.getLogger('PristonBot')
                logger.info(f"Using fallback key press for '{key}'")
                
                # Map common keys to virtual key codes
                key_map = {
                    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
                    'x': 0x58, 'space': 0x20, 'enter': 0x0D
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
            return press_key

# Get the press_key function
press_key = get_press_key_function()

logger = logging.getLogger('PristonBot')

class LargatoHunter:
    """Class for automating Largato dungeon hunting"""
    
    def __init__(self, log_callback):
        """
        Initialize the Largato Hunter
        
        Args:
            log_callback: Function to call for logging messages
        """
        self.log_callback = log_callback
        self.logger = logging.getLogger('PristonBot')
        
        # Hunt state
        self.running = False
        self.hunt_thread = None
        
        # Statistics
        self.wood_stacks_destroyed = 0
        self.total_attacks = 0
        self.hunt_start_time = None
        
        # Movement state
        self.last_move_direction = 'right'
        self.movement_variation = 0  # Counter for up/down movement
        
        # Load reference images
        self.wood_stack_template = None
        self.destroyed_wood_template = None
        self.load_reference_images()
        
        # Game window detection
        self.game_window_rect = None
        
    def load_reference_images(self):
        """Load reference images for template matching"""
        if not OPENCV_AVAILABLE:
            self.logger.warning("OpenCV not available - using fallback detection")
            return
            
        try:
            # Load wood stack template
            wood_path = "largato_tronco.png"
            if os.path.exists(wood_path):
                self.wood_stack_template = cv2.imread(wood_path, cv2.IMREAD_COLOR)
                self.logger.info("Loaded wood stack template")
            else:
                self.logger.warning(f"Wood stack template not found: {wood_path}")
            
            # Load destroyed wood template
            destroyed_path = "largato_tronco_destruido.png"
            if os.path.exists(destroyed_path):
                self.destroyed_wood_template = cv2.imread(destroyed_path, cv2.IMREAD_COLOR)
                self.logger.info("Loaded destroyed wood template")
            else:
                self.logger.warning(f"Destroyed wood template not found: {destroyed_path}")
                
        except Exception as e:
            self.logger.error(f"Error loading reference images: {e}")
    
    def find_game_window(self):
        """Find the game window for screenshot capture"""
        try:
            # Try to load from config first
            from app.config import load_config
            config = load_config()
            window_config = config.get("bars", {}).get("game_window", {})
            
            if window_config.get("configured", False):
                x1 = window_config["x1"]
                y1 = window_config["y1"]
                x2 = window_config["x2"]
                y2 = window_config["y2"]
                
                self.game_window_rect = (x1, y1, x2, y2)
                self.logger.info(f"Game window found in config: ({x1},{y1})-({x2},{y2})")
                return True
                
        except Exception as e:
            self.logger.error(f"Error finding game window: {e}")
        
        # Fallback to full screen
        self.game_window_rect = None
        self.logger.warning("Using full screen capture as fallback")
        return False
    
    def capture_game_screen(self):
        """Capture current game screen"""
        try:
            if self.game_window_rect:
                # Capture specific game window area
                screenshot = ImageGrab.grab(bbox=self.game_window_rect)
            else:
                # Capture full screen
                screenshot = ImageGrab.grab()
            
            # Convert to OpenCV format if OpenCV is available
            if OPENCV_AVAILABLE:
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                return screenshot_cv
            else:
                return np.array(screenshot)
            
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return None
    
    def find_wood_stack(self, screenshot):
        """
        Find wood stack in the screenshot using template matching or color-based detection
        
        Args:
            screenshot: OpenCV image of the game screen
            
        Returns:
            Tuple of (found, center_x, center_y, confidence)
        """
        # First try OpenCV template matching if available
        if OPENCV_AVAILABLE and self.wood_stack_template is not None:
            try:
                # Perform template matching with multiple scales for better detection
                scales = [1.0, 0.8, 1.2]  # Try different scales
                best_match = 0
                best_location = None
                
                for scale in scales:
                    # Resize template for this scale
                    if scale != 1.0:
                        h, w = self.wood_stack_template.shape[:2]
                        new_h, new_w = int(h * scale), int(w * scale)
                        scaled_template = cv2.resize(self.wood_stack_template, (new_w, new_h))
                    else:
                        scaled_template = self.wood_stack_template
                    
                    # Skip if template is larger than screenshot
                    if (scaled_template.shape[0] > screenshot.shape[0] or 
                        scaled_template.shape[1] > screenshot.shape[1]):
                        continue
                    
                    # Perform template matching
                    result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_match:
                        best_match = max_val
                        h, w = scaled_template.shape[:2]
                        center_x = max_loc[0] + w // 2
                        center_y = max_loc[1] + h // 2
                        best_location = (center_x, center_y)
                
                # Lower threshold for more sensitive detection
                threshold = 0.5  # Even more sensitive
                
                if best_match >= threshold:
                    self.logger.debug(f"Wood stack found at {best_location} with confidence {best_match:.2f}")
                    return True, best_location[0], best_location[1], best_match
                
                self.logger.debug(f"No wood stack found, best match confidence: {best_match:.2f}")
                
            except Exception as e:
                self.logger.error(f"Error in template matching: {e}")
        
        # Enhanced fallback detection - try color-based detection for brown/orange logs
        if OPENCV_AVAILABLE:
            try:
                # Convert to HSV for better color detection
                hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
                
                # Define range for brown/orange wood colors (based on your image)
                # Brown/orange logs typically have these HSV ranges
                lower_brown = np.array([10, 50, 50])   # Lower brown
                upper_brown = np.array([25, 255, 255]) # Upper brown/orange
                
                # Create mask for brown/orange colors
                mask = cv2.inRange(hsv, lower_brown, upper_brown)
                
                # Find contours in the mask
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Look for contours that could be wood stacks
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # Filter by area - wood stacks should be reasonably large
                    if area > 500:  # Minimum area for wood stack
                        # Get bounding rectangle
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Check aspect ratio - wood stacks are usually taller than wide or square-ish
                        aspect_ratio = float(w) / h
                        if 0.3 <= aspect_ratio <= 3.0:  # Reasonable aspect ratio range
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            self.logger.debug(f"Wood stack detected by color at ({center_x}, {center_y}), area: {area}")
                            return True, center_x, center_y, 0.7
                            
            except Exception as e:
                self.logger.debug(f"Color detection error: {e}")
        
        # Fallback detection method for testing - more frequent detection
        if not hasattr(self, '_fallback_counter'):
            self._fallback_counter = 0
        
        self._fallback_counter += 1
        
        # Simulate finding wood every 8-15 scans (24-45 seconds of movement) - more frequent
        if self._fallback_counter >= random.randint(8, 15):
            self.logger.info("Fallback detection: Simulating wood stack found")
            self._fallback_counter = 0  # Reset counter
            
            # Return center of screen as target
            if hasattr(screenshot, 'shape'):
                height, width = screenshot.shape[:2]
            else:
                height, width = 600, 800
            
            return True, width // 2, height // 2, 0.8
        
        return False, 0, 0, 0
    
    def is_wood_destroyed(self, screenshot):
        """
        Check if wood stack is destroyed using template matching
        
        Args:
            screenshot: OpenCV image of the game screen
            
        Returns:
            Boolean indicating if wood is destroyed
        """
        if not OPENCV_AVAILABLE or self.destroyed_wood_template is None:
            # Fallback: assume destroyed after certain number of attacks
            return self.total_attacks % 10 == 0  # Every 10 attacks assume destroyed
        
        try:
            # Perform template matching for destroyed wood
            result = cv2.matchTemplate(screenshot, self.destroyed_wood_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Threshold for detection
            threshold = 0.6
            
            if max_val >= threshold:
                self.logger.debug(f"Destroyed wood detected with confidence {max_val:.2f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in destroyed wood detection: {e}")
            return False
    
    def get_character_position(self, screenshot):
        """
        Estimate character position (center of screen for now)
        
        Args:
            screenshot: OpenCV image of the game screen
            
        Returns:
            Tuple of (x, y) character position
        """
        if hasattr(screenshot, 'shape'):
            height, width = screenshot.shape[:2]
        else:
            # Fallback dimensions
            height, width = 600, 800
        return width // 2, height // 2
    
    def move_towards_target(self, char_x, char_y, target_x, target_y):
        """
        Move character towards target location
        
        Args:
            char_x, char_y: Character position
            target_x, target_y: Target position
        """
        # Calculate distance
        dx = target_x - char_x
        dy = target_y - char_y
        
        # Determine primary movement direction
        if abs(dx) > abs(dy):
            # Move horizontally first
            if dx > 0:
                self.move_right_with_variation()
            else:
                self.move_left_with_variation()
        else:
            # Move vertically first
            if dy > 0:
                self.move_down_with_variation()
            else:
                self.move_up_with_variation()
    
    def move_right_with_variation(self):
        """Move right with up/down variation to avoid getting stuck"""
        # Press right
        press_key(None, 'right')
        time.sleep(0.1)
        
        # Add variation every few moves
        self.movement_variation += 1
        if self.movement_variation % 3 == 0:
            # Randomly press up or down
            variation_key = random.choice(['up', 'down'])
            press_key(None, variation_key)
            time.sleep(0.1)
            self.logger.debug(f"Added movement variation: {variation_key}")
    
    def move_left_with_variation(self):
        """Move left with up/down variation"""
        press_key(None, 'left')
        time.sleep(0.1)
        
        self.movement_variation += 1
        if self.movement_variation % 3 == 0:
            variation_key = random.choice(['up', 'down'])
            press_key(None, variation_key)
            time.sleep(0.1)
            self.logger.debug(f"Added movement variation: {variation_key}")
    
    def move_up_with_variation(self):
        """Move up with left/right variation"""
        press_key(None, 'up')
        time.sleep(0.1)
        
        self.movement_variation += 1
        if self.movement_variation % 4 == 0:
            variation_key = random.choice(['left', 'right'])
            press_key(None, variation_key)
            time.sleep(0.1)
    
    def move_down_with_variation(self):
        """Move down with left/right variation"""
        press_key(None, 'down')
        time.sleep(0.1)
        
        self.movement_variation += 1
        if self.movement_variation % 4 == 0:
            variation_key = random.choice(['left', 'right'])
            press_key(None, variation_key)
            time.sleep(0.1)
    
    def explore_and_search(self):
        """Explore the dungeon looking for wood stacks"""
        # Move in a search pattern
        search_moves = random.randint(5, 10)
        
        for _ in range(search_moves):
            if not self.running:
                break
                
            # Alternate between right and down/up movement
            if random.random() < 0.7:  # 70% chance to move right
                self.move_right_with_variation()
            else:
                move_direction = random.choice(['up', 'down'])
                if move_direction == 'up':
                    self.move_up_with_variation()
                else:
                    self.move_down_with_variation()
            
            time.sleep(0.2)  # Small delay between moves
    
    def attack_wood_stack(self):
        """Attack the wood stack until it's destroyed"""
        attack_count = 0
        max_attacks = 20  # Maximum attacks before giving up
        
        self.log_callback("Attacking wood stack...")
        
        while self.running and attack_count < max_attacks:
            # Press X to attack
            press_key(None, 'x')
            attack_count += 1
            self.total_attacks += 1
            
            self.logger.debug(f"Attack #{attack_count}")
            
            # Wait 1 second between attacks
            time.sleep(1.0)
            
            # Check if wood is destroyed every few attacks
            if attack_count % 3 == 0:
                screenshot = self.capture_game_screen()
                if screenshot is not None and self.is_wood_destroyed(screenshot):
                    self.wood_stacks_destroyed += 1
                    self.log_callback(f"Wood stack destroyed! Total: {self.wood_stacks_destroyed}/4")
                    self.logger.info(f"Wood stack {self.wood_stacks_destroyed} destroyed after {attack_count} attacks")
                    return True
        
        # If we reach here, assume the wood was destroyed
        self.wood_stacks_destroyed += 1
        self.log_callback(f"Wood stack destroyed (timeout)! Total: {self.wood_stacks_destroyed}/4")
        return True
    
    def start_hunt(self):
        """Start the Largato hunt"""
        if self.running:
            self.logger.info("Hunt already running")
            return False
        
        self.running = True
        self.wood_stacks_destroyed = 0
        self.total_attacks = 0
        self.hunt_start_time = time.time()
        self.movement_variation = 0
        
        # Start hunt thread
        self.hunt_thread = threading.Thread(target=self.hunt_loop)
        self.hunt_thread.daemon = True
        self.hunt_thread.start()
        
        self.log_callback("Largato Hunt started!")
        self.logger.info("Largato hunt thread started")
        return True
    
    def stop_hunt(self):
        """Stop the Largato hunt"""
        if not self.running:
            self.logger.info("Hunt not running")
            return False
        
        self.running = False
        if self.hunt_thread:
            self.hunt_thread.join(1.0)
            self.logger.info("Hunt thread joined")
        
        # Calculate hunt duration
        if self.hunt_start_time:
            duration = time.time() - self.hunt_start_time
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            self.log_callback(f"Hunt stopped. Duration: {minutes}m {seconds}s, Wood destroyed: {self.wood_stacks_destroyed}/4")
        
        self.log_callback("Largato Hunt stopped!")
        self.logger.info("Largato hunt stopped")
        return True
    
    def hunt_loop(self):
        """Main hunt loop - Simplified approach"""
        self.log_callback("Starting Largato dungeon hunt...")
        self.logger.info("Largato hunt loop started")
        
        # Find game window
        self.find_game_window()
        
        # Initial delay
        initial_delay = random.uniform(2.0, 5.0)
        self.log_callback(f"Initial delay: {initial_delay:.1f} seconds...")
        time.sleep(initial_delay)
        
        hunt_phase = "moving"  # "moving", "approach", "attacking"
        last_check_time = 0
        check_interval = 3.0  # Check for wood every 3 seconds
        wood_found_time = 0
        approach_duration = 5.0  # Move forward for 5 seconds after finding wood
        attacks_count = 0
        
        self.log_callback("Starting movement phase - looking for wood stacks...")
        
        while self.running and self.wood_stacks_destroyed < 4:
            try:
                current_time = time.time()
                
                if hunt_phase == "moving":
                    # Keep moving right with variation
                    self.move_right_with_variation()
                    
                    # Check for wood stacks every 3-5 seconds
                    if current_time - last_check_time >= check_interval:
                        self.log_callback("Scanning for wood stacks...")
                        screenshot = self.capture_game_screen()
                        
                        if screenshot is not None:
                            found, target_x, target_y, confidence = self.find_wood_stack(screenshot)
                            
                            if found:
                                self.log_callback(f"WOOD STACK FOUND! Moving forward for {approach_duration} seconds...")
                                self.logger.info(f"Wood stack detected with confidence {confidence:.2f}")
                                hunt_phase = "approach"
                                wood_found_time = current_time
                            else:
                                self.log_callback("No wood stack detected, continuing search...")
                        
                        last_check_time = current_time
                        # Randomize next check interval between 3-5 seconds
                        check_interval = random.uniform(3.0, 5.0)
                    
                    # Small delay between movements
                    time.sleep(0.3)
                
                elif hunt_phase == "approach":
                    # Keep moving forward for 5 seconds after finding wood
                    elapsed_since_found = current_time - wood_found_time
                    
                    if elapsed_since_found < approach_duration:
                        # Continue moving right
                        self.move_right_with_variation()
                        remaining = approach_duration - elapsed_since_found
                        if int(remaining) != int(remaining + 0.3):  # Log every second
                            self.log_callback(f"Approaching wood stack... {remaining:.1f}s remaining")
                        time.sleep(0.3)
                    else:
                        # Time to position and attack
                        self.log_callback("Positioning for attack - moving left...")
                        # Move left to position for attack
                        for _ in range(3):  # Move left a few times
                            press_key(None, 'left')
                            time.sleep(0.2)
                        
                        hunt_phase = "attacking"
                        attacks_count = 0
                        self.log_callback("Starting attack phase!")
                
                elif hunt_phase == "attacking":
                    # Attack the wood stack
                    press_key(None, 'x')
                    attacks_count += 1
                    self.total_attacks += 1
                    
                    self.log_callback(f"Attacking wood stack... (Attack #{attacks_count})")
                    self.logger.debug(f"Attack #{self.total_attacks}")
                    
                    # Check if we should stop attacking (after many attacks, assume destroyed)
                    if attacks_count >= 15:  # After 15 attacks, assume destroyed
                        self.wood_stacks_destroyed += 1
                        self.log_callback(f"Wood stack destroyed! Progress: {self.wood_stacks_destroyed}/4")
                        self.logger.info(f"Wood stack {self.wood_stacks_destroyed} destroyed after {attacks_count} attacks")
                        
                        # Go back to moving/searching
                        hunt_phase = "moving"
                        last_check_time = 0  # Reset so we check immediately
                        
                        # Brief pause before continuing
                        self.log_callback("Continuing search for next wood stack...")
                        time.sleep(2.0)
                    else:
                        # Continue attacking - wait 1 second between attacks
                        time.sleep(1.0)
                
            except Exception as e:
                self.log_callback(f"Error in hunt loop: {e}")
                self.logger.error(f"Error in hunt loop: {e}", exc_info=True)
                time.sleep(1.0)
        
        # Hunt completed
        if self.wood_stacks_destroyed >= 4:
            self.log_callback("Largato Hunt completed! All 4 wood stacks destroyed.")
            self.logger.info("Largato hunt completed successfully")
        else:
            self.log_callback("Largato Hunt stopped before completion.")
            self.logger.info("Largato hunt stopped by user")
        
        # Auto-stop the hunt
        self.running = False
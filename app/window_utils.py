"""
Improved Window utilities for the Priston Tale Potion Bot
-----------------------------------------------
This module provides utilities for simulating key presses and mouse clicks regardless of window focus.
"""

import time
import logging
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

logger = logging.getLogger('PristonBot')

# Define key input structures for SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class InputI(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", InputI)
    ]


def get_virtual_key_code(key):
    """
    Convert a key string to virtual key code
    
    Args:
        key: Key string (e.g., "1", "a", "enter")
        
    Returns:
        Virtual key code
    """
    # Map common keys to virtual key codes
    key_map = {
        '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
        '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
        'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'esc': 0x1B,
        'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
        'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
        'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B
    }
    
    # Convert key to lowercase
    key = key.lower() if isinstance(key, str) else str(key)
    
    # Look up key in map
    if key in key_map:
        return key_map[key]
    
    # Use ASCII value as fallback
    logger.warning(f"Key '{key}' not found in key map, using ASCII value")
    try:
        return ord(key.upper()[0])
    except:
        logger.error(f"Could not determine virtual key code for '{key}'")
        return 0

def press_key(hwnd, key):
    """
    Press a key, either in a specific window or using SendInput globally
    
    Args:
        hwnd: Window handle or None to use SendInput
        key: Key to press
        
    Returns:
        True if successful, False otherwise
    """
    try:
        vk_code = get_virtual_key_code(key)
        
        # If hwnd is provided, send message to that window
        if hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            logger.info(f"Sending key '{key}' (VK: {vk_code}) to window '{window_title}'")
            
            # Send key down message
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.05)  # Small delay between down and up
            
            # Send key up message
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
        else:
            # Use SendInput (works for both focused and background windows)
            logger.info(f"Sending key '{key}' (VK: {vk_code}) using SendInput")
            
            # Define constants
            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            
            # Key down
            extra = ctypes.c_ulong(0)
            ii_ = InputI()
            ii_.ki = KeyBdInput(vk_code, 0, 0, 0, ctypes.pointer(extra))
            x = Input(INPUT_KEYBOARD, ii_)  # INPUT_KEYBOARD = 1
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            
            # Small delay
            time.sleep(0.05)
            
            # Key up
            extra = ctypes.c_ulong(0)
            ii_ = InputI()
            ii_.ki = KeyBdInput(vk_code, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
            x = Input(INPUT_KEYBOARD, ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            
        return True
    except Exception as e:
        logger.error(f"Error sending key '{key}': {e}", exc_info=True)
        return False


def press_right_mouse(hwnd):
    """
    Try multiple methods to simulate a right-click and log the success or failure of each.
    
    Args:
        hwnd: Window handle or None
    
    Returns:
        True if at least one method worked, False otherwise
    """
    logger = logging.getLogger('PristonBot')
    logger.debug("Entered press_right_mouse function")
    success = False

    try:
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010

        if hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            logger.info(f"Attempting SendMessage right-click on window: '{window_title}'")
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                width = right - left
                height = bottom - top
                center_x = left + width // 2
                center_y = top + height // 2
                client_coords = win32gui.ScreenToClient(hwnd, (center_x, center_y))

                win32api.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON,
                                     win32api.MAKELONG(client_coords[0], client_coords[1]))
                time.sleep(0.05)
                win32api.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0,
                                     win32api.MAKELONG(client_coords[0], client_coords[1]))
                logger.info("SendMessage right-click succeeded")
                success = True
            except Exception as e:
                logger.warning(f"SendMessage right-click failed: {e}", exc_info=True)

        # Always try SendInput as fallback
        try:
            logger.info("Attempting SendInput right-click")
            INPUT_MOUSE = 0
            extra = ctypes.c_ulong(0)

            # Mouse down
            ii_ = InputI()
            ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
            x = Input(INPUT_MOUSE, ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

            time.sleep(0.05)

            # Mouse up
            ii_ = InputI()
            ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, ctypes.pointer(extra))
            x = Input(INPUT_MOUSE, ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

            logger.info("SendInput right-click succeeded")
            success = True
        except Exception as e:
            logger.warning(f"SendInput right-click failed: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Critical error in press_right_mouse: {e}", exc_info=True)

    if not success:
        logger.error("All click methods failed!")
    return success


def find_game_window(window_name="Priston Tale"):
    """
    Find the game window by name
    
    Args:
        window_name: The name of the window to find (default: "Priston Tale")
        
    Returns:
        Window handle if found, None otherwise
    """
    logger.info(f"Searching for game window: {window_name}")
    
    # Try direct match first
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd != 0:
        logger.info(f"Found exact window match with handle {hwnd}")
        return hwnd
    
    # If not found, try partial match
    windows = []
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_name.lower() in title.lower():
                windows.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(callback, windows)
    
    if windows:
        logger.info(f"Found similar window: '{windows[0][1]}' with handle {windows[0][0]}")
        return windows[0][0]
    
    logger.warning(f"Game window '{window_name}' not found")
    return None

def focus_game_window(hwnd):
    """
    Bring the game window to the foreground
    
    Args:
        hwnd: Window handle
        
    Returns:
        True if successful, False otherwise
    """
    if not hwnd:
        logger.warning("Cannot focus window: Invalid handle")
        return False
    
    try:
        # Get window title for logging
        window_title = win32gui.GetWindowText(hwnd)
        logger.info(f"Focusing window: {window_title}")
        
        # Check if window is already in foreground
        current_foreground = win32gui.GetForegroundWindow()
        if current_foreground == hwnd:
            logger.debug("Window already in foreground")
            return True
            
        # Try to bring window to foreground
        logger.debug(f"Current foreground: {win32gui.GetWindowText(current_foreground)}, need to focus {window_title}")
        
        # Check if window is minimized
        if win32gui.IsIconic(hwnd):
            logger.debug("Window is minimized, restoring")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)  # Give it time to restore
        
        # Try multiple methods to focus the window
        try:
            # Standard method
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.warning(f"Standard SetForegroundWindow failed: {e}")
            try:
                # Alternative method using AttachThreadInput
                foreground_thread = ctypes.windll.user32.GetWindowThreadProcessId(
                    win32gui.GetForegroundWindow(), None)
                current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
                
                # Attach threads
                ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, True)
                
                # Show and focus window
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                
                # Detach threads
                ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, False)
            except Exception as e2:
                logger.error(f"Alternative focus method failed: {e2}")
                
                try:
                    # Final attempt using ASFW_ANY
                    SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
                    SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
                    SPIF_SENDCHANGE = 0x2
                    
                    # Save current timeout
                    timeout_buf = wintypes.DWORD(0)
                    ctypes.windll.user32.SystemParametersInfoW(
                        SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(timeout_buf), 0)
                    
                    # Set timeout to 0
                    ctypes.windll.user32.SystemParametersInfoW(
                        SPI_SETFOREGROUNDLOCKTIMEOUT, 0, ctypes.c_void_p(0), SPIF_SENDCHANGE)
                    
                    # Try to set foreground window
                    win32gui.SetForegroundWindow(hwnd)
                    
                    # Restore timeout
                    ctypes.windll.user32.SystemParametersInfoW(
                        SPI_SETFOREGROUNDLOCKTIMEOUT, 0, timeout_buf, SPIF_SENDCHANGE)
                except Exception as e3:
                    logger.error(f"Final focus attempt failed: {e3}")
        
        # Give window time to come to foreground
        time.sleep(0.2)
        
        # Verify window is in foreground
        new_foreground = win32gui.GetForegroundWindow()
        if new_foreground != hwnd:
            logger.warning(f"Focus verification failed. Current foreground: {win32gui.GetWindowText(new_foreground)}")
            return False
        
        logger.info("Window focus successful")
        return True
        
    except Exception as e:
        logger.error(f"Error focusing game window: {e}", exc_info=True)
        return False

def get_window_rect(hwnd):
    """
    Get the rectangle coordinates of a window
    
    Args:
        hwnd: Window handle
        
    Returns:
        Tuple of (left, top, right, bottom) or None if failed
    """
    if not hwnd:
        logger.warning("Cannot get window rectangle: Invalid handle")
        return None
    
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception as e:
        logger.error(f"Error getting window rectangle: {e}")
        return None
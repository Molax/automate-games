"""
Mouse Input Utilities
--------------------
This module provides utilities for simulating mouse input.
"""

import time
import logging
import win32gui
import win32con
import win32api
import ctypes

from app.window_utils import MouseInput, InputI, Input
from app.window_utils import get_virtual_key_code

logger = logging.getLogger('PristonBot')

def press_right_mouse(hwnd=None, target_x=None, target_y=None, method=None):
    """
    Try specific or all mouse click methods to simulate a right-click
    
    Args:
        hwnd: Window handle or None
        target_x: X-coordinate for the click, or None to use current position
        target_y: Y-coordinate for the click, or None to use current position
        method: Specific method to use, or None to try all methods
    
    Returns:
        True if at least one method worked, False otherwise
    """
    logger.debug(f"Entered press_right_mouse function with target: ({target_x}, {target_y})")
    success = False

    # Store original cursor position if we're moving it
    original_pos = None
    if target_x is not None and target_y is not None:
        try:
            cursor_info = win32gui.GetCursorInfo()
            original_pos = cursor_info[2]  # (x, y) tuple
            logger.debug(f"Saved original cursor position: {original_pos}")
        except Exception as e:
            logger.warning(f"Could not get original cursor position: {e}")
    
    try:
        # Move cursor to target position if specified
        if target_x is not None and target_y is not None:
            logger.debug(f"Moving cursor to position ({target_x}, {target_y})")
            ctypes.windll.user32.SetCursorPos(target_x, target_y)
            # Small delay to ensure cursor is moved
            time.sleep(0.05)
        
        # Dictionary of available methods
        click_methods = {
            "SendInput": lambda: _click_method_send_input(),
            "SendInputAbsolute": lambda: _click_method_send_input_absolute(hwnd, target_x, target_y),
            "KeyCombination": lambda: _click_method_key_combination(),
            "SetCursorPos": lambda: _click_method_set_cursor_pos(hwnd, target_x, target_y),
            "MouseEvent": lambda: _click_method_mouse_event()
        }
        
        # If a specific method is requested
        if method and method in click_methods:
            try:
                logger.info(f"Attempting click method: {method}")
                success = click_methods[method]()
                logger.info(f"Click method {method} " + ("succeeded" if success else "failed"))
                return success
            except Exception as e:
                logger.error(f"Error with click method {method}: {e}", exc_info=True)
                return False
        
        # Try methods in order (most likely to work first)
        methods_to_try = [
            "SendInput",          # Most reliable cross-application
            "MouseEvent",         # Fallback
            "SendInputAbsolute"   # Alternative with position
        ]
        
        # Add window-specific methods if we have a window handle
        if hwnd:
            methods_to_try = ["SendMessage", "PostMessage"] + methods_to_try
        
        # Try each method until one succeeds
        for method_name in methods_to_try:
            try:
                if method_name in click_methods:
                    logger.info(f"Attempting click method: {method_name}")
                    if click_methods[method_name]():
                        logger.info(f"Click method {method_name} succeeded")
                        success = True
                        break
                    else:
                        logger.warning(f"Click method {method_name} failed")
            except Exception as e:
                logger.warning(f"Error with click method {method_name}: {e}")
        
        # Last resort: try key combination
        if not success:
            try:
                logger.info("Attempting keyboard shortcut as last resort")
                success = click_methods["KeyCombination"]()
                logger.info(f"Key combination method " + ("succeeded" if success else "failed"))
            except Exception as e:
                logger.warning(f"Error with key combination method: {e}")
        
        if not success:
            logger.error("All click methods failed!")
        
        return success
        
    finally:
        # Restore original cursor position if we moved it
        if original_pos is not None:
            logger.debug(f"Restoring cursor to original position: {original_pos}")
            ctypes.windll.user32.SetCursorPos(original_pos[0], original_pos[1])

def press_left_mouse(hwnd=None, target_x=None, target_y=None):
    """
    Simulate a left mouse button click
    
    Args:
        hwnd: Window handle or None
        target_x: X-coordinate for the click, or None to use current position
        target_y: Y-coordinate for the click, or None to use current position
        
    Returns:
        True if successful, False otherwise
    """
    logger.debug(f"Entered press_left_mouse function with target: ({target_x}, {target_y})")
    
    # Store original cursor position if we're moving it
    original_pos = None
    if target_x is not None and target_y is not None:
        try:
            cursor_info = win32gui.GetCursorInfo()
            original_pos = cursor_info[2]  # (x, y) tuple
            logger.debug(f"Saved original cursor position: {original_pos}")
        except Exception as e:
            logger.warning(f"Could not get original cursor position: {e}")
    
    try:
        # Move cursor to target position if specified
        if target_x is not None and target_y is not None:
            logger.debug(f"Moving cursor to position ({target_x}, {target_y})")
            ctypes.windll.user32.SetCursorPos(target_x, target_y)
            # Small delay to ensure cursor is moved
            time.sleep(0.05)
        
        # Use SendInput for left-click
        INPUT_MOUSE = 0
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        
        # Mouse down
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.05)
        
        # Mouse up
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        return True
        
    except Exception as e:
        logger.error(f"Error in press_left_mouse: {e}", exc_info=True)
        return False
        
    finally:
        # Restore original cursor position if we moved it
        if original_pos is not None:
            logger.debug(f"Restoring cursor to original position: {original_pos}")
            ctypes.windll.user32.SetCursorPos(original_pos[0], original_pos[1])

def test_click_methods(hwnd=None):
    """
    Test multiple mouse click methods and log results to determine which works
    
    Args:
        hwnd: Window handle or None to test global methods
        
    Returns:
        Dictionary with results of each test method
    """
    logger.info("Starting comprehensive mouse click testing")
    
    results = {}
    window_title = "Unknown"
    
    if hwnd:
        try:
            window_title = win32gui.GetWindowText(hwnd)
            logger.info(f"Testing click methods on window: '{window_title}' (handle: {hwnd})")
        except:
            logger.error("Could not get window title for provided handle")
    else:
        logger.info("Testing global click methods (no window handle)")
    
    # Test all the click methods
    click_methods = {
        "SendInput": lambda: _click_method_send_input(),
        "SendInputAbsolute": lambda: _click_method_send_input_absolute(hwnd),
        "MouseEvent": lambda: _click_method_mouse_event(),
        "KeyCombination": lambda: _click_method_key_combination(),
        "SetCursorPos": lambda: _click_method_set_cursor_pos(hwnd)
    }
    
    # If a window handle is provided, add window-specific methods
    if hwnd:
        click_methods["SendMessage"] = lambda: _click_method_send_message(hwnd)
        click_methods["PostMessage"] = lambda: _click_method_post_message(hwnd)
    
    # Test each method and log results
    for method_name, method_func in click_methods.items():
        try:
            logger.info(f"Testing {method_name} method...")
            success = method_func()
            result = "Succeeded" if success else "Failed (returned False)"
            results[method_name] = result
            logger.info(f"  Result: {result}")
        except Exception as e:
            results[method_name] = f"Error: {str(e)}"
            logger.error(f"  Error: {e}")
    
    # Log a summary of results
    logger.info("Mouse click method testing completed. Results:")
    for method, result in results.items():
        logger.info(f"  {method}: {result}")
    
    return results

# Private click method implementations
def _click_method_send_message(hwnd):
    """SendMessage method for window-specific clicking"""
    if not hwnd:
        return False
        
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        center_x = left + width // 2
        center_y = top + height // 2
        client_coords = win32gui.ScreenToClient(hwnd, (center_x, center_y))
        
        lParam = win32api.MAKELONG(client_coords[0], client_coords[1])
        win32api.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
        time.sleep(0.05)
        win32api.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)
        return True
    except Exception as e:
        logger.debug(f"SendMessage click failed: {e}")
        return False

def _click_method_post_message(hwnd):
    """PostMessage method for window-specific clicking"""
    if not hwnd:
        return False
        
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        center_x = left + width // 2
        center_y = top + height // 2
        client_coords = win32gui.ScreenToClient(hwnd, (center_x, center_y))
        
        lParam = win32api.MAKELONG(client_coords[0], client_coords[1])
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
        time.sleep(0.05)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)
        return True
    except Exception as e:
        logger.debug(f"PostMessage click failed: {e}")
        return False

def _click_method_mouse_event():
    """mouse_event method for global clicking"""
    try:
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        return True
    except Exception as e:
        logger.debug(f"mouse_event click failed: {e}")
        return False

def _click_method_send_input():
    """SendInput method for global clicking"""
    try:
        INPUT_MOUSE = 0
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        
        # Mouse down
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.05)
        
        # Mouse up
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        return True
    except Exception as e:
        logger.debug(f"SendInput click failed: {e}")
        return False

def _click_method_set_cursor_pos(hwnd=None, target_x=None, target_y=None):
    """SetCursorPos + mouse_event method"""
    try:
        # Get current cursor position to restore later
        cursor_info = win32gui.GetCursorInfo()
        original_x, original_y = cursor_info[2]
        
        # Calculate target position if not provided
        if target_x is None or target_y is None:
            target_x, target_y = original_x, original_y
            if hwnd:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                target_x = left + (right - left) // 2
                target_y = top + (bottom - top) // 2
        
        # Move cursor
        ctypes.windll.user32.SetCursorPos(target_x, target_y)
        
        # Click
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        
        # Restore cursor position
        ctypes.windll.user32.SetCursorPos(original_x, original_y)
        
        return True
    except Exception as e:
        logger.debug(f"SetCursorPos click failed: {e}")
        return False

def _click_method_send_input_absolute(hwnd=None, target_x=None, target_y=None):
    """SendInput with absolute coordinates method"""
    try:
        # Get screen dimensions for coordinate conversion
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        
        # Calculate position if not provided
        if target_x is None or target_y is None:
            target_x, target_y = screen_width // 2, screen_height // 2
            if hwnd:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                target_x = left + (right - left) // 2
                target_y = top + (bottom - top) // 2
        
        logger.debug(f"Using target position: ({target_x}, {target_y})")
        
        # Convert to normalized coordinates (0..65535)
        norm_x = int(65535 * target_x / screen_width)
        norm_y = int(65535 * target_y / screen_height)
        
        INPUT_MOUSE = 0
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        MOUSEEVENTF_ABSOLUTE = 0x8000
        MOUSEEVENTF_MOVE = 0x0001
        
        # Move mouse to position
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(norm_x, norm_y, 0, MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.05)
        
        # Mouse down
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.05)
        
        # Mouse up
        extra = ctypes.c_ulong(0)
        ii_ = InputI()
        ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_RIGHTUP, 0, ctypes.pointer(extra))
        x = Input(INPUT_MOUSE, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        return True
    except Exception as e:
        logger.debug(f"SendInput absolute click failed: {e}")
        return False

def _click_method_key_combination():
    """Try keyboard shortcut (Right Ctrl + Right Alt) as alternative"""
    try:
        VK_RCONTROL = 0xA3
        VK_RMENU = 0xA5  # Right Alt key
        KEYEVENTF_KEYUP = 0x0002
        
        # Press Right Control
        ctypes.windll.user32.keybd_event(VK_RCONTROL, 0, 0, 0)
        time.sleep(0.05)
        # Press Right Alt
        ctypes.windll.user32.keybd_event(VK_RMENU, 0, 0, 0)
        time.sleep(0.05)
        # Release Right Alt
        ctypes.windll.user32.keybd_event(VK_RMENU, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        # Release Right Control
        ctypes.windll.user32.keybd_event(VK_RCONTROL, 0, KEYEVENTF_KEYUP, 0)
        
        return True
    except Exception as e:
        logger.debug(f"Key combination click failed: {e}")
        return False
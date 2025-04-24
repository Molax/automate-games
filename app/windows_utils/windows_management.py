"""
Window Management Utilities
--------------------------
This module provides utilities for finding, focusing, and getting information about windows.
"""

import time
import logging
import win32gui
import win32con
import ctypes
from ctypes import wintypes

logger = logging.getLogger('PristonBot')

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

def get_client_area(hwnd):
    """
    Get the client area rectangle of a window
    
    Args:
        hwnd: Window handle
        
    Returns:
        Tuple of (left, top, right, bottom) or None if failed
    """
    if not hwnd:
        logger.warning("Cannot get client area: Invalid handle")
        return None
    
    try:
        # Get window rect in screen coordinates
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        
        # Get client rect in client coordinates (relative to window)
        client_rect = win32gui.GetClientRect(hwnd)
        client_left, client_top, client_right, client_bottom = client_rect
        
        # Convert the client rect to screen coordinates
        client_left_screen, client_top_screen = win32gui.ClientToScreen(hwnd, (client_left, client_top))
        client_right_screen, client_bottom_screen = win32gui.ClientToScreen(hwnd, (client_right, client_bottom))
        
        return (client_left_screen, client_top_screen, client_right_screen, client_bottom_screen)
    except Exception as e:
        logger.error(f"Error getting client area: {e}")
        return None

def get_window_center(hwnd):
    """
    Get the center point of a window
    
    Args:
        hwnd: Window handle
        
    Returns:
        Tuple of (center_x, center_y) or None if failed
    """
    rect = get_window_rect(hwnd)
    if rect:
        left, top, right, bottom = rect
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        return (center_x, center_y)
    return None

def get_all_windows():
    """
    Get a list of all visible windows with titles
    
    Returns:
        List of (hwnd, title) tuples
    """
    windows = []
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only include windows with titles
                windows.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(callback, windows)
    return windows
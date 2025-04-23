#!/usr/bin/env python3
"""
Priston Tale Potion Bot - Main Entry Point
-----------------------------------------
This script launches the Priston Tale Potion Bot application.
It checks for dependencies and starts the GUI.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from app.config import setup_logging
from app.gui import PristonTaleBot

def check_dependencies():
    """Check for required libraries"""
    missing_libs = []
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
    except ImportError:
        missing_libs.append("pywin32")
    
    try:
        import cv2
    except ImportError:
        missing_libs.append("opencv-python")
        
    try:
        import numpy
    except ImportError:
        missing_libs.append("numpy")
        
    try:
        from PIL import Image, ImageTk, ImageGrab
    except ImportError:
        missing_libs.append("pillow")
    
    return missing_libs

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log unhandled exceptions"""
    logger = logging.getLogger('PristonBot')
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def main():
    """Main application entry point"""
    # Set up logging
    logger = setup_logging()
    
    # Set up the exception hook
    sys.excepthook = handle_exception
    
    logger.info("Starting Priston Tale Potion Bot application")
    print("Starting Priston Tale Potion Bot...")
    
    # Check for required libraries
    missing_libs = check_dependencies()
    if missing_libs:
        error_message = "The following required libraries are missing:\n"
        for lib in missing_libs:
            error_message += f"- {lib}\n"
        error_message += "\nPlease install them using:\n"
        error_message += "pip install " + " ".join(missing_libs)
        
        # Try to show a messagebox if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_message)
            root.destroy()
        except:
            # Fall back to console output
            print("ERROR: Missing dependencies")
            print(error_message)
            
        sys.exit(1)
        
    # Create required directories
    for directory in ["logs", "debug_images"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    
    # Start the application
    try:
        root = tk.Tk()
        root.title("Priston Tale Potion Bot")
        
        # Configure styles
        style = ttk.Style(root)
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))
        
        # Create a custom style for the Start button
        style.configure("Start.TButton", 
                        background="green", 
                        foreground="white", 
                        font=("Arial", 12, "bold"))
        
        # Create a custom style for the Stop button
        style.configure("Stop.TButton", 
                        background="red", 
                        foreground="white", 
                        font=("Arial", 12, "bold"))
        
        # Set icon if available
        try:
            root.iconbitmap("resources/bot_icon.ico")
        except:
            logger.info("Icon file not found")
        
        # Create the application
        app = PristonTaleBot(root)
        
        # Display startup information in the log
        app.log("Application started successfully")
        app.log("Step 1: Select your Health, Mana, and Stamina bars")
        app.log("Step 2: Configure thresholds and keys")
        app.log("Step 3: Configure spell casting (optional)")
        app.log("Step 4: Click Start Bot to begin monitoring")
        
        # Run the application
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", f"A fatal error occurred:\n{e}\n\nCheck the logs for details.")
            root.destroy()
        except:
            print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
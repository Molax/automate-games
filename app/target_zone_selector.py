"""
Monster Target Zone Selector for Priston Tale Potion Bot
------------------------------------------------------
This module implements a target zone selector that allows the user
to define an area where monsters typically appear for better spell targeting.
Save this file as app/target_zone_selector.py
"""

import tkinter as tk
import logging
from PIL import ImageGrab, ImageTk, Image
import os
import random
import numpy as np
import math

class TargetZoneSelector:
    """Class for selecting the monster target zone"""
    
    def __init__(self, root):
        """
        Initialize the target zone selector
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.logger = logging.getLogger('PristonBot')
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None
        self.is_selecting = False
        self.is_configured = False
        self.selection_window = None
        self.canvas = None
        self.selection_rect = None
        self.screenshot_tk = None
        self.preview_image = None
        self.title = "Monster Target Zone"
        self.color = "green"
        
        # Store a list of specific target points within the zone
        self.target_points = []
        self.num_target_points = 8  # Number of target points to generate
        
    def is_setup(self):
        """Check if the target zone is configured"""
        return self.is_configured
    
    def configure_from_saved(self, x1, y1, x2, y2, target_points=None):
        """Configure target zone from saved coordinates without UI interaction
        
        Args:
            x1, y1: Top-left coordinates
            x2, y2: Bottom-right coordinates
            target_points: Optional list of specific target points
            
        Returns:
            True if successful
        """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.is_configured = True
        
        # If target points were provided, use them
        if target_points and isinstance(target_points, list) and len(target_points) > 0:
            self.target_points = target_points
        else:
            # Otherwise generate new target points
            self.generate_target_points()
            
        self.logger.info(f"Target zone configured from saved coordinates: ({x1},{y1}) to ({x2},{y2})")
        self.logger.info(f"Target zone contains {len(self.target_points)} targeting points")
        return True
        
    def start_selection(self):
        """Start the target zone selection process"""
        self.logger.info(f"Starting selection: {self.title}")
        
        # Create selection window that covers the entire screen
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title(self.title)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.8)  # Semi-transparent
        self.selection_window.configure(bg='black')
        
        # Take a screenshot of the entire screen
        self.logger.debug("Taking screenshot for selection")
        screenshot = ImageGrab.grab()
        self.screenshot_tk = ImageTk.PhotoImage(screenshot)
        self.full_screenshot = screenshot  # Save the full screenshot for later use
        
        # Create a canvas to display the screenshot and allow selection
        self.canvas = tk.Canvas(self.selection_window, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, image=self.screenshot_tk, anchor=tk.NW)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Add instructions
        instruction_text = f"Click and drag to select the Monster Target Zone. Press ESC to cancel."
        self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text=instruction_text,
            fill="white",
            font=("Arial", 18),
        )
        
        # Bind escape key to cancel
        self.selection_window.bind("<Escape>", self._on_escape)
        
    def _on_escape(self, event):
        """Handle escape key press"""
        self.logger.info(f"Selection canceled by user (ESC key)")
        self.selection_window.destroy()
        
    def on_press(self, event):
        """Handle mouse button press"""
        self.is_selecting = True
        self.x1 = event.x
        self.y1 = event.y
        self.logger.debug(f"Started selection at ({self.x1}, {self.y1})")
        
        # Create the selection rectangle
        self.selection_rect = self.canvas.create_rectangle(
            self.x1, self.y1, self.x1, self.y1, 
            outline=self.color, width=2
        )
        
    def on_drag(self, event):
        """Handle mouse drag"""
        if self.is_selecting:
            self.x2 = event.x
            self.y2 = event.y
            self.canvas.coords(self.selection_rect, self.x1, self.y1, self.x2, self.y2)
            
    def on_release(self, event):
        """Handle mouse button release"""
        if not self.is_selecting:
            return
            
        self.is_selecting = False
        self.x2 = event.x
        self.y2 = event.y
        self.logger.debug(f"Completed selection to ({self.x2}, {self.y2})")
        
        # Ensure coordinates are ordered correctly (top-left to bottom-right)
        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1
            
        # Display selected area details
        self.canvas.create_text(
            (self.x1 + self.x2) // 2,
            self.y2 + 20,
            text=f"Selected: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})",
            fill="white",
            font=("Arial", 12),
        )
        
        # Generate target points within the selected area
        self.generate_target_points()
        
        # Draw the target points
        self._draw_target_points()
        
        # Ask for confirmation
        confirmation = tk.messagebox.askyesno(
            f"Confirm {self.title} Selection",
            f"Is this the correct area for monster targeting?\nCoordinates: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})\n\n{len(self.target_points)} target points generated."
        )
        
        if confirmation:
            self.is_configured = True
            self.logger.info(f"{self.title} selection confirmed: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})")
            
            # Capture preview image of selected area
            try:
                preview = self.full_screenshot.crop((self.x1, self.y1, self.x2, self.y2))
                self.preview_image = preview
                
                # Save the preview image for debugging
                debug_dir = "debug_images"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                    
                # Save the preview with target points
                preview_with_points = preview.copy()
                from PIL import ImageDraw
                draw = ImageDraw.Draw(preview_with_points)
                
                # Draw the target points in the preview
                for point in self.target_points:
                    # Convert to relative coordinates in the preview
                    rel_x = point[0] - self.x1
                    rel_y = point[1] - self.y1
                    draw.ellipse((rel_x-5, rel_y-5, rel_x+5, rel_y+5), outline=(0, 255, 0), width=2)
                    
                preview_with_points.save(f"{debug_dir}/target_zone_preview.png")
                
            except Exception as e:
                self.logger.error(f"Error creating preview image: {e}")
                
            self.selection_window.destroy()
        else:
            self.logger.info(f"{self.title} selection canceled, retrying")
            self.canvas.delete(self.selection_rect)
            self.target_points = []
            
            # Clear target point markers
            for item in self.canvas.find_all():
                if self.canvas.type(item) == "oval":
                    self.canvas.delete(item)
    
    def _draw_target_points(self):
        """Draw the target points on the canvas"""
        # Clear any existing target point markers
        for item in self.canvas.find_all():
            if self.canvas.type(item) == "oval":
                self.canvas.delete(item)
                
        # Draw each target point
        for x, y in self.target_points:
            # Draw a circle for each target point
            self.canvas.create_oval(
                x-5, y-5, x+5, y+5,
                outline=self.color,
                fill=self.color,
                width=2
            )
            
    def generate_target_points(self):
        """Generate target points within the selected area
        
        These points will be used for monster targeting, focusing on areas
        where monsters are likely to appear (forming a semi-circle around
        the character).
        """
        if not all([self.x1, self.y1, self.x2, self.y2]):
            self.logger.warning("Cannot generate target points: coordinates not set")
            return
            
        # Clear existing target points
        self.target_points = []
        
        # Calculate the width and height of the target zone
        width = self.x2 - self.x1
        height = self.y2 - self.y1
        
        # Calculate the center of the target zone (character position)
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        
        # Generate target points in a semi-circle pattern in the lower half
        # of the selection area, similar to the green circles in the screenshot
        
        # Determine radius based on the smaller dimension, with some margin
        radius = min(width, height) * 0.4
        
        # Method 1: Create points in a circular pattern around the character
        for i in range(self.num_target_points):
            # Calculate angle, focusing more on the lower half
            # Angles range from -135 to 135 degrees (focusing on lower half)
            angle = math.radians(random.uniform(-135, 135))
            
            # Add some randomness to the radius
            rand_radius = radius * random.uniform(0.7, 1.0)
            
            # Calculate point coordinates
            x = center_x + int(rand_radius * math.cos(angle))
            y = center_y + int(rand_radius * math.sin(angle))
            
            # Ensure the point is within the selection bounds
            x = max(self.x1, min(x, self.x2))
            y = max(self.y1, min(y, self.y2))
            
            self.target_points.append((x, y))
        
        self.logger.info(f"Generated {len(self.target_points)} target points")
        
    def get_random_target(self):
        """Get a random target point within the selection
        
        Returns:
            Tuple of (x, y) coordinates for targeting
        """
        # If we have target points, choose one randomly
        if self.target_points:
            return random.choice(self.target_points)
        
        # Fallback: If no target points available, generate a random point
        if not all([self.x1, self.y1, self.x2, self.y2]):
            self.logger.warning("Cannot get random target: target zone not configured")
            return None
            
        # Random coordinates within the selection
        x = random.randint(self.x1, self.x2)
        y = random.randint(self.y1, self.y2)
        
        return (x, y)
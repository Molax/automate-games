"""
Improved Settings UI components for Priston Tale Potion Bot
-------------------------------------------------
This module handles the UI for potion, spellcasting, and advanced settings.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from app.bot.interfaces import SettingsProvider

logger = logging.getLogger('PristonBot')

class SettingsUI(SettingsProvider):
    """Class for managing settings UI components"""
    
    def __init__(self, main_frame):
        """
        Initialize the settings UI components
        
        Args:
            main_frame: The main frame to add UI elements to
        """
        # Create settings frame
        self.settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=5)
        self.settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create tabbed interface for better organization
        settings_notebook = ttk.Notebook(self.settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Create tabs
        potion_tab = ttk.Frame(settings_notebook)
        spell_tab = ttk.Frame(settings_notebook)
        advanced_tab = ttk.Frame(settings_notebook)
        
        settings_notebook.add(potion_tab, text="Potions")
        settings_notebook.add(spell_tab, text="Spellcasting")
        settings_notebook.add(advanced_tab, text="Advanced")
        
        # ---- Potion Settings Tab ----
        # Create compact layout with two sections side-by-side
        potion_frame = ttk.Frame(potion_tab)
        potion_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Left section - Thresholds
        thresholds_frame = ttk.LabelFrame(potion_frame, text="Thresholds")
        thresholds_frame.grid(row=0, column=0, padx=2, pady=2, sticky=tk.NSEW)
        
        # HP threshold
        ttk.Label(thresholds_frame, text="Health %:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.hp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.hp_threshold.set(50)
        self.hp_threshold.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        
        # MP threshold
        ttk.Label(thresholds_frame, text="Mana %:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.mp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.mp_threshold.set(30)
        self.mp_threshold.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)
        
        # SP threshold
        ttk.Label(thresholds_frame, text="Stamina %:").grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        self.sp_threshold = ttk.Spinbox(thresholds_frame, from_=1, to=99, width=5)
        self.sp_threshold.set(40)
        self.sp_threshold.grid(row=2, column=1, padx=2, pady=2, sticky=tk.W)
        
        # Right section - Keys
        keys_frame = ttk.LabelFrame(potion_frame, text="Potion Keys")
        keys_frame.grid(row=0, column=1, padx=2, pady=2, sticky=tk.NSEW)
        
        # HP key
        ttk.Label(keys_frame, text="Health Key:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.hp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.hp_key.set("1")
        self.hp_key.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        
        # MP key
        ttk.Label(keys_frame, text="Mana Key:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.mp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.mp_key.set("3")
        self.mp_key.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)
        
        # SP key
        ttk.Label(keys_frame, text="Stamina Key:").grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        self.sp_key = ttk.Combobox(keys_frame, values=list("123456789"), width=3)
        self.sp_key.set("2")
        self.sp_key.grid(row=2, column=1, padx=2, pady=2, sticky=tk.W)
        
        # Configure grid weights
        potion_frame.columnconfigure(0, weight=1)
        potion_frame.columnconfigure(1, weight=1)
        
        # ---- Spellcasting Tab ----
        # Enable spellcasting checkbox
        self.spellcast_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            spell_tab, 
            text="Enable Auto Spellcasting", 
            variable=self.spellcast_enabled
        ).pack(anchor=tk.W, pady=2)
        
        # Create a frame for spell settings
        spell_settings_frame = ttk.Frame(spell_tab)
        spell_settings_frame.pack(fill=tk.X, pady=2)
        
        # Spell key selection
        ttk.Label(spell_settings_frame, text="Spell Key:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.spell_key = ttk.Combobox(
            spell_settings_frame, 
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"], 
            width=5
        )
        self.spell_key.set("F5")
        self.spell_key.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        
        # Spellcasting interval
        ttk.Label(spell_settings_frame, text="Cast Interval (sec):").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.spell_interval = ttk.Spinbox(spell_settings_frame, from_=0.5, to=10.0, increment=0.5, width=5)
        self.spell_interval.set(3.0)
        self.spell_interval.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W)
        
        # Configure grid weights
        spell_settings_frame.columnconfigure(0, weight=1)
        spell_settings_frame.columnconfigure(1, weight=1)
        
        # ---- Advanced Settings Tab ----
        adv_frame = ttk.Frame(advanced_tab)
        adv_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scan interval
        ttk.Label(adv_frame, text="Scan Interval (seconds):").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.scan_interval = ttk.Spinbox(adv_frame, from_=0.1, to=5.0, increment=0.1, width=5)
        self.scan_interval.set(0.5)
        self.scan_interval.grid(row=0, column=1, padx=2, pady=2, sticky=tk.W)
        
        # Debug mode checkbox
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_frame, text="Enable Debug Mode", variable=self.debug_var).grid(
            row=1, column=0, columnspan=2, padx=2, pady=2, sticky=tk.W)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get all current settings as a dictionary"""
        return {
            "thresholds": {
                "health": float(self.hp_threshold.get()),
                "mana": float(self.mp_threshold.get()),
                "stamina": float(self.sp_threshold.get())
            },
            "potion_keys": {
                "health": self.hp_key.get(),
                "mana": self.mp_key.get(),
                "stamina": self.sp_key.get()
            },
            "spellcasting": {
                "enabled": self.spellcast_enabled.get(),
                "spell_key": self.spell_key.get(),
                "spell_interval": float(self.spell_interval.get())
            },
            "scan_interval": float(self.scan_interval.get()),
            "debug_enabled": self.debug_var.get()
        }
        
    def set_settings(self, settings: Dict[str, Any]) -> None:
        """
        Apply settings from a dictionary
        
        Args:
            settings: Dictionary containing settings
        """
        # Potion keys
        potion_keys = settings.get("potion_keys", {})
        self.hp_key.set(potion_keys.get("health", "1"))
        self.mp_key.set(potion_keys.get("mana", "3"))
        self.sp_key.set(potion_keys.get("stamina", "2"))
        
        # Thresholds
        thresholds = settings.get("thresholds", {})
        self.hp_threshold.set(thresholds.get("health", 50))
        self.mp_threshold.set(thresholds.get("mana", 30))
        self.sp_threshold.set(thresholds.get("stamina", 40))
        
        # Spellcasting settings
        spellcasting = settings.get("spellcasting", {})
        self.spellcast_enabled.set(spellcasting.get("enabled", False))
        self.spell_key.set(spellcasting.get("spell_key", "F5"))
        self.spell_interval.set(spellcasting.get("spell_interval", 3.0))
        
        # Other settings
        self.scan_interval.set(settings.get("scan_interval", 0.5))
        self.debug_var.set(settings.get("debug_enabled", True))
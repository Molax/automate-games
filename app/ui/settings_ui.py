"""
Improved Settings UI for the Priston Tale Potion Bot
------------------------------------------------
This module contains the settings UI components with better use of space.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('PristonBot')

class SettingsUI:
    """Class that handles the settings UI with horizontal layout"""
    
    def __init__(self, parent, save_callback):
        """
        Initialize the settings UI
        
        Args:
            parent: Parent frame to place UI elements
            save_callback: Function to call to save settings
        """
        self.parent = parent
        self.save_callback = save_callback
        
        # Create the UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components with horizontal layout"""
        # Create notebook (tabs) for settings categories
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Potion settings tab
        potion_tab = ttk.Frame(self.notebook)
        self.notebook.add(potion_tab, text="Potion Settings")
        
        # Spell settings tab
        spell_tab = ttk.Frame(self.notebook)
        self.notebook.add(spell_tab, text="Spell Settings")
        
        # Advanced settings tab
        adv_tab = ttk.Frame(self.notebook)
        self.notebook.add(adv_tab, text="Advanced")
        
        # Create potion settings
        self._create_potion_settings(potion_tab)
        
        # Create spell settings
        self._create_spell_settings(spell_tab)
        
        # Create advanced settings
        self._create_advanced_settings(adv_tab)
        
        # Save button at the bottom
        save_frame = ttk.Frame(self.parent)
        save_frame.pack(fill=tk.X, pady=5)
        
        self.save_button = tk.Button(
            save_frame,
            text="Save Configuration",
            command=self.save_callback,
            bg="#4CAF50",  # Green background
            fg="black",    # Black text for visibility
            font=("Arial", 10, "bold"),
            height=1
        )
        self.save_button.pack(fill=tk.X, pady=5)
    
    def _create_potion_settings(self, parent):
        """Create the potion settings UI"""
        # Thresholds frame
        thresholds_frame = ttk.LabelFrame(parent, text="Potion Thresholds", padding=5)
        thresholds_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Brief help text
        ttk.Label(thresholds_frame, 
                 text="Set when potions should be used (percentage of bar remaining)").pack(
                     anchor=tk.W, pady=(0, 5))
        
        # Two columns for thresholds
        threshold_frame = ttk.Frame(thresholds_frame)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        # Health threshold
        hp_frame = ttk.Frame(threshold_frame)
        hp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(hp_frame, text="Health %:", width=12).pack(side=tk.LEFT)
        self.hp_threshold = ttk.Spinbox(hp_frame, from_=1, to=99, width=5)
        self.hp_threshold.set(50)
        self.hp_threshold.pack(side=tk.LEFT)
        
        # Mana threshold
        mp_frame = ttk.Frame(threshold_frame)
        mp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mp_frame, text="Mana %:", width=12).pack(side=tk.LEFT)
        self.mp_threshold = ttk.Spinbox(mp_frame, from_=1, to=99, width=5)
        self.mp_threshold.set(30)
        self.mp_threshold.pack(side=tk.LEFT)
        
        # Stamina threshold
        sp_frame = ttk.Frame(threshold_frame)
        sp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sp_frame, text="Stamina %:", width=12).pack(side=tk.LEFT)
        self.sp_threshold = ttk.Spinbox(sp_frame, from_=1, to=99, width=5)
        self.sp_threshold.set(40)
        self.sp_threshold.pack(side=tk.LEFT)
        
        # Potion keys frame
        keys_frame = ttk.LabelFrame(parent, text="Potion Keys", padding=5)
        keys_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Brief help text
        ttk.Label(keys_frame, 
                 text="Set which keyboard keys are used for each potion type").pack(
                     anchor=tk.W, pady=(0, 5))
        
        # Two columns for keys
        key_frame = ttk.Frame(keys_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        # Health key
        hp_key_frame = ttk.Frame(key_frame)
        hp_key_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(hp_key_frame, text="Health Key:", width=12).pack(side=tk.LEFT)
        self.hp_key = ttk.Combobox(hp_key_frame, values=list("123456789"), width=3)
        self.hp_key.set("1")
        self.hp_key.pack(side=tk.LEFT)
        
        # Mana key
        mp_key_frame = ttk.Frame(key_frame)
        mp_key_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mp_key_frame, text="Mana Key:", width=12).pack(side=tk.LEFT)
        self.mp_key = ttk.Combobox(mp_key_frame, values=list("123456789"), width=3)
        self.mp_key.set("3")
        self.mp_key.pack(side=tk.LEFT)
        
        # Stamina key
        sp_key_frame = ttk.Frame(key_frame)
        sp_key_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sp_key_frame, text="Stamina Key:", width=12).pack(side=tk.LEFT)
        self.sp_key = ttk.Combobox(sp_key_frame, values=list("123456789"), width=3)
        self.sp_key.set("2")
        self.sp_key.pack(side=tk.LEFT)
    
    def _create_spell_settings(self, parent):
        """Create the spell settings UI"""
        # Spellcasting frame
        spell_frame = ttk.LabelFrame(parent, text="Auto Spellcasting", padding=5)
        spell_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Brief help text
        ttk.Label(spell_frame, 
                 text="Configure automatic spell casting at regular intervals").pack(
                     anchor=tk.W, pady=(0, 5))
        
        # Enable spellcasting
        enable_frame = ttk.Frame(spell_frame)
        enable_frame.pack(fill=tk.X, pady=5)
        
        self.spellcast_enabled = tk.BooleanVar(value=False)
        enable_check = ttk.Checkbutton(
            enable_frame, 
            text="Enable Auto Spellcasting", 
            variable=self.spellcast_enabled
        )
        enable_check.pack(anchor=tk.W)
        
        # Spell key
        key_frame = ttk.Frame(spell_frame)
        key_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(key_frame, text="Spell Key:", width=12).pack(side=tk.LEFT)
        self.spell_key = ttk.Combobox(
            key_frame, 
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"], 
            width=5
        )
        self.spell_key.set("F5")
        self.spell_key.pack(side=tk.LEFT)
        
        # Spell interval
        interval_frame = ttk.Frame(spell_frame)
        interval_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(interval_frame, text="Cast Interval:", width=12).pack(side=tk.LEFT)
        self.spell_interval = ttk.Spinbox(interval_frame, from_=0.5, to=10.0, increment=0.5, width=5)
        self.spell_interval.set(3.0)
        self.spell_interval.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(interval_frame, text="seconds").pack(side=tk.LEFT)
        
        # Spell targets
        target_frame = ttk.LabelFrame(parent, text="Spell Target (optional)", padding=5)
        target_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(target_frame, 
                 text="Configure where to click after pressing the spell key").pack(
                     anchor=tk.W, pady=(0, 5))
        
        # Target coordinates (placeholder for future enhancement)
        coord_frame = ttk.Frame(target_frame)
        coord_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(coord_frame, text="Uses right mouse click at current cursor position").pack(
            anchor=tk.W, pady=5)
    
    def _create_advanced_settings(self, parent):
        """Create the advanced settings UI"""
        # Scanning parameters
        scan_frame = ttk.LabelFrame(parent, text="Scanning Parameters", padding=5)
        scan_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Brief help text
        ttk.Label(scan_frame, 
                 text="Configure how frequently the bot checks bar values").pack(
                     anchor=tk.W, pady=(0, 5))
        
        # Scan interval
        interval_frame = ttk.Frame(scan_frame)
        interval_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(interval_frame, text="Scan Interval:", width=12).pack(side=tk.LEFT)
        self.scan_interval = ttk.Spinbox(interval_frame, from_=0.1, to=2.0, increment=0.1, width=5)
        self.scan_interval.set(0.5)
        self.scan_interval.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(interval_frame, text="seconds").pack(side=tk.LEFT)
        
        # Potion cooldown
        cooldown_frame = ttk.Frame(scan_frame)
        cooldown_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(cooldown_frame, text="Potion Cooldown:", width=12).pack(side=tk.LEFT)
        self.potion_cooldown = ttk.Spinbox(cooldown_frame, from_=1.0, to=10.0, increment=0.5, width=5)
        self.potion_cooldown.set(3.0)
        self.potion_cooldown.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(cooldown_frame, text="seconds").pack(side=tk.LEFT)
        
        # Debug options
        debug_frame = ttk.LabelFrame(parent, text="Debug Options", padding=5)
        debug_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Debug mode
        self.debug_var = tk.BooleanVar(value=True)
        debug_check = ttk.Checkbutton(
            debug_frame, 
            text="Enable Debug Mode (saves screenshots and logs extra information)", 
            variable=self.debug_var
        )
        debug_check.pack(anchor=tk.W, pady=5)
    
    def get_settings(self):
        """Get current settings as a dictionary"""
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
    
    def set_settings(self, settings):
        """Set settings from a dictionary"""
        # Thresholds
        thresholds = settings.get("thresholds", {})
        self.hp_threshold.set(thresholds.get("health", 50))
        self.mp_threshold.set(thresholds.get("mana", 30))
        self.sp_threshold.set(thresholds.get("stamina", 40))
        
        # Potion keys
        potion_keys = settings.get("potion_keys", {})
        self.hp_key.set(potion_keys.get("health", "1"))
        self.mp_key.set(potion_keys.get("mana", "3"))
        self.sp_key.set(potion_keys.get("stamina", "2"))
        
        # Spellcasting
        spellcasting = settings.get("spellcasting", {})
        self.spellcast_enabled.set(spellcasting.get("enabled", False))
        self.spell_key.set(spellcasting.get("spell_key", "F5"))
        self.spell_interval.set(spellcasting.get("spell_interval", 3.0))
        
        # Other settings
        self.scan_interval.set(settings.get("scan_interval", 0.5))
        self.debug_var.set(settings.get("debug_enabled", True))
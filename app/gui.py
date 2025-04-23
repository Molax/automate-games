"""
Legacy entry point for the Priston Tale Potion Bot
-------------------------------------------------
This module maintains backwards compatibility by importing from the new structure.
"""

import logging

# Import the main GUI class
from app.ui.main_gui import PristonTaleBot

# Import other components for backwards compatibility
from app.ui.scrollable_frame import ScrollableFrame
from app.ui.bar_selector_ui import BarSelectorUI, BarAdapter
from app.ui.window_selector_ui import WindowSelectorUI
from app.ui.settings_ui import SettingsUI
from app.bot.potion_bot import PotionBot
from app.bot.config_manager import ConfigManager

logger = logging.getLogger('PristonBot')
logger.info("Using legacy gui.py module (compatibility mode)")

# The original class is now imported directly from app.ui.main_gui
# All other imports are maintained for backwards compatibility
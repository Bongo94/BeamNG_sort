# mod_sorter/config/app_config.py
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Configuration constants for the application"""
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 800
    IMAGE_DISPLAY_WIDTH = 600
    IMAGE_DISPLAY_HEIGHT = 400
    MARKER_EXTENSION = ".mod_sorted"
    MOVE_FOLDERS_CONFIG = "config/move_folders.json"
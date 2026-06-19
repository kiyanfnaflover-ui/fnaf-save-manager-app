import sys
import os
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from core.game_detector import get_profile_by_id

def get_absolute_asset_path(relative_path: str) -> str:
    """
    Dynamically resolves paths for both development and PyInstaller EXE execution.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running inside the compiled PyInstaller standalone EXE
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Running normally via 'python main.py'
    # __file__ is inside 'ui/' folder, so going up one level gets us to the root project folder
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, relative_path)

class GameSelector(QListWidget):
    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(64, 64))
        self.setSpacing(10)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("GameSelector")

    def add_game(self, game_id: str):
        profile = get_profile_by_id(game_id)
        if not profile: 
            return
        
        item = QListWidgetItem(profile.title)
        item.setData(Qt.ItemDataRole.UserRole, game_id)
        
        # Build the exact path to the target game icon
        icon_relative_path = f"assets/{profile.icon_name}"
        icon_absolute_path = get_absolute_asset_path(icon_relative_path)
        
        item.setIcon(QIcon(icon_absolute_path))
        self.addItem(item)
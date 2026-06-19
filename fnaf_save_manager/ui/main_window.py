import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStatusBar, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.game_selector import GameSelector
from ui.game_editor import GameEditor
from core.scanner import ScannerThread

def resolve_resource_path(relative_path: str) -> str:
    """Looks for files next to the .exe when compiled, or in the project directory during dev."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FNAF Save Manager")
        self.resize(1000, 650)
        
        logo_path = resolve_resource_path("favicon.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        self.found_games = {} 
        self.setup_ui()
        self.start_scan()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.selector = GameSelector()
        self.selector.itemClicked.connect(self.on_game_selected)
        
        self.rescan_btn = QPushButton("🔄 Rescan System")
        self.rescan_btn.clicked.connect(self.start_scan)
        
        left_layout.addWidget(self.selector)
        left_layout.addWidget(self.rescan_btn)
        
        self.editor = GameEditor()
        self.editor.status_update.connect(self.show_status)
        
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([300, 700])
        
        main_layout.addWidget(self.splitter)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def start_scan(self):
        self.selector.clear()
        self.found_games.clear()
        self.rescan_btn.setEnabled(False)
        
        self.scanner = ScannerThread()
        self.scanner.progress.connect(self.show_status)
        self.scanner.game_found.connect(self.on_game_found)
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.start()

    def on_game_found(self, game_id: str, file_path: Path):
        self.found_games[game_id] = file_path
        self.selector.add_game(game_id)
        self.show_status(f"Found game data: {file_path.name}")

    def on_scan_finished(self):
        self.rescan_btn.setEnabled(True)
        count = len(self.found_games)
        if count == 0:
            self.show_status("Scan complete. No save files found.")
        else:
            self.show_status(f"Scan complete. Discovered {count} game(s).")

    def on_game_selected(self, item):
        game_id = item.data(Qt.ItemDataRole.UserRole)
        file_path = self.found_games.get(game_id)
        if file_path:
            self.editor.load_game(game_id, file_path)

    def show_status(self, message: str):
        self.status_bar.showMessage(message, 5000)
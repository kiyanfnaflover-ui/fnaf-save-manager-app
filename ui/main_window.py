import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStatusBar, QPushButton, QLabel, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.game_selector import GameCarousel
from ui.game_editor import GameEditor
from core.scanner import ScannerThread
from core.game_detector import get_profile_by_id

APP_VERSION = "v3.0"
CREATOR = "Created by K_F_"

def resolve_resource_path(relative_path: str) -> str:
    """Resolves bundled assets for both dev runs and compiled PyInstaller EXE."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            meipass = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(meipass):
                return meipass
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FNAF Save Manager v3.0 - Created by K_F_")
        self.resize(1080, 660)
        self.setMinimumSize(900, 540)

        logo_path = resolve_resource_path("favicon.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.found_games = {}
        self.scanner = None
        self.setup_ui()
        self.start_scan()

    def setup_ui(self):
        self.editor = GameEditor()
        self.editor.status_update.connect(self.set_status)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(12)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        self.splitter.addWidget(self._build_sidebar())
        self.splitter.addWidget(self.editor)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([270, 810])

        body_layout.addWidget(self.splitter)
        root.addWidget(body, 1)

        root.addWidget(self._build_action_bar())
        self.setup_status_bar()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        texts = QVBoxLayout()
        texts.setSpacing(1)
        title = QLabel("FNAF Save Manager")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Edit save files for Five Nights at Freddy's 1-6 and Ultimate Custom Night")
        subtitle.setObjectName("headerSubtitle")
        texts.addWidget(title)
        texts.addWidget(subtitle)

        version = QLabel(APP_VERSION)
        version.setObjectName("versionBadge")

        layout.addLayout(texts)
        layout.addStretch()
        layout.addWidget(version)
        return header

    def _build_sidebar(self) -> QWidget:
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        caption = QLabel("GAMES")
        caption.setObjectName("navCaption")

        self.selector = GameCarousel()
        self.selector.game_selected.connect(self.on_game_selected)

        panel_layout.addWidget(caption)
        panel_layout.addWidget(self.selector, 1)
        return panel

    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("actionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.rescan_btn = QPushButton("Rescan System")
        self.rescan_btn.setToolTip("Scan for FNAF save files again")
        self.rescan_btn.clicked.connect(self.start_scan)

        self.btn_reload = QPushButton("Reload from Disk")
        self.btn_reload.setEnabled(False)
        self.btn_reload.clicked.connect(self.editor.reload_game)

        self.btn_backup = QPushButton("Create Backup")
        self.btn_backup.setEnabled(False)
        self.btn_backup.clicked.connect(self.editor.create_backup)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.editor.save_changes)

        layout.addWidget(self.rescan_btn)
        layout.addStretch()
        layout.addWidget(self.btn_reload)
        layout.addWidget(self.btn_backup)
        layout.addWidget(self.btn_save)
        return bar

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.set_status("Ready")

    def set_status(self, message: str, timeout: int = 5000):
        self.status_bar.showMessage(message, timeout)

    def start_scan(self):
        if self.scanner is not None and self.scanner.isRunning():
            return

        self.selector.clear()
        self.found_games.clear()
        self.rescan_btn.setEnabled(False)
        self.set_status("Scanning for FNAF save files...")

        self.scanner = ScannerThread()
        self.scanner.progress.connect(self.set_status)
        self.scanner.game_found.connect(self.on_game_found)
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.start()

    def on_game_found(self, game_id: str, file_path: Path):
        if game_id in self.found_games:
            return
        self.found_games[game_id] = file_path
        self.selector.add_game(game_id)
        self.set_status(f"Found save file: {file_path.name}")

    def on_scan_finished(self):
        self.rescan_btn.setEnabled(True)
        count = len(self.found_games)
        if count == 0:
            self.set_status("No save file detected. Have you played the games yet?")
            self.editor.show_empty()
        else:
            self.set_status(f"Scan complete. Found {count} game(s).")
            self.selector.select_game(0, animate=False)

    def on_game_selected(self, game_id: str):
        file_path = self.found_games.get(game_id)
        if file_path:
            self.editor.load_game(game_id, file_path)
            self.btn_reload.setEnabled(True)
            self.btn_backup.setEnabled(True)
            self.btn_save.setEnabled(True)
            profile = get_profile_by_id(game_id)
            title = profile.title if profile else game_id
            self.set_status(f"Editing: {title}")
        else:
            self.editor.show_empty()

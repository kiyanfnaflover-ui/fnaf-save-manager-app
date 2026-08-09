import sys
import os
import ctypes
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStatusBar, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from ui.game_selector import GameCarousel, FOCUS_H
from ui.game_editor import GameEditor
from core.scanner import ScannerThread
from core.game_detector import get_profile_by_id

APP_VERSION = "v4.0"
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
        self.setWindowTitle("FNAF Save Manager v4.0 - Created by K_F_")
        self.resize(1180, 740)
        self.setMinimumSize(960, 600)

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

        self.carousel = GameCarousel()
        self.carousel.setFixedHeight(FOCUS_H + 66)
        self.carousel.game_selected.connect(self.on_game_selected)
        root.addWidget(self.carousel)

        root.addWidget(self.editor, 1)
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
        subtitle = QLabel("Edit save files across all Five Nights at Freddy's titles")
        subtitle.setObjectName("headerSubtitle")
        texts.addWidget(title)
        texts.addWidget(subtitle)

        version = QLabel(APP_VERSION)
        version.setObjectName("versionBadge")

        layout.addLayout(texts)
        layout.addStretch()
        layout.addWidget(version)
        return header

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

        self.btn_open_folder = QPushButton("Open Save Folder")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_save_folder)

        self._apply_button_icon(self.rescan_btn, "refresh")
        self._apply_button_icon(self.btn_reload, "reload")
        self._apply_button_icon(self.btn_backup, "backup")
        self._apply_button_icon(self.btn_save, "save")
        self._apply_button_icon(self.btn_open_folder, "folder")

        layout.addWidget(self.rescan_btn)
        layout.addStretch()
        layout.addWidget(self.btn_reload)
        layout.addWidget(self.btn_backup)
        layout.addWidget(self.btn_open_folder)
        layout.addWidget(self.btn_save)
        return bar

    def _apply_button_icon(self, button: QPushButton, icon_name: str):
        """Attach a downloaded/generated button icon. Never crashes if missing."""
        path = resolve_resource_path(f"assets/icons/{icon_name}.svg")
        if not os.path.exists(path):
            return
        icon = QIcon(path)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.set_status("Ready")

    def set_status(self, message: str, timeout: int = 5000):
        self.status_bar.showMessage(message, timeout)

    # ---------- native interop ----------

    def open_save_folder(self):
        """Open the folder of the currently selected save file via the native C
        Win32 ShellExecuteW API (shell32) - no Python/PySide involvement."""
        path = getattr(self, '_current_save_path', None)
        if not path:
            return
        folder = os.path.dirname(str(path))
        if not folder or not os.path.isdir(folder):
            folder = os.path.dirname(folder) or os.path.expanduser("~")
        try:
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "open", folder, None, None, 1)
            if result <= 32:
                self.set_status(f"Could not open folder (native error {result}).")
            else:
                self.set_status(f"Opened save folder: {folder}")
        except Exception as exc:
            self.set_status(f"Could not open folder: {exc}")

    # ---------- scanning ----------

    def start_scan(self):
        if self.scanner is not None and self.scanner.isRunning():
            return

        self.carousel.populate_all()
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
        self.carousel.set_available(game_id)
        self.set_status(f"Found save file: {file_path.name}")

    def on_scan_finished(self):
        self.rescan_btn.setEnabled(True)
        count = len(self.found_games)
        if count == 0:
            self.set_status("No save file detected. Have you played the games yet?")
            self.editor.show_empty()
        else:
            self.set_status(f"Scan complete. Found {count} game(s). Use arrow keys or click a cover to navigate.")
            self.carousel.select_first_available()

    def on_game_selected(self, game_id: str):
        file_path = self.found_games.get(game_id)
        if file_path:
            self._current_save_path = file_path
            self.editor.load_game(game_id, file_path)
            self.btn_reload.setEnabled(True)
            self.btn_backup.setEnabled(True)
            self.btn_save.setEnabled(True)
            self.btn_open_folder.setEnabled(True)
            profile = get_profile_by_id(game_id)
            title = profile.title if profile else game_id
            self.set_status(f"Editing: {title}")
        else:
            self.editor.show_empty()

import os
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from core.game_detector import get_all_profiles

class ScannerThread(QThread):
    progress = Signal(str)
    game_found = Signal(str, Path)  # Emits (game_id, file_path)
    finished = Signal()

    def run(self):
        self.progress.emit("Scanning for FNAF save files...")

        appdata = os.environ.get('APPDATA')
        localappdata = os.environ.get('LOCALAPPDATA')

        mmf_dir = Path(appdata) / "MMFApplications" if appdata else None

        profiles = get_all_profiles()
        found_any = False

        for profile in profiles:
            candidates = []
            if profile.root == "APPDATA_MMF":
                if mmf_dir is not None:
                    candidates.append(mmf_dir / profile.save_name)
            elif profile.root == "APPDATA_JRSSAVE":
                if appdata:
                    candidates.append(Path(appdata) / "JRs" / profile.save_name)
            elif profile.root == "LOCALAPPDATA":
                if localappdata:
                    candidates.append(Path(localappdata) / profile.save_name)

            for save_path in candidates:
                if save_path.exists():
                    self.game_found.emit(profile.id, save_path)
                    found_any = True

        if not found_any:
            self.progress.emit("No MMFApplications or UE4 save folders found. Have you played the games yet?")

        self.finished.emit()

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
        
        # FNAF games save to C:\Users\<User>\AppData\Roaming\MMFApplications
        appdata = os.environ.get('APPDATA')
        if not appdata:
            self.progress.emit("Error: Could not locate AppData directory.")
            self.finished.emit()
            return

        mmf_dir = Path(appdata) / "MMFApplications"
        
        if not mmf_dir.exists():
            self.progress.emit("No MMFApplications folder found. Have you played the games yet?")
            self.finished.emit()
            return

        # Fetch the new game profiles we just created
        profiles = get_all_profiles()
        
        for profile in profiles:
            save_path = mmf_dir / profile.save_filename
            if save_path.exists():
                # Pass the exact ID and Path back to the Main Window
                self.game_found.emit(profile.id, save_path)
                
        self.finished.emit()
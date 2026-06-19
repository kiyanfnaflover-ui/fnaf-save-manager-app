import shutil
from pathlib import Path
from datetime import datetime
import os

class BackupManager:
    """Creates timestamped backups before applying user mutations."""
    
    @staticmethod
    def create_backup(original_file: Path) -> Path | None:
        if not original_file.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original_file.name}_{timestamp}.bak"
        backup_path = original_file.parent / backup_name
        
        try:
            shutil.copy2(original_file, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
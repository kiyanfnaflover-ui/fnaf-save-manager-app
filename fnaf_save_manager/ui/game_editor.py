from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSpinBox, QPushButton, QGroupBox, QCheckBox, QMessageBox, QScrollArea)
from PySide6.QtCore import Signal
from core.save_parser import SaveParser
from core.backup_manager import BackupManager

class GameEditor(QWidget):
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.parser = None
        self.current_game_id = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll)
        
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save Changes")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_changes)
        
        self.btn_backup = QPushButton("📦 Create Backup")
        self.btn_backup.setEnabled(False)
        self.btn_backup.clicked.connect(self.create_backup)
        
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_backup)
        self.layout.addLayout(button_layout)

    def clear_layout(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_game(self, game_id: str, file_path):
        self.current_game_id = game_id
        self.parser = SaveParser(file_path)
        self.parser.load()
        
        self.btn_save.setEnabled(True)
        self.btn_backup.setEnabled(True)
        self.clear_layout()
        
        # Route to the correct UI builder
        if game_id in ["fnaf1", "fnaf2", "fnaf3", "fnaf4"]:
            self.build_standard_nights_ui(game_id)
        elif game_id == "fnaf5":
            self.build_fnaf5_ui()
        elif game_id == "fnaf6":
            self.build_fnaf6_ui()
        elif game_id == "ucn":
            self.build_ucn_ui()
            
        self.scroll_layout.addStretch()
        self.status_update.emit(f"Loaded: {file_path.name}")

    def build_standard_nights_ui(self, game_id):
        group_level = QGroupBox("Main Progression")
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Current Night:"))
        self.spin_night = QSpinBox()
        
        max_night = 8 if game_id == "fnaf4" else 7 
        self.spin_night.setRange(1, max_night)
        
        # FIX: FNAF 4 uses "night" in its save file, while 1-3 use "level"
        night_key = "night" if game_id == "fnaf4" else "level"
        self.spin_night.setValue(self.parser.get_int(night_key, 1))
        
        level_layout.addWidget(self.spin_night)
        group_level.setLayout(level_layout)
        self.scroll_layout.addWidget(group_level)

        group_extras = QGroupBox("Stars & Extras")
        extras_layout = QVBoxLayout()
        
        self.chk_beatgame = QCheckBox("Unlock Star 1 (Beat Game)")
        self.chk_beatgame.setChecked(self.parser.get_int("beatgame") == 1)
        extras_layout.addWidget(self.chk_beatgame)
        
        self.chk_beat6 = QCheckBox("Unlock Star 2 (Beat Night 6)")
        self.chk_beat6.setChecked(self.parser.get_int("beat6") == 1)
        extras_layout.addWidget(self.chk_beat6)

        if game_id == "fnaf2":
            self.chk_fnaf2_plushies = QCheckBox("🧸 Unlock All Custom Night Desk Plushies")
            self.chk_fnaf2_plushies.setChecked(self.parser.get_int("c1") == 1)
            extras_layout.addWidget(self.chk_fnaf2_plushies)
            
        elif game_id == "fnaf3":
            self.chk_fnaf3_goodend = QCheckBox("✨ Unlock Good Ending (3rd Star)")
            self.chk_fnaf3_goodend.setChecked(self.parser.get_int("goodending") == 1)
            extras_layout.addWidget(self.chk_fnaf3_goodend)
            
        elif game_id == "fnaf4":
            self.chk_beat7 = QCheckBox("Unlock Star 3 (Beat Nightmare)")
            self.chk_beat7.setChecked(self.parser.get_int("beat7") == 1)
            self.chk_beat8 = QCheckBox("Unlock Star 4 (Beat 20/20/20/20)")
            self.chk_beat8.setChecked(self.parser.get_int("beat8") == 1)
            extras_layout.addWidget(self.chk_beat7)
            extras_layout.addWidget(self.chk_beat8)

        group_extras.setLayout(extras_layout)
        self.scroll_layout.addWidget(group_extras)

    def build_fnaf5_ui(self):
        group_main = QGroupBox("Sister Location Progression")
        layout = QVBoxLayout()
        
        row_night = QHBoxLayout()
        row_night.addWidget(QLabel("Current Night:"))
        self.spin_sl_night = QSpinBox()
        self.spin_sl_night.setRange(1, 5)
        self.spin_sl_night.setValue(self.parser.get_int("current", 1))
        row_night.addWidget(self.spin_sl_night)
        layout.addLayout(row_night)
        
        self.chk_sl_beat1 = QCheckBox("Unlock Star 1 (Beat Night 5)")
        self.chk_sl_beat1.setChecked(self.parser.get_int("beat1") == 1)
        layout.addWidget(self.chk_sl_beat1)
        
        self.chk_sl_keycard = QCheckBox("Unlock Keycard (Baby's Minigame)")
        self.chk_sl_keycard.setChecked(self.parser.get_int("keycard") == 1)
        layout.addWidget(self.chk_sl_keycard)

        self.chk_sl_beat3 = QCheckBox("Unlock Star 3 (Custom Night/Ennard)")
        self.chk_sl_beat3.setChecked(self.parser.get_int("beat3") == 1)
        layout.addWidget(self.chk_sl_beat3)

        group_main.setLayout(layout)
        self.scroll_layout.addWidget(group_main)

    def build_fnaf6_ui(self):
        group_main = QGroupBox("Pizzeria Simulator Stats")
        layout = QVBoxLayout()
        
        row_night = QHBoxLayout()
        row_night.addWidget(QLabel("Current Night/Phase:"))
        self.spin_f6_night = QSpinBox()
        self.spin_f6_night.setRange(1, 6) # Max is Saturday
        self.spin_f6_night.setValue(self.parser.get_int("night", 1))
        row_night.addWidget(self.spin_f6_night)
        layout.addLayout(row_night)
        
        row_money = QHBoxLayout()
        row_money.addWidget(QLabel("Money ($):"))
        self.spin_f6_money = QSpinBox()
        self.spin_f6_money.setRange(0, 9999999) 
        self.spin_f6_money.setValue(self.parser.get_int("money", 0))
        row_money.addWidget(self.spin_f6_money)
        layout.addLayout(row_money)

        row_play = QHBoxLayout()
        row_play.addWidget(QLabel("Play Tokens:"))
        self.spin_f6_play = QSpinBox()
        self.spin_f6_play.setRange(0, 999)
        self.spin_f6_play.setValue(self.parser.get_int("play", 0))
        row_play.addWidget(self.spin_f6_play)
        layout.addLayout(row_play)
        
        group_main.setLayout(layout)
        self.scroll_layout.addWidget(group_main)

        group_certs = QGroupBox("Certificates & Endings")
        cert_layout = QVBoxLayout()
        
        self.chk_cert1 = QCheckBox("Certificate 1 (Completion / Good Ending)")
        self.chk_cert1.setChecked(self.parser.get_int("cert1") == 1)
        cert_layout.addWidget(self.chk_cert1)
        
        self.chk_cert2 = QCheckBox("Certificate 2 (Mediocrity)")
        self.chk_cert2.setChecked(self.parser.get_int("cert2") == 1)
        cert_layout.addWidget(self.chk_cert2)
        
        self.chk_cert3 = QCheckBox("Certificate 3 (Insanity)")
        self.chk_cert3.setChecked(self.parser.get_int("cert3") == 1)
        cert_layout.addWidget(self.chk_cert3)
        
        self.chk_cert4 = QCheckBox("Certificate 4 (Blacklisted)")
        self.chk_cert4.setChecked(self.parser.get_int("cert4") == 1)
        cert_layout.addWidget(self.chk_cert4)
        
        self.chk_cert5 = QCheckBox("Certificate 5 (Bankruptcy)")
        self.chk_cert5.setChecked(self.parser.get_int("cert5") == 1)
        cert_layout.addWidget(self.chk_cert5)
        
        self.chk_cert6 = QCheckBox("Certificate 6 (Lorekeeper)")
        self.chk_cert6.setChecked(self.parser.get_int("cert6") == 1)
        cert_layout.addWidget(self.chk_cert6)
        
        group_certs.setLayout(cert_layout)
        self.scroll_layout.addWidget(group_certs)

    def build_ucn_ui(self):
        group_ucn = QGroupBox("UCN Powerups & Stats")
        layout = QVBoxLayout()
        
        hs_layout = QHBoxLayout()
        hs_layout.addWidget(QLabel("Best High Score:"))
        self.spin_hs = QSpinBox()
        self.spin_hs.setRange(0, 10600)
        self.spin_hs.setSingleStep(100)
        self.spin_hs.setValue(self.parser.get_int("hs", 0))
        hs_layout.addWidget(self.spin_hs)
        layout.addLayout(hs_layout)
        
        self.spin_coins = self.create_ucn_spinbox(layout, "Faz-Coins", "coins")
        self.spin_fridge = self.create_ucn_spinbox(layout, "Frigid (AC)", "fridge")
        self.spin_battery = self.create_ucn_spinbox(layout, "3-Coins", "battery")
        self.spin_dd = self.create_ucn_spinbox(layout, "DD Repel", "dd")

        group_ucn.setLayout(layout)
        self.scroll_layout.addWidget(group_ucn)

    def create_ucn_spinbox(self, layout, label_text, key):
        row = QHBoxLayout()
        row.addWidget(QLabel(f"{label_text}:"))
        spin = QSpinBox()
        spin.setRange(0, 99)
        spin.setValue(self.parser.get_int(key, 0))
        row.addWidget(spin)
        layout.addLayout(row)
        return spin

    def save_changes(self):
        if not self.parser: return
        
        if self.current_game_id in ["fnaf1", "fnaf2", "fnaf3", "fnaf4"]:
            night_key = "night" if self.current_game_id == "fnaf4" else "level"
            self.parser.set_int(night_key, self.spin_night.value())
            self.parser.set_int("beatgame", 1 if getattr(self, "chk_beatgame", False) and self.chk_beatgame.isChecked() else 0)
            self.parser.set_int("beat6", 1 if getattr(self, "chk_beat6", False) and self.chk_beat6.isChecked() else 0)
            
            if self.current_game_id == "fnaf2" and getattr(self, "chk_fnaf2_plushies", False) and self.chk_fnaf2_plushies.isChecked():
                for i in range(1, 11):
                    self.parser.set_int(f"c{i}", 1)
            
            if self.current_game_id == "fnaf3" and getattr(self, "chk_fnaf3_goodend", False):
                self.parser.set_int("goodending", 1 if self.chk_fnaf3_goodend.isChecked() else 0)
                
            if self.current_game_id == "fnaf4":
                self.parser.set_int("beat7", 1 if getattr(self, "chk_beat7", False) and self.chk_beat7.isChecked() else 0)
                self.parser.set_int("beat8", 1 if getattr(self, "chk_beat8", False) and self.chk_beat8.isChecked() else 0)

        elif self.current_game_id == "fnaf5":
            self.parser.set_int("current", self.spin_sl_night.value())
            self.parser.set_int("beat1", 1 if self.chk_sl_beat1.isChecked() else 0)
            self.parser.set_int("keycard", 1 if self.chk_sl_keycard.isChecked() else 0)
            self.parser.set_int("beat3", 1 if self.chk_sl_beat3.isChecked() else 0)

        elif self.current_game_id == "fnaf6":
            self.parser.set_int("night", self.spin_f6_night.value())
            self.parser.set_int("money", self.spin_f6_money.value())
            self.parser.set_int("play", self.spin_f6_play.value())
            
            self.parser.set_int("cert1", 1 if self.chk_cert1.isChecked() else 0)
            self.parser.set_int("cert2", 1 if self.chk_cert2.isChecked() else 0)
            self.parser.set_int("cert3", 1 if self.chk_cert3.isChecked() else 0)
            self.parser.set_int("cert4", 1 if self.chk_cert4.isChecked() else 0)
            self.parser.set_int("cert5", 1 if self.chk_cert5.isChecked() else 0)
            self.parser.set_int("cert6", 1 if self.chk_cert6.isChecked() else 0)
            
            # Sync internal hidden achievements to prevent the game from glitching
            self.parser.set_int("comp", 1 if self.chk_cert1.isChecked() else 0)
            self.parser.set_int("insanity", 1 if self.chk_cert3.isChecked() else 0)
            self.parser.set_int("bankrupt", 1 if self.chk_cert5.isChecked() else 0)
            self.parser.set_int("lorekeeper", 1 if self.chk_cert6.isChecked() else 0)

        elif self.current_game_id == "ucn":
            self.parser.set_int("hs", self.spin_hs.value())
            self.parser.set_int("coins", self.spin_coins.value())
            self.parser.set_int("fridge", self.spin_fridge.value())
            self.parser.set_int("battery", self.spin_battery.value())
            self.parser.set_int("dd", self.spin_dd.value())

        self.parser.save()
        QMessageBox.information(self, "Success", "Save file updated safely!")
        self.status_update.emit("Save successful.")

    def create_backup(self):
        if not self.parser: return
        backup_path = BackupManager.create_backup(self.parser.file_path)
        if backup_path:
            QMessageBox.information(self, "Backup Created", f"Backed up to:\n{backup_path}")
            self.status_update.emit("Backup created.")
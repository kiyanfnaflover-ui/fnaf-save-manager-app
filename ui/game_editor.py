import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QGroupBox, QCheckBox, QScrollArea, QStackedWidget, QFormLayout, QFrame
)
from PySide6.QtCore import Signal, Qt
from core.save_parser import SaveParser
from core.backup_manager import BackupManager

class GameEditor(QStackedWidget):
    """Save editor. Page 0 = empty placeholder, page 1 = editor content."""
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.parser = None
        self.cert_parser = None
        self.current_game_id = None
        self._file_bar_path = None
        self.checkboxes = {}
        self.setup_ui()

    # ---------- UI construction ----------

    def setup_ui(self):
        empty = QWidget()
        empty.setObjectName("placeholderPane")
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(30, 30, 30, 30)
        self.empty_label = QLabel("Select a game on the left to edit its save data.\n\n"
                                  "If no games appear, launch one of the FNAF titles first,\n"
                                  "then press Rescan System.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setObjectName("mutedLabel")
        empty_layout.addWidget(self.empty_label)
        self.addWidget(empty)

        content = QWidget()
        content.setObjectName("placeholderPane")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(10)

        self.file_bar = QFrame()
        self.file_bar.setObjectName("fileBar")
        file_bar_layout = QHBoxLayout(self.file_bar)
        file_bar_layout.setContentsMargins(10, 4, 10, 4)
        file_label = QLabel("SAVE FILE")
        file_label.setObjectName("fileLabel")
        self.file_name_label = QLabel("")
        self.file_name_label.setObjectName("fileName")
        file_bar_layout.addWidget(file_label)
        file_bar_layout.addWidget(self.file_name_label)
        file_bar_layout.addStretch()
        self.content_layout.addWidget(self.file_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(4, 0, 8, 4)
        self.scroll.setWidget(self.scroll_content)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_layout.addWidget(self.scroll, 1)

        self.addWidget(content)
        self.setCurrentIndex(0)

    def show_empty(self, message: str = None):
        if message:
            self.empty_label.setText(message)
        self.setCurrentIndex(0)

    def clear_layout(self):
        self.checkboxes.clear()
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # ---------- Load / reload ----------

    def load_game(self, game_id: str, file_path):
        self.current_game_id = game_id
        self._current_file_path = str(file_path)
        self.parser = SaveParser(file_path, game_id)
        self.parser.load()

        self.cert_parser = None
        if game_id == "fnaf6":
            cert_path = os.path.join(os.path.dirname(str(file_path)), "CERT")
            self.cert_parser = SaveParser(cert_path, "fnaf6")
            self.cert_parser.load()

        self.clear_layout()

        if game_id in ["fnaf1", "fnaf2", "fnaf3", "fnaf4"]:
            self.build_standard_nights_ui(game_id)
        elif game_id == "fnaf5":
            self.build_fnaf5_ui()
        elif game_id == "fnaf6":
            self.build_fnaf6_ui()
        elif game_id == "ucn":
            self.build_ucn_ui()

        self.scroll_layout.addStretch()
        self.file_name_label.setText(os.path.basename(str(file_path)))
        self.file_bar.setToolTip(str(file_path))
        self.setCurrentIndex(1)

    def reload_game(self):
        if not self.parser:
            return
        self.parser.load()
        if self.cert_parser:
            self.cert_parser.load()
        self.load_game(self.current_game_id, self._current_file_path)
        self.status_update.emit("Save file reloaded from disk.")

    def _group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout(group)
        form.setContentsMargins(12, 10, 12, 10)
        form.setSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return group, form

    # ---------- FNAF 1-4 ----------

    def build_standard_nights_ui(self, game_id):
        group, form = self._group("Main Progression")
        max_night = 8 if game_id == "fnaf4" else 7
        night_key = "night" if game_id == "fnaf4" else "level"
        self.spin_night = self._add_row(form, "Current night", night_key, 1, max_night)
        self.scroll_layout.addWidget(group)

        group2, form2 = self._group("Stars & Menu Unlocks")
        self.add_checkbox(form2, "Unlock Star 1 (beat the game / night 5)", "beatgame")
        self.add_checkbox(form2, "Unlock Star 2 (beat night 6)", "beat6")
        if game_id == "fnaf1":
            self.add_checkbox(form2, "Unlock Star 3 (beat 4/20 mode)", "beat7")
        elif game_id == "fnaf2":
            self.add_checkbox(form2, "Unlock Star 3 (beat custom night 10/20)", "beat7")
            self.add_checkbox(form2, "Unlock all custom night desk plushies (c1-c10)", "c1")
        elif game_id == "fnaf3":
            self.add_checkbox(form2, "Unlock star (good ending, souls rested)", "goodending")
            self.add_checkbox(form2, "Unlock star (beat aggressive nightmare mode)", "beat7")
        elif game_id == "fnaf4":
            self.add_checkbox(form2, "Unlock Star 3 (beat nightmare / night 7)", "beat7")
            self.add_checkbox(form2, "Unlock Star 4 (beat 20/20/20/20 / night 8)", "beat8")
        self.scroll_layout.addWidget(group2)

    # ---------- FNAF 5 / Sister Location ----------

    def build_fnaf5_ui(self):
        group, form = self._group("Progression")
        self.spin_sl_night = self._add_row(form, "Current night", "current", 1, 5)
        self.scroll_layout.addWidget(group)

        group2, form2 = self._group("Stars")
        self.add_checkbox(form2, "Unlock Star 1 (real ending / night 5)", "beat1")
        self.add_checkbox(form2, "Unlock Star 2 (keycard / Baby's death minigame)", "keycard")
        self.add_checkbox(form2, "Unlock Star 3 (fake ending / Ennard private room)", "beat3")
        self.add_checkbox(form2, "Unlock Star 4 (beat 10/20 Golden Freddy challenge)", "beat4")
        self.scroll_layout.addWidget(group2)

    # ---------- FNAF 6 ----------

    def build_fnaf6_ui(self):
        group, form = self._group("Pizzeria Simulator")
        self.spin_f6_night = self._add_row(form, "Current night/day", "night", 1, 5, default=self.parser.get_int("day", 1))
        self.spin_f6_money = self._add_row(form, "Money ($)", "money", 0, 9999999)
        self.spin_f6_play = self._add_row(form, "Play tokens", "play", 0, 999)
        self.scroll_layout.addWidget(group)

        group2, form2 = self._group("Certificates & Stars (saved in the CERT file)")
        certs_info = [
            ("Certificate 1 + Star: Completion (good ending)", "6th"),
            ("Certificate 2 + Star: Mediocrity", "med"),
            ("Certificate 3: Insanity", "ins"),
            ("Certificate 4 + Star: Blacklisted", "bla"),
            ("Certificate 5 + Star: Bankruptcy", "ban"),
            ("Certificate 6: Lorekeeper / Alternate", "com"),
        ]
        for label, key in certs_info:
            self.add_checkbox(form2, label, key, custom_parser=self.cert_parser)
        self.scroll_layout.addWidget(group2)

    # ---------- UCN ----------

    def build_ucn_ui(self):
        group, form = self._group("Ultimate Custom Night")
        self.spin_hs = self._add_row(form, "Best high score", "hs", 0, 10600, step=50)
        self.spin_coins = self._add_row(form, "Faz-Coins", "coins", 0, 99)
        self.spin_fridge = self._add_row(form, "Frigid (AC)", "fridge", 0, 99)
        self.spin_battery = self._add_row(form, "Plush coins", "battery", 0, 99)
        self.spin_dd = self._add_row(form, "DD repel", "dd", 0, 99)
        self.scroll_layout.addWidget(group)

    # ---------- helpers ----------

    def _add_row(self, layout, label: str, key: str, lo: int, hi: int, default: int = 0, step: int = 1):
        from PySide6.QtWidgets import QSpinBox
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSingleStep(step)
        spin.setValue(self.parser.get_int(key, default))
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(110)
        layout.addRow(label, spin)
        return spin

    def add_checkbox(self, layout, label_text, key, custom_parser=None):
        p = custom_parser if custom_parser else self.parser
        chk = QCheckBox(label_text)
        chk.setChecked(p.get_int(key) == 1)
        layout.addRow(chk)
        self.checkboxes[(key, p)] = chk

    # ---------- Write ----------

    def write_values(self):
        gid = self.current_game_id
        if gid in ["fnaf1", "fnaf2", "fnaf3", "fnaf4"]:
            night_key = "night" if gid == "fnaf4" else "level"
            self.parser.set_int(night_key, self.spin_night.value())
        elif gid == "fnaf5":
            self.parser.set_int("current", self.spin_sl_night.value())
        elif gid == "fnaf6":
            self.parser.set_int("day", self.spin_f6_night.value())
            self.parser.set_int("night", self.spin_f6_night.value())
            self.parser.set_int("money", self.spin_f6_money.value())
            self.parser.set_int("play", self.spin_f6_play.value())
        elif gid == "ucn":
            self.parser.set_int("hs", self.spin_hs.value())
            self.parser.set_int("coins", self.spin_coins.value())
            self.parser.set_int("fridge", self.spin_fridge.value())
            self.parser.set_int("battery", self.spin_battery.value())
            self.parser.set_int("dd", self.spin_dd.value())

        for (key, p), chk in self.checkboxes.items():
            p.set_int(key, 1 if chk.isChecked() else 0)

        if gid == "fnaf2":
            c1_chk = self.checkboxes.get(("c1", self.parser))
            if c1_chk and c1_chk.isChecked():
                for i in range(2, 11):
                    self.parser.set_int(f"c{i}", 1)

    def save_changes(self):
        if not self.parser:
            return
        self.write_values()
        self.parser.save()
        if self.cert_parser:
            self.cert_parser.save()
        self.reload_game()
        self.status_update.emit("Changes saved successfully.")

    def create_backup(self):
        if not self.parser:
            return
        saved = []
        main_bak = BackupManager.create_backup(self.parser.file_path)
        if main_bak:
            saved.append(main_bak.name)
        if self.current_game_id == "fnaf6" and self.cert_parser and os.path.exists(self.cert_parser.file_path):
            cert_bak = BackupManager.create_backup(self.cert_parser.file_path)
            if cert_bak:
                saved.append(cert_bak.name)
        if saved:
            self.status_update.emit("Backup created: " + ", ".join(saved))
        else:
            self.status_update.emit("Could not create a backup.")
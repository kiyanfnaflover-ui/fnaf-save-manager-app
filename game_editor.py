import os
import sys
import configparser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QGroupBox, QCheckBox, QScrollArea, QStackedWidget, QFormLayout, QFrame
)
from PySide6.QtCore import Signal, Qt
from core.save_parser import SaveParser
from core.gvas_parser import GvasSave
from core.backup_manager import BackupManager
from core.game_detector import get_profile_by_id


def _make_group(title: str):
    group = QGroupBox(title)
    form = QFormLayout(group)
    form.setContentsMargins(12, 10, 12, 10)
    form.setSpacing(6)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return group, form


class GameEditor(QStackedWidget):
    """Config-driven save editor. Page 0 = empty placeholder, page 1 = editor."""
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.parser = None          # SaveParser (ini)
        self.cert_parser = None     # SaveParser for FNAF6 CERT
        self.gvas = None            # GvasSave (Help Wanted)
        self.current_game_id = None
        self._current_file_path = None
        self.spins = {}
        self.checkboxes = {}
        self.setup_ui()

    # ---------- UI construction ----------

    def setup_ui(self):
        empty = QWidget()
        empty.setObjectName("placeholderPane")
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(30, 30, 30, 30)
        self.empty_label = QLabel("Choose a game cover above to edit its save data.\n\n"
                                  "Games with a detected save are highlighted in the carousel.\n"
                                  "Launch an unrecognized game first, then press Rescan System.")
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
        self.spins.clear()
        self.checkboxes.clear()
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # ---------- Load / reload ----------

    def load_game(self, game_id: str, file_path):
        self.current_game_id = game_id
        self._current_file_path = str(file_path)
        profile = get_profile_by_id(game_id)

        self.parser = None
        self.cert_parser = None
        self.gvas = None

        if profile and profile.engine == "gvas":
            self.gvas = GvasSave(file_path).load()
        else:
            self.parser = SaveParser(file_path, game_id)
            self.parser.load()
            if game_id == "fnaf6":
                cert_path = os.path.join(os.path.dirname(str(file_path)), "CERT")
                self.cert_parser = SaveParser(cert_path, "fnaf6")
                self.cert_parser.load()

        self.clear_layout()
        if profile:
            self._build_fields(profile)
        self.scroll_layout.addStretch()
        self.file_name_label.setText(os.path.basename(str(file_path)))
        self.file_bar.setToolTip(str(file_path))
        self.setCurrentIndex(1)

    def reload_game(self):
        if not (self.parser or self.gvas):
            return
        if self.parser:
            self.parser.load()
            if self.cert_parser:
                self.cert_parser.load()
        else:
            self.gvas.load()
        self.load_game(self.current_game_id, self._current_file_path)
        self.status_update.emit("Save file reloaded from disk.")

    # ---------- config-driven field building ----------

    def _build_fields(self, profile):
        main_group, main_form = _make_group("Main Progression")
        cert_group, cert_form = _make_group("Certificates & Stars (saved in the CERT file)")
        main_has, cert_has = False, False

        for f in profile.fields:
            if f.kind == "cert_bool":
                cert_has = True
                self._add_checkbox(cert_form, f.label, f.key, parser=self.cert_parser, key_name=f.key)
            elif f.kind == "bool":
                main_has = True
                self._add_checkbox(main_form, f.label, f.key)
            elif f.kind == "int":
                main_has = True
                self._add_spin(main_form, f.label, f.key, f.lo, f.hi, f.step)
            elif f.kind == "gvas_int":
                main_has = True
                self._add_gvas_spin(main_form, f.label, f.key, f.lo, f.hi, f.step)
            elif f.kind == "gvas_bool":
                main_has = True
                self._add_gvas_check(main_form, f.label, f.key)
            elif f.kind == "gvas_set":
                main_has = True
                self._add_gvas_set(main_form, f.label, f.key, f.lo, f.hi, f.step)

        if main_has:
            self.scroll_layout.addWidget(main_group)
        if cert_has:
            self.scroll_layout.addWidget(cert_group)

        if not profile.fields:
            group, form = _make_group(profile.title)
            info = QLabel("No editable fields are configured for this game's save format yet.")
            info.setObjectName("mutedLabel")
            info.setWordWrap(True)
            form.addRow(info)
            self.scroll_layout.addWidget(group)

    # ---------- widget helpers ----------

    def _add_spin(self, form, label, key, lo, hi, step):
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSingleStep(step)
        spin.setValue(self.parser.get_int(key, min(lo, 0)))
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(110)
        form.addRow(label, spin)
        self.spins[(key, None)] = spin
        return spin

    def _add_gvas_spin(self, form, label, key, lo, hi, step):
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSingleStep(step)
        spin.setValue(int(self.gvas.get(key, lo)))
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(110)
        form.addRow(label, spin)
        self.spins[(key, "gvas")] = spin
        return spin

    def _add_gvas_check(self, form, label, key):
        chk = QCheckBox(label)
        chk.setChecked(bool(self.gvas.get(key, 0)))
        form.addRow(chk)
        self.checkboxes[(key, "gvas")] = chk
        return chk

    def _add_gvas_set(self, form, label, key, lo, hi, step):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        count = len(self.gvas.get(key, []))
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSingleStep(step)
        spin.setValue(count)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(70)
        lbl = QLabel("collected")
        lbl.setObjectName("mutedLabel")
        row_layout.addWidget(spin)
        row_layout.addWidget(lbl)
        row_layout.addStretch()
        form.addRow(label, row)
        self.spins[(key, "gvas_set")] = spin
        return spin

    def _add_checkbox(self, form, label_text, key, parser=None, key_name=None):
        p = parser if parser is not None else self.parser
        chk = QCheckBox(label_text)
        chk.setChecked(p.get_int(key) == 1)
        form.addRow(chk)
        self.checkboxes[(key, p)] = chk
        return chk

    # ---------- Write ----------

    def write_values(self):
        # ini fields
        for (key, p), spin in self.spins.items():
            if p is None:
                self.parser.set_int(key, spin.value())
        for (key, p), chk in self.checkboxes.items():
            if isinstance(p, SaveParser):
                p.set_int(key, 1 if chk.isChecked() else 0)
        # fnaf2 c1..c10 cascade
        if self.current_game_id == "fnaf2":
            c1_chk = self.checkboxes.get(("c1", self.parser))
            if c1_chk and c1_chk.isChecked():
                for i in range(2, 11):
                    self.parser.set_int(f"c{i}", 1)

        # gvas fields
        if self.gvas is not None:
            for (key, kind), spin in self.spins.items():
                if kind == "gvas":
                    self.gvas.set(key, spin.value())
                elif kind == "gvas_set":
                    n = spin.value()
                    self.gvas.set(key, list(range(1, n + 1)))
            for (key, kind), chk in self.checkboxes.items():
                if kind == "gvas":
                    self.gvas.set(key, 1 if chk.isChecked() else 0)

    def save_changes(self):
        if not (self.parser or self.gvas):
            return
        if self._auto_backup_enabled():
            self.create_backup()
        self.write_values()
        if self.parser:
            self.parser.save()
            if self.cert_parser:
                self.cert_parser.save()
        if self.gvas:
            self.gvas.save()
        self.reload_game()
        self.status_update.emit("Changes saved successfully.")

    def _auto_backup_enabled(self) -> bool:
        """Honors 'autobackup' from the fsm_config.ini the installer writes."""
        try:
            base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) \
                else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cfg = os.path.join(base, "fsm_config.ini")
            if not os.path.exists(cfg):
                return False
            parser = configparser.ConfigParser()
            parser.read(cfg)
            return parser.getboolean("options", "autobackup", fallback=False)
        except Exception:
            return False

    def create_backup(self):
        if not (self.parser or self.gvas):
            return
        saved = []
        if self.parser:
            main_bak = BackupManager.create_backup(self.parser.file_path)
            if main_bak:
                saved.append(main_bak.name)
            if self.current_game_id == "fnaf6" and self.cert_parser and os.path.exists(self.cert_parser.file_path):
                cert_bak = BackupManager.create_backup(self.cert_parser.file_path)
                if cert_bak:
                    saved.append(cert_bak.name)
        if self.gvas:
            g_bak = BackupManager.create_backup(self.gvas.file_path)
            if g_bak:
                saved.append(g_bak.name)
        if saved:
            self.status_update.emit("Backup created: " + ", ".join(saved))
        else:
            self.status_update.emit("Could not create a backup.")

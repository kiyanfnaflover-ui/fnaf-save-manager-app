import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow, resolve_resource_path

APP_NAME = "FNAF Save Manager"
APP_VERSION = "v4.0"
CREATOR = "Created by K_F_"

# One Dark palette theme
# bg            #1E2127   panels   #282C34
# panels-darker #21252B   fg       #ABB2BF
# fg-bright     #D7DAE0   accent   #C2462C (FNAF accent)
ONE_DARK_QSS = """
QMainWindow {
    background-color: #1E2127;
}
QWidget {
    color: #ABB2BF;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #C2462C;
    selection-color: #FFFFFF;
}
#header {
    background-color: #21252B;
    border-bottom: 1px solid #2E3440;
    padding: 10px 16px;
}
#headerTitle {
    font-size: 17px;
    font-weight: 700;
    color: #E6E8EA;
}
#headerSubtitle {
    font-size: 12px;
    color: #7F848E;
}
#versionBadge {
    color: #C9CDD4;
    background-color: #2C313A;
    border: 1px solid #3A4048;
    border-radius: 9px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
}
#bannerHeader {
    background-color: #21252B;
    border-bottom: 1px solid #2E3440;
    padding: 10px 0;
}
#bannerImage {
    border-radius: 10px;
}
#bannerTitle {
    font-size: 30px;
    font-weight: 700;
    color: #E6E8EA;
}
#bannerGameId {
    font-size: 15px;
    color: #7F848E;
}
#navCaption {
    font-size: 11px;
    font-weight: 600;
    color: #7F848E;
    padding: 0 2px;
}
#GameCarousel {
    background-color: #1E2127;
    border-bottom: 1px solid #2E3440;
    outline: none;
}
#fileBar {
    background-color: #282C34;
    border: 1px solid #3A4048;
    border-radius: 6px;
    padding: 6px 10px;
}
#fileLabel {
    color: #7F848E;
    font-size: 12px;
    font-weight: 600;
}
#fileName {
    color: #E6E8EA;
    font-size: 12px;
    font-weight: 600;
}
QGroupBox {
    background-color: #282C34;
    border: 1px solid #3A4048;
    border-radius: 6px;
    font-weight: 600;
    color: #ABB2BF;
    margin-top: 14px;
    padding: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
    top: -2px;
    color: #D7DAE0;
}
QLabel {
    color: #ABB2BF;
}
#mutedLabel {
    color: #7F848E;
    font-size: 12px;
}
QSpinBox {
    background-color: #1E2127;
    border: 1px solid #4A5058;
    border-radius: 2px;
    padding: 4px 6px;
    min-width: 84px;
    color: #D7DAE0;
}
QSpinBox:focus {
    border: 1px solid #C2462C;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    background-color: #31363F;
    border-radius: 2px;
    border: none;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #3A4048;
}
QCheckBox {
    spacing: 6px;
    color: #ABB2BF;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 1px;
    border: 1px solid #5A626B;
    background-color: #1E2127;
}
QCheckBox::indicator:hover {
    border: 1px solid #C2462C;
}
QCheckBox::indicator:checked {
    background-color: #C2462C;
    border: 1px solid #C2462C;
}
QPushButton {
    background-color: #31363F;
    border: 1px solid #4A5058;
    border-radius: 3px;
    padding: 6px 16px;
    color: #D7DAE0;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #3A4048;
}
QPushButton:pressed {
    background-color: #262B33;
}
QPushButton:disabled {
    background-color: #282C34;
    color: #5C6370;
    border: 1px solid #3A4048;
}
#PrimaryButton {
    background-color: #C2462C;
    border: 1px solid #C2462C;
    color: #FFFFFF;
}
#PrimaryButton:hover {
    background-color: #D04F33;
}
#PrimaryButton:pressed {
    background-color: #A93D26;
}
#PrimaryButton:disabled {
    background-color: #3A3130;
    border: 1px solid #3A4048;
    color: #8A7F7C;
}
#actionBar {
    background-color: #21252B;
    border-top: 1px solid #3A4048;
    border-bottom: 1px solid #1B1E24;
    padding: 8px 12px;
}
#placeholderPane {
    background-color: #282C34;
    border: 1px solid #4A5058;
    border-radius: 3px;
}
QGroupBox {
    background-color: #21252B;
    border: 1px solid #4A5058;
    border-radius: 3px;
    margin-top: 14px;
    font-weight: 600;
    color: #D7DAE0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #21252B;
    border: 1px solid #4A5058;
    border-radius: 2px;
    padding: 2px 8px;
    color: #E6E8EA;
}
QScrollBar:vertical {
    background: #1E2127;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #4A5058;
    border-radius: 2px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #5A626B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea {
    border: none;
    background: transparent;
}
QToolTip {
    background-color: #21252B;
    color: #D7DAE0;
    border: 1px solid #4A5058;
    padding: 4px 8px;
}
"""


def main():
    # -- Native Win32 interop via ctypes (safe C API calls) -----------------
    try:
        # Per-monitor v2 DPI awareness (user32) - crisper rendering on scaled displays.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        pass
    try:
        # Pin the taskbar AppUserModelID (shell32) so the app's favicon.ico is
        # used in the taskbar / Alt-Tab instead of the generic Python icon.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "FKF.FnafSaveManager.v4")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(ONE_DARK_QSS)

    # Favicon in the app window / taskbar (also embedded via the EXE).
    icon_path = resolve_resource_path("favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

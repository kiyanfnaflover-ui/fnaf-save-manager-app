import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

APP_NAME = "FNAF Save Manager"
APP_VERSION = "v3.0"
CREATOR = "Created by K_F_"

# Dark native Windows theme - restrained charcoal, subtle accents, no emoji
DARK_THEME_QSS = """
QMainWindow {
    background-color: #202225;
}
QWidget {
    color: #E8E9EB;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #3A4A55;
    selection-color: #FFFFFF;
}
#header {
    background-color: #26282C;
    border-bottom: 1px solid #34373C;
    padding: 10px 14px;
}
#headerTitle {
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
}
#headerSubtitle {
    font-size: 12px;
    color: #A6ABB2;
}
#versionBadge {
    color: #C9CDD4;
    background-color: #32353C;
    border: 1px solid #464A52;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
}
#navCaption {
    font-size: 11px;
    font-weight: 600;
    color: #8A8F96;
}
#GameCarousel {
    background-color: #2B2D31;
    border: 1px solid #383B41;
    border-radius: 6px;
    outline: none;
}
#GameCarousel::item {
    padding: 10px 8px;
    border-radius: 5px;
    color: #D5D8DC;
}
#GameCarousel::item:hover {
    background-color: #34373C;
}
#GameCarousel::item:selected {
    background-color: #3A4249;
    color: #FFFFFF;
    font-weight: 600;
}
#fileBar {
    background-color: #2B2D31;
    border: 1px solid #34373B;
    border-radius: 6px;
    padding: 6px 10px;
}
#fileLabel {
    color: #8A8F96;
    font-size: 12px;
    font-weight: 600;
}
#fileName {
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
}
QGroupBox {
    background-color: #2B2D31;
    border: 1px solid #34373B;
    border-radius: 6px;
    font-weight: 600;
    color: #B7BDC4;
    margin-top: 14px;
    padding: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
    top: -2px;
}
QLabel {
    color: #D5D8DC;
}
#mutedLabel {
    color: #9A9EA6;
    font-size: 12px;
}
#sectionSpacing {
}
QFormLayout {
}
QSpinBox {
    background-color: #1C1E22;
    border: 1px solid #3A3D44;
    border-radius: 4px;
    padding: 4px 6px;
    min-width: 84px;
    color: #FFFFFF;
}
QSpinBox:focus {
    border: 1px solid #5C7A8A;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    background-color: #32353A;
    border-radius: 2px;
    border: none;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #40444A;
}
QCheckBox {
    spacing: 6px;
    color: #D5D8DC;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid #4A4E56;
    background-color: #1C1E22;
}
QCheckBox::indicator:hover {
    border: 1px solid #6B7280;
}
QCheckBox::indicator:checked {
    background-color: #2F7F4C;
    border: 1px solid #2F7F4C;
}
QPushButton {
    background-color: #3A3D44;
    border: 1px solid #4A4E56;
    border-radius: 5px;
    padding: 6px 16px;
    color: #E8E9EB;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #454950;
}
QPushButton:pressed {
    background-color: #2E3136;
}
QPushButton:disabled {
    background-color: #2B2D31;
    color: #6A6E75;
    border: 1px solid #34373B;
}
#PrimaryButton {
    background-color: #2F7F4C;
    border: 1px solid #2F7F4C;
    color: #FFFFFF;
}
#PrimaryButton:hover {
    background-color: #379A59;
}
#PrimaryButton:pressed {
    background-color: #27693F;
}
#PrimaryButton:disabled {
    background-color: #2C3236;
    border: 1px solid #34373B;
    color: #7A7E86;
}
#actionBar {
    background-color: #202225;
    border-top: 1px solid #34373B;
    padding: 8px 10px;
}
#placeholderPane {
    background-color: #2B2D31;
    border: 1px solid #34373B;
    border-radius: 6px;
}
QStatusBar {
    background-color: #1A1C1F;
    border-top: 1px solid #34373B;
    color: #9A9EA6;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}
QSplitter::handle {
    background-color: transparent;
    width: 5px;
}
QScrollBar:vertical {
    background: #2B2D31;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3A3D44;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #4A4E56;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea {
    border: none;
    background: transparent;
}
QToolTip {
    background-color: #26282C;
    color: #E8E9EB;
    border: 1px solid #4A4E56;
    padding: 4px 8px;
}
"""

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FNAF Save Manager")
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
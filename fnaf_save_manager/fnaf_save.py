import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Modern Dark Theme with rounded corners and smooth accents
DARK_THEME_QSS = """
    QMainWindow {
        background-color: #121212;
    }
    QWidget {
        color: #E0E0E0;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }
    #GameSelector {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 8px;
        outline: none;
    }
    #GameSelector::item {
        padding: 12px;
        border-radius: 6px;
        margin: 4px;
    }
    #GameSelector::item:hover {
        background-color: #2D2D2D;
    }
    #GameSelector::item:selected {
        background-color: #3498DB;
        color: #FFFFFF;
        font-weight: bold;
    }
    #EditorHeader {
        font-size: 24px;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 15px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #333333;
        border-radius: 8px;
        margin-top: 15px;
        padding-top: 20px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 15px;
        top: -5px;
    }
    QSpinBox {
        background-color: #2D2D2D;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 6px;
        min-width: 100px;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 24px;
        background-color: #383838;
        border-radius: 2px;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #4A4A4A;
    }
    QPushButton {
        background-color: #2D2D2D;
        border: 1px solid #444444;
        border-radius: 6px;
        padding: 10px 15px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3A3A3A;
    }
    #PrimaryButton {
        background-color: #27AE60;
        border: none;
        color: white;
    }
    #PrimaryButton:hover {
        background-color: #2ECC71;
    }
    #PrimaryButton:disabled {
        background-color: #2D2D2D;
        color: #777777;
    }
    QStatusBar {
        background-color: #1A1A1A;
        border-top: 1px solid #333333;
        color: #888888;
    }
    QSplitter::handle {
        background-color: transparent;
    }
"""

def main():
    app = QApplication(sys.argv)
    
    # Apply modern typography and QSS styling globally
    app.setStyleSheet(DARK_THEME_QSS)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
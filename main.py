import sys
from PyQt6.QtWidgets import QApplication
from gui.gui import main_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main_window()
    window.show()
    sys.exit(app.exec())

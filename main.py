import os
import sys

from PySide6.QtWidgets import QApplication

from gui.gui import main_window


def check_system():
    if not os.path.exists("./log"):
        os.mkdir("./log")
    if not os.path.exists("./temp"):
        os.mkdir("./temp")

if __name__ == "__main__":
    check_system()
    app = QApplication(sys.argv)
    window = main_window()
    window.show()
    sys.exit(app.exec())

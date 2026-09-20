import os
import sys

from PySide6.QtWidgets import QApplication

from gui.gui import main_window


def check_system():
    os.makedirs("./log", exist_ok=True)
    os.makedirs("./temp", exist_ok=True)


def main():
    check_system()
    app = QApplication(sys.argv)
    window = main_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

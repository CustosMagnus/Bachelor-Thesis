from gui.video_display import *

from PyQt6.QtWidgets import (
    QWidget, QTabWidget,
    QVBoxLayout, QLabel
)

class main_window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyzer")
        self.setGeometry(300, 300, 400, 200)

        # Main layout
        layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tab1_UI(), "video sync.")
        self.tabs.addTab(self.tab2_UI(), "settings")
        self.tabs.addTab(self.tab3_UI(), "output")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def tab1_UI(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create instance of the OpenCV video player widget
        video_player = VideoPlayerWidget()

        # Add the video player widget to the layout
        layout.addWidget(video_player)

        tab.setLayout(layout)
        return tab

    def tab2_UI(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is Tab 2"))
        tab.setLayout(layout)
        return tab

    def tab3_UI(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is Tab 3"))
        tab.setLayout(layout)
        return tab


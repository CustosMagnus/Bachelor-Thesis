from PySide6.QtWidgets import (
    QWidget, QTabWidget,
    QVBoxLayout, QLabel
)

from gui.video_display import VideoPlayerWidget
from video_processing.video_processor import Video_PreProcessor


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

        # Creating video player using opencv
        video_player = VideoPlayerWidget()
        layout.addWidget(video_player)
        # Creating cropping abilities
        video_cropper = Video_PreProcessor(video_player)
        layout.addWidget(video_cropper)

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


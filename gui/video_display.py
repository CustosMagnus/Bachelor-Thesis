import cv2
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QGridLayout, QSlider, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class VideoPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.video_capture = None
        self.frame_count = 0
        self.current_frame = 0

        layout = QVBoxLayout(self)

        self.top_label = QLabel("""1) Upload up to 4 videos below.
        2) Search for the synchronisation point of the videos.
        3) Confirm your synchronisation points.""")
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.top_label)

        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)

        self.buttons = []
        self.video_labels = []
        self.sliders = []
        self.captures = []
        self.timers = []

        # Create 4 cells with a button, video display, slider
        for i in range(4):
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)

            btn = QPushButton(f"Upload Video {i+1}")
            cell_layout.addWidget(btn)

            video_label = QLabel("No video loaded")
            video_label.setFixedSize(320, 240)
            video_label.setStyleSheet("background-color: black;")
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.addWidget(video_label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setValue(0)
            slider.setEnabled(False)
            cell_layout.addWidget(slider)

            self.buttons.append(btn)
            self.video_labels.append(video_label)
            self.sliders.append(slider)

            ### left right 1 frame ###
            btn_layout = QHBoxLayout()

            btn_prev = QPushButton("Previous Frame")
            btn_next = QPushButton("Next Frame")

            btn_layout.addWidget(btn_prev)
            btn_layout.addWidget(btn_next)

            cell_layout.addLayout(btn_layout)

            btn_prev.clicked.connect(lambda checked, idx=i: self.go_previous_frame(idx))
            btn_next.clicked.connect(lambda checked, idx=i: self.go_next_frame(idx))
            ### /left right 1 frame ###

            # variable for the video
            self.captures.append(None)

            btn.clicked.connect(lambda checked, idx=i: self.load_video(idx))
            slider.sliderMoved.connect(lambda pos, idx=i: self.seek_frame(idx, pos))

            self.grid_layout.addWidget(cell_widget, i // 2, i % 2)

        self.setLayout(layout)

    def load_video(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                self.video_labels[idx].setText("Error loading video")
                return

            self.captures[idx] = cap
            self.sliders[idx].setEnabled(True)

            # Frame count
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.sliders[idx].setMaximum(frame_count - 1)
            self.sliders[idx].setValue(0)

            self.update_frame(idx, 0)

    # The QTMultiMedia module seems to be unavailable so opencv is being used instead
    def update_frame(self, idx, frame_pos):
        cap = self.captures[idx]
        if cap is None:
            return
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img).scaled(self.video_labels[idx].size(), Qt.AspectRatioMode.KeepAspectRatio)
            self.video_labels[idx].setPixmap(pixmap)
            self.sliders[idx].setValue(frame_pos)
        else:
            self.video_labels[idx].setText("End of video")

    def seek_frame(self, idx, frame_pos):
        if self.captures[idx] is None:
            return
        self.update_frame(idx, frame_pos)

    ### left right 1 frame ###
    def go_previous_frame(self, idx):
        if self.captures[idx] is None:
            return
        pos = self.sliders[idx].value()
        if pos > 0:
            pos -= 1
            self.update_frame(idx, pos)

    def go_next_frame(self, idx):
        if self.captures[idx] is None:
            return
        pos = self.sliders[idx].value()
        if pos < self.sliders[idx].maximum():
            pos += 1
            self.update_frame(idx, pos)
    ### /left right 1 frame ###
from collections import OrderedDict

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QGridLayout, QSlider, QFileDialog, QHBoxLayout
)


class VideoPlayerWidget(QWidget):
    def __init__(self, cache_limit=60):
        super().__init__()

        self.video_capture = None
        self.frame_count = 0
        self.current_frame = 0
        self.cache_limit = max(1, int(cache_limit))

        self.btn_prev = []
        self.btn_next = []
        self.file_paths = []
        self.current_positions = []
        self.capture_next_positions = []
        self.frame_caches = []

        layout = QVBoxLayout(self)

        self.top_label = QLabel("""1) Upload up to 4 videos below.
        2) Search for the synchronisation point of the videos.
        3) Confirm your synchronisation points.
        4) Crop the videos to reduce computation time""")
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

            # keep references for external enabling/disabling
            self.btn_prev.append(btn_prev)
            self.btn_next.append(btn_next)

            btn_prev.clicked.connect(lambda checked=False, idx=i: self.go_previous_frame(idx))
            btn_next.clicked.connect(lambda checked=False, idx=i: self.go_next_frame(idx))
            ### /left right 1 frame ###

            # variable for the video
            self.captures.append(None)
            self.file_paths.append(None)
            self.current_positions.append(None)
            self.capture_next_positions.append(None)
            self.frame_caches.append(OrderedDict())

            btn.clicked.connect(lambda checked=False, idx=i: self.load_video(idx))
            slider.sliderMoved.connect(lambda pos, idx=i: self.seek_frame(idx, pos))

            self.grid_layout.addWidget(cell_widget, i // 2, i % 2)

        self.setLayout(layout)

    @staticmethod
    def has_cuda_support():
        """Return whether this OpenCV build reports a usable CUDA device."""
        try:
            return hasattr(cv2, "cuda") and cv2.cuda.getCudaEnabledDeviceCount() > 0
        except (AttributeError, cv2.error):
            return False

    def load_video(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                cap.release()
                self.video_labels[idx].setText("Error loading video")
                return

            old_capture = self.captures[idx]
            if old_capture is not None:
                old_capture.release()

            self.captures[idx] = cap
            self.file_paths[idx] = file_path
            self.invalidate_frame_state(idx)
            self.capture_next_positions[idx] = 0
            self.sliders[idx].setEnabled(True)

            # Frame count
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.sliders[idx].setMaximum(frame_count - 1)
            self.sliders[idx].setValue(0)

            self.update_frame(idx, 0)

    # The QTMultiMedia module seems to be unavailable so opencv is being used instead
    def get_frame(self, idx, frame_pos):
        """Get a display-ready frame using cache, sequential read, or random seek."""
        cap = self.captures[idx]
        if cap is None:
            return None

        cache = self.frame_caches[idx]
        cached_pixmap = cache.get(frame_pos)
        if cached_pixmap is not None:
            cache.move_to_end(frame_pos)
            return cached_pixmap

        # VideoCapture already points at the next frame after a successful read.
        # Reuse that position for forward navigation and seek only on a jump.
        if self.capture_next_positions[idx] != frame_pos:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        ret, frame = cap.read()
        if not ret:
            self.capture_next_positions[idx] = None
            return None

        self.capture_next_positions[idx] = frame_pos + 1
        pixmap = self._frame_to_pixmap(idx, frame)
        cache[frame_pos] = pixmap
        cache.move_to_end(frame_pos)
        while len(cache) > self.cache_limit:
            cache.popitem(last=False)
        return pixmap

    def _frame_to_pixmap(self, idx, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_img).scaled(
            self.video_labels[idx].size(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def render_frame(self, idx, frame_pos, pixmap):
        self.video_labels[idx].setPixmap(pixmap)
        self.sliders[idx].setValue(frame_pos)
        self.current_positions[idx] = frame_pos

    def update_frame(self, idx, frame_pos):
        if self.captures[idx] is None:
            return False

        frame_pos = max(0, min(int(frame_pos), self.sliders[idx].maximum()))
        pixmap = self.get_frame(idx, frame_pos)
        if pixmap is None:
            self.video_labels[idx].setText("End of video")
            return False

        self.render_frame(idx, frame_pos, pixmap)
        return True

    def invalidate_frame_state(self, idx, clear_cache=True):
        """Forget decoder state after another operation moves the capture."""
        self.current_positions[idx] = None
        self.capture_next_positions[idx] = None
        if clear_cache:
            self.frame_caches[idx].clear()

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

    def closeEvent(self, event):
        for cap in self.captures:
            if cap is not None:
                cap.release()
        super().closeEvent(event)

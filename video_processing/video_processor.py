import cv2, sys
from datetime import datetime
from PyQt6.QtWidgets import QSlider, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QPushButton, QWidget, QLabel)


class Video_PreProcessor(QWidget):
    def __init__(self, vid_player):
        super().__init__()

        ### general variables ###
        self.sync_location = []
        self.min_vid_val = 0
        self.max_vid_val = 0
        ### /general variables ###

        self.Video_Player = vid_player
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.sync_button = QPushButton("sync")
        v1_layout = QVBoxLayout()
        self.crop_a_label = QLabel("crop beginning")
        self.crop_a_slider = QSlider(Qt.Orientation.Horizontal)
        self.crop_a_button = QPushButton("crop beginning")
        v2_layout = QVBoxLayout()
        self.crop_o_label = QLabel("crop end")
        self.crop_o_slider = QSlider(Qt.Orientation.Horizontal)
        self.crop_o_button = QPushButton("crop end")


        self.sync_button.clicked.connect(self.sync)

        layout.addWidget(self.sync_button)
        v1_layout.addWidget(self.crop_a_label)
        v1_layout.addWidget(self.crop_a_slider)
        v1_layout.addWidget(self.crop_a_button)
        v2_layout.addWidget(self.crop_o_label)
        v2_layout.addWidget(self.crop_o_slider)
        v2_layout.addWidget(self.crop_o_button)
        layout.addLayout(v1_layout)
        layout.addLayout(v2_layout)

        self.crop_a_button.setEnabled(False)
        self.crop_a_slider.setEnabled(False)
        self.crop_o_button.setEnabled(False)
        self.crop_o_slider.setEnabled(False)

        self.crop_a_slider.sliderMoved.connect(self.crop_beginning_slider)
        self.crop_o_slider.sliderMoved.connect(self.crop_end_slider)

        self.crop_a_button.clicked.connect(self.crop_beginning_button)
        self.crop_o_button.clicked.connect(self.crop_end_button)

        self.setLayout(layout)

    def sync(self):
        sort = [None, None, None, None]
        # at which position is a video and get frame location
        vid_loc = self.Video_Player.captures
        for i in range(len(vid_loc)):
            if vid_loc[i] is not None:
                sort[i] = self.Video_Player.sliders[i].value()
        # sync to smallest position and set sliders and video accordingly
        min_val = min(filter(lambda x: x is not None, sort))
        for i in range(len(sort)):
            if sort[i] is not None:
                self.sync_location.append(sort[i] - min_val)
                self.Video_Player.update_frame(i, self.sync_location[-1])
                self.min_vid_val = min_val
            else:
                self.sync_location.append(None)

        # disable sliders from syncing part
        for slider in self.Video_Player.sliders:
            slider.setEnabled(False)
        for button in self.Video_Player.buttons:
            button.setEnabled(False)
        for prev_btn in self.Video_Player.btn_prev:
            prev_btn.setEnabled(False)
        for next_btn in self.Video_Player.btn_next:
            next_btn.setEnabled(False)
        self.sync_button.setEnabled(False)
        # enable cropping beginning
        self.crop_a_slider.setEnabled(True)
        self.crop_a_button.setEnabled(True)
        # set boundaries
        self.crop_a_slider.setValue(self.min_vid_val)
        self.update_all_videos(self.min_vid_val)
        self.crop_a_slider.setMinimum(int(self.min_vid_val))

        max_frames_per_vid = []
        for i in range(len(self.Video_Player.captures)):
            if self.Video_Player.captures[i] is not None:
                max_frames_per_vid.append(self.Video_Player.captures[i].get(cv2.CAP_PROP_FRAME_COUNT) - self.sync_location[i])
        self.max_vid_val = min(filter(lambda x: x is not None, max_frames_per_vid))
        self.crop_a_slider.setMaximum(int(self.max_vid_val - 1))


    def crop_beginning_slider(self):
        self.update_all_videos(self.crop_a_slider.value())

    def crop_beginning_button(self):
        # enable / disable cropping sliders / buttons
        self.crop_a_slider.setEnabled(False)
        self.crop_a_button.setEnabled(False)
        self.crop_o_slider.setEnabled(True)
        self.crop_o_button.setEnabled(True)
        self.crop_o_slider.setMinimum(int(self.crop_a_slider.value()))
        self.crop_o_slider.setMaximum(int(self.max_vid_val - 1))
        self.crop_o_slider.setValue(int(self.max_vid_val - 1))
        self.update_all_videos(int(self.max_vid_val - 1))
        print(self.crop_a_slider.value())


    def crop_end_slider(self):
        self.update_all_videos(self.crop_o_slider.value())

    def crop_end_button(self):
        self.crop_o_slider.setEnabled(False)
        self.crop_o_button.setEnabled(False)
        print(self.crop_o_slider.value())
        self.export_cropped_video()

    def update_all_videos(self, loc):
        for i in range(len(self.sync_location)):
            if self.sync_location[i] is not None:
                self.Video_Player.update_frame(i, (self.sync_location[i] + loc))
                
    def export_cropped_video(self):
        # Determine crop range in the shared synced timeline
        start_loc = int(self.crop_a_slider.value())
        end_loc = int(self.crop_o_slider.value())

        for i, cap in enumerate(self.Video_Player.captures):
            if cap is None:
                continue

            # Compute per-video absolute frame indices
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            start_frame = int(self.sync_location[i] + start_loc)
            end_frame = int(self.sync_location[i] + end_loc)

            if not (start_frame <= end_frame < total_frames - 1):
                self.log(f"Invalid crop range for video {i}: [{start_frame}, {end_frame}]")

            # Gather writer properties
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if not fps or fps <= 0:
                self.log(f"Invalid FPS for video {i}: {fps}")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width <= 0 or height <= 0:
                self.log(f"Invalid frame size for video {i}: ({width}, {height})")
            size = (width, height)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            # Prepare writer
            writer = cv2.VideoWriter(f"./temp/vid{i}.mp4", fourcc, fps, size)
            if not writer.isOpened():
                self.log(f"Failed to open writer for video {i}")

            # Save current UI position to restore later
            current_ui_pos = self.Video_Player.sliders[i].value()

            try:
                # Read and write frames
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                frames_to_write = end_frame - start_frame + 1
                for _ in range(frames_to_write):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # Ensure frame size matches writer size
                    if frame.shape[1] != size[0] or frame.shape[0] != size[1]:
                        frame = cv2.resize(frame, size)
                    writer.write(frame)
            except Exception as e:
                self.log(f"Error while processing video {i}\n{e}")
            finally:
                writer.release()
                # Restore UI frame display position
                restore_frame = int(self.sync_location[i] + current_ui_pos)
                self.Video_Player.update_frame(i, restore_frame)

    def log(self, txt):
        with open("./log/error.log", "a") as f:
            f.write(datetime.now().strftime("%Y.%m.%d-%H:%M:%S")+" >> "+txt+"\n")
            sys.exit(1)
# player_widget.py
import os
import vlc
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QStyle)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QKeyEvent

base_path = os.path.dirname(os.path.abspath(__file__))

class ClickableSlider(QSlider):
    def __init__(self, orientation):
        super().__init__(orientation)
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            if self.orientation() == Qt.Horizontal:
                value = self.minimum() + (self.maximum() - self.minimum()) * event.pos().x() / self.width()
            else:
                value = self.minimum() + (self.maximum() - self.minimum()) * event.pos().y() / self.height()
            self.setValue(int(value))
            self.sliderMoved.emit(int(value))

class PlayerWidget(QWidget):
    back_to_browser_requested = Signal()
    def __init__(self):
        super().__init__()
        self.instance = vlc.Instance(['--no-xlib'])
        self.player = self.instance.media_player_new()
        
        icon_path = os.path.join(base_path, 'icons')
        self.play_icon = QIcon(os.path.join(icon_path, 'play.png'))
        self.pause_icon = QIcon(os.path.join(icon_path, 'pause.png'))
        if self.play_icon.isNull() or self.pause_icon.isNull():
            self.play_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
            self.pause_icon = self.style().standardIcon(QStyle.SP_MediaPause)

        self.init_ui()
        self.timer = QTimer(self); self.timer.setInterval(200); self.timer.timeout.connect(self.update_ui)
        
        self.setFocusPolicy(Qt.StrongFocus)

    def init_ui(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background: transparent;")
        
        control_bar_widget = QWidget()
        control_bar_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.6);")
        
        control_bar_layout = QHBoxLayout(control_bar_widget)
        control_bar_layout.setContentsMargins(10, 5, 10, 5)

        self.back_btn = QPushButton("返回列表")
        self.back_btn.clicked.connect(self.request_back)
        self.play_pause_btn = QPushButton(); self.play_pause_btn.setObjectName("play_pause_btn")
        self.play_pause_btn.setIcon(self.play_icon); self.play_pause_btn.setIconSize(QSize(24, 24)); self.play_pause_btn.setFixedSize(QSize(40, 40))
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.position_slider = ClickableSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000); self.position_slider.sliderMoved.connect(self.set_position)
        self.time_label = QLabel("--:-- / --:--"); self.time_label.setStyleSheet("color: #FFFFFF; background: transparent;")

        control_bar_layout.addWidget(self.back_btn); control_bar_layout.addSpacing(10)
        control_bar_layout.addWidget(self.play_pause_btn); control_bar_layout.addWidget(self.position_slider)
        control_bar_layout.addWidget(self.time_label)
        control_bar_layout.setStretchFactor(self.position_slider, 1)

        main_layout.addWidget(self.video_frame, 1)
        main_layout.addWidget(control_bar_widget, 0)

    def start_playback(self, video_path):
        media = self.instance.media_new(video_path)
        self.player.set_media(media); self.player.set_hwnd(self.video_frame.winId())
        self.player.play(); self.play_pause_btn.setIcon(self.pause_icon); self.timer.start()
        
    def stop_playback(self):
        if self.player.is_playing(): self.player.stop()
        self.timer.stop(); self.time_label.setText("--:-- / --:--")
        self.position_slider.setValue(0); self.play_pause_btn.setIcon(self.play_icon)

    def toggle_play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_pause_btn.setIcon(self.play_icon)
        else:
            self.player.play()
            self.play_pause_btn.setIcon(self.pause_icon)

    def set_position(self, position):
        self.player.set_position(position / 1000.0)

    def update_ui(self):
        pos = self.player.get_position(); self.position_slider.setValue(int(pos * 1000))
        total_ms = self.player.get_length(); curr_ms = self.player.get_time()
        if total_ms > 0:
            total = f"{total_ms // 60000:02}:{total_ms // 1000 % 60:02}"; curr = f"{curr_ms // 60000:02}:{curr_ms // 1000 % 60:02}"
            self.time_label.setText(f"{curr} / {total}")
        if self.player.get_state() == vlc.State.Ended:
            self.stop_playback()

    def request_back(self):
        self.back_to_browser_requested.emit()
        self.stop_playback()
        
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘按下事件"""
        key = event.key()
        
        if key == Qt.Key_Escape:
            self.request_back()
            event.accept()  # ### 关键修复：消费掉这个事件 ###
        elif key == Qt.Key_Space:
            self.toggle_play_pause()
            event.accept()  # ### 关键修复：消费掉这个事件 ###
        else:
            super().keyPressEvent(event)
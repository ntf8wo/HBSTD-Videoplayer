# player_widget.py
import os
import sys
import vlc
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QStyle)
from PySide2.QtCore import Qt, QSize, Signal, QTimer
from PySide2.QtGui import QIcon, QKeyEvent

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()

class ClickableSlider(QSlider):
    def __init__(self, o): super().__init__(o)
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button()==Qt.LeftButton:
            v=self.minimum()+(self.maximum()-self.minimum())*e.pos().x()/self.width()
            self.setValue(int(v)); self.sliderMoved.emit(int(v))

class PlayerWidget(QWidget):
    back_to_browser_requested = Signal()
    def __init__(self):
        super().__init__()
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # 修正路径：确保在 _internal 或开发目录中找到 icons
        icon_path = os.path.join(base_path, 'icons')
        
        self.play_icon = QIcon(os.path.join(icon_path, 'play.png'))
        self.pause_icon = QIcon(os.path.join(icon_path, 'pause.png'))
        if self.play_icon.isNull() or self.pause_icon.isNull():
            self.play_icon, self.pause_icon = self.style().standardIcon(QStyle.SP_MediaPlay), self.style().standardIcon(QStyle.SP_MediaPause)

        self.init_ui()
        self.timer = QTimer(self); self.timer.setInterval(200); self.timer.timeout.connect(self.update_ui)
        self.setFocusPolicy(Qt.StrongFocus)  # 允许获取焦点
    
    def init_ui(self):
        self.setAttribute(Qt.WA_TranslucentBackground); main_layout=QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)
        self.video_frame=QWidget(); self.video_frame.setStyleSheet("background:transparent;")
        ctrl_bar=QWidget(); ctrl_bar.setStyleSheet("background-color:rgba(0,0,0,0.6);")
        ctrl_layout=QHBoxLayout(ctrl_bar); ctrl_layout.setContentsMargins(10,5,10,5)
        self.back_btn=QPushButton("返回列表"); self.back_btn.clicked.connect(self.request_back)
        self.play_pause_btn=QPushButton(); self.play_pause_btn.setObjectName("play_pause_btn"); self.play_pause_btn.setIcon(self.play_icon); self.play_pause_btn.setIconSize(QSize(24,24)); self.play_pause_btn.setFixedSize(QSize(40,40)); self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.pos_slider=ClickableSlider(Qt.Horizontal); self.pos_slider.setRange(0,1000); self.pos_slider.sliderMoved.connect(self.set_position)
        self.time_label=QLabel("--:-- / --:--"); self.time_label.setStyleSheet("color:#FFFFFF;background:transparent;")
        ctrl_layout.addWidget(self.back_btn); ctrl_layout.addSpacing(10); ctrl_layout.addWidget(self.play_pause_btn); ctrl_layout.addWidget(self.pos_slider); ctrl_layout.addWidget(self.time_label); ctrl_layout.setStretchFactor(self.pos_slider,1)
        main_layout.addWidget(self.video_frame,1); main_layout.addWidget(ctrl_bar,0)
    def start_playback(self, p):
        m=self.instance.media_new(p); self.player.set_media(m); self.player.set_hwnd(self.video_frame.winId()); self.player.play(); self.play_pause_btn.setIcon(self.pause_icon); self.timer.start()
    def stop_playback(self):
        if self.player.is_playing(): self.player.stop()
        self.timer.stop(); self.time_label.setText("--:-- / --:--"); self.pos_slider.setValue(0); self.play_pause_btn.setIcon(self.play_icon)
    def toggle_play_pause(self):
        if self.player.is_playing(): self.player.pause(); self.play_pause_btn.setIcon(self.play_icon)
        else: self.player.play(); self.play_pause_btn.setIcon(self.pause_icon)
    def set_position(self, pos): self.player.set_position(pos/1000.0)
    def update_ui(self):
        pos=self.player.get_position(); self.pos_slider.setValue(int(pos*1000)); total_ms=self.player.get_length(); curr_ms=self.player.get_time()
        if total_ms>0: total=f"{total_ms//60000:02}:{total_ms//1000%60:02}"; curr=f"{curr_ms//60000:02}:{curr_ms//1000%60:02}"; self.time_label.setText(f"{curr} / {total}")
        if self.player.get_state()==vlc.State.Ended: self.stop_playback()
    def request_back(self): self.back_to_browser_requested.emit(); self.stop_playback()
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.request_back()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        else:
            super().keyPressEvent(event)
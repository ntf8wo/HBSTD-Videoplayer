# main_window.py
import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QFileDialog, 
                               QLabel, QMessageBox, QScrollArea, QGridLayout, 
                               QToolButton, QStackedWidget)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QMovie, QPalette, QBrush, QImage

from workers import ThumbnailWorker
from player_widget import PlayerWidget

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # 修正路径：区分开发环境和打包环境
        if getattr(sys, 'frozen', False): # 打包后的环境
            self.ffmpeg_path = os.path.join(base_path, 'ffmpeg.exe')
        else: # 开发环境
            self.ffmpeg_path = os.path.join(base_path, 'bin', 'ffmpeg', 'ffmpeg.exe')

        # 在打包后，将缓存文件夹创建在 .exe 旁边，而不是临时目录里
        cache_base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else base_path
        self.thumbnail_cache_dir = os.path.join(cache_base, '.thumb_cache')
        
        self.root_folder, self.video_buttons, self.thumbnail_worker = "", {}, None
        
        # 禁用加载动画
        self.loading_movie = None
        
        if not os.path.exists(self.ffmpeg_path): 
            QMessageBox.critical(self, "错误", f"未找到 ffmpeg.exe，程序无法启动。\n期望路径: {self.ffmpeg_path}")
            sys.exit(1)
        os.makedirs(self.thumbnail_cache_dir, exist_ok=True)
        
        self.init_ui()
        self.apply_stylesheet()
        self.set_background_image(os.path.join(base_path, 'background.jpg'))
        self.showFullScreen()
    
    def set_background_image(self, image_path):
        if not os.path.exists(image_path): print(f"警告：背景图片未找到：{image_path}"); return
        palette = self.palette(); image = QImage(image_path)
        brush = QBrush(image.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        palette.setBrush(QPalette.Window, brush); self.setPalette(palette); self.setAutoFillBackground(True)
    def resizeEvent(self, event): self.set_background_image(os.path.join(base_path, 'background.jpg')); super().resizeEvent(event)
    def init_ui(self):
        self.setWindowTitle("科普视频选择器");main_layout = QVBoxLayout(self); main_layout.setContentsMargins(20, 20, 20, 20);self.stacked_widget = QStackedWidget();self.stacked_widget.setStyleSheet("background: transparent;");main_layout.addWidget(self.stacked_widget);self.browser_widget = QWidget();self.browser_widget.setStyleSheet("background: transparent;");browser_layout = QVBoxLayout(self.browser_widget); browser_layout.setContentsMargins(0, 0, 0, 0);self.tab_widget = QTabWidget();self.tab_widget.setDocumentMode(True); self.tab_widget.tabBar().setExpanding(True);self.initial_label = QLabel("正在等待选择视频文件夹..."); self.initial_label.setAlignment(Qt.AlignCenter);browser_layout.addWidget(self.tab_widget); browser_layout.addWidget(self.initial_label);self.player_widget = PlayerWidget();self.player_widget.back_to_browser_requested.connect(self.return_to_browser);self.stacked_widget.addWidget(self.browser_widget); self.stacked_widget.addWidget(self.player_widget);QTimer.singleShot(100, self.prompt_for_folder)
    def prompt_for_folder(self):
        start_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else base_path, 'videos')
        folder = QFileDialog.getExistingDirectory(self, "请选择存放视频的主文件夹", start_path if os.path.exists(start_path) else os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else base_path)
        if folder: self.root_folder = folder; self.initial_label.hide(); self.tab_widget.show(); self.load_all_content()
        else: QMessageBox.warning(self, "操作取消", "您没有选择文件夹，程序将退出。"); self.close()
    def return_to_browser(self): self.stacked_widget.setCurrentWidget(self.browser_widget)
    def load_all_content(self):
        if self.thumbnail_worker and self.thumbnail_worker.isRunning(): self.thumbnail_worker.stop(); self.thumbnail_worker.wait()
        self.tab_widget.clear(); self.video_buttons.clear()
        try:
            subfolders = [f.name for f in os.scandir(self.root_folder) if f.is_dir()]
            if not subfolders: self.show_warning_message("选择的文件夹内没有找到任何子文件夹。"); return
            all_video_files = []
            for category_name in sorted(subfolders):
                category_path = os.path.join(self.root_folder, category_name);scroll_area, grid_layout = self.create_tab_layout();video_files = self.find_videos_in_path(category_path);all_video_files.extend(video_files)
                if not video_files: grid_layout.addWidget(QLabel("此分类下没有视频文件。"), 0, 0, Qt.AlignCenter)
                else:
                    columns = 4
                    for i, video_path in enumerate(video_files): button = self.create_video_button(video_path); grid_layout.addWidget(button, i // columns, i % columns); self.video_buttons[video_path] = button
                self.tab_widget.addTab(scroll_area, category_name)
            if all_video_files: self.start_thumbnail_generation(all_video_files)
        except Exception as e: self.show_error_message(f"加载内容时发生错误: {e}")
    def create_tab_layout(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);scroll_area.setStyleSheet("background: transparent; border: none;");content_widget = QWidget(); content_widget.setStyleSheet("background: transparent;");scroll_area.setWidget(content_widget);grid_layout = QGridLayout(content_widget); grid_layout.setSpacing(30); grid_layout.setContentsMargins(30, 30, 30, 30);return scroll_area, grid_layout
    def find_videos_in_path(self, path):
        formats = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv');return sorted([os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(formats)])
    def create_video_button(self, video_path):
        button = QToolButton(); button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);button.setIconSize(QSize(250, 140)); button.setFixedSize(QSize(270, 200));button.setText(os.path.splitext(os.path.basename(video_path))[0]); button.setFont(QFont("Microsoft YaHei", 11))
        button.clicked.connect(lambda: self.play_video(video_path)); return button
    def start_thumbnail_generation(self, video_files):
        self.thumbnail_worker = ThumbnailWorker(video_files, self.thumbnail_cache_dir, self.ffmpeg_path)
        self.thumbnail_worker.thumbnail_ready.connect(self.update_button_icon)
        self.thumbnail_worker.error_occurred.connect(self.show_error_message)
        self.thumbnail_worker.start()
    def update_button_icon(self, video_path, thumb_path):
        if video_path in self.video_buttons:
            pixmap = QImage(thumb_path)
            if pixmap.isNull():
                print(f"错误：无法从路径加载缩略图文件: {thumb_path}")
                return
            self.video_buttons[video_path].setIcon(QIcon(thumb_path))
    def play_video(self, video_path):
        self.stacked_widget.setCurrentWidget(self.player_widget)
        self.player_widget.start_playback(video_path)
        self.player_widget.setFocus()  # 让播放器获取焦点
    def closeEvent(self, event):
        if self.thumbnail_worker and self.thumbnail_worker.isRunning(): self.thumbnail_worker.stop(); self.thumbnail_worker.wait()
        self.player_widget.stop_playback(); event.accept()
    def show_error_message(self, message): QMessageBox.critical(self, "错误", message)
    def show_warning_message(self, message): QMessageBox.warning(self, "提醒", message)
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QStackedWidget, QTabWidget::pane { background: transparent; border: none; } QWidget { color: #FFFFFF; font-family: "Microsoft YaHei UI", SimHei, Arial; } QTabBar { font-size: 16px; font-weight: bold; } QTabBar::tab { background: rgba(0, 50, 100, 0.7); border: 1px solid rgba(255, 255, 255, 0.3); border-bottom: none; color: #DDDDDD; padding: 15px; border-top-left-radius: 8px; border-top-right-radius: 8px; } QTabBar::tab:hover { background: rgba(0, 80, 150, 0.8); } QTabBar::tab:selected { background: rgba(20, 120, 220, 0.8); color: #FFFFFF; border-bottom: 2px solid #FFFFFF; } QToolButton { background-color: rgba(0, 0, 0, 0.5); border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 8px; color: #FFFFFF; } QToolButton:hover { background-color: rgba(20, 120, 220, 0.5); border-color: rgba(255, 255, 255, 0.8); } PlayerWidget QPushButton { background-color: #0078D7; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; } PlayerWidget QPushButton:hover { background-color: #005A9E; } QPushButton#play_pause_btn { background-color: transparent; border: none; padding: 0px; } QSlider::groove:horizontal { border: 1px solid #4A4A4A; background: #666666; height: 6px; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; border: 1px solid #FFFFFF; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; } QSlider::sub-page:horizontal { background: #0078D7; border: 1px solid #4A4A4A; height: 6px; border-radius: 3px; } QScrollBar:vertical { border: none; background: rgba(0,0,0,0.3); width: 12px; margin: 0px; } QScrollBar::handle:vertical { background: rgba(0, 120, 215, 0.7); min-height: 20px; border-radius: 6px; } QScrollBar::handle:vertical:hover { background: rgba(0, 120, 215, 1.0); } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; } QMessageBox { background-color: #001f3f; }
        """)
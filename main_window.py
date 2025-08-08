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
        
        # 检查Windows版本并进行相应设置
        self.setup_windows_compatibility()
        
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
    
    def setup_windows_compatibility(self):
        """
        设置Windows兼容性选项
        """
        if sys.platform.startswith('win'):
            try:
                import platform
                version = platform.version()
                major, minor, build = map(int, version.split('.'))
                # Windows 7 是 6.1 版本
                if major == 6 and minor == 1:
                    # Windows 7 特定设置
                    os.environ['QT_OPENGL'] = 'software'
                    os.environ['QT_DEBUG_PLUGINS'] = '1'
            except Exception as e:
                print(f"检查Windows版本时出错: {e}")
    
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
    def load_all_content(self): 
        if self.thumbnail_worker and self.thumbnail_worker.isRunning(): self.thumbnail_worker.request_stop(); self.thumbnail_worker.wait()
        self.thumbnail_worker = ThumbnailWorker(self.root_folder, self.thumbnail_cache_dir, self.ffmpeg_path)
        self.thumbnail_worker.thumbnail_ready.connect(self.update_thumbnail); self.thumbnail_worker.finished.connect(self.on_thumbnail_generation_finished)
        self.thumbnail_worker.start(); self.show_loading_animation()
    def on_thumbnail_generation_finished(self): self.hide_loading_animation()
    def show_loading_animation(self):
        for button in self.video_buttons.values(): button.setIcon(QIcon(QMovie(os.path.join(base_path, "loading.gif"))))
    def hide_loading_animation(self): 
        for movie in [button.icon().movie() for button in self.video_buttons.values() if button.icon().movie()]: movie.stop()
    def update_thumbnail(self, video_path, thumbnail_path):
        if video_path in self.video_buttons:
            pixmap = QImage(thumbnail_path)
            icon = QIcon(pixmap)
            self.video_buttons[video_path].setIcon(icon)
            self.video_buttons[video_path].setIconSize(QSize(320, 180))
    def play_video(self, video_path): self.player_widget.load_video(video_path); self.stacked_widget.setCurrentWidget(self.player_widget)
    def return_to_browser(self): self.stacked_widget.setCurrentWidget(self.browser_widget)
    def load_content(self, folder_path, grid_layout):
        from functools import partial
        for i in reversed(range(grid_layout.count())): 
            widget = grid_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
        videos = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(video_extensions)]
        self.video_buttons = {}
        for i, video in enumerate(videos):
            video_path = os.path.join(folder_path, video)
            button = QToolButton()
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setText(video if len(video) <= 20 else video[:17] + "...")
            button.setIconSize(QSize(320, 180))
            button.setFixedSize(340, 220)
            button.clicked.connect(partial(self.play_video, video_path))
            self.video_buttons[video_path] = button
            row, col = divmod(i, 3)
            grid_layout.addWidget(button, row, col)
    def apply_stylesheet(self): self.setStyleSheet("""
QWidget { font-family: "Microsoft YaHei"; background-color: rgba(0, 0, 0, 150); }
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab { 
    background: rgba(0, 0, 0, 100); color: white; padding: 8px 20px; margin: 2px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected { background: rgba(50, 50, 50, 150); font-weight: bold; }
QTabBar::tab:hover:!selected { background: rgba(30, 30, 30, 150); }
QLabel { color: white; font-size: 14px; }
QToolButton { 
    background-color: rgba(0, 0, 0, 100); border: 2px solid rgba(255, 255, 255, 30);
    border-radius: 8px; color: white; font-size: 12px; font-weight: bold;
}
QToolButton:hover { background-color: rgba(30, 30, 30, 150); border: 2px solid rgba(255, 255, 255, 80); }
QToolButton:pressed { background-color: rgba(50, 50, 50, 200); }
QScrollBar:vertical { background: rgba(0, 0, 0, 100); width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: rgba(255, 255, 255, 100); border-radius: 6px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 150); }
""")
# workers.py
import os
import subprocess
from PySide6.QtCore import QThread, Signal

class ThumbnailWorker(QThread):
    thumbnail_ready = Signal(str, str)
    def __init__(self, video_files, cache_dir, ffmpeg_path):
        super().__init__()
        self.video_files, self.cache_dir, self.ffmpeg_path = video_files, cache_dir, ffmpeg_path
        self._is_running = True
    def run(self):
        for p in self.video_files:
            if not self._is_running: break
            base_name = os.path.basename(p)
            thumbnail_name = f"{os.path.splitext(base_name)[0]}.jpg"
            thumbnail_path = os.path.join(self.cache_dir, thumbnail_name)
            if os.path.exists(thumbnail_path):
                self.thumbnail_ready.emit(p, thumbnail_path)
                continue
            command = [self.ffmpeg_path, '-ss', '00:00:01', '-i', p, '-vframes', '1', '-q:v', '2', '-y', thumbnail_path]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if os.path.exists(thumbnail_path):
                    self.thumbnail_ready.emit(p, thumbnail_path)
            except subprocess.CalledProcessError as e:
                print(f"警告: 无法为'{p}'生成缩略图. FFmpeg错误:{e.stderr}")
    def stop(self):
        self._is_running = False
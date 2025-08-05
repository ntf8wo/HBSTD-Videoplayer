# workers.py
import os
import sys
from PySide6.QtCore import QThread, Signal, QProcess

class ThumbnailWorker(QThread):
    thumbnail_ready = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, video_files, cache_dir, ffmpeg_path):
        super().__init__()
        self.video_files = video_files
        self.cache_dir = cache_dir
        self.ffmpeg_path = ffmpeg_path
        self._is_running = True
        
    def run(self):
        for p in self.video_files:
            if not self._is_running:
                break
            
            try:
                base_name = os.path.basename(p)
                thumbnail_name = f"{os.path.splitext(base_name)[0]}.jpg"
                thumbnail_path = os.path.join(self.cache_dir, thumbnail_name)
                
                if os.path.exists(thumbnail_path):
                    self.thumbnail_ready.emit(p, thumbnail_path)
                    continue
                
                process = QProcess()
                process.setProcessChannelMode(QProcess.MergedChannels)
                
                command = self.ffmpeg_path
                args = ['-y', '-ss', '00:00:01', '-i', p, '-vframes', '1', '-q:v', '2', thumbnail_path]
                
                process.start(command, args)
                if not process.waitForFinished(30000): # 30秒超时
                    process.kill()
                    raise RuntimeError("FFmpeg process timed out.")
                
                exit_code = process.exitCode()
                if exit_code != 0:
                    error_output = process.readAllStandardError().data().decode('utf-8', errors='ignore')
                    raise RuntimeError(f"FFmpeg failed with exit code {exit_code}:\n{error_output}")

                if os.path.exists(thumbnail_path):
                    self.thumbnail_ready.emit(p, thumbnail_path)
                else:
                    raise IOError(f"FFmpeg ran successfully but thumbnail file was not created for {p}")

            except Exception as e:
                error_message = f"无法为视频生成缩略图:\n{os.path.basename(p)}\n\n错误: {e}"
                print(error_message)
                self.error_occurred.emit(error_message)

    def stop(self):
        self._is_running = False
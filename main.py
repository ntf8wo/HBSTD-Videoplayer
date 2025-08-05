# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

# 1. 设置 VLC 环境 (必须在导入 main_window 之前)
base_path = os.path.dirname(os.path.abspath(__file__))
vlc_dll_path = os.path.join(base_path, 'bin', 'vlc')
if sys.platform.startswith('win32'):
    if not os.path.isdir(vlc_dll_path):
        print(f"致命错误：找不到VLC库目录：{vlc_dll_path}，程序无法启动。")
        sys.exit(1)
    os.environ['PATH'] = f"{vlc_dll_path}{os.pathsep}{os.environ['PATH']}"

# 2. 导入我们的主窗口
from main_window import MainWindow

# 3. 启动应用
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    # showFullScreen() 会自动调用 show()
    sys.exit(app.exec())
# main.py
import sys
import os
from PySide6.QtWidgets import QApplication

def get_base_path():
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 文件夹打包环境"""
    if getattr(sys, 'frozen', False):
        # 如果程序被 PyInstaller 打包了
        # sys.executable 指向 .exe 文件
        # 所有资源都在和 .exe 同级的 _internal 文件夹内
        return os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        # 如果是直接运行 .py 文件的开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 1. 设置 VLC 环境
base_path = get_base_path()
# 开发环境下路径是 bin/vlc，打包后所有DLL都在根目录 (_internal)
vlc_dll_path = os.path.join(base_path, 'bin', 'vlc') if not getattr(sys, 'frozen', False) else base_path

if sys.platform.startswith('win32'):
    os.environ['PATH'] = f"{vlc_dll_path}{os.pathsep}{os.environ['PATH']}"
    # 插件文件夹也被解压到了根目录(_internal)下的 plugins 文件夹
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(base_path, 'plugins')

# 添加Windows 7兼容性检查
def check_windows_compatibility():
    """
    检查Windows版本兼容性
    """
    if sys.platform.startswith('win'):
        try:
            import platform
            version = platform.version()
            major, minor, build = map(int, version.split('.'))
            # Windows 7 是 6.1 版本
            if major < 6 or (major == 6 and minor < 1):
                print(f"警告：检测到Windows版本 {version}，可能不完全兼容")
        except Exception as e:
            print(f"无法检测Windows版本: {e}")

check_windows_compatibility()

from main_window import MainWindow

# 2. 启动应用
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
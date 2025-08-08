# main.py
import sys
import os

# 1. 导入 PySide2 模块
# 所有 PySide6 的引用已全部更改为 PySide2
from PySide2.QtWidgets import QApplication

def get_base_path():
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 文件夹打包环境"""
    if getattr(sys, 'frozen', False):
        # 如果程序被 PyInstaller 打包了
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接运行 .py 文件的开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 2. 设置 VLC 环境 (已修正)
base_path = get_base_path()
# 开发环境下路径是 bin/vlc，打包后所有DLL都在根目录
vlc_dll_path = os.path.join(base_path, 'bin', 'vlc') if not getattr(sys, 'frozen', False) else base_path

if sys.platform.startswith('win32'):
    # 强制将VLC库目录添加到系统PATH的最前面，这是最直接有效的方式
    os.environ['PATH'] = vlc_dll_path + os.pathsep + os.environ['PATH']
    # 同时设置插件路径
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(vlc_dll_path, 'plugins')


# 3. 尝试导入vlc模块 (已增强错误处理)
try:
    import vlc
except ImportError as e:
    from PySide2.QtWidgets import QMessageBox
    # 在显示任何UI元素（如QMessageBox）之前，必须先创建一个QApplication实例
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "VLC库加载错误",
                         f"无法导入或加载VLC模块: {e}\n\n"
                         "请确认以下几点：\n"
                         "1. 项目 'bin/vlc' 目录下是否包含了 libvlc.dll 等文件。\n"
                         "2. 您的 Python 和 VLC 的架构是否完全一致 (例如：同为64位或同为32位)。\n"
                         "3. 您的系统是否已安装了VLC所需的 VC++ 运行库。")
    sys.exit(1)

# 4. 导入主窗口
from main_window import MainWindow

# 5. 启动应用
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    # 对于 PySide2，使用 app.exec_() 是更兼容的写法
    sys.exit(app.exec_())
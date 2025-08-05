# VideoSelector.spec (文件夹模式终极版)

import os

# 使用 PyInstaller 提供的 SPECPATH 变量
BASE_DIR = SPECPATH

# 定义所有需要打包的数据文件
datas = [
    (os.path.join(BASE_DIR, 'icons'), 'icons'),
    (os.path.join(BASE_DIR, 'background.jpg'), '.'),
    (os.path.join(BASE_DIR, 'loading.gif'), '.'),
    (os.path.join(BASE_DIR, 'bin/vlc/plugins'), 'plugins'),
    (os.path.join(BASE_DIR, 'bin/vlc/libvlc.dll'), '.'),
    (os.path.join(BASE_DIR, 'bin/vlc/libvlccore.dll'), '.'),
    (os.path.join(BASE_DIR, 'bin/ffmpeg/ffmpeg.exe'), '.'),
    (os.path.join(BASE_DIR, 'bin/ffmpeg/ffprobe.exe'), '.'),
    (os.path.join(BASE_DIR, 'bin/ffmpeg/ffplay.exe'), '.')
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=None
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='VideoSelector',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=None
)

# 使用 COLLECT 来创建文件夹模式的发行版
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoSelector' # 这是最终生成的文件夹的名称
)
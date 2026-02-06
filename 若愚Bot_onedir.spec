# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs
import sys
import os

# 收集所有需要的数据和二进制文件
datas = [('icon.ico', '.')]
binaries = []
hiddenimports = [
    'comtypes',
    'comtypes.stream',
    'comtypes.gen',
    'win32com',
    'win32com.client',
    'win32timezone',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'pywintypes',
    'schedule',
    'wxauto',
    'wxauto.uia',
    'wxauto.ui',
    'ctypes',
    'ctypes.wintypes',
    '_ctypes',
    'ctypes.util',
    'ctypes._endian',
]

# 收集 wxauto 的所有资源
tmp_ret = collect_all('wxauto')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 收集 comtypes 的所有资源
tmp_ret = collect_all('comtypes')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 收集 ctypes 的动态库
try:
    ctypes_libs = collect_dynamic_libs('ctypes')
    binaries += ctypes_libs
except:
    pass

# 添加 Python DLLs 目录中的关键文件
python_dir = os.path.dirname(sys.executable)
dlls_dir = os.path.join(python_dir, 'DLLs')
if os.path.exists(dlls_dir):
    # 添加 _ctypes.pyd
    ctypes_pyd = os.path.join(dlls_dir, '_ctypes.pyd')
    if os.path.exists(ctypes_pyd):
        binaries.append((ctypes_pyd, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onedir 模式（推荐用于调试）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='若愚Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 调试时显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='若愚Bot',
)

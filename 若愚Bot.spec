# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os

# 获取 Python 安装目录
python_dir = os.path.dirname(sys.executable)
dlls_dir = os.path.join(python_dir, 'DLLs')

# 初始化
datas = [('icon.ico', '.')]
binaries = []
hiddenimports = [
    'ctypes',
    'ctypes.wintypes',
    '_ctypes',
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

# 关键：手动添加 _ctypes.pyd 和相关 DLL
print("\n正在查找必要的 DLL 文件...")
if os.path.exists(dlls_dir):
    # 添加 _ctypes.pyd
    ctypes_pyd = os.path.join(dlls_dir, '_ctypes.pyd')
    if os.path.exists(ctypes_pyd):
        binaries.append((ctypes_pyd, '.'))
        print(f"✓ 找到 _ctypes.pyd")
    else:
        print(f"✗ 未找到 _ctypes.pyd")

    # 添加其他可能需要的 DLL
    for dll_name in ['libffi-7.dll', 'libffi-8.dll', 'sqlite3.dll']:
        dll_path = os.path.join(dlls_dir, dll_name)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
            print(f"✓ 找到 {dll_name}")

# 添加 Python 根目录的 DLL
for dll_name in ['python3.dll', 'python39.dll', 'python310.dll', 'python311.dll', 'python312.dll']:
    dll_path = os.path.join(python_dir, dll_name)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))
        print(f"✓ 找到 {dll_name}")

print(f"\n总共添加了 {len(binaries)} 个二进制文件\n")

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

# 文件夹模式（onedir）- 推荐使用，DLL 加载更稳定
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
    console=False,
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

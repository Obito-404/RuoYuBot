# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os
import sys


python_roots = []
for root in [os.path.dirname(sys.executable), sys.prefix, getattr(sys, 'base_prefix', '')]:
    if root and root not in python_roots:
        python_roots.append(root)

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
    'tkinter',
    'tkinter.scrolledtext',
    'wxauto',
]

tmp_ret = collect_all('wxauto')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('comtypes')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


def add_binary_if_exists(path, dest='.'):
    if os.path.exists(path):
        entry = (path, dest)
        if entry not in binaries:
            binaries.append(entry)


for root in python_roots:
    dlls_dir = os.path.join(root, 'DLLs')
    for dll_name in ['_ctypes.pyd', 'libffi-7.dll', 'libffi-8.dll', 'sqlite3.dll']:
        add_binary_if_exists(os.path.join(dlls_dir, dll_name))

    for dll_name in ['python3.dll', 'python39.dll', 'python310.dll', 'python311.dll', 'python312.dll']:
        add_binary_if_exists(os.path.join(root, dll_name))


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

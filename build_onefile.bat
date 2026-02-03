@echo off
chcp 65001 >nul
echo ========================================
echo 若愚Bot 一键打包工具 (基于成功配置)
echo ========================================
echo.

echo [1/4] 清理旧的构建文件...
if exist "dist" (
    rmdir /s /q "dist"
    echo 已删除 dist 目录
)
if exist "build" (
    rmdir /s /q "build"
    echo 已删除 build 目录
)
if exist "*.spec" (
    del /q "*.spec"
    echo 已删除旧的 spec 文件
)
echo.

echo [2/4] 检查依赖...
python -c "import comtypes" 2>nul
if errorlevel 1 (
    echo comtypes 未安装，正在安装...
    pip install comtypes
)
echo.

echo [3/4] 开始打包 (单文件模式)...
echo 使用之前成功的配置...
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --hidden-import comtypes ^
    --hidden-import comtypes.stream ^
    --hidden-import comtypes.gen ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import win32timezone ^
    --hidden-import win32api ^
    --hidden-import win32con ^
    --hidden-import win32gui ^
    --hidden-import win32process ^
    --hidden-import pywintypes ^
    --hidden-import schedule ^
    --hidden-import wxauto ^
    --hidden-import wxauto.uia ^
    --hidden-import wxauto.ui ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --add-data "icon.ico;." ^
    main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 打包失败！请检查错误信息
    echo ========================================
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo ========================================
echo 打包成功！
echo ========================================
echo.
echo 可执行文件位置: dist\若愚Bot.exe
echo.

if exist "dist\若愚Bot.exe" (
    echo 文件信息:
    dir "dist\若愚Bot.exe" | findstr "若愚Bot.exe"
    echo.
    echo 提示: 这是单文件版本，首次启动可能较慢
    echo.
    echo 是否打开输出目录？(Y/N)
    set /p open_dir=
    if /i "%open_dir%"=="Y" (
        explorer "dist"
    )
) else (
    echo 警告: 未找到输出文件
)

echo.
pause

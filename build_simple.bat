@echo off
chcp 65001 >nul
title 若愚Bot 简化打包工具

echo ========================================
echo   若愚Bot 简化打包工具
echo ========================================
echo.
echo 此脚本使用最简单的方式打包，避免复杂配置
echo.

:confirm
set /p confirm=确认开始打包？(Y/N):
if /i not "%confirm%"=="Y" exit

echo.
echo [1/4] 清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo ✓ 清理完成
echo.

echo [2/4] 开始打包...
echo 使用文件夹模式，不使用 spec 文件
echo.

pyinstaller ^
    --clean ^
    --onedir ^
    --windowed ^
    --name "若愚Bot-Simple" ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --collect-all win32com ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
    --hidden-import comtypes ^
    --hidden-import comtypes.client ^
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
    --hidden-import tkinter ^
    --hidden-import tkinter.scrolledtext ^
    --noupx ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    echo.
    echo 可能的原因：
    echo 1. 缺少依赖包，请运行: pip install -r requirements.txt
    echo 2. PyInstaller 版本问题，请运行: pip install --upgrade pyinstaller
    echo 3. Python 版本不兼容，建议使用 Python 3.9-3.11
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] 复制配置文件...
if exist "config.ini" (
    copy "config.ini" "dist\若愚Bot-Simple\" >nul 2>&1
    echo ✓ 已复制 config.ini
)
if exist "scheduled_tasks.json" (
    copy "scheduled_tasks.json" "dist\若愚Bot-Simple\" >nul 2>&1
    echo ✓ 已复制 scheduled_tasks.json
)

echo.
echo [4/4] 测试运行...
echo 正在启动程序进行测试...
echo.

start "" "dist\若愚Bot-Simple\若愚Bot-Simple.exe"

timeout /t 3 >nul

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 📁 程序位置: dist\若愚Bot-Simple\若愚Bot-Simple.exe
echo.
echo 💡 测试步骤：
echo 1. 程序应该已经自动启动
echo 2. 检查是否有错误提示
echo 3. 如果正常启动，说明打包成功
echo 4. 如果出错，请查看错误信息
echo.
echo 📦 分发说明：
echo - 将整个 dist\若愚Bot-Simple 文件夹复制给其他人
echo - 或者压缩成 zip 文件分发
echo.

pause

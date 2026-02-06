@echo off
chcp 65001 >nul
title 若愚Bot 调试打包工具

echo ========================================
echo   若愚Bot 调试打包工具
echo ========================================
echo.
echo 此脚本会显示控制台窗口，方便查看错误
echo.

:confirm
set /p confirm=确认开始打包？(Y/N):
if /i not "%confirm%"=="Y" exit

echo.
echo [1/4] 清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo ✓ 清理完成
echo.

echo [2/4] 开始打包（调试模式）...
echo 注意：此版本会显示控制台窗口，可以看到详细错误信息
echo.

pyinstaller ^
    --clean ^
    --onedir ^
    --console ^
    --name "若愚Bot-Debug" ^
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
    --debug all ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 复制配置文件...
if exist "config.ini" (
    copy "config.ini" "dist\若愚Bot-Debug\" >nul 2>&1
    echo ✓ 已复制 config.ini
)
if exist "scheduled_tasks.json" (
    copy "scheduled_tasks.json" "dist\若愚Bot-Debug\" >nul 2>&1
    echo ✓ 已复制 scheduled_tasks.json
)

echo.
echo [4/4] 启动调试版本...
echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 📁 程序位置: dist\若愚Bot-Debug\若愚Bot-Debug.exe
echo.
echo 💡 调试说明：
echo - 程序会显示控制台窗口
echo - 可以看到详细的错误信息和日志
echo - 如果出现错误，请截图控制台内容
echo.

echo 正在启动调试版本...
start "" "dist\若愚Bot-Debug\若愚Bot-Debug.exe"

echo.
echo 请查看程序窗口中的错误信息（如果有）
echo.

pause

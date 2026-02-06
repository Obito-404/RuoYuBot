@echo off
chcp 65001 >nul
title 若愚Bot 打包工具

:menu
cls
echo ========================================
echo       若愚Bot 打包工具
echo ========================================
echo.
echo 请选择打包模式：
echo.
echo [1] 快速打包（推荐）
echo     - 文件夹模式，启动快
echo     - 适合日常使用和调试
echo.
echo [2] 单文件打包
echo     - 打包成单个 exe
echo     - 方便分发，但启动较慢
echo.
echo [3] 调试模式
echo     - 显示控制台输出
echo     - 用于排查问题
echo.
echo [0] 退出
echo.
echo ========================================
set /p choice=请输入选项 (0-3):

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto onefile
if "%choice%"=="3" goto debug
if "%choice%"=="0" exit
goto menu

:quick
cls
echo ========================================
echo 快速打包模式（文件夹）
echo ========================================
echo.
call :clean
call :build_onedir
goto end

:onefile
cls
echo ========================================
echo 单文件打包模式
echo ========================================
echo.
call :clean
call :build_onefile
goto end

:debug
cls
echo ========================================
echo 调试模式
echo ========================================
echo.
call :clean
call :build_debug
goto end

:clean
echo [1/3] 清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo ✓ 清理完成
echo.
goto :eof

:build_onedir
echo [2/3] 开始打包（文件夹模式）...
pyinstaller --clean ^
    --onedir ^
    --windowed ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
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
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    call :show_error
    pause
    exit /b 1
)

call :copy_files "dist\若愚Bot"
call :show_success "dist\若愚Bot\若愚Bot.exe"
goto :eof

:build_onefile
echo [2/3] 开始打包（单文件模式）...
pyinstaller --clean ^
    --onefile ^
    --windowed ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
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
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    call :show_error
    pause
    exit /b 1
)

call :copy_files "dist"
call :show_success "dist\若愚Bot.exe"
goto :eof

:build_debug
echo [2/3] 开始打包（调试模式）...
pyinstaller --clean ^
    --onedir ^
    --console ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
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
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    call :show_error
    pause
    exit /b 1
)

call :copy_files "dist\若愚Bot"
call :show_success "dist\若愚Bot\若愚Bot.exe"
goto :eof

:copy_files
echo.
echo [3/3] 复制配置文件...
if exist "config.ini" (
    copy "config.ini" "%~1\" >nul 2>&1
    echo ✓ 已复制 config.ini
)
if exist "scheduled_tasks.json" (
    copy "scheduled_tasks.json" "%~1\" >nul 2>&1
    echo ✓ 已复制 scheduled_tasks.json
)
goto :eof

:show_success
echo.
echo ========================================
echo ✅ 打包成功！
echo ========================================
echo.
echo 📁 可执行文件：%~1
echo.
echo 💡 使用提示：
echo - 首次运行会自动创建配置文件
echo - 可以将整个文件夹复制到其他电脑使用
echo - 确保目标电脑已安装微信 PC 版
echo.
goto :eof

:show_error
echo.
echo 常见问题解决方案：
echo 1. 确保已安装所有依赖：pip install -r requirements.txt
echo 2. 确保 PyInstaller 是最新版本：pip install --upgrade pyinstaller
echo 3. 尝试使用管理员权限运行
echo 4. 检查杀毒软件是否阻止了打包
echo 5. 查看 PACKAGING_TROUBLESHOOTING.md 获取更多帮助
echo.
goto :eof

:end
echo.
set /p again=是否继续打包？(Y/N):
if /i "%again%"=="Y" goto menu
exit

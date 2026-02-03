@echo off
chcp 65001 >nul
echo ========================================
echo 若愚Bot 打包工具 (带控制台 - 用于调试)
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

echo [3/4] 开始打包 (单文件模式 + 控制台)...
echo 此版本会显示控制台窗口，便于查看错误信息
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --console ^
    --name "若愚Bot_debug" ^
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
echo 可执行文件位置: dist\若愚Bot_debug.exe
echo.
echo 注意: 此版本会显示控制台窗口
echo 如果运行正常，可以使用 build_onefile.bat 创建无控制台版本
echo.

if exist "dist\若愚Bot_debug.exe" (
    echo 文件信息:
    dir "dist\若愚Bot_debug.exe" | findstr "若愚Bot_debug.exe"
    echo.
    echo 是否立即测试运行？(Y/N)
    set /p test_run=
    if /i "%test_run%"=="Y" (
        echo.
        echo 正在启动程序...
        start "" "dist\若愚Bot_debug.exe"
        echo.
        echo 请查看程序是否正常启动
        echo 如果出现错误，控制台会显示详细信息
    )
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

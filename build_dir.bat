@echo off
chcp 65001 >nul
echo ========================================
echo 若愚Bot 一键打包工具 (目录模式)
echo ========================================
echo.
echo 注意: 此版本使用目录模式打包，便于调试
echo.

echo [1/5] 清理旧的构建文件...
if exist "dist" (
    rmdir /s /q "dist"
    echo 已删除 dist 目录
)
if exist "build" (
    rmdir /s /q "build"
    echo 已删除 build 目录
)
echo.

echo [2/5] 检查依赖...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 错误: 未安装 PyInstaller
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装失败，请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
)
echo PyInstaller 已就绪
echo.

echo [3/5] 检查 comtypes...
python -c "import comtypes" 2>nul
if errorlevel 1 (
    echo comtypes 未安装，正在安装...
    pip install comtypes
)
echo.

echo [4/5] 开始打包 (目录模式)...
echo 这将创建一个包含所有依赖的文件夹
echo.

pyinstaller --clean ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --hidden-import "win32timezone" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "win32gui" ^
    --hidden-import "win32process" ^
    --hidden-import "win32com" ^
    --hidden-import "win32com.client" ^
    --hidden-import "pywintypes" ^
    --hidden-import "schedule" ^
    --hidden-import "wxauto" ^
    --hidden-import "wxauto.uia" ^
    --hidden-import "wxauto.ui" ^
    --hidden-import "ctypes" ^
    --hidden-import "ctypes.wintypes" ^
    --hidden-import "_ctypes" ^
    --hidden-import "comtypes" ^
    --hidden-import "comtypes.client" ^
    --collect-all "wxauto" ^
    --collect-all "comtypes" ^
    --console ^
    --noupx ^
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
echo [5/5] 打包完成！
echo.
echo ========================================
echo 打包成功！
echo ========================================
echo.
echo 可执行文件位置: dist\若愚Bot\若愚Bot.exe
echo.
echo 注意: 这是目录模式，需要分发整个 dist\若愚Bot 文件夹
echo.

if exist "dist\若愚Bot\若愚Bot.exe" (
    echo 文件夹内容:
    dir "dist\若愚Bot" /b
    echo.
    echo 是否打开输出目录？(Y/N)
    set /p open_dir=
    if /i "%open_dir%"=="Y" (
        explorer "dist\若愚Bot"
    )
) else (
    echo 警告: 未找到输出文件
)

echo.
echo 提示: 如果程序运行正常，可以使用 build.bat 创建单文件版本
echo.
pause

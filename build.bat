@echo off
chcp 65001 >nul
echo ========================================
echo 若愚Bot 一键打包工具
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
echo.

echo [2/4] 检查依赖...
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

echo [3/4] 开始打包...
echo 使用配置文件: 若愚Bot.spec
echo.
pyinstaller --clean "若愚Bot.spec"

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
    echo 文件大小:
    dir "dist\若愚Bot.exe" | findstr "若愚Bot.exe"
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

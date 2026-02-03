@echo off
chcp 65001 >nul
echo ========================================
echo 修复打包依赖问题
echo ========================================
echo.

echo 正在安装/更新必要的依赖...
echo.

echo [1/3] 安装 comtypes...
pip install comtypes
echo.

echo [2/3] 安装 pywin32...
pip install pywin32
echo.

echo [3/3] 重新安装 PyInstaller...
pip install --upgrade pyinstaller
echo.

echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 现在可以尝试重新打包：
echo   - 目录模式: build_dir.bat
echo   - 单文件模式: build.bat
echo.
pause

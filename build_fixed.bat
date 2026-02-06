@echo off
chcp 65001 >nul
echo ========================================
echo 若愚Bot 打包工具
echo ========================================
echo.

echo [1/4] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo 清理完成！
echo.

echo [2/4] 开始打包（onedir 模式）...
pyinstaller --clean 若愚Bot_onedir.spec
echo.

if %errorlevel% neq 0 (
    echo ❌ 打包失败！
    echo.
    echo 常见问题解决方案：
    echo 1. 确保已安装所有依赖：pip install -r requirements.txt
    echo 2. 确保 PyInstaller 是最新版本：pip install --upgrade pyinstaller
    echo 3. 尝试使用管理员权限运行
    echo 4. 检查杀毒软件是否阻止了打包
    pause
    exit /b 1
)

echo [3/4] 检查打包结果...
if exist "dist\若愚Bot\若愚Bot.exe" (
    echo ✅ 打包成功！
    echo.
    echo 输出目录：dist\若愚Bot\
    echo 可执行文件：dist\若愚Bot\若愚Bot.exe
) else (
    echo ❌ 未找到可执行文件！
    pause
    exit /b 1
)

echo.
echo [4/4] 复制配置文件...
if not exist "dist\若愚Bot\config.ini" (
    if exist "config.ini" (
        copy "config.ini" "dist\若愚Bot\"
        echo 已复制 config.ini
    )
)
if not exist "dist\若愚Bot\scheduled_tasks.json" (
    if exist "scheduled_tasks.json" (
        copy "scheduled_tasks.json" "dist\若愚Bot\"
        echo 已复制 scheduled_tasks.json
    )
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 📁 输出目录：dist\若愚Bot\
echo 🚀 运行程序：dist\若愚Bot\若愚Bot.exe
echo.
echo 提示：
echo - 首次运行会自动创建配置文件
echo - 可以将整个 dist\若愚Bot 文件夹复制到其他电脑使用
echo.
pause

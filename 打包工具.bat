@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║          若愚Bot 打包工具 - 选择打包方式              ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo  请选择打包方式：
echo.
echo  [1] 调试版本 (单文件 + 控制台) ⭐ 推荐首次使用
echo      - 可以看到错误信息
echo      - 用于测试和调试
echo      - 输出: 若愚Bot_debug.exe
echo.
echo  [2] 发布版本 (单文件 + 无控制台)
echo      - 用户体验最好
echo      - 适合最终发布
echo      - 输出: 若愚Bot.exe
echo.
echo  [3] 目录版本 (最稳定)
echo      - 最稳定，不会有 DLL 问题
echo      - 需要分发整个文件夹
echo      - 输出: dist\若愚Bot\ 文件夹
echo.
echo  [4] 修复依赖
echo      - 安装/更新必要的依赖包
echo      - 如果打包失败，先运行此选项
echo.
echo  [0] 退出
echo.
echo ════════════════════════════════════════════════════════
echo.

set /p choice=请输入选项 (0-4):

if "%choice%"=="1" goto debug
if "%choice%"=="2" goto onefile
if "%choice%"=="3" goto dir
if "%choice%"=="4" goto fix
if "%choice%"=="0" goto end
echo.
echo 无效的选项，请重新选择
pause
goto start

:debug
cls
echo.
echo 正在使用调试模式打包...
echo.
call build_debug.bat
goto end

:onefile
cls
echo.
echo 正在使用单文件模式打包...
echo.
call build_onefile.bat
goto end

:dir
cls
echo.
echo 正在使用目录模式打包...
echo.
call build_dir.bat
goto end

:fix
cls
echo.
echo 正在修复依赖...
echo.
call fix_deps.bat
echo.
echo 依赖修复完成！
echo.
pause
cls
goto start

:end
echo.
echo 感谢使用！
echo.

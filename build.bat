@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
set "APP_NAME=RuoYuBot"
set "NO_PROMPT="

if not exist "%PYTHON_EXE%" (
    echo ERROR: Missing venv Python: %PYTHON_EXE%
    echo Run: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "SPEC_FILE="
for %%F in (*.spec) do set "SPEC_FILE=%%F"

if /i "%~1"=="quick" (
    set "NO_PROMPT=1"
    goto quick
)
if /i "%~1"=="onefile" (
    set "NO_PROMPT=1"
    goto onefile
)
if /i "%~1"=="debug" (
    set "NO_PROMPT=1"
    goto debug
)

:menu
cls
echo ========================================
echo        RuoYuBot Build Tool
echo ========================================
echo.
echo [1] Quick build  - folder mode, recommended
echo [2] Onefile build
echo [3] Debug build  - console mode
echo [0] Exit
echo.
set /p choice=Choose (0-3):

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto onefile
if "%choice%"=="3" goto debug
if "%choice%"=="0" exit /b 0
goto menu

:quick
cls
echo ========================================
echo Quick build
echo ========================================
echo.
call :clean
call :build_onedir
goto end

:onefile
cls
echo ========================================
echo Onefile build
echo ========================================
echo.
call :clean
call :build_onefile
goto end

:debug
cls
echo ========================================
echo Debug build
echo ========================================
echo.
call :clean
call :build_debug
goto end

:clean
echo [1/3] Cleaning old files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo OK: clean complete
echo.
goto :eof

:build_onedir
echo [2/3] Building folder package...
if not defined SPEC_FILE (
    echo ERROR: No .spec file found in %CD%
    call :show_error
    pause
    exit /b 1
)
echo Using spec: %SPEC_FILE%
echo.
"%PYTHON_EXE%" -m PyInstaller --clean -y "%SPEC_FILE%"
if errorlevel 1 (
    echo.
    echo ERROR: build failed
    call :show_error
    pause
    exit /b 1
)

call :find_dist_dir
if not defined DIST_DIR (
    echo ERROR: dist folder output not found
    pause
    exit /b 1
)

call :copy_files "%DIST_DIR%"
call :find_exe "%DIST_DIR%"
call :show_success "%EXE_PATH%"
goto :eof

:build_onefile
echo [2/3] Building onefile package...
"%PYTHON_EXE%" -m PyInstaller --clean ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
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
if errorlevel 1 (
    echo.
    echo ERROR: build failed
    call :show_error
    pause
    exit /b 1
)

call :copy_files "dist"
call :show_success "dist\%APP_NAME%.exe"
goto :eof

:build_debug
echo [2/3] Building debug package...
"%PYTHON_EXE%" -m PyInstaller --clean ^
    --onedir ^
    --console ^
    --name "%APP_NAME%" ^
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
if errorlevel 1 (
    echo.
    echo ERROR: build failed
    call :show_error
    pause
    exit /b 1
)

call :copy_files "dist\%APP_NAME%"
call :show_success "dist\%APP_NAME%\%APP_NAME%.exe"
goto :eof

:find_dist_dir
set "DIST_DIR="
for /d %%D in ("dist\*") do set "DIST_DIR=%%~fD"
goto :eof

:find_exe
set "EXE_PATH="
for %%E in ("%~1\*.exe") do set "EXE_PATH=%%~fE"
goto :eof

:copy_files
echo.
echo [3/3] Copying config files...
if exist "config.ini" (
    copy "config.ini" "%~1\" >nul 2>&1
    echo OK: copied config.ini
)
if exist "scheduled_tasks.json" (
    copy "scheduled_tasks.json" "%~1\" >nul 2>&1
    echo OK: copied scheduled_tasks.json
)
goto :eof

:show_success
echo.
echo ========================================
echo OK: build succeeded
echo ========================================
echo.
echo EXE: %~1
echo.
echo Use the whole output folder when distributing folder-mode builds.
echo.
goto :eof

:show_error
echo.
echo Troubleshooting:
echo 1. Run: .venv\Scripts\python.exe -m pip install -r requirements.txt
echo 2. Run: .venv\Scripts\python.exe -m pip install --upgrade pyinstaller
echo 3. Try running this bat as administrator
echo 4. Check whether antivirus blocked the build
echo 5. Read PACKAGING_TROUBLESHOOTING.md
echo.
goto :eof

:end
echo.
if defined NO_PROMPT exit /b 0
set /p again=Build again? (Y/N):
if /i "%again%"=="Y" goto menu
exit /b 0

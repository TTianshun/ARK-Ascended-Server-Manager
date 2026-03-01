@echo off
REM ARK: Survival Ascended Server Manager - EXE build script (Windows batch)
REM This script calls the Python build script

setlocal enabledelayedexpansion

echo.
echo ======================================
echo ARK Ascended Server Manager - EXE Build
echo ======================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+.
    echo Make sure Python is available in PATH.
    pause
    exit /b 1
)

REM Show menu
echo Select build mode:
echo 1. One-file EXE (recommended) [default]
echo 2. One-dir build (faster startup)
echo 3. One-file EXE + clean old files
echo 4. One-dir build + clean old files
echo 5. Show console window (debug)
echo 6. Exit
echo.

set /p choice="Choose (default=1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo Building one-file EXE...
    python build_exe.py --onefile
) else if "%choice%"=="2" (
    echo Building one-dir output...
    python build_exe.py --onedir
) else if "%choice%"=="3" (
    echo Cleaning old files and building one-file EXE...
    python build_exe.py --onefile --clean
) else if "%choice%"=="4" (
    echo Cleaning old files and building one-dir output...
    python build_exe.py --onedir --clean
) else if "%choice%"=="5" (
    echo Building one-file EXE with console window...
    python build_exe.py --onefile --console
) else if "%choice%"=="6" (
    echo Exited.
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    pause
    exit /b 1
)

REM Check build result
if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b 1
) else (
    echo.
    echo Build complete. Press any key to open dist folder...
    pause
    start explorer "dist"
)

endlocal

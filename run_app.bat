@echo off
title FBX Unreal Rescaler Launcher
cd /d "%~dp0"

:: 1. Try pythonw in conda environment unimate if present
if exist "D:\Conda\envs\unimate\pythonw.exe" (
    start "" "D:\Conda\envs\unimate\pythonw.exe" "src\main.py"
    exit /b 0
)

if exist "D:\Conda\envs\unimate\python.exe" (
    start "" "D:\Conda\envs\unimate\pythonw.exe" "src\main.py"
    exit /b 0
)

:: 2. Fallback to pythonw on system PATH
where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw "src\main.py"
    exit /b 0
)

:: 3. Fallback to standard python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" python "src\main.py"
    exit /b 0
)

echo [ERROR] Python not found on the system.
pause

@echo off
title Build FBX Unreal Rescaler Executable
cd /d "%~dp0"

echo ========================================================
echo Building FBX Unreal Rescaler into standalone .exe
echo ========================================================
echo.

set PYTHON_EXE=python
if exist "D:\Conda\envs\unimate\python.exe" (
    set PYTHON_EXE=D:\Conda\envs\unimate\python.exe
)

"%PYTHON_EXE%" -m PyInstaller --clean pyinstaller.spec

echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Standalone executable created successfully at:
    echo dist\FBX_Unreal_Rescaler\FBX_Unreal_Rescaler.exe
    echo.
    echo You can now run the .exe directly!
) else (
    echo [ERROR] PyInstaller compilation failed.
)

pause

@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title CropSense Precision Agriculture System
cd /d "%~dp0"
echo ========================================================
echo        CropSense Precision Agriculture System
echo ========================================================
echo.
echo Starting CropSense Backend and opening dashboard...

:: Ensure Python is found (including Anaconda installations)
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\anaconda3\python.exe" (
        set "PATH=%USERPROFILE%\anaconda3;%USERPROFILE%\anaconda3\Scripts;%PATH%"
    )
)

python run_server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Retrying with Anaconda Python directly...
    if exist "%USERPROFILE%\anaconda3\python.exe" (
        "%USERPROFILE%\anaconda3\python.exe" run_server.py
    ) else (
        py run_server.py
    )
)
pause

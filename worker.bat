@echo off
title TikTok Motion - PC Automation Worker
cls

echo ===================================================
echo     TikTok Motion - SMM Panel PC Order Worker
echo ===================================================
echo [*] Listening for new SMM Panel orders...
echo.

:: Detect Python executable
set "PY_CMD="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else if exist "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" (
    set PY_CMD="C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PY_CMD=py -3
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            set PY_CMD=python
        )
    )
)

if "%PY_CMD%"=="" (
    echo [!] Python was not found on your system or in PATH.
    pause
    exit /b 1
)

%PY_CMD% pc_worker.py
pause

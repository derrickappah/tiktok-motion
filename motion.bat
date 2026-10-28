@echo off
title TikTok Motion by Dee
cls

echo ===================================================
echo     TikTok Motion - Bot & Menu Controller
echo ===================================================
echo [*] Starting Telegram Bot in companion window...
echo [*] Opening Terminal Menu in this window...
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
    echo Please install Python 3 or add it to PATH.
    pause
    exit /b 1
)

:: Terminate any previous bot instance to prevent Telegram Conflict error
taskkill /F /FI "WINDOWTITLE eq TikTok Motion Telegram Bot*" 2>nul
if exist .bot_pid (
    for /f "usebackq tokens=*" %%p in (".bot_pid") do taskkill /F /PID %%p 2>nul
    del /f /q .bot_pid 2>nul
)

:: 1. Launch Telegram Bot in dedicated companion window
start "TikTok Motion Telegram Bot" %PY_CMD% telegram_bot.py

:: 2. Launch Interactive Terminal Menu in this window
%PY_CMD% app.py

:: Clean up companion bot on exit
taskkill /F /FI "WINDOWTITLE eq TikTok Motion Telegram Bot*" 2>nul
if exist .bot_pid (
    for /f "usebackq tokens=*" %%p in (".bot_pid") do taskkill /F /PID %%p 2>nul
    del /f /q .bot_pid 2>nul
)

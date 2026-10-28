@echo off
title TikTok Motion - Add Accounts
cls

:: Check local Python312 installation
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" add_account.py %*
    goto end
)

if exist "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" add_account.py %*
    goto end
)

:: Try py launcher
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 add_account.py %*
    goto end
)

:: Try default python in PATH
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python add_account.py %*
    goto end
)

echo [!] Python was not found on your system or in PATH.
echo Please install Python 3 or add it to PATH.
pause
exit /b 1

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Press any key to exit...
    pause >nul
)

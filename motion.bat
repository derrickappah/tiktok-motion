@echo off
title TikTok Motion by Dee
cls

:: Check user Python312 installation where packages (playwright, etc.) are installed
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
    goto end
)

if exist "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" app.py
    goto end
)

:: Try py launcher (usually points to global Python)
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 app.py
    goto end
)

:: Try default python in PATH
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app.py
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

@echo off
title TikTok Motion by Dee
cls

:: Try system python or python launcher first, then fallback to local paths
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py app.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
    goto end
)

if exist "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" app.py
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

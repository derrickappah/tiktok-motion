@echo off
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python tiktok_auto.py %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py tiktok_auto.py %*
    exit /b %ERRORLEVEL%
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" tiktok_auto.py %*
    exit /b %ERRORLEVEL%
)

"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" tiktok_auto.py %*

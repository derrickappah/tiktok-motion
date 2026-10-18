@echo off
title TikTok Motion by Dee
cls
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Press any key to exit...
    pause >nul
)

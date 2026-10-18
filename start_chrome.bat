@echo off
echo Starting Google Chrome with acc_1 profile on debug port 9222...
taskkill /F /IM chrome.exe >nul 2>&1
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%~dp0profiles\acc_1"
echo Google Chrome started with acc_1!

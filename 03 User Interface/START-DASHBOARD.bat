@echo off
title WattWise Dashboard Server
cd /d "%~dp0"
echo Starting WattWise dashboard...
echo.
echo   When your browser opens, the dashboard is ready.
echo   Keep this window open while using the dashboard.
echo   Close it (or press Ctrl+C) to stop.
echo.
start "" "http://127.0.0.1:8917"
..\.venv\Scripts\python.exe -m http.server 8917 --bind 127.0.0.1
pause

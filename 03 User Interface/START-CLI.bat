@echo off
title WattWise CLI Monitor
cd /d "%~dp0"
echo WattWise terminal monitor - same data as the dashboard.
echo.
echo   commands: help | select ^<building^> | set time HH:MM | mode wattwise | play | tab reports | quit
echo.
python wattwise.py %*
pause

@echo off
setlocal
title MarketWise Runner
"%~dp0backend\.venv\Scripts\python.exe" "%~dp0scripts\start.py"
if errorlevel 1 (
  echo Startup failed. See README.md and server-error.log.
  pause
  exit /b 1
)
pause

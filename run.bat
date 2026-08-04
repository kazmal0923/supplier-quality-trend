@echo off
setlocal
cd /d "%~dp0"

python main.py
set "RESULT=%ERRORLEVEL%"

if /I "%~1"=="scheduled" (
  exit /b %RESULT%
)

if not "%RESULT%"=="0" (
  echo ERROR_LOG=logs\error.log
  pause
)

exit /b %RESULT%

@echo off
setlocal
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
if errorlevel 1 (
  echo [virtucraft] exited with error - window held open
  pause
  exit /b 1
)
endlocal
exit /b 0

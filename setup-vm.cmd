@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-vm.ps1"
set "setup_exit=%ERRORLEVEL%"
echo.
if not "%setup_exit%"=="0" (
  echo Installazione non completata. Mostra questo messaggio al docente.
)
pause
exit /b %setup_exit%

@echo off
REM Stop AI Trading Bot running on port 8000
echo Stopping AI Trading Bot background service...
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { if ($_ -ne 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }"
echo AI Trading Bot stopped successfully.
pause

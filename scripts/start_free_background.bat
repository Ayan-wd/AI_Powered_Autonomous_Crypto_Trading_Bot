@echo off
REM Start AI Trading Bot in the background silently (detached) on Windows
echo Starting AI Trading Bot background service...
powershell -WindowStyle Hidden -Command "Start-Process -WindowStyle Hidden python -ArgumentList '-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000'"
timeout /t 3 /nobreak >nul
echo Bot is now running live in the background!
echo Access dashboard at: http://localhost:8000/
echo To stop, run scripts\stop_free_background.bat
pause

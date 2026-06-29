@echo off
rem Start the Mayou ADB controller (file-bridge). Keep this window OPEN while playing.
cd /d "%~dp0"
where py >nul 2>nul && (py -3 controller.py) || (python controller.py)
echo.
echo Controller stopped.
pause

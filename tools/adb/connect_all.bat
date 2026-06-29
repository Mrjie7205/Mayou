@echo off
setlocal enabledelayedexpansion
rem Ports from RedFinger "ADB Debug -> Build All". They change each session; tell Claude if so.
set "ADB=%~dp0..\platform-tools\adb.exe"
if not exist "%ADB%" set "ADB=adb"
set "OUT=%~dp0..\..\assets\adb"
if not exist "%OUT%" mkdir "%OUT%"

for %%P in (V1-4=32702 V1-5=32704 V1-6=32705 V1-7=32707) do (
  for /f "tokens=1,2 delims==" %%a in ("%%P") do (
    echo === %%a   127.0.0.1:%%b ===
    "%ADB%" connect 127.0.0.1:%%b
    "%ADB%" -s 127.0.0.1:%%b shell wm size
    "%ADB%" -s 127.0.0.1:%%b shell screencap -p /sdcard/mayou_%%a.png
    "%ADB%" -s 127.0.0.1:%%b pull /sdcard/mayou_%%a.png "%OUT%\%%a.png" >nul
    echo   saved: assets\adb\%%a.png
    echo.
  )
)
echo === connected devices ===
"%ADB%" devices
echo.
echo Screenshots in: D:\AI Projects\Mayou\assets\adb\
pause

@echo off
chcp 65001 >nul
setlocal
rem === Mayou ADB 连通性验证（只读，不发点击） ===
rem 优先用项目内 platform-tools，其次用红手指/系统 PATH 里的 adb
set "ADB=%~dp0..\platform-tools\adb.exe"
if not exist "%ADB%" set "ADB=adb"

set "PORT=%~1"
if "%PORT%"=="" set /p "PORT=输入端口号(127.0.0.1: 后面的数字): "

echo.
echo === adb 版本 ===
"%ADB%" version
echo.
echo === 连接 127.0.0.1:%PORT% ===
"%ADB%" connect 127.0.0.1:%PORT%
echo.
echo === 设备列表(应能看到 127.0.0.1:%PORT%  device) ===
"%ADB%" devices
echo.
echo === 屏幕分辨率 ===
"%ADB%" -s 127.0.0.1:%PORT% shell wm size
echo.
echo === 截图到 assets\adb_test.png ===
"%ADB%" -s 127.0.0.1:%PORT% shell screencap -p /sdcard/mayou_adb_test.png
"%ADB%" -s 127.0.0.1:%PORT% pull /sdcard/mayou_adb_test.png "%~dp0..\..\assets\adb_test.png"
echo.
echo 若上面没有报错, 截图已保存到: D:\AI Projects\Mayou\assets\adb_test.png
echo 把这个文件和上面的输出反馈给 Claude 即可。
echo.
pause

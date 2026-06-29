@echo off
setlocal
set "DEST=%~dp0..\platform-tools"
echo Downloading Android platform-tools (adb), trying CN mirrors...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $urls=@('https://mirrors.tuna.tsinghua.edu.cn/android/repository/platform-tools-latest-windows.zip','https://mirrors.cloud.tencent.com/AndroidSDK/platform-tools-latest-windows.zip','https://mirrors.bfsu.edu.cn/android/repository/platform-tools-latest-windows.zip','https://dl.google.com/android/repository/platform-tools-latest-windows.zip'); $zip=Join-Path $env:TEMP 'mayou_pt.zip'; $ok=$false; foreach($u in $urls){ try{ Write-Host ('Trying: '+$u); Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $zip -TimeoutSec 60; if((Get-Item $zip).Length -gt 1000000){ $ok=$true; Write-Host 'Downloaded OK'; break } } catch { Write-Host ('  failed: '+$_.Exception.Message) } }; if($ok){ Expand-Archive -Force -Path $zip -DestinationPath (Split-Path -Parent '%DEST%'); Write-Host 'Extracted' } else { Write-Host 'ALL MIRRORS FAILED' }"
echo.
if exist "%DEST%\adb.exe" ( echo [OK] adb.exe ready & "%DEST%\adb.exe" version ) else ( echo [FAIL] adb.exe not found - tell Claude )
echo.
pause

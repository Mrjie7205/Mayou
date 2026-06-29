@echo off
rem One-click: commit ONLY the ADB files and push. Safe against the CRLF-flip noise.
cd /d "%~dp0..\.."
echo Repo: %CD%
if exist ".git\index.lock" ( echo Removing stale index.lock & del /f /q ".git\index.lock" )
rem unstage everything (keep working tree), then add only our files
git reset -q
git add .gitignore .gitattributes docs/08-adb-control.md tools/adb/README.md tools/adb/controller.py tools/adb/start_controller.bat tools/adb/setup_adb.bat tools/adb/connect_all.bat tools/adb/connect_test.bat tools/adb/git_push_adb.bat
echo === staged ===
git status -s
git commit -m "feat(adb): RedFinger official ADB channel + file-bridge controller"
echo === pushing ===
git push origin main
echo.
echo Done. If push asked for login, complete it and re-run.
pause

@echo off
chcp 65001 > nul
title ComfyUI Backend Server (Port 8188)
echo ========================================================
echo  ComfyUI 백엔드 서버를 포트 8188로 시작합니다...
echo ========================================================
echo.

set TARGET_DIR=D:\01.AntiGravity\Video_Create_Studio\ComfyUI

if not exist "%TARGET_DIR%\main.py" (
    echo [오류] ComfyUI가 설치되지 않았습니다. 먼저 'setup_comfyui.bat'을 실행하십시오.
    pause
    exit /b 1
)

cd /d "%TARGET_DIR%"
python main.py --listen 127.0.0.1 --port 8188 --windows-standalone-build
pause

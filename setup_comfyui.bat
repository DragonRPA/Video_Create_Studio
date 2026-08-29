@echo off
chcp 65001 > nul
title ComfyUI 자동 설치 및 환경 설정
echo ========================================================
echo  ComfyUI + MiniMax H3 로컬 백엔드 자동 설치 마법사
echo ========================================================
echo.

set TARGET_DIR=D:\01.AntiGravity\Video_Create_Studio\ComfyUI

:: 1. Git 설치 확인
git --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Git이 설치되어 있지 않습니다. Git for Windows를 설치해 주십시오.
    pause
    exit /b 1
)

:: 2. ComfyUI 저장소 클론
if not exist "%TARGET_DIR%" (
    echo [1/4] ComfyUI 공식 저장소를 복제합니다...
    git clone https://github.com/comfyanonymous/ComfyUI.git "%TARGET_DIR%"
) else (
    echo [1/4] ComfyUI 디렉터리가 이미 존재합니다. 최신 버전을 확인합니다...
    cd /d "%TARGET_DIR%"
    git pull
)

:: 3. 필수 Custom Nodes 설치 (VideoHelperSuite)
echo.
echo [2/4] 비디오 렌더링용 확장 노드(VideoHelperSuite) 설치 중...
set NODES_DIR=%TARGET_DIR%\custom_nodes
if not exist "%NODES_DIR%\ComfyUI-VideoHelperSuite" (
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "%NODES_DIR%\ComfyUI-VideoHelperSuite"
)

:: 4. PyTorch (CUDA) 및 필수 패키지 설치
echo.
echo [3/4] PyTorch (CUDA 12.1) 및 의존성 패키지를 설치합니다...
echo (이 작업은 네트워크 속도에 따라 수 분이 소요될 수 있습니다)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r "%TARGET_DIR%\requirements.txt"
pip install -r "%NODES_DIR%\ComfyUI-VideoHelperSuite\requirements.txt"

:: 5. 모델 경로(extra_model_paths.yaml) 자동 연결
echo.
echo [4/4] 다운로드된 MiniMax H3 모델 경로를 연결합니다...
copy /Y "D:\01.AntiGravity\Video_Create_Studio\extra_model_paths.yaml" "%TARGET_DIR%\extra_model_paths.yaml"

echo.
echo ========================================================
echo  ComfyUI 환경 설정이 완료되었습니다!
echo  이제 'run_comfyui.bat'을 실행하여 백엔드를 구동하십시오.
echo ========================================================
pause

@echo off
chcp 65001 > nul
title MiniMax H3 영상 생성 스튜디오
echo ========================================================
echo  MiniMax H3 로컬 독립실행 영상 생성 스튜디오 실행 중...
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Ollama 백그라운드 확인
echo [1/3] 로컬 SLM (Ollama) 상태 확인 중...
ollama list > nul 2>&1
if %errorlevel% neq 0 (
    echo [경고] Ollama가 실행 중이지 않습니다. 'ollama serve'를 실행해 주십시오.
) else (
    echo [확인] Ollama 엔진 정상 작동 중.
)

:: 2. 필수 라이브러리 검사
echo.
echo [2/3] 파이썬 패키지 의존성 점검 중...
pip install -r requirements.txt > nul 2>&1

:: 3. GUI 메인 스튜디오 실행
echo.
echo [3/3] MiniMax H3 데스크톱 GUI 스튜디오를 시작합니다...
python main.py

pause

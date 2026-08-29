@echo off
chcp 65001 >nul
title MiniMax H3 Video Create Studio
cd /d "%~dp0"

echo ========================================================
echo  MiniMax H3 Video Create Studio
echo ========================================================
echo.

python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Studio closed with an error.
    pause
)

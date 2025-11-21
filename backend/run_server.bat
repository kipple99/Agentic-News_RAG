@echo off
chcp 65001 >nul
echo ========================================
echo Agentic News RAG - Backend Server 시작
echo ========================================
echo.

cd /d "%~dp0"
python app.py

pause


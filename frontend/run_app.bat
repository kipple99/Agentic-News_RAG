@echo off
chcp 65001 >nul
echo ========================================
echo Agentic News RAG - 뉴스 검색 앱 시작
echo ========================================
echo.

cd /d "%~dp0"
streamlit run search_app.py

pause


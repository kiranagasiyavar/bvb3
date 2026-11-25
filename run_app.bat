@echo off
setlocal
cd /d "%~dp0"
title Anticipatory Commerce AI Agent - Web Dashboard

echo ======================================================================
echo   ANTICIPATORY COMMERCE AI AGENT - STREAMLIT LAUNCHER
echo   Project Directory: %CD%
echo ======================================================================
echo.

if exist ".\.venv\Scripts\streamlit.exe" (
    echo [OK] Virtual environment found.
    echo [INFO] Launching Streamlit web application on http://localhost:8501 ...
    echo [INFO] Press Ctrl+C in this window to stop the server.
    echo.
    ".\.venv\Scripts\streamlit.exe" run app.py --server.port 8501
) else (
    echo [ERROR] Virtual environment not found in: %CD%\.venv
    echo Please make sure the .venv folder is present.
)

pause

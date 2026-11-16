@echo off
echo =====================================================================
echo Starting Personal Finance Tracker — Frontend Web App (Streamlit)
echo Opening http://127.0.0.1:8501
echo =====================================================================
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_frontend.ps1"
if %ERRORLEVEL% neq 0 (
    set PYTHONPATH=%CD%
    uv run streamlit run src/frontend/app.py --server.port 8501 --server.address 127.0.0.1
)
pause

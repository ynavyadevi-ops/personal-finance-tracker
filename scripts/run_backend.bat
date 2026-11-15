@echo off
echo =====================================================================
echo Starting Personal Finance Tracker — Backend API Server (FastAPI)
echo Binding to http://127.0.0.1:8000
echo =====================================================================
cd /d "%~dp0\.."
uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
pause

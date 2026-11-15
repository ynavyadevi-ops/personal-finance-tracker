@echo off
echo =====================================================================
echo Personal Finance Tracker — Secure Administrative Enrollment CLI
echo =====================================================================
cd /d "%~dp0\.."
uv run python -m src.cli.enroll %*
pause

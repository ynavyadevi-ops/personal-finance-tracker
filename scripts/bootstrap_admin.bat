@echo off
echo =====================================================================
echo Personal Finance Tracker — Administrative Bootstrap CLI
echo =====================================================================
cd /d "%~dp0\.."
uv run python -m src.cli.bootstrap_admin %*
pause

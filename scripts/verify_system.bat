@echo off
echo =====================================================================
echo Personal Finance Tracker — Local Quality Gates Verification
echo =====================================================================
cd /d "%~dp0\.."

echo.
echo [1/4] Running automated test suite with coverage...
uv run --no-sync pytest --cov=src
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Test suite failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Running Ruff linter...
uv run --no-sync ruff check .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ruff linter failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Running Ruff format check...
uv run --no-sync ruff format --check .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ruff format check failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Running Mypy strict type checker...
uv run --no-sync mypy
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Mypy type check failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =====================================================================
echo [SUCCESS] All quality gates passed cleanly!
echo =====================================================================
pause

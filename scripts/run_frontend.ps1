# =====================================================================
# Personal Finance Tracker — Streamlit Frontend Launcher (PowerShell)
# =====================================================================
[CmdletBinding()]
param(
    [int]$Port = 8501,
    [string]$Address = "127.0.0.1"
)

# 1. Resolve repository root directory regardless of caller's working directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Resolve-Path "$ScriptDir\..").Path

# 2. Change working directory to repository root
Set-Location -Path $RepoRoot

# 3. Export PYTHONPATH to repository root for all child processes
$env:PYTHONPATH = $RepoRoot

# 4. Terminate any duplicate process listening on the target port
try {
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $pids) {
            Write-Host "[INFO] Stopping duplicate process on port $Port (PID: $p)..." -ForegroundColor Yellow
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }
} catch {
    # Non-fatal if connection inspection permissions are restricted
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Personal Finance Tracker — Streamlit Frontend" -ForegroundColor Cyan
Write-Host "Repository Root : $RepoRoot" -ForegroundColor Gray
Write-Host "PYTHONPATH      : $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "Binding Address : http://$($Address):$Port" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

# 5. Launch Streamlit within the project's uv virtual environment
uv run streamlit run src/frontend/app.py --server.port $Port --server.address $Address

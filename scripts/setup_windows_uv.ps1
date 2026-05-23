$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

Write-Step "Checking uv"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is not installed or is not on PATH."
    Write-Host "Install uv from: https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "Then restart PowerShell and run this script again."
    exit 1
}

if (-not $env:UV_CACHE_DIR) {
    $env:UV_CACHE_DIR = Join-Path (Get-Location) ".uv-cache"
    Write-Host "Using workspace uv cache: $env:UV_CACHE_DIR"
}

Write-Step "Installing Python 3.12 with uv"
uv python install 3.12

Write-Step "Checking for existing .venv"
if (Test-Path ".venv") {
    Write-Host ".venv already exists. This script will not delete it automatically."
    Write-Host "If you want a clean Python 3.12 environment, run this command from the repo root:"
    Write-Host "Remove-Item -Recurse -Force .venv" -ForegroundColor Yellow
    Write-Host "Then run this setup script again."
    exit 1
}

Write-Step "Creating .venv with Python 3.12"
uv venv --python 3.12

Write-Step "Syncing dependencies"
uv sync

Write-Step "Verifying Python version"
$pythonVersion = uv run python --version
Write-Host $pythonVersion
if (-not $pythonVersion.StartsWith("Python 3.12")) {
    Fail "uv is not using Python 3.12. Remove .venv and rerun this script."
}

Write-Step "Verifying core backend imports"
uv run python -c "import pydantic; import fastapi; import pyodbc; print('ok')"

Write-Step "Setup complete"
Write-Host "Next commands:"
Write-Host "cd procurement-agent/backend" -ForegroundColor Green
Write-Host "uv run python scripts/check_environment.py" -ForegroundColor Green

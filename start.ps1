# VirtuCraft start script
param([switch]$Mcp = $false)
$ErrorActionPreference = "Stop"

$env:Path = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:Path"
if ($null -eq (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: uv not found on PATH." -ForegroundColor Red
    exit 1
}

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "[virtucraft] Creating virtual environment..." -ForegroundColor Cyan
    & uv venv
    & uv pip install -e .
}

if ($Mcp) {
    & uv run virtucraft-cli mcp
} else {
    & uv run virtucraft-cli host info
    & uv run virtucraft-cli vm list
}

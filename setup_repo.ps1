param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$Seed,
    [switch]$Docker
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Circle Court repo setup" -ForegroundColor Green
Write-Host "Root: $Root"

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Write-Step "Creating .env from .env.example"
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path "backend\.env") -and (Test-Path ".env")) {
    Write-Step "Creating backend/.env from root .env"
    Copy-Item ".env" "backend\.env"
}

if ($Docker) {
    Write-Step "Starting Docker Compose stack"
    Require-Command "docker"
    docker compose up --build
    exit $LASTEXITCODE
}

if (-not $SkipBackend) {
    Write-Step "Setting up Python backend"
    Require-Command "python"

    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }

    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r "backend\requirements.txt"

    Write-Step "Checking backend imports"
    & $Python -m compileall "backend\app"

    if ($Seed) {
        Write-Step "Seeding example contracts and disputes"
        Push-Location "backend"
        try {
            & $Python -m app.seed.seed
        } finally {
            Pop-Location
        }
    }
}

if (-not $SkipFrontend) {
    Write-Step "Setting up React frontend"
    Require-Command "npm.cmd"
    Push-Location "frontend"
    try {
        npm.cmd install --no-audit --no-fund
        npm.cmd run build
    } finally {
        Pop-Location
    }
}

Write-Step "Setup complete"
Write-Host "Backend dev server:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend"
Write-Host "Frontend dev server:" -ForegroundColor Yellow
Write-Host "  cd frontend; npm.cmd run dev"
Write-Host "Docker stack:" -ForegroundColor Yellow
Write-Host "  .\setup_repo.ps1 -Docker"

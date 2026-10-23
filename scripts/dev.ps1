<#
  AniCharaLib development task runner (Windows PowerShell 5.1+ / PowerShell 7).
  Use through dev.cmd in the repository root, e.g.  .\dev.cmd setup
  Run  .\dev.cmd help  for the command list.
#>
param(
    [Parameter(Position = 0)][string]$Command = "help",
    [Parameter(Position = 1)][string]$Name,
    [switch]$SkipDocker,
    [switch]$Yes,
    [switch]$Volume
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Venv = Join-Path $Backend ".venv"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$ComposeFile = Join-Path $Root "docker-compose.yml"
$MinPython = [version]"3.11"
$MinNode = [version]"20.19"

function Write-Step([string]$Text) { Write-Host "==> $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "    $Text" -ForegroundColor Green }
function Fail([string]$Text) { throw $Text }

# Run a native program and stop on a non-zero exit code.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments, [string]$WorkDir = $Root)
    Push-Location $WorkDir
    try {
        & $Exe @Arguments
        if ($LASTEXITCODE -ne 0) { Fail "Command failed ($LASTEXITCODE): $Exe $($Arguments -join ' ')" }
    }
    finally { Pop-Location }
}

function Test-Command([string]$Name) { return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Get-FileHashText([string[]]$Paths) {
    $text = ($Paths | ForEach-Object { (Get-FileHash -Algorithm SHA256 $_).Hash }) -join ","
    return $text
}

# ---------------------------------------------------------------- prerequisites

function Find-SystemPython {
    # Prefer the py launcher; "python" may be the Microsoft Store stub.
    $candidates = @()
    if (Test-Command "py") { $candidates += , @("py", "-3") }
    if (Test-Command "python") { $candidates += , @("python") }
    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $prefix = @($candidate | Select-Object -Skip 1)
        try {
            $out = & $exe @prefix -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out -and ([version]$out.Trim() -ge $MinPython)) {
                return , $candidate
            }
        }
        catch { }
    }
    Fail "Python $MinPython or newer was not found. Install it from https://www.python.org/downloads/ (enable 'py launcher')."
}

function Assert-Node {
    if (-not (Test-Command "node")) { Fail "Node.js was not found. Install Node.js 22 LTS from https://nodejs.org/" }
    $version = [version]((& node --version).TrimStart("v"))
    if ($version -lt $MinNode) { Fail "Node.js $version is too old; $MinNode or newer is required." }
    Write-Ok "Node.js $version"
}

function Assert-Docker {
    if (-not (Test-Command "docker")) {
        Fail "Docker was not found. Install Docker Desktop (https://www.docker.com/products/docker-desktop/), or pass -SkipDocker to use your own PostgreSQL from .env."
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) { Fail "Docker is installed but not running. Start Docker Desktop and retry." }
    Write-Ok "Docker is running"
}

function Initialize-EnvFile {
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $Root ".env.example") $envFile
        Write-Ok "Created .env from .env.example"
    }
    else { Write-Ok ".env already exists (kept)" }
}

# ---------------------------------------------------------------- building blocks

function Start-Database {
    if ($SkipDocker) { Write-Ok "Skipping Docker; using the PostgreSQL configured in .env"; return }
    Assert-Docker
    Write-Step "Starting PostgreSQL (docker compose)"
    Invoke-Native "docker" @("compose", "-f", $ComposeFile, "up", "-d", "--wait", "db")
}

function Install-Backend {
    if (-not (Test-Path $VenvPython)) {
        Write-Step "Creating Python virtual environment"
        $python = Find-SystemPython
        $exe = $python[0]
        $prefix = @($python | Select-Object -Skip 1)
        Invoke-Native $exe ($prefix + @("-m", "venv", $Venv))
    }
    $requirements = @((Join-Path $Backend "requirements.txt"), (Join-Path $Backend "requirements-dev.txt"))
    $stamp = Join-Path $Venv ".requirements.sha256"
    $hash = Get-FileHashText $requirements
    if ((Test-Path $stamp) -and ((Get-Content $stamp -Raw).Trim() -eq $hash)) {
        Write-Ok "Python dependencies up to date"
        return
    }
    Write-Step "Installing Python dependencies"
    Invoke-Native $VenvPython @("-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", "requirements-dev.txt") $Backend
    Set-Content -Path $stamp -Value $hash -Encoding ascii
}

function Install-Frontend {
    Assert-Node
    $lock = Join-Path $Frontend "package-lock.json"
    $stamp = Join-Path $Frontend "node_modules\.package-lock.sha256"
    $hash = Get-FileHashText @($lock)
    if ((Test-Path $stamp) -and ((Get-Content $stamp -Raw).Trim() -eq $hash)) {
        Write-Ok "Frontend dependencies up to date"
        return
    }
    Write-Step "Installing frontend dependencies (npm ci)"
    Invoke-Native "npm" @("ci", "--no-audit", "--no-fund") $Frontend
    Set-Content -Path $stamp -Value $hash -Encoding ascii
}

function Assert-Venv {
    if (-not (Test-Path $VenvPython)) { Fail "Backend environment missing. Run: .\dev.cmd setup" }
}

function Invoke-Manage([string[]]$Arguments) {
    Assert-Venv
    Invoke-Native $VenvPython (@("-m", "app.manage") + $Arguments) $Backend
}

# ---------------------------------------------------------------- commands

function Invoke-Setup {
    Write-Step "Checking prerequisites"
    $python = Find-SystemPython
    Write-Ok "Python: $($python -join ' ')"
    Assert-Node
    Initialize-EnvFile
    Start-Database
    Install-Backend
    Write-Step "Migrating database and importing demo data"
    Invoke-Manage @("init")
    Install-Frontend
    Write-Host ""
    Write-Host "Setup complete. Start the app in two terminals:" -ForegroundColor Green
    Write-Host "    .\dev.cmd backend     # FastAPI  http://localhost:8000/docs"
    Write-Host "    .\dev.cmd frontend    # Vite     http://localhost:5173"
}

function Invoke-Reset {
    if ($Volume) {
        if ($SkipDocker) { Fail "-Volume needs Docker; drop -SkipDocker or use plain 'reset'." }
        Assert-Docker
        Write-Host "This deletes the Docker volume with ALL local database data and recreates it from migrations + seed files." -ForegroundColor Yellow
        if (-not $Yes) {
            $answer = Read-Host "Type RESET to confirm"
            if ($answer -ne "RESET") { Write-Host "Aborted, nothing was changed."; exit 1 }
        }
        Write-Step "Removing database container and volume"
        Invoke-Native "docker" @("compose", "-f", $ComposeFile, "down", "-v")
        Start-Database
        Invoke-Manage @("init")
        return
    }
    $arguments = @("reset")
    if ($Yes) { $arguments += "--yes" }
    Invoke-Manage $arguments
}

function Invoke-NewMigration {
    if (-not $Name) { Fail "Usage: .\dev.cmd migration ""describe the change""" }
    Write-Step "Checking that the database is at the latest migration"
    Invoke-Manage @("status")
    Write-Step "Generating migration from model changes"
    Invoke-Native $VenvPython @("-m", "alembic", "revision", "--autogenerate", "-m", $Name) $Backend
    Write-Host ""
    Write-Host "Review the new file in backend\alembic\versions, then run .\dev.cmd migrate and commit it together with the model change." -ForegroundColor Yellow
}

function Show-Help {
    @"
AniCharaLib dev commands  (.\dev.cmd <command> [options])

  setup              Install everything and initialise the database (safe to re-run,
                     e.g. after git pull). Options: -SkipDocker
  db                 Start PostgreSQL in Docker
  db-stop            Stop the PostgreSQL container (data is kept in the Docker volume)
  backend            Apply pending migrations, then run FastAPI with auto-reload (:8000)
  frontend           Run the Vite dev server (:5173)
  migrate            Apply pending Alembic migrations
  seed               Re-sync demo data from backend\data\*.yaml
  status             Show database connection and migration state
  migration "msg"    Autogenerate a migration after changing app\models.py
  test               Run backend tests and the frontend type check
  reset              Drop all tables, migrate and re-seed (asks for confirmation)
                     Options: -Yes (no prompt), -Volume (delete the Docker volume instead)
"@ | Write-Host
}

try {
    switch ($Command.ToLower()) {
        "setup" { Invoke-Setup }
        "db" { Start-Database; Invoke-Manage @("wait") }
        "db-stop" { Assert-Docker; Invoke-Native "docker" @("compose", "-f", $ComposeFile, "stop") }
        "backend" {
            Invoke-Manage @("migrate")
            Invoke-Native $VenvPython @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000") $Backend
        }
        "frontend" {
            if (-not (Test-Path (Join-Path $Frontend "node_modules"))) { Install-Frontend }
            Invoke-Native "npm" @("run", "dev") $Frontend
        }
        "migrate" { Invoke-Manage @("migrate") }
        "seed" { Assert-Venv; Invoke-Native $VenvPython @("-m", "app.seed") $Backend }
        "status" { Invoke-Manage @("status") }
        "migration" { Invoke-NewMigration }
        "test" {
            Assert-Venv
            Invoke-Native $VenvPython @("-m", "pytest") $Backend
            Invoke-Native "npm" @("run", "typecheck") $Frontend
        }
        "reset" { Invoke-Reset }
        default { Show-Help }
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# start-server.ps1
# Usage: Run from the backend folder. Sets env vars for this session and starts Waitress.
param(
    [string]$BindHost = "0.0.0.0",
    [int]$BindPort = 5000
)

$ErrorActionPreference = "Stop"

try {
    Write-Host "Starting StegCrypt+ (host=$BindHost port=$BindPort)..."

    # Set environment variables for this session (override these with secure values)
    $env:FLASK_ENV = "production"
    $env:FLASK_APP = "wsgi:app"
    $env:DATABASE_URL = "postgresql://steguser:strongpassword@127.0.0.1:5432/stegcryptdb"
    $env:RATELIMIT_STORAGE_URL = "redis://127.0.0.1:6379/0"
    $env:SECRET_KEY = "replace-with-a-secure-secret"
    $env:JWT_SECRET_KEY = "replace-with-a-secure-jwt-secret"

    # Activate virtualenv (PowerShell activation script)
    $venvActivate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "Activating virtualenv..."
        & $venvActivate
    } else {
        throw "Virtualenv activate script not found at: $venvActivate"
    }

    # Resolve waitress executable path inside venv
    $waitressExe = Join-Path $PSScriptRoot "venv\Scripts\waitress-serve.exe"
    if (-not (Test-Path $waitressExe)) {
        # fallback to module entry if waitress-serve.exe missing
        Write-Host "waitress-serve.exe not found, trying python -m waitress..."
        $pythonExe = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
        if (-not (Test-Path $pythonExe)) {
            throw "python.exe not found in venv at: $pythonExe"
        }
        # Use Start-Process so stdout/stderr flow to console
        $listenArg = "--listen=$($BindHost):$BindPort"
        Write-Host "Launching: $pythonExe -m waitress $listenArg wsgi:app"
        & $pythonExe -m waitress $listenArg wsgi:app
        return
    }

    # Build listen argument safely (avoid PowerShell variable parsing issues)
    $listenArg = "--listen=$($BindHost):$BindPort"

    Write-Host "Launching: $waitressExe $listenArg wsgi:app"
    & $waitressExe $listenArg "wsgi:app"
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.InnerException) {
        Write-Host "INNER: $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
    exit 1
}

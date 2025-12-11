$scriptPath = Join-Path (Get-Location) 'run_waitress.ps1'
@'
# run_waitress.ps1 - start backend with Waitress
# Place this file in C:\Stegcrypt+\backend

# optional: activate a venv by uncommenting and editing the path
# & "C:\path\to\venv\Scripts\Activate.ps1"

# ensure environment file variables are available (optional)
# If you want to load .env into the current process, install python-dotenv and use python to load it
# We rely on NSSM/AppEnvironmentExtra or system env vars for production

# install requirements (idempotent)
python -m pip install --upgrade pip
if (Test-Path -Path ".\requirements.txt") {
    python -m pip install -r .\requirements.txt
}

# Start waitress -- adjust module:object if your wsgi entrypoint differs
# Default expects backend/wsgi.py exposing `app` (i.e. from wsgi import app)
Write-Host "Starting Waitress on port 8000..."
# If your app is created with create_app factory, use: waitress-serve --port=8000 --call 'wsgi:create_app'
waitress-serve --port=8000 wsgi:app
'@ | Set-Content -Path $scriptPath -Encoding UTF8

Write-Host "Wrote run_waitress.ps1 -> $scriptPath"

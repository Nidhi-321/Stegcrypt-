# create_and_run_install_nssm.ps1 — run this in an Administrator PowerShell
$backend = 'C:\Stegcrypt+\backend'
$installPath = Join-Path $backend 'install_nssm.ps1'

@'
# install_nssm.ps1 - Requires Administrator
# This script installs an NSSM service to run run_waitress.ps1 in C:\Stegcrypt+\backend
# Edit the environment string below before running if you want different secrets.

$nssm = "C:\nssm\nssm.exe"
if (-not (Test-Path $nssm)) {
    Write-Error "nssm not found at $nssm. Please install/extract NSSM and set the path in this script."
    exit 1
}

$svcName = "StegcryptBackend"
$app = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$workdir = "C:\Stegcrypt+\backend"
$script = "$workdir\run_waitress.ps1"
$args = "-ExecutionPolicy Bypass -File `"$script`""

Write-Host "Installing service $svcName using $nssm..."

# install (non-interactive)
& $nssm install $svcName $app $args

Start-Sleep -Seconds 1

# configure service
& $nssm set $svcName AppDirectory $workdir

# setup logs
$logDir = Join-Path $workdir 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stdout = Join-Path $logDir 'service_stdout.log'
$stderr = Join-Path $logDir 'service_stderr.log'
& $nssm set $svcName AppStdout $stdout
& $nssm set $svcName AppStderr $stderr
& $nssm set $svcName AppRotateFiles 1

# environment variables - change values before running if needed
$envString = "DATABASE_URL=postgresql+psycopg2://dbuser:dbpass@127.0.0.1:5432/stegcrypt;SECRET_KEY=replace-with-strong-secret;REDIS_URL=redis://127.0.0.1:6379/0"
& $nssm set $svcName AppEnvironmentExtra $envString

# auto start and start now
& $nssm set $svcName Start SERVICE_AUTO_START
& $nssm start $svcName

Write-Host "Service $svcName install script finished. Check logs in $logDir"
'@ | Set-Content -Path $installPath -Encoding UTF8

Write-Host "Wrote installer to: $installPath"
Write-Host "Running installer now..."

# execute the installer script we just wrote (must be running as Administrator)
& $installPath

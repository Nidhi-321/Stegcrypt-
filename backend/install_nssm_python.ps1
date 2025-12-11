# backend/install_nssm_python.ps1  (RUN AS ADMIN)
$nssm = "C:\nssm\nssm.exe"
if (-not (Test-Path $nssm)) { Write-Error "nssm not found at $nssm"; exit 1 }

$svcName = "StegcryptBackend"
$pythonExe = "C:\Users\Nidhin Dev D\AppData\Local\Programs\Python\Python311\python.exe"
$workdir = "C:\Stegcrypt+\backend"
$logDir = Join-Path $workdir 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stdout = Join-Path $logDir 'service_stdout.log'
$stderr = Join-Path $logDir 'service_stderr.log'

# Set env string (edit secrets BEFORE running)
$envString = "DATABASE_URL=postgresql+psycopg2://dbuser:dbpass@127.0.0.1:5432/stegcrypt;SECRET_KEY=replace-with-strong-secret;REDIS_URL=redis://127.0.0.1:6379/0;RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/1"

# stop existing and remove
Try { & $nssm stop $svcName } Catch {}
Try { & $nssm remove $svcName confirm } Catch {}

# install
& $nssm install $svcName $pythonExe "-m waitress --port=8000 wsgi:app"
& $nssm set $svcName AppDirectory $workdir
& $nssm set $svcName AppStdout $stdout
& $nssm set $svcName AppStderr $stderr
& $nssm set $svcName AppRotateFiles 1
& $nssm set $svcName AppEnvironmentExtra $envString
& $nssm set $svcName Start SERVICE_AUTO_START

# start
& $nssm start $svcName
& $nssm status $svcName
Write-Host "Installed service $svcName. Logs: $stdout / $stderr"

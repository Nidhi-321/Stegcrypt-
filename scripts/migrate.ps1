# backend/scripts/migrate.ps1
# run in an elevated or appropriate user shell (not necessarily admin)
$python = "C:\Users\Nidhin Dev D\AppData\Local\Programs\Python\Python311\python.exe"
Set-Location (Split-Path $MyInvocation.MyCommand.Path -Parent)
& $python -m alembic upgrade head

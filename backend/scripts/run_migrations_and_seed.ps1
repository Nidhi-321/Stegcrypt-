# run_migrations_and_seed.ps1
Set-Location (Join-Path $PSScriptRoot ..)
& "C:\Users\Nidhin Dev D\AppData\Local\Programs\Python\Python311\python.exe" -m alembic upgrade head
# optionally run a seed script if you have one:
# & "C:\Users\Nidhin Dev D\AppData\Local\Programs\Python\Python311\python.exe" scripts/seed_db.py

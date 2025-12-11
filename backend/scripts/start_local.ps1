# start_local.ps1
Set-Location (Join-Path $PSScriptRoot ..)
& "C:\Users\Nidhin Dev D\AppData\Local\Programs\Python\Python311\python.exe" -m waitress --port=8000 wsgi:app

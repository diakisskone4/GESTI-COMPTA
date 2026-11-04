# Démarrage local sous Windows : backend Django (port 8000) + frontend Vite (port 5173).
# Usage depuis la racine du projet :  powershell -ExecutionPolicy Bypass -File scripts\dev-start.ps1
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

Push-Location (Join-Path $root 'backend')
& $python manage.py migrate --noinput
& $python manage.py bootstrap_data --demo
Start-Process -FilePath $python -ArgumentList 'manage.py', 'runserver', '127.0.0.1:8000' -WorkingDirectory (Get-Location)
Pop-Location

Push-Location (Join-Path $root 'frontend')
if (-not (Test-Path 'node_modules')) { npm install }
Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'dev' -WorkingDirectory (Get-Location)
Pop-Location

Write-Host "Application : http://localhost:5173   (API : http://127.0.0.1:8000/api/)"

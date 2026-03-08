#requires -Version 5.1
$ErrorActionPreference = 'Stop'
function Get-PythonCmd {
  if (Get-Command py -ErrorAction SilentlyContinue) { return 'py' }
  if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
  throw "No se encontró Python. Instalar Python 3.10+ y marcar 'Add Python to PATH'."
}
function Run-Step($title, $command) {
  Write-Host "`n==== $title ====" -ForegroundColor Cyan
  Write-Host $command -ForegroundColor DarkGray
  Invoke-Expression $command
}
if (-not (Test-Path ".\elpasaje_v1.py")) { throw "No se encontró elpasaje_v1.py en la carpeta actual." }
$py = Get-PythonCmd
New-Item -ItemType Directory -Force -Path .\database | Out-Null
New-Item -ItemType Directory -Force -Path .\backups | Out-Null
Run-Step "Actualizar pip" "$py -m pip install --upgrade pip"
Run-Step "Instalar dependencias" "$py -m pip install -r .\requirements.txt"
if (-not (Test-Path ".\database\elpasaje.db")) { Run-Step "Primer arranque" "$py .\scripts\primer_arranque.py" }
Run-Step "Doctor entorno" "$py .\scripts\doctor_local_setup.py"
Run-Step "Smoke datos" "$py .\scripts\smoke_check.py"
Run-Step "Backup DB" "$py .\scripts\backup_sqlite.py"
Write-Host "`n✅ Listo. Abrí la app con:" -ForegroundColor Green
Write-Host "$py -m streamlit run .\elpasaje_v1.py --server.port 8601" -ForegroundColor Magenta

# Runbook de despliegue y operación — El Pasaje

## Variables de entorno

Definir antes de ejecutar en productivo:

- `EP_ADMIN_USER`
- `EP_ADMIN_PASSWORD`
- `EP_OPS_USER`
- `EP_OPS_PASSWORD`

## Arranque (Windows PowerShell)

```powershell
cd "C:\ruta\La_Piedad_Tech_Design"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run elpasaje_v1.py --server.port 8501
```

## Errores frecuentes (Windows)

### 1) `[Errno 2] No such file or directory: 'elpasaje_v1.py'`

Estás ejecutando desde una carpeta incorrecta (por ejemplo `magnitud19-backend`).

```powershell
cd "C:\Users\ar028883\Documents\La_Piedad_Tech_Design"
```

### 2) `can't open file ... scripts\smoke_check.py`

Tu copia local no tiene la carpeta `scripts/` (repo desactualizado o copia incompleta).

Verificá:

```powershell
dir .\scripts
```

Si no existe, actualizá la copia del proyecto principal de El Pasaje antes de correr smoke.

### 3) `Port 8501 is not available`

Usá otro puerto:

```powershell
streamlit run .\elpasaje_v1.py --server.port 8502
```

### 4) `python` no se reconoce

Activá el entorno virtual y usá `py` como alternativa:

```powershell
& ".\.venv\Scripts\Activate.ps1"
py -m py_compile .\elpasaje_v1.py
```

### 5) Activación mal tipeada de venv en `magnitud19-backend`

La ruta correcta es **sin espacios**:

```powershell
cd "C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend"
& "..\.venv\Scripts\Activate.ps1"
```

### 6) La app abre pero se ve vieja (EPCC v1.0 / módulos en desarrollo)

Eso indica que `elpasaje_v1.py` local está desactualizado.

Chequeo rápido:

```powershell
Select-String -Path .\elpasaje_v1.py -Pattern "VERSION =|MENU_ALIASES|EPCC v2.0"
```

Si muestra `VERSION = "1.0 Enterprise"`, actualizá el archivo local por la versión actual del repo y volvé a correr:

```powershell
streamlit cache clear
streamlit run .\elpasaje_v1.py --server.port 8601
```

Tip: `python .\scripts\smoke_check.py` ahora detecta explícitamente la versión legacy 1.0.


## Arranque (Linux)

```bash
cd /ruta/proyecto
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run elpasaje_v1.py --server.port 8501
```

## Respaldo diario de SQLite

Ejecutar diariamente:

```bash
python scripts/backup_sqlite.py
```

Esto genera respaldo con timestamp en `backups/`.

## Verificaciones operativas diarias

1. Abrir app y validar login admin.
2. Revisar `logs/elpasaje.log`.
3. Verificar que `database/elpasaje.db` y backups existen.
4. Confirmar que se pueden leer productos en catálogo.

## Plan de rollback

1. Detener Streamlit.
2. Restaurar backup más reciente de `backups/` sobre `database/elpasaje.db`.
3. Volver a iniciar Streamlit.

## Criterio de salida a producción controlada

- QA checklist completo sin bloqueantes.
- Credenciales configuradas por variables de entorno.
- Backup diario funcionando.
- Responsable operativo asignado para incidencias.

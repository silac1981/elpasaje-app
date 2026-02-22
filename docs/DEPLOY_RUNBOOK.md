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

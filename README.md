# elpasaje-app
Plataforma oficial El Pasaje - público general y B2B.

## Estado del proyecto

El estado operativo actual y el plan para completar la puesta en marcha están documentados en:

- `PLAN_PUESTA_EN_MARCHA.md`

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run elpasaje_v1.py
```

## Variables de entorno (prioridad)

Copiar `.env.example` y definir credenciales administrativas fuera del código fuente.

```bash
cp .env.example .env
# editar .env con valores reales
```

Variables usadas por la app:

- `EP_ADMIN_USER`
- `EP_ADMIN_PASSWORD`
- `EP_OPS_USER`
- `EP_OPS_PASSWORD`

## Uso rápido (cargar clientes y fotos)

1. Ingresar como Admin (`EP_ADMIN_USER` / `EP_ADMIN_PASSWORD`).
2. Ir a **👥 Gestión** y crear clientes.
3. Ir a **📦 Inventario** y crear productos.
4. En alta de producto podés cargar foto desde **"Foto del producto"** (se guarda en `assets/productos/...`).
5. Revisar el resultado en **🛍️ Catálogo Completo**.

## Documentación operativa

- QA manual de cierre MVP: `docs/QA_CHECKLIST.md`
- Runbook de despliegue/operación: `docs/DEPLOY_RUNBOOK.md`
- Smoke check local: `python scripts/smoke_check.py`
- Backup manual de SQLite: `python scripts/backup_sqlite.py`

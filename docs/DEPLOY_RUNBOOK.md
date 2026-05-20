# Runbook de Despliegue y Operación — El Pasaje 3D Studio
## Sistema v3.0 · EPCC v2 · Mayo 2026

---

## Estructura del proyecto

```
magnitud19-backend-share/
├── main.py                  ← Punto de entrada principal (router + auth + sidebar)
├── crear_schema_v3.py       ← Init de DB — se llama automáticamente desde main.py
├── elpasaje_v2.db           ← Base de datos activa (SQLite, en la raíz del proyecto)
├── modules/
│   ├── dashboard_admin.py   ← Dashboard Alejandra + tab Mike
│   ├── panel_fer.py         ← Centro de producción Fernando (7 tabs)
│   ├── panel_socio.py       ← Panel socios (8 tabs)
│   ├── panel_mike.py        ← Panel inteligencia ecosistema
│   ├── cargar_pedido.py     ← Formulario de pedidos
│   └── inventario.py
├── utils/
│   ├── db.py                ← SQLAlchemy engine (elpasaje_v2.db)
│   ├── lineas.py            ← LINEAS dict, get_linea(), IP_RESTRINGIDA
│   ├── mike.py              ← get_alertas_dashboard(), preguntar_mike()
│   ├── pricing.py           ← cargar_materiales(), cálculos de costo
│   └── whatsapp.py          ← Generador de links WA
├── migration_v4.py          ← Correr si es la primera vez
├── migration_v5.py          ← Tabla pagos + pago_id en orders
├── migration_v5b.py         ← Tabla lineas_config + seed (11 líneas)
├── migration_v6.py          ← Tabla archivos_produccion
├── backup_manager.py        ← Backup multi-destino
└── slicer_parser.py         ← Parser de .gcode / .3mf de slicers
```

---

## Primera instalación (Windows PowerShell)

```powershell
# 1. Entrar al directorio del proyecto
cd "C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share"

# 2. Crear entorno virtual (una sola vez)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Correr las migraciones (una sola vez, en orden)
python migration_v4.py
python migration_v5.py
python migration_v5b.py
python migration_v6.py

# 5. Arrancar la app
streamlit run main.py --server.port 8501
```

> La DB `elpasaje_v2.db` se crea automáticamente en el primer `streamlit run` vía `crear_schema_v3.py`.
> Las migraciones son idempotentes — se pueden correr N veces sin romper nada.

---

## Arranque normal (sesión siguiente)

```powershell
cd "C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share"
.\.venv\Scripts\Activate.ps1
streamlit run main.py --server.port 8501
```

---

## Primera instalación (Linux / Mac)

```bash
cd /ruta/magnitud19-backend-share
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python migration_v4.py && python migration_v5.py && python migration_v5b.py && python migration_v6.py
streamlit run main.py --server.port 8501
```

---

## Agente Mike (análisis nocturno)

```powershell
# Análisis completo + envío de email
python ep_agente.py

# Solo análisis, sin email
python ep_agente.py silencioso
```

Corre automáticamente a las 20:00 hs via tarea programada de Windows o cron.
Resultados en la tabla `log_agente` y en el email `elpasaje.3d.studio@gmail.com`.

---

## Backup

```powershell
python backup_manager.py
```

Genera copia con timestamp en `backups/`. También respalda a GitHub y Google Drive si están configurados.
Correr manualmente o programar como tarea diaria.

---

## Verificar que la DB tiene las tablas correctas

```powershell
python check_v5.py
```

Tablas que deben existir: `tenants`, `products`, `materials`, `orders`, `order_items`,
`production_log`, `pagos`, `lineas_config`, `archivos_produccion`, `price_history`,
`stock_movements`, `senales_mercado`, `log_agente`, `donations`.

---

## Verificaciones operativas diarias

1. Entrar a la app con `admin@elpasaje.com` — confirmar que carga el dashboard
2. Ir a 🤖 Mike → verificar que las alertas aparecen (o "Sin alertas activas")
3. Confirmar que `elpasaje_v2.db` existe en la raíz del proyecto
4. Si hay backup programado: verificar que existe en `backups/` con timestamp del día

---

## Credenciales de acceso

| Usuario | Email | Rol |
|---------|-------|-----|
| admin | admin@elpasaje.com | Admin — acceso total |
| fer_produccion | fer@elpasaje.com | Producción — solo panel Fer |
| olivia_coquette | coquette@elpasaje.com | Socio — línea Coquette |
| francisco_sport | fsport@elpasaje.com | Socio — línea Sport |
| constantino_tech | coretech@elpasaje.com | Socio — línea Core Tech |
| aviation | aviation@elpasaje.com | Socio B2B — Aviation Pro |
| agustina | (ver lineas_config) | Socio multi — Oasis Animal + Oasis del Estero + VK-Home |

Passwords por defecto SHA-256: `admin123` o `123`. Fer tiene password propio (Alejandra lo asigna).

---

## Errores frecuentes

### `[Errno 2] No such file or directory: 'main.py'`
Estás parado en el directorio incorrecto.
```powershell
cd "C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share"
```

### `Port 8501 is not available`
```powershell
streamlit run main.py --server.port 8502
```

### `OperationalError: no such table: pagos`
Falta correr las migraciones:
```powershell
python migration_v5.py
python migration_v5b.py
python migration_v6.py
```

### `OperationalError: no such column: imagen_url`
La tabla `products` fue creada con un schema anterior. Correr:
```powershell
python -c "import sqlite3; c=sqlite3.connect('elpasaje_v2.db'); c.execute(\"ALTER TABLE products ADD COLUMN imagen_url TEXT\"); c.commit()"
```

### La app carga pero no aparece la pestaña 📁 Archivos en el panel de Fer
Falta la migración v6:
```powershell
python migration_v6.py
```

### `python` no se reconoce
```powershell
& ".\.venv\Scripts\Activate.ps1"
py -m streamlit run main.py
```

### La app se ve con layout viejo (v1 / v2)
Verificar que el archivo que se está corriendo es `main.py` y no `elpasaje_v1.py` o `main_viejo.py`.
Los archivos `elpasaje_v1.py`, `main_viejo.py`, `main_viejo2.py` son backups — no usarlos.
```powershell
streamlit run main.py
```

---

## Rollback de emergencia

1. Detener Streamlit (`Ctrl+C`)
2. Restaurar backup: copiar el `.db` más reciente de `backups/` sobre `elpasaje_v2.db`
3. Volver a arrancar: `streamlit run main.py`

No hay rollback de código — todo el historial está en Git.

---

## Variables de entorno (opcionales)

Solo necesarias si se configura email del agente Mike:

| Variable | Descripción |
|----------|-------------|
| `EP_GMAIL_USER` | Email del agente: `elpasaje.3d.studio@gmail.com` |
| `EP_GMAIL_APP_PWD` | App Password de Gmail (16 caracteres) |

Sin estas variables el agente corre en modo silencioso (sin email).

---

*El Pasaje 3D Studio · Runbook v3.0 · Mayo 2026*

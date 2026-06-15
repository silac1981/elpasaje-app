# CONTEXTO-EL-PASAJE.md
**Relevamiento técnico completo — El Pasaje 3D Studio**
Generado el 2026-06-15. Revisá la sección 7 antes de cada sprint.

---

## 1. ARQUITECTURA

### 1.1 Stack real

| Capa | Tecnología |
|------|------------|
| Frontend / App | Streamlit ≥ 1.32 (Python) — `main.py` es el único punto de entrada |
| Base de datos | SQLite — archivo `elpasaje_v2.db` en la raíz del repo |
| ORM / query layer | SQLAlchemy 2.x (engine compartido via `utils/db.py`); algunas funciones legacy usan `sqlite3` directo |
| IA (agente Mike) | Claude `claude-sonnet-4-6` via `anthropic` SDK — llamado desde `utils/mike.py` |
| Backup | `backup_manager.py` — Git push + copia a Google Drive + disco externo |
| Catálogo público | HTML estáticos hosteados en GitHub Pages (`silac1981.github.io/elpasaje-app`) |
| Imágenes productos | `static/productos/sport/` + URLs `assets/sport/` referenciadas en DB |
| Config | `.streamlit/config.toml` (no leído en este relevamiento, presumiblemente estándar) |
| Dependencias | `requirements.txt`: streamlit, pandas, plotly, Pillow, requests, sqlalchemy |
| **anthropic** | No está en `requirements.txt` — dependencia implícita para Mike |

### 1.2 Cómo se sirve

```
streamlit run main.py
```

`main.py` llama `init_schema()` (desde `crear_schema_v3.py`) y las migrations `v7` a `v10` **en cada arranque**. Todas son idempotentes (`INSERT OR IGNORE`, `ALTER TABLE … IF NOT EXISTS` vía try/except). La DB se crea si no existe.

### 1.3 Mapa de archivos

#### Raíz — archivos activos

| Archivo | Propósito |
|---------|-----------|
| `main.py` | Router principal, auth, sidebar, CSS global, arranque de DB |
| `crear_schema_v3.py` | DDL completo + seed inicial de tenants/materiales/productos. Tiene dos modos: `init_schema()` (seguro) y `crear_schema()` (destructivo) |
| `ep_agente.py` | Lógica de alertas automáticas (stock, entregas, fallos, inactividad). Se importa desde `utils/mike.py`. También puede correr standalone y enviar email |
| `context_elpasaje.py` | System prompt de Mike + `get_data_context()` (datos frescos de la DB para el LLM) |
| `backup_manager.py` | Backup a Git + Google Drive + disco externo |
| `migration_v7.py` | Agrega `precio_reventa` a products, corrige precios OE-* |
| `migration_v8.py` | Seed productos Magnitud 19 + Melómano |
| `migration_v9.py` | Seed catálogo Oasis del Estero (macetas, jardinería, kits) |
| `migration_v10.py` | Seed cajitas Porta-Figuritas F-Zone (FSP-*) |
| `migration_v11.py` | *(no leído en detalle — existente, pendiente de análisis)* |
| `requirements.txt` | Dependencias pip |
| `CLAUDE_INSTRUCTIONS.md` | Reglas de trabajo para Claude en este proyecto |

#### Raíz — archivos legacy / código muerto

| Archivo | Estado |
|---------|--------|
| `ep_database.py` | Schema antiguo (odv_cabecera/clientes). Deprecado — referenciado en `context_elpasaje.py` como "schema anterior". **No se usa en runtime** |
| `ep_core.py` | Wrapper mínimo, 277 bytes. Probable vestigio |
| `context_sia.py`, `context_sia_v3.py` | Contexto del proyecto paralelo SIA (Aerolíneas). No relevante para El Pasaje |
| `context_loader.py` | Loader genérico. Uso incierto |
| `agent_core.py` | Wrapper de agente (1.6 KB). Probable vestigio |
| `database_engine.py` | Wrapper de engine. Probablemente reemplazado por `utils/db.py` |
| `log_maestro.py` | Log maestro genérico. Uso incierto |
| `check_db.py`, `check_v5.py` | Scripts de diagnóstico puntuales |
| `cargar_sport.py` | Script one-shot para cargar productos Sport |
| `setup_materiales.py`, `setup_redes.py` | Scripts de setup one-shot |
| `fix_fsp_costo.py` | Fix puntual de costos FSP |
| `migration_v4.py` a `migration_v6.py` | Migrations históricas anteriores al schema v3 actual |
| `slicer_parser.py` | Parser de archivos de slicer. Funcionalidad no expuesta en UI |
| `El_Pasaje_3D.html` | Página standalone (posible versión anterior del catálogo) |
| `index.html` | Posible landing page o catálogo HTML viejo |
| `onboarding_agustina.md` | Documento de onboarding, no código |
| `ELPASAJE_NotebookLM.md`, `REPORTE_TECNICO_FERNANDO.md` | Documentos informativos |

#### `modules/` — paneles del dashboard

| Módulo | Panel | Rol que lo ve |
|--------|-------|---------------|
| `dashboard_admin.py` | CONTROL — tabs: Dashboard, Mike, Magnitud 19, Pagos | admin |
| `inventario.py` | STOCK — filamentos + catálogo + fotos | admin |
| `panel_fer.py` | TALLER — producción, materiales, cola, archivos, Mike, Finanzas CFO | produccion |
| `panel_socios.py` | LÍNEAS — vista consolidada de todos los socios | admin |
| `panel_socio.py` | MI LÍNEA — panel individual del socio (Resumen, Stats, Productos, Pedidos, Tienda, Presupuesto, Mike, Mi Línea) | socio, socio_multi |
| `cargar_pedido.py` | PEDIDO — formulario de nuevo pedido para socios | socio, socio_multi |
| `clientes.py` | CRM — clientes, señales de mercado | admin |
| `impacto.py` | IMPACTO — fondos solidarios y donaciones | admin |
| `panel_mike.py` | Pestaña Mike embebida en dashboard_admin y panel_fer | admin, produccion |

#### `utils/`

| Archivo | Propósito |
|---------|-----------|
| `db.py` | Motor SQLAlchemy singleton (`engine`), path relativo al repo |
| `lineas.py` | Diccionario `LINEAS` (id → nombre/color/emoji), `PAGINAS_SOCIOS`, constantes de estado, tipos de producto, helper `get_linea()`, `get_lineas_usuario()` |
| `pricing.py` | `calcular_costo_pieza()`, `cargar_productos()` (con columnas calculadas), `cargar_materiales()`, `calcular_split()` |
| `mike.py` | Wrapper `preguntar_mike()` que llama al SDK de Anthropic con el system prompt de `context_elpasaje.py` |
| `whatsapp.py` | Generación de URLs `wa.me` para producto y presupuesto |
| `exports.py` | Exportación de catálogo a JSON para GitHub Pages |

### 1.4 Routing

El router vive en `main.py` al final del archivo. Es un `if/elif` sobre la variable `menu` que viene del `st.radio()` del sidebar:

```python
CONTROL    → modules.dashboard_admin.render()
STOCK      → modules.inventario.render()
TALLER     → modules.panel_fer.render()
LÍNEAS     → modules.panel_socios.render()
MI LÍNEA   → modules.panel_socio.render()
PEDIDO     → modules.cargar_pedido.render()
CRM        → modules.clientes.render()
IMPACTO    → modules.impacto.render()
```

Opciones de menú según rol:
- `admin` → CONTROL, STOCK, TALLER, LÍNEAS, CRM, IMPACTO
- `produccion` → TALLER
- `socio_multi` → MI LÍNEA, PEDIDO (más selector de línea en sidebar)
- `socio` → MI LÍNEA, PEDIDO

### 1.5 Estado y sesión

`st.session_state` guarda:

| Clave | Valor |
|-------|-------|
| `auth` | bool |
| `user` | nombre del tenant |
| `role` | `"admin"` / `"produccion"` / `"socio_multi"` / `"socio"` |
| `uid` | `id` del tenant en la DB |
| `linea_filtro` | lista de linea_ids (solo socio_multi) |
| `linea_sel` | nombre de la línea seleccionada en el selectbox (socio_multi) |
| `mike_history` | historial de mensajes Mike (últimos 20) |
| `cp_sel_sku` | SKU seleccionado en el formulario de pedido |

---

## 2. MODELO DE DATOS

Base: `elpasaje_v2.db` (SQLite). DB path definido en `utils/db.py` relativo al repo. El schema se inicializa en `crear_schema_v3.py`.

### 2.1 Tablas activas

#### `tenants` — usuarios del sistema + socios + clientes B2B

```sql
id                    TEXT PRIMARY KEY   -- "admin", "olivia_coquette", etc.
name                  TEXT NOT NULL
email                 TEXT UNIQUE NOT NULL
password              TEXT NOT NULL      -- SHA-256 hexdigest
telefono              TEXT
tipo                  TEXT DEFAULT 'familia'  -- 'admin'|'familia'|'b2b'|'socio'|'socio_multi'|'produccion'|'cliente_externo'
sector                TEXT
fecha_alta            TEXT
activo                INTEGER DEFAULT 1
segmento              TEXT               -- 'B2B'|'B2C'|null
lead_source           TEXT
potencial             TEXT               -- 'Alto'|'Medio'|'Bajo'
canal_preferido       TEXT
ciudad                TEXT DEFAULT 'Buenos Aires'
rubro                 TEXT
notas_agente          TEXT
es_cliente_real       INTEGER DEFAULT 0
fecha_primer_contacto TEXT
linea_interes         TEXT
```

#### `tenant_lineas` — relación socio_multi ↔ líneas que puede ver

```sql
tenant_id  TEXT  REFERENCES tenants(id)
linea_id   TEXT  REFERENCES tenants(id)
PRIMARY KEY (tenant_id, linea_id)
```

#### `materials` — filamentos en stock

```sql
material_id      TEXT PRIMARY KEY  -- "petg_gris", "pla_rosa", etc.
name             TEXT NOT NULL
tipo             TEXT              -- "PETG"|"PLA"|"ABS"|"TPU"|etc.
color            TEXT
proveedor        TEXT
stock_gr         REAL DEFAULT 0
cost_kg          REAL DEFAULT 0    -- precio en ARS por kg
stock_minimo_gr  INTEGER DEFAULT 200
fecha_compra     TEXT
precio_compra    REAL
activo           INTEGER DEFAULT 1
```

#### `products` — catálogo unificado de todas las líneas

```sql
sku                   TEXT PRIMARY KEY   -- "AVP-001", "COQ-MON-001", etc.
client_id             TEXT  REFERENCES tenants(id)   -- = linea_id
material_id           TEXT  REFERENCES materials(material_id)
name                  TEXT NOT NULL
description           TEXT
categoria             TEXT
color                 TEXT               -- color hex para UI
price                 REAL DEFAULT 0     -- precio de venta al socio / cliente
weight_gr             REAL DEFAULT 0     -- gramos del objeto impreso
tiempo_impresion_min  INTEGER DEFAULT 0
stock                 INTEGER DEFAULT 0
imagen_url            TEXT
fecha_alta            TEXT
activo                INTEGER DEFAULT 1
tipo_producto         TEXT DEFAULT 'propio_3d'  -- 'propio_3d'|'linea_propio'|'compartido'|'kit_mixto'
visibilidad           TEXT DEFAULT 'publico'     -- 'publico'|'borrador'|'pausado'
proveedor_ref         TEXT
precio_reventa        REAL DEFAULT 0     -- precio que el socio cobra a su cliente final
```

#### `orders` — pedidos de producción

```sql
id                       INTEGER PRIMARY KEY AUTOINCREMENT
client_id                TEXT  REFERENCES tenants(id)
status                   TEXT DEFAULT 'Pendiente'  -- 'Pendiente'|'En Proceso'|'Listo'|'Cancelado'|'Entregado'
date                     TEXT DEFAULT CURRENT_TIMESTAMP
fecha_entrega_est        TEXT
notas                    TEXT
color_pedido             TEXT
maquina_id               TEXT DEFAULT 'creality_k2_plus_01'
horas_impresion          REAL
gramos_consumidos        REAL
costo_real               REAL
fallo_impresion          INTEGER DEFAULT 0
motivo_fallo             TEXT
referencia_archivo       TEXT
fecha_entrega_solicitada TEXT
canal_origen             TEXT
```

#### `order_items` — líneas de producto dentro de un pedido

```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
order_id        INTEGER  REFERENCES orders(id)
product_sku     TEXT     REFERENCES products(sku)
cantidad        INTEGER DEFAULT 1
precio_unitario REAL DEFAULT 0
```

#### `price_history` — historial de cambios de precio

```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
product_sku     TEXT  REFERENCES products(sku)
precio_anterior REAL
precio_nuevo    REAL
fecha           TEXT DEFAULT CURRENT_DATE
motivo          TEXT
```

#### `stock_movements` — movimientos de stock

```sql
id          INTEGER PRIMARY KEY AUTOINCREMENT
product_sku TEXT  REFERENCES products(sku)
tipo        TEXT NOT NULL
cantidad    INTEGER NOT NULL
fecha       TEXT DEFAULT CURRENT_TIMESTAMP
referencia  TEXT
```

#### `production_log` — registro de fabricaciones

```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
order_id        INTEGER  REFERENCES orders(id)
product_sku     TEXT     REFERENCES products(sku)
material_id     TEXT     REFERENCES materials(material_id)
gramos_usados   REAL
tiempo_real_min INTEGER
fecha_inicio    TEXT
fecha_fin       TEXT
resultado       TEXT DEFAULT 'ok'
```

#### `sales_context` — contexto de venta

```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
order_id        INTEGER  REFERENCES orders(id)
canal           TEXT
sector_empresa  TEXT
fue_con_muestra INTEGER DEFAULT 0
referido_por    TEXT
primera_compra  INTEGER DEFAULT 0
```

#### `donations` — fondo solidario

```sql
id          INTEGER PRIMARY KEY AUTOINCREMENT
fondo       TEXT NOT NULL   -- 'refugio_oasis'|'mentes_brillantes'|'fondo_general'
monto       REAL NOT NULL
tipo        TEXT            -- 'urna'|'qr'|'redondeo'|'producto'
descripcion TEXT
fecha       TEXT DEFAULT CURRENT_DATE
```

#### `log_agente` — señales y hallazgos del agente

```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
proyecto        TEXT DEFAULT 'ElPasaje'
tipo            TEXT NOT NULL   -- 'Patron de Margen'|'Alerta Entrega'|'Cliente Recurrente'|etc.
senal           TEXT NOT NULL
dato_observado  TEXT
accion_sugerida TEXT
etiquetas       TEXT           -- pipe-separated: "margen_alto|corporativo"
confianza       REAL DEFAULT 0.7
origen          TEXT DEFAULT 'agente'  -- 'agente'|'manual'
fecha           TEXT DEFAULT CURRENT_TIMESTAMP
```

#### `senales_mercado` — señales de mercado observadas

```sql
id                  INTEGER PRIMARY KEY AUTOINCREMENT
fecha               TEXT DEFAULT CURRENT_DATE
cliente_id          TEXT
linea               TEXT
producto            TEXT
reaccion            TEXT   -- 'Le encantó'|'Pidió muestra'|'Quiere hablar con alguien'|etc.
oportunidad         TEXT
fuente              TEXT
canal               TEXT
notas               TEXT
procesado_por_ia    INTEGER DEFAULT 0
segmento_detectado  TEXT
```

#### `pagos` — acreditación de cobros (creada vía migration, no en DDL principal)

```sql
id        INTEGER PRIMARY KEY AUTOINCREMENT
order_id  INTEGER  REFERENCES orders(id)
monto     REAL
metodo    TEXT    -- 'efectivo'|'transferencia'|'mercadopago'
estado    TEXT    -- 'pendiente'|'acreditado'|'devuelto'
fecha     TEXT
notas     TEXT
```

#### `revenue_rules` — reglas de split para productos compartidos (Tipo C)

```sql
product_sku  TEXT
linea_a      TEXT    -- linea_id que aporta el producto
linea_b      TEXT    -- linea que co-vende
split_a      REAL    -- fracción [0-1] para linea_a
split_b      REAL    -- fracción [0-1] para linea_b
notas        TEXT
activo       INTEGER DEFAULT 1
created_at   TEXT
```

### 2.2 Relaciones entre entidades

```
tenants (1) ─── (N) products          [client_id → tenants.id]
tenants (M) ─── (N) tenants           [tenant_lineas — para socio_multi]
tenants (1) ─── (N) orders            [client_id → tenants.id]
orders  (1) ─── (N) order_items       [order_id → orders.id]
order_items (N) ─── (1) products      [product_sku → products.sku]
products (N) ─── (1) materials        [material_id → materials.material_id]
products (1) ─── (N) price_history    [product_sku]
products (1) ─── (N) stock_movements  [product_sku]
orders  (1) ─── (N) production_log    [order_id]
orders  (1) ─── (1) pagos             [order_id]
products (1) ─── (N) revenue_rules    [product_sku]
```

### 2.3 Tenants seed (datos reales en código)

| id | name | tipo | role que genera | linea |
|----|------|------|-----------------|-------|
| admin | Alejandra | admin | admin | Magnitud 19 |
| olivia_coquette | Olivia | familia | socio | Coquette |
| francisco_sport | Francisco | familia | socio | Francisco Sport / F-Zone |
| constantino_tech | Constantino | familia | socio | Core Tech |
| aviation | Fernando Gomez Aguilera (Nando) | b2b | socio | Aviation Pro |
| oasis_animal | Oasis Animal | socio_multi | socio_multi | Oasis Animal + VK-Home |
| oasis_del_estero | Fede | socio | socio | Oasis del Estero |
| pharma_delux | Pharma DeLux | b2b | socio | Pharma DeLux |
| fer_produccion | Fernando (Fer) | produccion | produccion | Melómano (sin acceso económico) |
| agustina | Agustina | socio_multi | socio_multi | Oasis Animal + VK-Home |
| vkhome_cliente | VK-Home / Agustina | cliente_externo | socio* | VK-Home |

*`vkhome_cliente` tiene tipo `cliente_externo` pero en la práctica es manejado por Agustina como `socio_multi`.

### 2.4 Materiales seed

| material_id | tipo | color | stock_gr | cost_kg |
|-------------|------|-------|----------|---------|
| petg_gris | PETG | Gris Mecánico | 800 | 2350 |
| petg_naranja | PETG | Naranja Seguridad | 600 | 2400 |
| pla_seda_azul | PLA | Azul Aerolínea | 500 | 2600 |
| pla_seda_gris | PLA | Gris Acero | 400 | 2550 |
| pla_rosa | PLA | Rosa | 700 | 2400 |
| pla_blanco | PLA | Blanco | 1000 | 2200 |
| pla_negro | PLA | Negro | 1000 | 2200 |

### 2.5 Datos mock vs. datos reales

- **Seed en código** (`crear_schema_v3.py`, migrations): precios, productos, tenants — son datos reales del negocio, no ficticios.
- **Pedidos históricos**: dos órdenes seed (Oasis Animal × 29 llaveros, VK-Home × bandejas) insertadas vía `init_schema()` con la marca `HIST_AGUSTINA_ULTIMO`.
- **Donations**: tabla vacía hasta que Alejandra registre manualmente.
- **`revenue_rules`**: tabla creada pero sin datos seed — se agrega al crear Productos Tipo C desde el panel admin.
- **`lineas_config`** (para WhatsApp): tabla referenciada en `utils/whatsapp.py` pero no en el DDL principal — si no existe, `get_numero_linea()` devuelve el placeholder `5491100000000`.

---

## 3. ROLES Y PRIVACIDAD

### 3.1 Definición de roles

| Role string | Quién | Cómo se asigna |
|-------------|-------|----------------|
| `admin` | Alejandra | `uid == "admin"` en la query de login |
| `produccion` | Fer (Fernando, esposo) | `tipo == "produccion"` en `tenants` |
| `socio_multi` | Agustina, Oasis Animal | `tipo == "socio_multi"` en `tenants` |
| `socio` | Olivia, Francisco, Constantino, Nando, Fede, Pharma, VK-Home | todos los demás |

Código de asignación en `main.py`:
```python
role = "admin" if uid == "admin" else (
    "produccion" if tipo == "produccion" else (
        "socio_multi" if tipo == "socio_multi" else "socio"
    )
)
```

### 3.2 Matriz de visibilidad dato × rol

| Dato | Público (sin login) | admin | produccion | socio_multi | socio |
|------|--------------------|----|----------|-----------|-----|
| Catálogo HTML (GitHub Pages) | ✅ precio de venta, foto, descripción | ✅ | ✅ | ✅ | ✅ |
| Precio de venta del producto | ✅ (catalogo web) | ✅ | ✅ (en cola, como peso_gr) | ✅ (su línea) | ✅ (su línea) |
| Precio de costo (filamento + merma) | ❌ | ✅ | ❌ | ✅ (su línea, tab Productos) | ✅ (su línea, tab Productos) |
| Margen % | ❌ | ✅ | ❌ | ✅ (su línea) | ✅ (su línea) |
| Ganancia unitaria y total | ❌ | ✅ | ❌ | ✅ (su línea) | ✅ (su línea) |
| P&L global (facturado total, split) | ❌ | ✅ | Tab "Finanzas CFO" (¡ver nota!) | ❌ | ❌ |
| Pedidos de otras líneas | ❌ | ✅ | ✅ (todos, sin precio) | ❌ | ❌ |
| Datos de otros socios (nombres, monto) | ❌ | ✅ | ✅ (cola: nombre + gramos, sin precio) | ❌ | ❌ |
| Stock de materiales | ❌ | ✅ | ✅ | ❌ | ❌ |
| Alertas Mike | ❌ | ✅ | ✅ | ❌ solo pregunta libre | Solo pregunta libre |
| CRM / señales de mercado | ❌ | ✅ | ❌ | ❌ | ❌ (tab Mike muestra sus señales) |
| Donaciones / Impacto Social | ❌ | ✅ | ❌ | ❌ | ❌ |
| Revenue rules / splits | ❌ | ✅ | ❌ | ❌ | ❌ |
| Pagos (acreditación) | ❌ | ✅ | ❌ | Pago badge propio | Pago badge propio |

**NOTA CRÍTICA — Tab "Finanzas CFO" en panel_fer:**
El panel de producción (`panel_fer.py`) tiene un tab llamado "💹 Finanzas CFO" (`tab_stats`). Este tab es visible para `fer_produccion`. Su contenido exacto no fue completamente relevado pero el nombre sugiere que podría exponer datos financieros a Fernando. Requiere verificación urgente antes de producción.

### 3.3 Privacidad real vs. privacidad visual

**Privacidad REAL (server-side):**
- El menú del sidebar solo muestra opciones permitidas para cada rol → las rutas de paneles no se cargan.
- Las queries SQL en `panel_socio.py` filtran por `client_id IN (lineas_activas)` donde `lineas_activas` viene de `tenant_lineas` y del uid del tenant. Un socio no puede ver pedidos de otra línea porque la query nunca los retorna.
- `preguntar_mike()` en `utils/mike.py` usa el system prompt de `context_elpasaje.py` que contiene datos de todas las líneas — el LLM recibe todo el contexto aunque el socio no vea los datos directamente en UI.

**Privacidad solo VISUAL (cliente-side, breakeable):**
- La restricción de "Fer no ve márgenes" está implementada en la UI de `panel_fer.py` omitiendo las columnas de costo/ganancia. Los datos están en la DB y podrían obtenerse via SQL directo si Fer tuviera acceso a la DB.
- El catálogo público HTML no tiene autenticación — cualquiera que tenga la URL ve precios y productos.
- IP_RESTRINGIDA es solo una lista en `utils/lineas.py` para advertencia visual, no bloqueo.

---

## 4. LÓGICA DE NEGOCIO

### 4.1 Cálculo de costo de producción

```python
# utils/pricing.py
COSTO_KG_DEFAULT = 2350.0   # ARS/kg — sincronizado en pricing.py y ep_agente.py
MERMA = 0.10                # 10% de desperdicio

def calcular_costo_pieza(weight_gr, cost_kg=2350.0, merma=0.10, tipo_producto="propio_3d"):
    if tipo_producto != "propio_3d":
        return 0.0
    return (weight_gr * (1 + merma) * cost_kg) / 1000
```

Solo aplica a `tipo_producto = 'propio_3d'`. Para Capa 2 (linea_propio, compartido, kit_mixto), el costo es 0.

### 4.2 Cálculo de margen

```python
# utils/pricing.py — en cargar_productos()
df["costo_unit"]    = calcular_costo_pieza(weight_gr, tipo_producto=tipo_producto)
df["ganancia_unit"] = df["price"] - df["costo_unit"]
df["margen_pct"]    = (df["ganancia_unit"] / df["price"].replace(0, NaN) * 100).round(1)
df["valor_stock"]   = df["price"] * df["stock"]
df["costo_stock"]   = df["costo_unit"] * df["stock"]
df["ganancia_stock"]= df["ganancia_unit"] * df["stock"]
```

El system prompt de Mike explica:
```
MARKUP 100%: precio = costo_material × 2  →  margen real = 50% sobre precio
margen% = (precio - costo) / precio × 100   ← siempre ÷ precio, no ÷ costo
```

Categorías de margen:
- **High**: margen > 50%
- **Medium**: margen 30–50%
- **Low**: margen < 30%

### 4.3 P&L real con split estudio / socio

```sql
-- dashboard_admin.py — _dash_main()
SELECT
    SUM(oi.precio_unitario * oi.cantidad)                            AS facturado,
    SUM(CASE WHEN p.tipo_producto='propio_3d'
        THEN p.weight_gr * 1.10 * 2350.0 / 1000.0 * oi.cantidad
        ELSE 0 END)                                                  AS costo_prod,
    COUNT(DISTINCT o.id)                                             AS n_pedidos
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.sku = oi.product_sku
WHERE o.status IN ('Listo','Entregado')
```

```python
# En Python:
ganancia_bruta = facturado - costo_prod
cuota_socios   = round(ganancia_bruta * 0.5)   # 50%
para_ep        = ganancia_bruta - cuota_socios  # 50%
```

El split 50/50 es **fijo** hoy. La tabla `revenue_rules` permite splits configurables por producto (Tipo C), pero no hay productos Tipo C con reglas cargadas en el seed.

### 4.4 Fondo solidario

El fondo solidario existe como tabla `donations` con tres fondos predefinidos:

| Fondo ID | Nombre | Meta mensual |
|----------|--------|-------------|
| refugio_oasis | Refugio Oasis Animal | $50.000 |
| mentes_brillantes | Mentes Brillantes | $40.000 |
| fondo_general | Fondo General | $30.000 |

El porcentaje de aporte automático **no está implementado**. Las donaciones se registran manualmente desde el panel IMPACTO (solo admin). En `context_elpasaje.py` y en el catálogo de Oasis Animal dice "10% de ventas al refugio solidario" pero no hay lógica automática que lo calcule o descuente.

### 4.5 Presupuestador

El presupuestador vive en `panel_socio.py` (tab "🧮 Presupuesto") y en `dashboard_admin.py` (sub-función `_dash_m19()`). Permite:
- Seleccionar productos del catálogo con multiselect
- Ingresar cantidades
- Ver total
- Generar link de WhatsApp (`utils/whatsapp.py → link_presupuesto()`) y texto plano
- Usar `precio_reventa` si está configurado (precio que el socio cobra a su cliente, distinto del precio EP)

El texto del presupuesto incluye:
```
PRESUPUESTO — {linea_nombre}
─────────────────────────────────
• {cantidad}x {nombre}  ${subtotal}
─────────────────────────────────
TOTAL  ${total}

Valido por 48 horas - Entrega bajo pedido 48-72hs
El Pasaje 3D Studio - WA: {numero}
```

### 4.6 Estados de pedido y transiciones

```
Pendiente → En Proceso → Listo → Entregado
                       ↓
                    Cancelado
```

- **Socio puede**: cancelar un pedido en estado `Pendiente`, confirmar recepción de un pedido `Listo` → pasa a `Entregado`
- **Fer puede**: cambiar estado a Pendiente/En Proceso/Listo/Cancelado desde el expander del panel de producción
- **Admin**: control total via CONTROL y TALLER

### 4.7 Alertas automáticas de Mike (ep_agente.py)

Las alertas se evalúan en cada render del sidebar/panel. Cuatro reglas:

1. **Stock crítico**: materiales con `stock_gr ≤ stock_minimo_gr`. Nivel `critico`. Calcula días restantes a consumo histórico de 30 días.
2. **Pedidos urgentes**: entrega ≤ 2 días y estado Pendiente/En Proceso. Nivel `critico` (0 días) o `atencion` (≤2 días).
3. **Tasa de fallos alta**: si en los últimos 7 días hay ≥ 3 fabricaciones y ≥ 25% fallos → `atencion`. Si ≥ 40% → `critico`.
4. **Socios inactivos**: socios con ≥ 2 órdenes históricas sin pedir hace más de 21 días → nivel `info`.

### 4.8 Tipos de producto (modelo de capas)

| tipo_producto | Capa | Descripción | Costo calculado |
|--------------|------|-------------|----------------|
| `propio_3d` | 1 | Impreso en El Pasaje por Fer | Sí (weight_gr × merma × cost_kg) |
| `linea_propio` | 2 | Propio de la línea, no 3D El Pasaje | No (0) |
| `compartido` | 2 | Tipo C — co-producido entre dos líneas, con revenue_rules | No |
| `kit_mixto` | 2 | Tipo D — kit con componentes de Capa 1 y Capa 2 | No |

---

## 5. FLUJOS DE USUARIO

### 5.1 Alejandra administra (rol admin)

1. **Login**: `admin@elpasaje.com` / password (SHA-256).
2. **Sidebar**: menú CONTROL, STOCK, TALLER, LÍNEAS, CRM, IMPACTO. Alertas Mike en sidebar si las hay.
3. **CONTROL** (dashboard_admin):
   - Tab Dashboard: KPIs de stock, P&L real, ranking por línea, señales de mercado, gestión de productos (visibilidad, precio, activo), revenue sharing.
   - Tab Mike: chat con el agente IA + alertas activas + top productos.
   - Tab Magnitud 19: catálogo de su línea, presupuestador rápido, exportación JSON a web.
   - Tab Pagos: acreditación manual de cobros pendientes.
4. **STOCK**: inventario de filamentos (stock, costo, valor) + catálogo global con fotos.
5. **LÍNEAS**: vista consolidada de todos los socios con KPIs individuales.
6. **CRM**: ver/agregar clientes, registrar señales de mercado.
7. **IMPACTO**: registrar donaciones a fondos solidarios.

### 5.2 Fer produce (rol produccion)

1. **Login**: `fer@elpasaje.com` / password.
2. **Sidebar**: solo TALLER.
3. **TALLER** (panel_fer):
   - Tab Mi Panel: KPIs (pendientes, hoy, fabricadas, críticos), cola activa con expanders por pedido, cambio de estado.
   - Tab Cargar Fabricación: registrar gramos, material, tiempo real → escribe en `production_log`.
   - Tab Materiales: stock de filamentos + alertas.
   - Tab Cola de Pedidos: vista de todos los pedidos activos.
   - Tab Archivos: (contenido no relevado en detalle).
   - Tab Mike: chat con el agente IA.
   - Tab Finanzas CFO: **requiere verificación** (posible exposición de datos financieros).

Fer **no ve precios** en la cola de pedidos — ve producto, gramos estimados, fecha de entrega y línea (socio).

### 5.3 Socio gestiona su línea

1. **Login**: `email@elpasaje.com` / password.
2. **Sidebar**: MI LÍNEA, PEDIDO. Si es socio_multi: selector de línea arriba.
3. **MI LÍNEA** (panel_socio):
   - Header con color de línea + link a página web pública (si tiene).
   - KPIs: Valor Stock, Productos activos, Facturado total, En Producción.
   - Tab Resumen: pedidos activos + top 3 productos por precio.
   - Tab Estadísticas: neon KPIs (facturado total, ticket promedio, mejor mes, growth), gráfico mensual, canales, top productos pedidos, pipeline.
   - Tab Productos: tarjetas con precio, stock, costo y ganancia (con margen %).
   - Tab Pedidos: historial filtrable por estado, con items, pago badge, acciones (cancelar / confirmar recepción).
   - Tab Mi Tienda: link a página pública + botones de red social.
   - Tab Presupuesto: presupuestador con link WA.
   - Tab Mike: chat libre con IA.
   - Tab Mi Línea: configuración (contenido no relevado).
4. **PEDIDO** (cargar_pedido): grid de productos propios → selecciona → ingresa cantidad, canal, fecha, notas → genera order en DB + opcionalmente pago pendiente.

### 5.4 Cliente compra (catálogo público)

- URL: `https://silac1981.github.io/elpasaje-app/{slug}.html`
- Páginas disponibles: `sport.html`, `coquette.html`, `core-tech.html`, `pharma-delux.html`, `oasis-animal.html`, `oasis-estero.html`, `aero-tech.html`, `melomano.html`, `magnitud19.html`, `luminis.html`, `vuelo-certero.html`
- Sin login. Ve productos, descripción, precios, fotos.
- CTA: botón de WhatsApp con mensaje pre-cargado (generado via `utils/whatsapp.py`).
- **No hay carrito ni checkout online**. Todo cierra por WhatsApp.

### 5.5 Fricciones y deuda técnica detectada

1. **Tab Finanzas CFO en panel_fer**: visible para Fernando. Si expone P&L o costos, rompe la regla de negocio "Fer no ve márgenes". Verificar urgente.
2. **Fondo solidario sin automatización**: el 10% prometido a Oasis Animal no se descuenta automáticamente de ninguna venta. Solo registro manual.
3. **`whatsapp_numero` sin seed**: la tabla `lineas_config` no tiene DDL en el schema principal. `get_numero_linea()` siempre devuelve `5491100000000` (placeholder). Los links de WA van al número genérico, no al de cada línea.
4. **`anthropic` no en requirements.txt**: si se despliega en un entorno limpio, `preguntar_mike()` falla con ImportError sin mensaje claro.
5. **f-strings en SQL**: `panel_socio.py` usa f-strings para construir `IN ('{_lid_str}')`. Rompe la convención de parámetros bindeados. Riesgo de SQL injection si un `linea_id` contiene comillas.
6. **DB dual**: `utils/db.py` apunta a `elpasaje_v2.db` (SQLAlchemy). `ep_agente.py` y `ep_database.py` usan `sqlite3` y tienen sus propios paths. Posible desincronización si se cambia la ubicación.
7. **`crear_schema_v3.py` corre migrations embebidas en `init_schema()`**: el bloque `_migrations` hace `ALTER TABLE` sin versioning — si se agrega una columna que ya existe en un sistema nuevo, el `try/except` la ignora silenciosamente. No hay forma de saber qué migrations corrieron.
8. **`stock_movements` nunca se actualiza**: la tabla existe pero no hay código que inserte movimientos cuando se fabrica (solo se actualiza `production_log`) o cuando se recibe filamento. El stock de materiales se actualiza manualmente desde el panel de inventario.
9. **`precio_reventa` rara vez usado**: la columna existe y `cargar_presupuesto()` la respeta, pero el panel de productos del socio no tiene UI para configurarla. Se resetea a 0 en `migration_v7.py`.
10. **`vkhome_cliente` tiene tipo `cliente_externo`** pero en la práctica es una línea de socio gestionada por Agustina. La UI la trata como socio, pero el tipo en DB puede generar inconsistencias en queries que filtran por tipo.

---

## 6. CONTENIDO Y NEGOCIO

### 6.1 Líneas activas con sus datos

| Línea | ID tenant | Color | Emoji | Rubro | Tipo | Catálogo web |
|-------|-----------|-------|-------|-------|------|-------------|
| Magnitud 19 | admin | #B87333 (cobre) | ⚡ | Oficina, fidgets, corporativo, Vuelo Certero | Familia / admin | magnitud19 |
| Melómano | fer_produccion | #9C6B3C | 🎵 | Audio, vinilo, escritorio melómano | Producción | melomano |
| Coquette | olivia_coquette | #F9A8D4 (rosa) | 🎀 | Accesorios femeninos, estética, XV años | Familia | coquette |
| F-Zone / Francisco Sport | francisco_sport | #F97316 (naranja) | ⚽ | Deportes, gaming, coleccionables | Familia | sport |
| Core Tech | constantino_tech | #64748B (gris) | ⚙️ | Electrónica, educación, tecnología | Familia | core-tech |
| Aviation Pro | aviation | #0F3460 (azul marino) | ✈️ | Aeronáutico (vía Nando en AA) | B2B | aero-tech |
| Oasis Animal | oasis_animal | #F472B6 (rosa fuerte) | 🐾 | Veterinario / mascotas | B2B/Socio multi | oasis-animal |
| Oasis del Estero | oasis_del_estero | #34D399 (verde) | 🌱 | Macetas, jardinería, plantas | Socio regional | oasis-estero |
| Pharma DeLux | pharma_delux | #FBBF24 (amarillo) | 💊 | Farmacéutico / médico | B2B | pharma-delux |
| VK-Home | vkhome_cliente | #A78BFA (violeta) | 🏡 | Decoración / deco hogar | Cliente externo / Agustina | (sin página) |
| Agustina | agustina | #6366F1 (índigo) | ✨ | Gestora Oasis Animal + VK-Home | Socio multi | (sin página) |

**Páginas sin cliente**: `luminis.html`, `vuelo-certero.html` — existen como HTML pero no corresponden a un tenant activo en el schema.

### 6.2 Canales B2B activos

| Canal | Contacto | Líneas que mueve |
|-------|---------|------------------|
| Red de Nando (Aerolíneas) | Fernando Gomez Aguilera | Aviation Pro, Oasis Animal, Oasis del Estero, Pharma DeLux |
| Agustina (VK-Home) | Agustina | Oasis Animal + VK-Home bandejas |
| Feria / Presencial | Alejandra | Todas las líneas de familia |
| WhatsApp / Instagram | Socios directos | Cada línea por separado |

### 6.3 Datos comerciales presentes en el código

- **Último pedido Agustina (Mayo 2026)**:
  - Oasis Animal: 29 × Llavero Perrito Globo × $1.000 = $29.000
  - VK-Home: 4× Oval S ($3.000) + 4× Oval M ($6.000) + 4× Oval L ($9.000) + 4× Redonda M ($8.000) = $104.000

- **Precios actuales VK-Home** (fijados en init_schema): OE-BOV-S $3.000 / OE-BOV-M $6.000 / OE-BOV-L $9.000 / OE-BRR-M $8.000.

- **Cajitas porta-figuritas FSP-***: precio $10.000 c/u, peso 1.470g, costo filamento+luz+máquina interno = $3.800.

- **Magnitud 19 / Vuelo Certero — productos estrella**: Quiver Pro $42.000 (peso 380g), Tournament Box $55.000, Porta-raqueta premium $16.000.

- **Aviation Pro — producto de mayor precio**: Soporte Monitor Desk $7.500 (180g, PETG gris).

- **Oasis Animal — Memory Litophany**: $35.000 (3.386g, 960 min impresión) — el producto de mayor margen de tiempo.

- **WhatsApp de contacto en footer login**: `wa.me/5491165497234` (número real de Alejandra).

- **Email del agente**: `elpasaje.3d.studio@gmail.com` (app password en texto plano en `ep_agente.py` CONFIG).

---

## 7. INVENTARIO PARA OPTIMIZAR

### 7.1 Bugs

| Bug | Archivo | Impacto | Esfuerzo fix |
|-----|---------|---------|-------------|
| App password en texto plano en CONFIG | `ep_agente.py:37` | Alto (seguridad) | Bajo — mover a variable de entorno |
| f-strings en SQL de panel_socio | `panel_socio.py:83–94` | Alto (SQL injection) | Bajo — refactorizar con parámetros |
| `anthropic` ausente en requirements.txt | `requirements.txt` | Alto (deploy fail) | Mínimo — agregar línea |
| Tab "Finanzas CFO" en panel_fer | `panel_fer.py:63` | Alto (privacidad) | Bajo a Medio — auditar contenido |
| `lineas_config` sin DDL | `utils/whatsapp.py:12–19` | Medio (links WA rotos) | Bajo — agregar tabla al schema |
| `stock_movements` nunca se actualiza | `inventario.py` | Medio (datos fantasma) | Medio — hookear a production_log y recepción |
| `precio_reventa` sin UI de edición | `panel_socio.py` | Medio (funcionalidad prometida) | Medio |
| Doble DB path (utils/db.py vs ep_agente.py) | ambos | Bajo a Medio (inconsistencia) | Bajo — consolidar en una constante |

### 7.2 Duplicaciones

| Duplicación | Archivos | Impacto | Esfuerzo |
|-------------|----------|---------|----------|
| CSS dark theme repetido en cada módulo | `panel_fer.py`, `panel_socio.py`, `cargar_pedido.py`, `inventario.py` | Bajo (mantenimiento) | Medio — mover a utils/styles.py |
| `COSTO_KG` y `MERMA` definidos en 3 lugares | `utils/pricing.py`, `ep_agente.py`, `context_elpasaje.py` | Medio (riesgo de desincronización) | Bajo — centralizar en una constante |
| Queries de pedidos duplicadas con try/except en panel_socio | `panel_socio.py:85–108` | Bajo | Bajo |
| Schema `log_agente` definido en `ep_agente.py` Y en `crear_schema_v3.py` | ambos | Bajo | Bajo |

### 7.3 Archivos huérfanos / candidatos a limpieza

| Archivo | Motivo | Riesgo de borrar |
|---------|--------|-----------------|
| `ep_database.py` | Schema deprecado, reemplazado por `crear_schema_v3.py` | Bajo (no importado en runtime) |
| `ep_core.py` | 277 bytes, probablemente vestigio | Bajo |
| `context_sia.py`, `context_sia_v3.py` | Proyecto SIA, no El Pasaje | Bajo |
| `database_engine.py` | Reemplazado por `utils/db.py` | Bajo |
| `agent_core.py` | Vestigio, 1.6 KB | Bajo |
| `log_maestro.py` | Uso incierto | Medio (verificar imports) |
| `migration_v4.py` a `migration_v6.py` | Migrations pre-schema v3 | Bajo (ya aplicadas en DB) |
| `check_db.py`, `check_v5.py` | Scripts de diagnóstico puntuales | Bajo |
| `cargar_sport.py`, `setup_materiales.py`, `setup_redes.py` | One-shots ya ejecutados | Bajo |
| `fix_fsp_costo.py` | Fix puntual ya aplicado | Bajo |
| `El_Pasaje_3D.html`, `El_Pasaje_3D_files/` | Versión anterior de catálogo | Bajo |
| `index.html` | Landing page vieja (138 KB) | Bajo |
| `slicer_parser.py` | Sin UI expuesta | Medio (potencial futuro) |
| `context_loader.py` | Uso incierto | Medio (verificar imports) |

### 7.4 Oportunidades de mejora (priorizadas)

| Mejora | Impacto | Esfuerzo |
|--------|---------|---------|
| Automatizar el 10% solidario en cada venta (crear trigger o lógica en cargar_pedido) | Alto (propuesta de valor Oasis Animal) | Medio |
| Agregar `anthropic` a `requirements.txt` + mover app_password a `st.secrets` o env var | Alto (deploy seguro) | Bajo |
| Unificar constantes `COSTO_KG` y `MERMA` en `utils/pricing.py` e importar desde ahí | Medio | Bajo |
| Crear `utils/styles.py` con el CSS dark compartido | Medio (mantenimiento) | Medio |
| Implementar `lineas_config` en schema con números de WhatsApp reales | Medio (UX socios) | Bajo |
| Agregar UI para que socios configuren `precio_reventa` | Medio (propuesta de valor presupuestador) | Medio |
| Auditar y documentar el tab "Finanzas CFO" de Fer | Alto (privacidad) | Bajo |
| Versioning de migrations con tabla `schema_version` | Medio (operacional) | Medio |
| Refactorizar f-strings SQL en panel_socio a queries parametrizadas | Alto (seguridad) | Bajo |
| Exponer `slicer_parser.py` en el panel de Fer (tab Archivos) | Medio (productividad) | Medio |

---

## CIERRE — LO MÁS IMPORTANTE QUE ENCONTRÉ

- **El app password de Gmail está en texto plano en `ep_agente.py:37`** (variable CONFIG). Si el repo se hace público o alguien tiene acceso al código, tiene acceso a esa cuenta. Mover a `st.secrets["GMAIL_APP_PASSWORD"]` o variable de entorno es la acción más urgente.

- **El split 50/50 estudio/socio es un número hardcodeado** (`_pnl_soc = round(_pnl_gb * 0.5)`) con una tabla `revenue_rules` diseñada para splits variables pero sin ninguna regla cargada. El negocio crece sobre una suposición de paridad que no tiene sustento escrito — si el acuerdo cambia con algún socio, hay que cambiar código, no configuración.

- **Fer tiene acceso a un tab "Finanzas CFO"** en su propio panel (panel_fer.py:63). La regla de negocio dice que Fer no ve márgenes ni costos. Si ese tab expone P&L o split, toda la arquitectura de privacidad está rota para el único rol de producción.

- **El fondo solidario del 10% para Oasis Animal existe como promesa en el catálogo HTML y en el system prompt de Mike, pero no hay ningún código que lo calcule ni descuente**. Es deuda de confianza con ese socio: si algún día se audita, no hay nada que mostrar.

- **El modelo de datos tiene dos esquemas vivos en el repo**: el schema antiguo (`ep_database.py` con odv_cabecera, clientes, productos) y el actual (`crear_schema_v3.py` con orders, tenants, products). El contexto de Mike (`context_elpasaje.py`) mapea explícitamente las columnas antiguas a las nuevas, lo que significa que hay código de contexto que mantiene una traducción mental de dos mundos. Limpiar los archivos del schema antiguo reduce la confusión y la superficie de mantenimiento.

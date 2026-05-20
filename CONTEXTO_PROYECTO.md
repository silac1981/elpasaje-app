# El Pasaje 3D Studio — Contexto del Proyecto

> Documento de referencia para Claude Projects.
> Última actualización: 2026-05-01

---

## 1. Descripción del negocio

**El Pasaje 3D Studio** es un negocio familiar de manufactura aditiva (impresión 3D FDM) en Buenos Aires, Argentina, fundado por Alejandra Gomez Aguilera. Es un ecosistema multi-línea: cada integrante de la familia gestiona su propia línea de productos dentro del mismo sistema.

Etapa actual: **arranque / crecimiento temprano**. Datos recientes, historial de órdenes corto.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Dashboard UI | Python 3.12 + Streamlit |
| Gráficos | Plotly Express + Plotly Graph Objects |
| ORM / DB | SQLAlchemy 2.x + SQLite |
| Agente IA | Python puro (sqlite3, smtplib) |
| Email | SMTP Gmail con App Password |
| Backup | GitHub + Google Drive + Disco externo |
| OS | Windows 11 Pro |

---

## 3. Archivos clave

```
magnitud19-backend-share/
├── main.py                  ← Dashboard Streamlit principal (v2.6, ~680 líneas)
├── crear_schema_v3.py       ← Crea/recrea la DB desde cero (destructivo)
├── ep_agente.py             ← Agente Mike: análisis diario + email (v2)
├── context_elpasaje.py      ← Reglas de negocio + system prompt del agente (v3)
├── backup_manager.py        ← Backup multi-destino: GitHub / Drive / disco
├── elpasaje_v2.db           ← Base de datos activa (SQLite)
├── CONTEXTO_PROYECTO.md     ← Este archivo
├── CLAUDE_INSTRUCTIONS.md   ← Instrucciones para Claude Projects
└── ELPASAJE_NotebookLM.md   ← Documento para NotebookLM
```

> **DB activa:** `elpasaje_v2.db` — path resuelto siempre relativo al directorio del script.
> No hay rutas hardcodeadas con `C:\Users\...` en ningún archivo activo.

---

## 4. Estructura de la base de datos (`elpasaje_v2.db`)

### 4.1 `tenants` — Usuarios del sistema (socios, B2B, admin, producción)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | TEXT PK | Identificador único (ej: `"admin"`, `"olivia_coquette"`) |
| `name` | TEXT | Nombre completo |
| `email` | TEXT UNIQUE | Email de acceso |
| `password` | TEXT | SHA-256 del password |
| `tipo` | TEXT | `'admin'` \| `'familia'` \| `'b2b'` \| `'produccion'` \| `'cliente_externo'` |
| `sector` | TEXT | Área dentro de la empresa |
| `activo` | INTEGER | 1 = activo |
| `segmento` | TEXT | `'B2C'` \| `'B2B'` \| `'Corporativo'` \| `'Institucional'` |
| `lead_source` | TEXT | Cómo llegó al ecosistema |
| `potencial` | TEXT | `'Alto'` \| `'Medio'` \| `'Bajo'` |
| `canal_preferido` | TEXT | Canal de contacto preferido |
| `ciudad` | TEXT | Ciudad (default: Buenos Aires) |
| `rubro` | TEXT | Sector / industria |
| `notas_agente` | TEXT | Notas del agente IA sobre el contacto |
| `es_cliente_real` | INTEGER | 1 = realizó al menos una compra |
| `fecha_primer_contacto` | TEXT | Fecha ISO de primer contacto |
| `linea_interes` | TEXT | Línea o marca de interés principal |

### 4.2 `products` — Catálogo de productos

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `sku` | TEXT PK | Código único (ej: `"AVP-001"`) |
| `client_id` | TEXT FK→tenants | Línea dueña del producto |
| `material_id` | TEXT FK→materials | Material principal |
| `name` | TEXT | Nombre del producto |
| `categoria` | TEXT | `'Taller'` \| `'Oficina'` \| `'Tech'` \| `'General'` |
| `price` | REAL | Precio de venta (pesos ARS) |
| `weight_gr` | REAL | Peso de impresión en gramos |
| `stock` | INTEGER | Unidades disponibles |
| `activo` | INTEGER | 1 = activo |

### 4.3 `materials` — Filamentos y materiales

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `material_id` | TEXT PK | ej: `"petg_gris"` |
| `name` | TEXT | Nombre del material |
| `tipo` | TEXT | `'PLA'` \| `'PETG'` \| `'TPU'` |
| `color` | TEXT | Color del filamento |
| `stock_gr` | REAL | Gramos disponibles |
| `cost_kg` | REAL | Costo por kg en ARS |
| `stock_minimo_gr` | INTEGER | Alerta de stock bajo |

### 4.4 `orders` — Pedidos / órdenes de producción

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | ID de orden |
| `client_id` | TEXT FK→tenants | Quién hizo el pedido |
| `status` | TEXT | `'Pendiente'` \| `'En Proceso'` \| `'Listo'` \| `'Cancelado'` |
| `date` | TEXT | Fecha de creación ISO |
| `fecha_entrega_est` | TEXT | Fecha estimada de entrega ISO |
| `notas` | TEXT | Instrucciones para Fer |
| `color_pedido` | TEXT | Color solicitado |

### 4.5 `order_items` — Detalle de cada orden

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK | |
| `order_id` | INTEGER FK→orders | Orden a la que pertenece |
| `product_sku` | TEXT FK→products | Producto pedido |
| `cantidad` | INTEGER | Unidades |
| `precio_unitario` | REAL | Precio al momento del pedido (histórico) |

### 4.6 `senales_mercado` — Señales comerciales

Captura reacciones de clientes, oportunidades detectadas, reportadas desde el dashboard por cualquier usuario.

| Columna | Descripción |
|---------|-------------|
| `cliente_id` | Nombre libre o id de tenants |
| `reaccion` | 'Le encantó' \| 'Preguntó el precio' \| 'Dudó' \| etc. |
| `oportunidad` | Descripción de la oportunidad |
| `procesado_por_ia` | 0=pendiente, 1=procesado por el agente |

### 4.7 `log_agente` — Historial del agente Mike

Registro automático de cada patrón detectado y acción sugerida.

### 4.8 Tablas estructurales (schema completo, sin UI todavía)

- `price_history` — historial de cambios de precio
- `stock_movements` — movimientos de stock (entradas, ventas, ajustes)
- `production_log` — log detallado de cada impresión (material usado, tiempo real)
- `donations` — donaciones a fondos solidarios
- `sales_context` — contexto de venta para modelos predictivos

---

## 5. Roles y credenciales de acceso

| ID tenant | Nombre | Rol en el sistema | Email |
|-----------|--------|------------------|-------|
| `admin` | Alejandra | Admin — acceso total, dashboard ejecutivo | admin@elpasaje.com |
| `fer_produccion` | Fernando (Fer) | Producción — solo ve cola de pedidos y materiales | fer@elpasaje.com |
| `olivia_coquette` | Olivia | Socio familia — ve su línea Coquette | coquette@elpasaje.com |
| `francisco_sport` | Francisco | Socio familia — ve su línea Sport | fsport@elpasaje.com |
| `constantino_tech` | Constantino | Socio familia — ve su línea Core Tech | coretech@elpasaje.com |
| `aviation` | Fernando Gomez Aguilera (Nando) | Socio B2B — Aviation Pro | aviation@elpasaje.com |
| `oasis_animal` | Oasis Animal | Socio B2B — veterinario/mascotas | oasisanimal@elpasaje.com |
| `oasis_del_estero` | Oasis del Estero | Socio B2B | oasisestero@elpasaje.com |
| `pharma_delux` | Pharma DeLux | Socio B2B — farmacéutico | pharma@elpasaje.com |

**Passwords por defecto (SHA-256):**
- `admin123` → `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`
- `123` → `a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3`
- Fer tiene password propio

---

## 6. Modelo de precios

```
costo_pieza = (weight_gr × (1 + merma) × costo_kg) / 1000
```

- **merma default:** 10% (`0.10`)
- **costo_kg default:** $2.350 ARS (PETG gris mecánico)
- Cada material tiene su propio `cost_kg` real

```
margen% = (precio - costo) / precio × 100   ← SIEMPRE dividir por precio
```

| Categoría | Margen | Acción |
|-----------|--------|--------|
| High | > 50% | Priorizar producción |
| Medium | 30–50% | Evaluar según volumen |
| Low | < 30% | Revisar estructura de costos |

**Markup estándar:** precio = costo × 2 → margen real = 50%

---

## 7. Líneas del ecosistema

| ID | Línea | Responsable | Tipo | Segmento |
|----|-------|-------------|------|----------|
| `admin` | Magnitud 19 | Alejandra (fundadora) | Familia | Corporativo / premium |
| `olivia_coquette` | Coquette | Olivia (hija) | Familia | B2C / estética femenina |
| `francisco_sport` | Francisco Sport | Francisco (hijo) | Familia | B2C / deportivo |
| `constantino_tech` | Core Tech | Constantino (hijo) | Familia | B2C / tech / industrial |
| `aviation` | Aviation Pro | Nando (hermano de Ale) | B2B | Aeronáutico (AA) |
| `oasis_animal` | Oasis Animal | Nando | B2B | Veterinario / mascotas |
| `oasis_del_estero` | Oasis del Estero | Nando | B2B | Veterinario regional |
| `pharma_delux` | Pharma DeLux | Nando | B2B | Farmacéutico |

> **Nota Nando:** Fernando Gomez Aguilera (hermano de Alejandra) trabaja en Aerolíneas Argentinas. Es el canal de acceso a los 4 socios B2B.

---

## 8. El Agente Mike (`ep_agente.py`)

**Función:** Análisis autónomo nocturno (20:00 hs). Corre sin intervención humana.

**Lo que hace:**
1. Detecta el producto con mayor margen
2. Identifica clientes recurrentes (≥ 2 órdenes)
3. Alerta sobre órdenes con entrega ≤ 2 días
4. Detecta la categoría con más demanda
5. Cuenta señales de mercado pendientes de análisis
6. Registra todos los hallazgos en `log_agente`
7. Envía resumen por email a `elpasaje.3d.studio@gmail.com`

**Cómo correrlo:**
```bash
python ep_agente.py            # análisis completo + email
python ep_agente.py silencioso # solo análisis, sin email
```

**Context provider:** `context_elpasaje.py` — contiene `SYSTEM_PROMPT` con todas las reglas de negocio y `get_data_context()` que arma el contexto dinámico de datos para pasarle a un LLM.

---

## 9. Menú del dashboard por rol

| Rol | Menú disponible |
|-----|----------------|
| `admin` | Dashboard Alejandra, Inventario Pro, Produccion (Fer), Socios, Clientes, Impacto Social |
| `produccion` (Fer) | Produccion (Fer) — solo cola de pedidos y stock de filamentos |
| `socio` (familia/B2B) | Mi Panel, Cargar Pedido |

---

## 10. Estado del sistema al 2026-05-01

### Resuelto en esta sesión

| # | Fix | Descripción |
|---|-----|-------------|
| 1 | SQL Injection | Todos los f-strings en queries reemplazados por parámetros bindeados |
| 2 | senales_mercado | Tabla agregada al schema (faltaba, main.py la usaba) |
| 3 | Tenants schema | Completadas 10 columnas de segmentación comercial |
| 4 | Aislamiento socios | Socios ven sus propios productos (no los de admin) |
| 5 | Rol Fer | `tipo='produccion'` separado en login y sidebar |
| 6 | Agente Mike | Reconectado a `elpasaje_v2.db` (schema actual) |
| 7 | Rutas hardcodeadas | `ep_agente.py` y `context_elpasaje.py` usan paths relativos |
| 8 | `log_agente` | Tabla creada con `CREATE TABLE IF NOT EXISTS` + en el schema |

### Pendiente / módulos vacíos

| Módulo | Estado | Tabla existente |
|--------|--------|----------------|
| Historial de precios | Sin UI | `price_history` ✅ |
| Log de producción (Fer) | Sin UI | `production_log` ✅ |
| Movimientos de stock | Sin UI | `stock_movements` ✅ |
| Contexto de venta | Sin UI | `sales_context` ✅ |
| `backup_manager.py` ruta ELPASAJE | Desactualizada | — |

---

## 11. Señales de contexto externas

- **Aerolíneas Argentinas:** Alejandra trabaja en Control de Gestión - Orden de Vuelo. En picos de AA (lunes, fin de mes, cierres logísticos) su disponibilidad para El Pasaje es menor.
- **Nando también trabaja en AA:** si hay turbulencia institucional en AA → puede afectar pedidos de los 4 clientes B2B de Nando.

---

## 12. Contacto del proyecto

- **CEO:** Alejandra Gomez Aguilera — `admin@elpasaje.com`
- **Producción:** Fernando (Fer) — `fer@elpasaje.com`
- **Email del sistema / agente:** `elpasaje.3d.studio@gmail.com`

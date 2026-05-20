# Arquitectura del Sistema — El Pasaje 3D Studio
## EPCC v2 · Sistema v3.0 · Mayo 2026

---

## Visión general

El sistema es un dashboard interno multi-rol construido en Python + Streamlit.
Corre como app web accesible desde cualquier dispositivo. La DB es SQLite local —
sin servidor externo, sin dependencias en la nube para el core.

```
Browser (Fer / Alejandra / Socios)
        │
        ▼
   main.py (router + auth + sidebar)
        │
        ├── modules/dashboard_admin.py  ← role: admin
        ├── modules/panel_fer.py        ← role: produccion
        ├── modules/panel_socio.py      ← role: socio / socio_multi
        ├── modules/cargar_pedido.py    ← role: socio / socio_multi
        ├── modules/inventario.py       ← role: admin
        ├── modules/impacto.py          ← role: admin
        ├── modules/clientes.py         ← role: admin
        └── modules/panel_mike.py       ← embebido en dashboard_admin
                │
        utils/db.py (SQLAlchemy engine)
                │
        elpasaje_v2.db (SQLite)
```

---

## Stack

| Capa | Tecnología | Versión |
|------|-----------|---------|
| UI / Dashboard | Streamlit | ≥ 1.30 |
| Gráficos | Plotly Express + Graph Objects | ≥ 5.x |
| ORM | SQLAlchemy 2.x | text() + named params |
| DB | SQLite | stdlib Python |
| Agente IA | Python puro + Anthropic API | ep_agente.py |
| Email | SMTP Gmail (App Password) | smtplib |
| Parsing slicers | Python puro | slicer_parser.py |
| Backup | GitHub + Google Drive + disco | backup_manager.py |
| OS / Deploy | Windows 11 Pro (local) + Streamlit Community Cloud | main.py |

---

## Archivos principales

```
magnitud19-backend-share/
│
├── main.py                  ← Router único. Maneja auth, sidebar, y despacha a módulos.
│                              Inicializa la DB vía crear_schema_v3.py en cada arranque.
│
├── crear_schema_v3.py       ← CREATE TABLE IF NOT EXISTS de las 13 tablas base.
│                              Llamado automáticamente desde main.py — idempotente.
│
├── elpasaje_v2.db           ← DB activa. Siempre en la raíz del proyecto.
│                              Path resuelto con os.path relativo, nunca hardcodeado.
│
├── ep_agente.py             ← Agente de análisis nocturno. Corre a las 20:00 hs.
│                              Lee la DB, detecta patrones, escribe en log_agente,
│                              envía email resumen a Alejandra.
│
├── context_elpasaje.py      ← SYSTEM_PROMPT del agente + get_data_context().
│                              Contiene las reglas de negocio hard-coded.
│
├── slicer_parser.py         ← Parser de archivos de slicer (.gcode / .3mf).
│                              Extrae: gramos, tiempo_min, material_tipo, color.
│                              Soporta: Bambu Studio, PrusaSlicer, Cura.
│
├── backup_manager.py        ← Backup multi-destino con timestamp.
│
├── migration_v4.py          ← Agrega columnas de segmentación a tenants.
├── migration_v5.py          ← Crea tabla pagos. ALTER orders ADD pago_id.
│                              ALTER lineas_config ADD whatsapp_numero.
├── migration_v5b.py         ← Crea tabla lineas_config + seed de 11 líneas.
├── migration_v6.py          ← Crea tabla archivos_produccion (BLOB storage).
│
├── modules/
│   ├── dashboard_admin.py   ← Dashboard ejecutivo Alejandra + tab Mike embebido.
│   ├── panel_fer.py         ← Centro de producción Fernando. 7 tabs:
│   │                           Mi Panel / Cargar Fab / Materiales / Cola /
│   │                           Archivos / Mike / Finanzas CFO
│   ├── panel_mike.py        ← Panel de inteligencia ecosistema. 5 secciones:
│   │                           A: Estado / B: Alertas / C: Top productos /
│   │                           D: Señales mercado / E: Historial precios
│   ├── panel_socio.py       ← Panel socios. 8 tabs:
│   │                           Resumen / Stats / Productos / Pedidos /
│   │                           Mi Tienda / Presupuestador / Mike / Mi Línea
│   ├── cargar_pedido.py     ← Formulario de pedido para socios.
│   │                           Cards con miniatura. Pago integrado.
│   └── inventario.py        ← Gestión de inventario (admin).
│
└── utils/
    ├── db.py                ← create_engine() con elpasaje_v2.db.
    ├── lineas.py            ← LINEAS dict (colores, emojis, nombres).
    │                           get_linea(uid), get_lineas_usuario(uid),
    │                           IP_RESTRINGIDA (lista de SKUs con licencia restringida).
    ├── mike.py              ← get_alertas_dashboard() → lista de alertas activas.
    │                           preguntar_mike(pregunta, contexto) → str.
    ├── pricing.py           ← cargar_materiales() → DataFrame.
    │                           calcular_costo_pieza(weight_gr, material_id).
    └── whatsapp.py          ← get_numero_linea(client_id, engine) → str.
                                link_producto(...) → URL wa.me.
                                link_presupuesto(...) → URL wa.me.
                                texto_presupuesto(...) → str copyable.
```

---

## Base de datos — Tablas activas

### Tablas del schema base (`crear_schema_v3.py`)

| Tabla | Descripción |
|-------|-------------|
| `tenants` | Todos los usuarios: socios, admin, Fer, clientes B2B |
| `tenant_lineas` | Relación N:N para socios multi-línea (ej: agustina → oasis_animal + vkhome_cliente) |
| `products` | Catálogo de productos por línea. Incluye `imagen_url`, `material_id`, `activo` |
| `materials` | Filamentos y materiales. `stock_gr`, `cost_kg`, `stock_minimo_gr` |
| `orders` | Pedidos. `status` (Pendiente→En Proceso→Listo→Cancelado), `canal_origen`, `color_pedido` |
| `order_items` | Detalle de cada pedido. `product_sku`, `cantidad`, `precio_unitario` |
| `production_log` | Cada fabricación de Fer: gramos usados, tiempo real, resultado |
| `price_history` | Historial de cambios de precio por producto |
| `stock_movements` | Entradas y salidas de materiales |
| `senales_mercado` | Observaciones comerciales registradas (tipo: demanda/competencia/tendencia/riesgo) |
| `sales_context` | Contexto de venta para el agente IA |
| `log_agente` | Registro de cada análisis del agente Mike |
| `donations` | Donaciones a fondos solidarios |

### Tablas de migraciones

| Tabla | Migración | Descripción |
|-------|-----------|-------------|
| `pagos` | v5 | Estado de pago por orden: `metodo` (transferencia/efectivo/mp), `estado` (pendiente/acreditado/devuelto) |
| `lineas_config` | v5b | Configuración mutable por línea: `whatsapp_numero`, `responsable`, `activa`, colores |
| `archivos_produccion` | v6 | Repositorio de archivos de impresión: `contenido` BLOB, `sku`, `order_id`, `tipo` |

---

## Modelo de roles y acceso

```
admin (Alejandra)
  ├── Dashboard ejecutivo (métricas, KPIs, alertas)
  ├── Tab Mike (ecosistema, top productos, señales de mercado, historial precios)
  ├── Inventario Pro
  ├── Panel Producción (mismo que Fer)
  ├── Socios (gestión de socios)
  └── Clientes (CRM básico)

produccion (Fernando)
  └── Panel Producción
        ├── Mi Panel (KPIs + cola activa + materiales para la semana)
        ├── Cargar Fabricación (registrar impresiones)
        ├── Materiales (stock + registrar compras)
        ├── Cola Inteligente (cards con 🟢/🔴 + botones de acción)
        ├── Archivos (repositorio .gcode/.3mf/.stl por SKU)
        ├── Mike (chat + alertas)
        └── Finanzas CFO (historial exportable)

socio (Olivia, Francisco, Constantino, Nando×4)
  ├── Mi Panel (resumen + stats + pedidos + tienda + presupuestador + Mike + config línea)
  └── Cargar Pedido (formulario con cards de productos)

socio_multi (Agustina)
  ├── Selector de línea en sidebar (Todas / por línea)
  ├── Mi Panel (mismo que socio, filtrado por línea)
  └── Cargar Pedido
```

### Restricciones de privacidad (hard-coded)

- Fernando **nunca** ve: nombre del cliente final, precios de venta, márgenes, facturación
- Fernando ve: nombre de la **línea** (Coquette, Core Tech, etc.), gramos, estado del pedido
- Socios **nunca** ven: pedidos de otras líneas, costos de materiales, márgenes del taller
- Productos `IP_RESTRINGIDA`: muestran badge 🔒 en el panel de Fer, sin link WhatsApp público

---

## Modelo de negocio EPCC v2 (reflejado en el sistema)

```
Capa 1 — Producción interna
  Fer fabrica todas las piezas en el taller
  Materiales: PLA, PETG, ABS, TPU, filamentos especiales
  Máquina: Creality K2 Plus CFS (multicolor FDM)

Capa 2 — Líneas de socios (B2C familia + B2B externos)
  Cada línea tiene su catálogo, sus precios, su identidad visual
  Los socios hacen pedidos → van a la cola de Fer
  El sistema es el intermediario entre el socio y la producción

Regla de margen: precio = costo × 2 → margen real = 50%
costo_pieza = (weight_gr × 1.10 × cost_kg) / 1000
```

---

## Flujo de dato principal (pedido → fabricación → pago)

```
1. Socio carga pedido (cargar_pedido.py)
   → INSERT orders (status='Pendiente')
   → INSERT order_items
   → INSERT pagos (estado='pendiente')

2. Fer ve el pedido en la cola (panel_fer.py · tab Cola)
   → Toca "▶ Iniciar fabricación"
   → UPDATE orders SET status='En Proceso'

3. Fer fabrica y registra (panel_fer.py · tab Cargar Fab)
   → INSERT production_log (gramos, tiempo, resultado)
   → UPDATE materials SET stock_gr = stock_gr - gramos_usados
   → Si Éxito: UPDATE orders SET status='Listo'
   → Si Fallo total: UPDATE orders SET status='Pendiente'

4. Alejandra registra el pago (dashboard_admin o futuro módulo)
   → UPDATE pagos SET estado='acreditado'

5. Agente Mike analiza a las 20:00
   → Lee órdenes, stock, señales
   → INSERT log_agente
   → Envía email resumen
```

---

## Seguridad

- Passwords almacenados como SHA-256 (no plain text)
- Todas las queries usan parámetros bindeados con `text()` de SQLAlchemy 2.x (no f-strings en SQL)
- Aislamiento de datos por `client_id` en todas las queries de socios
- No hay endpoints públicos — la app requiere login para cualquier vista

---

*El Pasaje 3D Studio · Architecture v3.0 · Mayo 2026*

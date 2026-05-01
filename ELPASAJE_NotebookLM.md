# El Pasaje 3D Studio — Documento de Conocimiento
## Para NotebookLM · Versión completa

---

## Descripción general del proyecto

El Pasaje 3D Studio es un negocio familiar de manufactura aditiva (impresión 3D FDM) en Buenos Aires, Argentina, fundado y dirigido por Alejandra Gomez Aguilera. Opera como un ecosistema multi-línea donde cada integrante de la familia gestiona su propia marca dentro de un sistema digital centralizado.

El sistema está en etapa de arranque y crecimiento temprano. Todos los datos son recientes y el historial de ventas es corto (comenzó a formalizarse digitalmente en 2026).

**Email del proyecto:** elpasaje.3d.studio@gmail.com

---

## Quién es quién

### Alejandra Gomez Aguilera — Fundadora y CEO
- Maneja la línea **Magnitud 19**, el segmento premium corporativo del ecosistema.
- Trabaja también en **Aerolíneas Argentinas** (AA), en Control de Gestión — Orden de Vuelo.
- Es la administradora única del sistema: acceso total al dashboard, visualiza márgenes, costos y datos de todos los socios.
- Email de trabajo en El Pasaje: admin@elpasaje.com

### Fernando "Fer" (esposo de Alejandra) — Producción
- Responsable de toda la fabricación: imprime, arma, controla materiales.
- Ciclo típico de producción: 2 a 5 días por pedido.
- Accede al sistema con rol **producción**: solo ve la cola de pedidos y el stock de filamentos. No tiene acceso a márgenes ni costos.
- Email: fer@elpasaje.com

### Olivia (hija) — Línea Coquette
- Gestiona productos femeninos y de estética.
- Acceso socio: ve solo su línea y puede cargar pedidos de producción.
- Email: coquette@elpasaje.com

### Francisco (hijo) — Línea Francisco Sport
- Gestiona equipamiento y accesorios deportivos.
- Acceso socio.
- Email: fsport@elpasaje.com

### Constantino (hijo) — Línea Core Tech
- Gestiona piezas técnicas e industriales.
- Acceso socio.
- Email: coretech@elpasaje.com

### Fernando Gomez Aguilera "Nando" (hermano de Alejandra) — Canal B2B
- Hermano de Alejandra. También trabaja en Aerolíneas Argentinas.
- Es el canal de acceso a los 4 clientes B2B del ecosistema.
- Gestiona las líneas: Aviation Pro, Oasis Animal, Oasis del Estero, Pharma DeLux.
- Si hay turbulencia institucional en AA, puede afectar los pedidos B2B.

---

## Las líneas del ecosistema

| Línea | ID interno | Responsable | Segmento |
|-------|-----------|-------------|----------|
| Magnitud 19 | `admin` | Alejandra | Corporativo / premium |
| Coquette | `olivia_coquette` | Olivia | B2C / estética femenina |
| Francisco Sport | `francisco_sport` | Francisco | B2C / deportivo |
| Core Tech | `constantino_tech` | Constantino | B2C / tech industrial |
| Aviation Pro | `aviation` | Nando | B2B / aeronáutico |
| Oasis Animal | `oasis_animal` | Nando | B2B / veterinario, mascotas |
| Oasis del Estero | `oasis_del_estero` | Nando | B2B / veterinario regional |
| Pharma DeLux | `pharma_delux` | Nando | B2B / farmacéutico |

---

## Modelo de pricing — La regla fundamental

El negocio usa un markup del 100% sobre el costo de material, lo que resulta en un margen real del 50%.

**Fórmula de costo de pieza:**
```
costo = (peso_en_gramos × (1 + merma) × precio_kg) / 1000
merma estándar = 10%
precio_kg de referencia = $2.350 ARS (PETG gris)
```

**Fórmula de margen:**
```
margen% = (precio_venta - costo) / precio_venta × 100
```

Es importante distinguir que el margen se calcula dividiendo por el precio de venta (no por el costo). Un producto con costo $1.000 y precio $2.000 tiene margen del 50%, no del 100%.

**Categorías de margen:**
- **High (>50%):** priorizar producción cuando haya demanda similar
- **Medium (30–50%):** evaluar según volumen
- **Low (<30%):** revisar estructura de costos

---

## Materiales de producción

Los materiales son filamentos termoplásticos para impresión FDM:

| Material | ID | Tipo | Color | Costo/kg |
|----------|-----|------|-------|----------|
| PETG Gris Mecánico | `petg_gris` | PETG | Gris Mecánico | $2.350 |
| PETG Naranja Seguridad | `petg_naranja` | PETG | Naranja | $2.400 |
| PLA Seda Azul Aerolínea | `pla_seda_azul` | PLA | Azul | $2.600 |
| PLA Seda Gris Acero | `pla_seda_gris` | PLA | Gris Acero | $2.550 |
| PLA Rosa Coquette | `pla_rosa` | PLA | Rosa | $2.400 |
| PLA Blanco | `pla_blanco` | PLA | Blanco | $2.200 |
| PLA Negro | `pla_negro` | PLA | Negro | $2.200 |

El stock se mide en gramos. El mínimo de alerta es 200g. La barra de progreso del dashboard toma 1kg como referencia.

---

## El sistema digital

### Stack tecnológico
- **Lenguaje:** Python 3.12
- **Dashboard:** Streamlit (interfaz web, corre localmente)
- **Base de datos:** SQLite (archivo `elpasaje_v2.db`)
- **ORM:** SQLAlchemy 2.x
- **Gráficos:** Plotly Express y Plotly Graph Objects
- **Agente:** Python puro (sqlite3, smtplib)
- **Backup:** GitHub + Google Drive + disco externo (automatizado)

### Archivos principales
- `main.py` — Dashboard completo, ~680 líneas
- `crear_schema_v3.py` — Crea la base de datos desde cero
- `ep_agente.py` — Agente Mike, análisis autónomo nocturno
- `context_elpasaje.py` — Reglas de negocio para el agente
- `backup_manager.py` — Backup multi-destino automatizado

---

## El dashboard — Módulos por rol

### Rol admin (Alejandra)
1. **Dashboard Alejandra** — KPIs globales: valor de stock, ganancia proyectada, costo de producción, valor de materiales. Gráfico de barras apiladas por línea, torta de distribución del ecosistema, ganancia por producto, estado de filamentos. Alertas de stock bajo (≤15 unidades).
2. **Inventario Pro** — Tabla filtrable de todos los productos con márgenes y stock.
3. **Produccion (Fer)** — Cola de pedidos con cambio de estado, stock de filamentos, calculadora de insumos.
4. **Socios** — Tarjetas por línea con stock, ganancia y margen promedio. Separados en Familia y B2B.
5. **Clientes** — CRM simple: listado de contactos con segmentación, formulario de nuevo cliente, módulo de señales de mercado.
6. **Impacto Social** — Fondos solidarios: Refugio Oasis Animal, Mentes Brillantes, Fondo General. Registro de donaciones.

### Rol producción (Fer)
- Solo accede a la pantalla de **Produccion**: cola de pedidos, actualización de estado, stock de filamentos y calculadora.

### Rol socio (familia y B2B)
- **Mi Panel** — Stock, ganancia proyectada y lista de sus productos.
- **Cargar Pedido** — Selección de producto de su propia línea, cantidad, notas para Fer.

---

## El Agente Mike (`ep_agente.py`)

Mike es el agente de inteligencia del ecosistema. Corre automáticamente todos los días a las 20:00 hs.

### Qué analiza
1. **Patrón de Margen** — Identifica el producto más rentable del catálogo activo.
2. **Clientes Recurrentes** — Detecta clientes con 2 o más órdenes.
3. **Alerta de Entrega** — Órdenes con entrega estimada en ≤2 días y estado activo.
4. **Patrón de Demanda** — Categoría con mayor revenue acumulado.
5. **Señales Pendientes** — Señales de mercado registradas pero no analizadas.

### Qué produce
- Guarda cada hallazgo en la tabla `log_agente` con tipo, señal, dato, acción sugerida y nivel de confianza.
- Envía un email HTML a `elpasaje.3d.studio@gmail.com` con el resumen del día: KPIs, órdenes activas, patrones detectados.

### Cómo correrlo manualmente
```bash
python ep_agente.py            # análisis completo + email
python ep_agente.py silencioso # análisis, sin email
```

---

## Flujo de una orden de producción

1. **Socio carga pedido** desde "Cargar Pedido" en su panel → se crea en `orders` con estado `Pendiente`.
2. **Fer ve el pedido** en su cola → cambia estado a `En Proceso` al empezar.
3. **Fer termina** → cambia a `Listo`.
4. El agente Mike detecta si una orden está en `En Proceso` con entrega en ≤2 días → alerta urgente.

---

## El módulo de Señales de Mercado

Captura inteligencia comercial desde el campo:
- Cualquier usuario puede registrar una reacción de un cliente (le encantó, preguntó el precio, dudó, pidió muestra, etc.)
- Se asocia a una línea y/o producto específico
- El agente detecta cuántas señales hay sin procesar y las incluye en su análisis diario
- Campo `procesado_por_ia = 0` indica que el agente aún no las analizó

---

## Fondos solidarios

El Pasaje destina parte de sus ingresos a tres fondos:

| Fondo | ID | Meta mensual |
|-------|-----|-------------|
| Refugio Oasis Animal | `refugio_oasis` | $50.000 ARS |
| Mentes Brillantes | `mentes_brillantes` | $40.000 ARS |
| Fondo General | `fondo_general` | $30.000 ARS |

Las donaciones pueden ser de tipo: urna física, QR, redondeo o producto donado.

---

## Sistema de backup

El backup corre automáticamente a las 20:00 hs como parte del ciclo del agente.

**Destinos:**
1. **GitHub** — Commit automático con timestamp y motivo, push a `main`
2. **Google Drive** — Copia los archivos clave a subcarpeta con fecha
3. **Disco externo (E:)** — Ídem, cuando el disco esté conectado

**Archivos que se respaldan en Google Drive y disco:**
- main.py, crear_schema_v3.py, ep_agente.py, context_elpasaje.py, backup_manager.py, CONTEXTO_PROYECTO.md

---

## Contexto institucional de Aerolíneas Argentinas

Tanto Alejandra como Nando trabajan en AA. Esto genera dos tipos de señal:

1. **Disponibilidad de Alejandra:** Los lunes, fin de mes y cierres de período logístico en AA reducen su tiempo disponible para El Pasaje.
2. **Pedidos de Nando:** Los 4 clientes B2B (Aviation Pro, Oasis Animal, Oasis del Estero, Pharma DeLux) pasan todos por Nando. Si hay tensión institucional en AA, puede haber demoras en los pedidos.

---

## Estado del sistema al 2026-05-01

### Fixes completados en la sesión de May 2026
1. Eliminada vulnerabilidad de SQL Injection en 6 puntos del dashboard
2. Tabla `senales_mercado` agregada al schema (faltaba)
3. 10 columnas de segmentación comercial completadas en `tenants`
4. Socios ahora ven sus propios productos (no los de admin) al cargar pedido
5. Fer separado con rol `produccion` propio en login y sidebar
6. Agente Mike reconectado a la DB activa (`elpasaje_v2.db`)
7. Rutas hardcodeadas eliminadas de `ep_agente.py` y `context_elpasaje.py`
8. Tabla `log_agente` creada en el schema y con auto-creación en runtime

### Módulos con estructura en DB pero sin pantalla en el dashboard
- `price_history` — historial de cambios de precio por producto
- `production_log` — log de cada impresión (material usado, tiempo real, resultado)
- `stock_movements` — movimientos de stock (entradas, ventas, ajustes, merma)
- `sales_context` — contexto de venta para modelos predictivos

---

## Glosario técnico

| Término | Definición |
|---------|-----------|
| FDM | Fused Deposition Modeling — técnica de impresión 3D por capas |
| PLA | Ácido poliláctico — filamento biodegradable, el más común |
| PETG | Polietileno tereftalato modificado — más resistente que PLA |
| SKU | Stock Keeping Unit — código único de producto |
| Merma | Porcentaje de material que se pierde en soporte, calibración, etc. |
| Markup | Margen sobre el costo. Markup 100% = precio doble del costo |
| ODV | Orden de Venta — concepto del sistema anterior (ahora: Order/Pedido) |
| B2B | Business to Business — venta a empresas |
| B2C | Business to Consumer — venta al consumidor final |

# Análisis de Flujos de Negocio — El Pasaje 3D Studio
**Fecha:** 2026-07-04 | **Ciclo 1 · Loop v3**

---

## Resumen ejecutivo

El sistema tiene módulos que funcionan de forma aislada. **Ningún flujo de negocio está conectado de punta a punta.** Los datos existen en la DB pero los efectos no se propagan: crear un pedido no verifica material, avanzar un estado no descuenta filamento, marcar "Entregado" no registra la venta. El sistema es un conjunto de formularios, no una máquina de estados.

---

## FLUJO 1 — VENTA

**Escenario:** Un cliente quiere una Bandeja Oval M (SKU: OE-BOV-M, línea VK-Home).

| Paso | Estado | Descripción |
|---|---|---|
| ¿Desde dónde crear el pedido? | ❌ ROTO | El admin (Ale) **no tiene** "Nueva Venta" en su menú. El menú admin es: Control / Stock / Taller / Líneas / CRM / Impacto / Mike. Para crear un pedido hay que ser socio y usar la tab "Pedido". |
| ¿Cuántos clicks para crear? | ⚠️ PARCIAL | Si sos socio: seleccionar producto (grid) → completar formulario → Confirmar. ~5 clicks, flujo aceptable. Pero el admin no puede hacerlo en absoluto. |
| ¿El pedido llega a la cola? | ✅ FUNCIONA | INSERT en `orders` con status='Pendiente'. Aparece en panel_fer. |
| ¿Verifica material disponible? | ❌ ROTO | No. Al crear el pedido no hay ninguna verificación de `materials.stock_gr`. El stock_movements INSERT está en un try/except que **falla silenciosamente**. |
| ¿Qué pasa al marcar Entregado? | ❌ ROTO | Solo un `UPDATE orders SET status='Entregado'`. No registra venta, no descuenta stock, no alimenta métricas. La tabla `production_log` tiene **0 registros** — nunca se usó. |
| ¿El stock del producto baja? | ❌ ROTO | No hay stock de producto terminado. Los stock_movements existen en DB pero no se insertan consistentemente. |

**Severidad: CRÍTICA** — El flujo de venta no existe para el admin, y el cierre del ciclo (Entregado → venta registrada) está completamente roto.

---

## FLUJO 2 — PRODUCCIÓN

**Escenario:** 3 pedidos en cola. Fabricar, avanzar estados, registrar.

| Paso | Estado | Descripción |
|---|---|---|
| ¿La cola muestra qué fabricar? | ✅ FUNCIONA | Panel Fer → "Mi Panel" y "Cola de Pedidos" muestran pedidos activos con línea, producto, gramos estimados, notas, urgente. |
| ¿Muestra semáforo de material? | ⚠️ PARCIAL | En "Materiales para esta semana" (expander en Mi Panel) hay un semáforo manual calculando demanda vs stock. No está en la fila del pedido. |
| ¿Avance de estado con 1 click? | ❌ ROTO | Requiere: abrir expander → selectbox → botón "Confirmar". **3 interacciones** para cambiar un estado. Sin efectos automáticos. |
| ¿Descuenta filamento al avanzar? | ❌ ROTO | El cambio de estado es un UPDATE directo sin ningún efecto secundario. `production_log` = 0 registros. |
| ¿Registra desperdicio si falla? | ❌ ROTO | No existe ese flujo. |
| Integridad transaccional | ❌ ROTO | Cambios de estado son INSERTs/UPDATEs sueltos. `PRAGMA foreign_keys` no está activado en `utils/db.py`. |

**Severidad: CRÍTICA** — La cola existe pero es solo visual. El avance de estados no tiene efectos. La producción real no está registrada.

---

## FLUJO 3 — MATERIAL

**Escenario:** Llega un rollo nuevo de PLA negro de 1kg.

| Paso | Estado | Descripción |
|---|---|---|
| ¿Se puede cargar un rollo? | ⚠️ PARCIAL | En panel_fer hay una tab "🧵 Materiales" — necesita verificación de si tiene formulario de alta. `inventario.py` dice "Agregá el primero desde el panel de Fer" — es solo visualización. |
| ¿Queda en stock_movements? | ❌ ROTO | stock_movements existe en DB pero no se usa consistentemente. La única inserción está en cargar_pedido.py con try/except silencioso. |
| ¿El sistema sabe cuánto filamento queda? | ✅ FUNCIONA | `materials.stock_gr` se muestra en Inventario Pro. Los datos actuales parecen ser seed data (25kg de cada material — números redondos, no reales). |
| ¿Avisa cuando está por acabarse? | ✅ FUNCIONA | Alertas de materiales críticos en sidebar y dashboard. Compara con `stock_minimo_gr`. |
| ¿Alta de rollo actualiza stock automáticamente? | ❌ INCIERTO | Necesita verificación de panel_fer tab materiales. |

**Severidad: ALTA** — El stock actual parece ser demo data, no real. La entrada de material no está integrada con stock_movements.

---

## FLUJO 4 — SOCIO

**Escenario:** Login de Agustina y Fede.

| Usuario | Credenciales | Estado | Detalle |
|---|---|---|---|
| Agustina | oasisanimal@elpasaje.com / 123 | ✅ FUNCIONA | uid='oasis_animal', tipo='socio_multi'. `tenant_lineas` confirma que ve: oasis_animal + vkhome_cliente. Hash '123' ✓ |
| Agustina alt | agustina@elpasaje.com | ⚠️ DESCONOCIDA | uid='agustina', tipo='socio_multi', también ve oasis_animal + vkhome_cliente via tenant_lineas. Pero el hash de password NO es '123'. Contraseña desconocida. |
| Fede | oasisdelestero@elpasaje.com / 123 | ✅ FUNCIONA | uid='oasis_del_estero', tipo='socio', hash '123' ✓. Ve solo su línea. |
| Fer | fer@elpasaje.com | ⚠️ LIMITADO | uid='fer_produccion', tipo='produccion' → role='produccion' → menú=['Taller']. **No ve márgenes, finanzas, clientes, Mike**. Según decisión de la CEO esto debe cambiar a admin. |

**El login de oasisanimal y oasisdelestero FUNCIONA.** El problema de Agustina es que gestiona dos líneas (Oasis Animal + VK-Home) desde el mismo login — esto está correctamente configurado en tenant_lineas.

**Severidad: MEDIA** — Los accesos básicos funcionan. Fer necesita migración a admin (decisión CEO). La cuenta `agustina@elpasaje.com` tiene contraseña desconocida.

---

## FLUJO 5 — DECISIÓN (el lunes de Ale)

**Escenario:** Alejandra abre el sistema y quiere saber en < 60 segundos: ventas semana, cola, material faltante, línea creciendo.

| Dato | Dónde está | Clicks para llegar | Estado |
|---|---|---|---|
| Ventas de la semana | "Control" (dashboard_admin) | 1 click | ✅ pero depende de que las ventas estén registradas (no lo están) |
| Cola activa | "Taller" → panel_fer → "Mi Panel" | 2 clicks | ✅ visible |
| Material crítico | Sidebar (alertas Mike) | 0 clicks | ✅ siempre visible |
| Línea creciendo | "Control" → gráficos Plotly | 1 click | ✅ si hay datos |
| Crear un pedido | No existe en menú admin | ∞ | ❌ ROTO |
| Avanzar un pedido a Entregado | "Taller" → panel_fer → expander → selectbox → botón | 4+ clicks | ⚠️ LENTO |

El dashboard muestra los datos correctos si los datos están registrados. El problema es que la mayoría de los datos no se registran automáticamente (ventas, producción).

**Severidad: MEDIA** — El dashboard visual está bien. El problema es upstream: los datos que debería mostrar no se generan automáticamente.

---

## Prioridad de implementación

| # | Qué | Por qué es urgente |
|---|---|---|
| 1 | `utils/orders.py` → `avanzar_estado()` | Columna vertebral. Sin esto ningún flujo conecta. |
| 2 | Migración Fer a admin | Decisión CEO aprobada. Cambio en DB + routing en main.py. |
| 3 | Verificación material al crear pedido | Sin esto Fer recibe pedidos imposibles de fabricar. |
| 4 | "Nueva Venta" en menú admin | Ale no puede cargar un pedido hoy. |
| 5 | Efectos automáticos: LISTO → descuenta filamento | Conecta producción con materiales. |
| 6 | Efectos automáticos: ENTREGADO → registra venta | Conecta producción con métricas. |
| 7 | Dark mode residual en cargar_pedido.py e inventario.py | Design system incompleto. |
| 8 | Contraseña desconocida de agustina@elpasaje.com | Cuenta potencialmente inutilizable. |

---

## Estado de la DB

- **Tablas:** tenants, tenant_lineas, materials, products, orders, order_items, price_history, stock_movements, production_log, sales_context, donations, log_agente, senales_mercado, revenue_rules, kit_components, pagos, lineas_config, archivos_produccion
- **Tenants:** 11 registros
- **Productos:** ~100 SKUs activos en todas las líneas
- **Orders:** 3 pedidos (2 Entregado del 2026-05-02, 1 En Proceso del 2026-05-28) — **datos de prueba, no producción real**
- **production_log:** 0 registros — nunca se registró una fabricación
- **materials:** 25,000g de cada material — seed data, probablemente no real
- **PRAGMA foreign_keys:** NO activado en utils/db.py

---

*Generado automáticamente · Loop v3 Ciclo 1 · 2026-07-04*

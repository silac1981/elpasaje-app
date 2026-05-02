# QA Checklist — El Pasaje 3D Studio
## Sistema v3.0 · Post-deploy / Post-migración · Mayo 2026

> Correr completo antes de cada deploy a producción o tras una migración de DB.
> Marcar con ✅ cada ítem al verificarlo. Ningún bloqueante debe quedar sin resolver.

---

## 1. Infraestructura y DB

- [ ] `elpasaje_v2.db` existe en la raíz del proyecto
- [ ] `python check_v5.py` no muestra errores — tablas `pagos` y `lineas_config` presentes
- [ ] Todas las migraciones corrieron sin error: v4, v5, v5b, v6
- [ ] Tabla `archivos_produccion` existe (`python migration_v6.py` idempotente)
- [ ] `products` tiene columna `imagen_url` (TEXT, nullable)
- [ ] `orders` tiene columnas `canal_origen`, `fecha_entrega_solicitada`, `referencia_archivo`
- [ ] `lineas_config` tiene 11 filas (admin + 10 líneas activas)
- [ ] Backup reciente en `backups/` con timestamp del día

---

## 2. Autenticación y roles

- [ ] Login con `admin@elpasaje.com` → accede al Dashboard Alejandra sin error
- [ ] Login con `fer@elpasaje.com` → accede únicamente a Producción (Fer) — sidebar solo muestra ese ítem
- [ ] Login con cualquier socio (ej: `coquette@elpasaje.com`) → ve Mi Panel y Cargar Pedido — NO ve Dashboard ni Producción
- [ ] Contraseña incorrecta → muestra "Credenciales incorrectas", no stacktrace
- [ ] Botón "Cerrar Sesión" funciona y vuelve al login
- [ ] El sidebar muestra el nombre del usuario y su rol correctamente

---

## 3. Panel Fernando — 📁 Archivos

- [ ] Tab "📁 Archivos" aparece en el panel de Fer (7 tabs en total)
- [ ] El acordeón "➕ Subir nuevo archivo" se expande y muestra el formulario
- [ ] Se puede subir un archivo .gcode y queda listado
- [ ] Se puede subir un archivo .3mf y queda listado
- [ ] El botón "⬇ Descargar" descarga el archivo correctamente
- [ ] El botón "🗑" elimina el archivo y la lista se actualiza
- [ ] Un SKU con archivo muestra badge "📁" en la Cola de Pedidos

---

## 4. Panel Fernando — Cola de Pedidos

- [ ] Tab "📋 Cola de Pedidos" muestra tarjetas con los pedidos activos
- [ ] Indicador 🟢 aparece cuando hay suficiente stock del material requerido
- [ ] Indicador 🔴 aparece cuando el stock es insuficiente
- [ ] Banner naranja aparece si la demanda total supera el stock disponible
- [ ] Botón "▶ Iniciar fabricación" cambia el pedido a "En Proceso" y recarga
- [ ] Botón "✅ Marcar listo" cambia el pedido a "Listo" y recarga
- [ ] Selectbox + "✓ Confirmar" funcionan para otros cambios de estado
- [ ] Los productos con `imagen_url` muestran miniatura a la derecha del card
- [ ] Los pedidos NO muestran el nombre del cliente final — solo la línea (Coquette, Core Tech, etc.)
- [ ] Los productos IP_RESTRINGIDA muestran badge "🔒"

---

## 5. Panel Fernando — Cargar Fabricación

- [ ] Solo aparecen pedidos en estado "En Proceso" en el selectbox
- [ ] El label muestra `#ID · Nombre · Línea` (nunca nombre de cliente final)
- [ ] Si el producto tiene imagen, se muestra miniatura sobre el formulario
- [ ] Radio de resultado tiene 3 opciones: ✅ Éxito, ⚠️ Fallo parcial, ❌ Fallo total
- [ ] Con "✅ Éxito" aparece checkbox "Marcar como Listo al guardar"
- [ ] Al guardar con Éxito + Listo: pedido cambia a Listo automáticamente
- [ ] Con "❌ Fallo total": pedido vuelve a Pendiente
- [ ] Los gramos se descuentan del stock del material seleccionado
- [ ] Importar desde slicer (.gcode / .3mf) pre-llena gramos y tiempo
- [ ] Las últimas 20 fabricaciones se muestran en la tabla al final del tab

---

## 6. Panel Fernando — Materiales

- [ ] Cada material muestra: stock actual, precio/kg, consumido este mes, días de stock estimados
- [ ] La barra de progreso cambia a rojo cuando el stock baja del mínimo
- [ ] Formulario "Registrar compra" suma los gramos al stock
- [ ] Si se ingresa precio, se recalcula el costo/kg promedio ponderado
- [ ] El badge ⚠️ aparece en el acordeón cuando stock ≤ mínimo

---

## 7. Panel Fernando — Mi Panel

- [ ] Los 4 KPIs se muestran (⏳ Pendientes, 🆕 Hoy, ✅ Fabricadas, ⚠️ Críticos)
- [ ] El acordeón "📦 Materiales para esta semana" muestra la demanda vs stock
- [ ] Materiales faltantes aparecen con 🔴 y texto "FALTA"
- [ ] La cola activa debajo de los KPIs lista los pedidos pendientes / en proceso

---

## 8. Socios — Cargar Pedido

- [ ] Los cards de productos se muestran en 3 columnas
- [ ] Si el producto tiene `imagen_url` válida (http), aparece la imagen como portada del card
- [ ] Al seleccionar un producto aparece el badge "✓ SELECCIONADO" en color de la línea
- [ ] El formulario de detalle (cantidad, fecha, color, urgente, notas, canal, archivos) funciona
- [ ] Radio de método de pago aparece: Transferencia / Efectivo / MercadoPago (próximamente)
- [ ] Al confirmar el pedido: se crea en `orders`, se crea el `order_items`, se crea el registro en `pagos`
- [ ] El número de pedido se muestra en el mensaje de éxito
- [ ] Pedido marcado como urgente muestra la advertencia naranja después de confirmar

---

## 9. Socios — Mi Panel (pestañas)

- [ ] Pestaña "📦 Mis Pedidos" muestra historial con badge de estado de pago (💳/✅/↩️)
- [ ] Pestaña "🛍️ Mi Tienda" muestra productos de la línea con botones de WhatsApp
- [ ] Si no hay `whatsapp_numero` configurado, muestra advertencia ⚠️ en vez del botón
- [ ] Pestaña "💰 Presupuestador": Paso 1 permite armar presupuesto, Paso 2 muestra texto copyable y link WA
- [ ] Pestaña "⚙️ Mi Línea" permite configurar el número de WhatsApp (valida 10-15 dígitos)

---

## 10. Dashboard Admin (Alejandra)

- [ ] El dashboard carga sin errores con `admin@elpasaje.com`
- [ ] Tab "🤖 Mike" en el dashboard muestra las 5 secciones (A-E)
- [ ] Sección A muestra los 3 KPIs del ecosistema con semáforos
- [ ] Sección B muestra alertas activas (o "Sin alertas activas" si no hay)
- [ ] Sección C muestra el Top 5 productos con barras de progreso
- [ ] Cada sección tiene acordeón "ℹ️ Qué analizar acá" con explicación
- [ ] Las alertas en el sidebar (mini-resumen) muestran el badge correcto (🔴/🟡/✅)

---

## 11. Agente Mike

- [ ] `python ep_agente.py silencioso` corre sin error y escribe en `log_agente`
- [ ] `python ep_agente.py` corre sin error (puede fallar solo si no hay credenciales de email)
- [ ] `get_alertas_dashboard()` devuelve lista (puede ser vacía, pero no lanza excepción)
- [ ] `preguntar_mike("¿cuál es el estado del taller?")` devuelve texto, no error

---

## 12. Integridad de datos crítica

- [ ] Fer nunca ve el nombre del cliente final en ninguna pestaña — solo el nombre de la línea
- [ ] Fer nunca ve precios de venta ni márgenes
- [ ] Los socios NO ven pedidos ni productos de otras líneas
- [ ] Los socios NO ven la pestaña "💹 Finanzas CFO" del panel de Fer (solo Fer y admin)
- [ ] Un producto marcado como IP_RESTRINGIDA muestra 🔒 y no tiene botón de WhatsApp público

---

## 13. Performance y estabilidad

- [ ] La app carga en menos de 5 segundos en la primera visita
- [ ] No hay `AttributeError` o `KeyError` sin capturar en ningún tab
- [ ] El panel de Fer carga aunque `archivos_produccion` esté vacía (tabla creada pero sin filas)
- [ ] El panel de socios carga aunque `pagos` no tenga filas para ese cliente
- [ ] `st.cache_data(ttl=300)` funciona — refrescar la página no re-ejecuta todas las queries

---

## Criterio de salida a producción

Todos los ítems de las secciones 1-5 deben estar ✅.
Las secciones 6-13 no deben tener ningún bloqueante (error que rompa el flujo del usuario).
Defectos cosméticos menores pueden dejarse como deuda técnica documentada.

---

*El Pasaje 3D Studio · QA Checklist v3.0 · Mayo 2026*

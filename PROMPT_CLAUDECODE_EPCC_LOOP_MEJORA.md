# PROMPT CLAUDE CODE — EL PASAJE 3D STUDIO
## Loop de mejora continua · a partir del 09/09/2026

Este prompt es para correr con `/loop` (intervalo a criterio del modelo, o el que defina Ale al lanzarlo). Cada iteración: elegir UN ítem del backlog de abajo, ejecutarlo completo (código → verificar → commit), y avanzar al siguiente. Un commit por ítem. Frenar y preguntar si un ítem requiere una decisión de Ale marcada como tal.

## 0. Lectura obligatoria antes de arrancar

1. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\MEMORY.md`
2. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\project_sesion_septiembre2026.md`
3. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\reference_supabase_org.md` — **crítico**: si algo falla por conexión a Supabase, el proyecto real está en la organización "El Pasaje 3D Studio" (ref `dzcypcrqcjducynmnnxx`), NO en "AlitaSuperStar". No perder tiempo ahí.

Repo canónico: `C:\Trabajo\ElPasaje`. Nunca reprecear (`AUDITORIA_PRICING_2026-07.md` sigue PRELIMINAR).

## 1. Backlog — en orden de impacto

### 🔴 Datos falsos visibles al público (prioridad más alta)
- **a)** ✅ **INVESTIGADO (09/09, loop)** — `luminis.html`: Luminis **no existe como línea/tenant en el backend** (cero referencias en `utils/lineas.py` ni en el seed). El contador hardcodeado (`11`) no tiene de dónde salir dinámicamente sin antes crear la línea y sus productos en la DB. **📋 Bloqueado — decisión de Ale**: ¿Luminis es una línea real con productos a cargar, o es contenido aspiracional/mockup? Si es real, necesita alta de tenant + productos antes de poder generar `luminis-catalog.json`.
- **b)** ✅ **INVESTIGADO (09/09, loop)** — `coquette.html`: `animCount('cnt-p',247)`, horas 1840, kg 18 (línea 1045) son stats de "impacto" (piezas producidas / horas de impresión / kg de filamento), no conteo de catálogo — no hay ninguna tabla que agregue esto hoy (`production_log`/`stock_movements` existen pero nadie los suma para este propósito). **📋 Bloqueado — decisión de Ale**: ¿se arma una query real (`SUM` sobre `production_log`/`stock_movements`) y se conecta, o queda como copy de marketing aproximado a sabiendas? Si son copy intencional, no es un bug — pero vale dejarlo explícito en el código con un comentario para que no se confunda con dato en vivo en el futuro.
- **c)** ✅ **INVESTIGADO (09/09, loop)** — `vuelo-certero.html`: sus 5 SKUs reales (`VC-QPR-U`, `VC-FJG-U`, `VC-TBX-U`, `VC-PPT-U`, `VC-PRA-U`) **ya están** en `exports/magnitud19-catalog.json` (comparten `client_id='admin'`). El problema no es de datos sino de contenido: la página es 100% estática con productos de fantasía que NO coinciden con los SKU reales (Estabilizadores de Arco, Cajas de Munición, etc. vs. Quiver Pro, Fletcher Jig, Tournament Box reales). **📋 Bloqueado — decisión de Ale**: ¿se reescribe la página para mostrar los productos reales (dinámico, filtrando `magnitud19-catalog.json` por SKU `VC-*` con el mismo patrón `_M19_TABS`), o el contenido actual es intencional/aspiracional y se deja estático?

### 🟡 Pendientes ya identificados en la auditoría del 09/09 (fotos + v17)
- **d)** Mover fotos: Batman/Darth Vader (14 archivos en `static/productos/sin_clasificar/`) → `static/productos/ip_restringida/`. Portacelular 360 → `static/productos/avp/`.
- **e)** Crear `migrations/migration_v17.sql`: mapear `imagen_url` de productos Oasis Animal que ya tienen foto en `static/productos/oasis-animal/`. **Antes de crear el archivo, confirmar con Ale el mapeo foto↔SKU** (mostrado en el reporte del Ciclo 1 — `clip_dispensador_A/B.jpg` y `chapas_poncho.jpg` no tienen SKU claro, y `soporte_comedero.jpg` vs `soporte_comedero_cruz.jpg` no distingue Huesito de Patita por nombre — no adivinar, preguntar).
- **f)** ✅ **HECHO (commit `7eb877c`, 09/09, loop)** — `utils/exports.py`: `imagen_url` agregado a los `SELECT` y a las listas whitelist de `_clean()` (productos_3d, productos_linea, kits). Falta que se regeneren los 9 JSON reales (se hace solo en el próximo deploy vía el botón "Regenerar TODOS los catálogos" o guardado de precios — no se pudo probar en vivo desde esta red, sin acceso a Supabase).
- **g)** M19 subcategoría: evaluar con Ale si vale la pena agregar columna `subcategoria` en `products` para reemplazar el filtro por SKU hardcodeado (`_M19_TABS`) en `magnitud19.html`, o si el mantenimiento manual sigue siendo aceptable dado el volumen bajo de SKUs nuevos.

### 🟢 Deuda técnica menor
- **h)** `elpasaje-app-win/`: decidir con Ale si se documenta como submódulo git real o se descarta — actualmente gitignoreado, sin resolver.
- **i)** Convención de migraciones: confirmar formalmente que `.sql` (vía `utils/migration_runner.py`) es el único estándar desde v17 en adelante — ya es el comportamiento de facto, falta que quede escrito en algún doc o en el propio runner.
- **j)** Revisión de consistencia de diseño repo-wide: correr `Select-String -Pattern "#0E0E10|#0e0e10|#C9A24B|#B87333|#0D1117|#161B22|#21262D|#8B949E|Cormorant|Jost" -Recurse *.py *.html` cada vez que se toque un módulo o página pública — el Ciclo 1 encontró y corrigió residuales que un fix anterior había dejado a medias (`cargar_pedido.py`, `panel_socio.py`) precisamente por no re-verificar después de un cambio.

### 📋 Bloqueado — no tocar sin Ale
- **k)** Pricing: `AUDITORIA_PRICING_2026-07.md` sigue PRELIMINAR. Bloqueado hasta que Fer pese productos reales en balanza y confirme costo/kg real de MakerPanda (`setup_materiales.py` ya tiene los precios de lista: PLA $24.140, PETG $19.920, etc. — son precios de compra, no confirman el peso real de cada pieza).
- **l)** pharma-delux nombres de marca ("Organizador ADN" etc.): no commitear a DB hasta que Ale confirme titularidad de la IP.

## 2. Reglas del loop

1. Un ítem por iteración. Verificar (compilar / levantar la app / grep de confirmación) antes de commitear.
2. Mensajes de commit en español, formato `tipo: descripción`.
3. Si un ítem toca `panel_fer.py`: editar **solo** en modo binario Python (mojibake preexistente, ver memoria `feedback-encoding-panelfer`), nunca con el editor de texto directo.
4. Nunca reprecear ni tocar `cost_kg`/`price` fuera de lo explícitamente descrito arriba.
5. Ítems marcados 📋 requieren confirmación de Ale antes de ejecutar — presentarlos y esperar, no asumir.
6. Al cerrar cada iteración: push a `origin/main` y confirmar que el deploy en Streamlit Cloud no rompe (si rompe por Supabase, ver memoria `reference-supabase-org` antes de tocar código).
7. Actualizar `MEMORY.md` (append, con fecha) al final de cada iteración con lo que se hizo.

---

*El Pasaje 3D Studio · Loop de mejora · generado 09/09/2026*

# PROMPT CLAUDE CODE — EL PASAJE 3D STUDIO
## Loop de mejora continua · a partir del 09/09/2026

Este prompt es para correr con `/loop` (intervalo a criterio del modelo, o el que defina Ale al lanzarlo). Cada iteración: elegir UN ítem del backlog de abajo, ejecutarlo completo (código → verificar → commit), y avanzar al siguiente. Un commit por ítem. Frenar y preguntar si un ítem requiere una decisión de Ale marcada como tal.

## 0. Lectura obligatoria antes de arrancar

1. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\MEMORY.md`
2. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\project_sesion_septiembre2026.md`
3. `C:\Users\ar028883\.claude\projects\c--Trabajo-ElPasaje\memory\reference_supabase_org.md` — **crítico**: si algo falla por conexión a Supabase, el proyecto real está en la organización "El Pasaje 3D Studio" (ref `dzcypcrqcjducynmnnxx`), NO en "AlitaSuperStar". No perder tiempo ahí.

Repo canónico: `C:\Trabajo\ElPasaje`. Nunca reprecear (`AUDITORIA_PRICING_2026-07.md` sigue PRELIMINAR).

## 1. Backlog — en orden de impacto

### 🔴 Bloqueante de negocio — acceso de Agustina (hallazgo 24/09, retoma tras 15 días parados)
- **m)** El hub público (`https://silac1981.github.io/elpasaje-app/`) está **live y funcionando** (verificado por fetch externo — 11 líneas visibles, sin errores). Pero `elpasaje.streamlit.app` (la app interna, donde Agustina loguearía con `oasisanimal@elpasaje.com`) **redirige a una pantalla de autenticación de Streamlit Cloud** (`share.streamlit.io/-/auth/app`) — esto es la restricción de **visibilidad de la app a nivel de plataforma** (Settings → Sharing en el dashboard de Streamlit Cloud), una capa *antes* del login interno de El Pasaje. Si la app está configurada como "privada", Agustina no puede llegar ni a ver la pantalla de login aunque su usuario y contraseña (`123`) ya estén verificados en la DB desde julio. **No es algo que se arregle con código** — Ale tiene que entrar a share.streamlit.io → la app → Settings → Sharing y confirmar que esté en "Public" (o agregar el mail de Agustina como viewer autorizado si se prefiere mantenerla privada). Este es el desbloqueante #1 para "mandarle a Agustina la suya".

### 🔴 Datos falsos visibles al público (prioridad más alta)
- **a)** ✅ **RESUELTO — decisión de Ale (09/09)**: Luminis es **contenido aspiracional**, la línea no se lanzó. **No tocar.** Queda registrado para retomar cuando se lance la línea de verdad (alta de tenant + productos en DB recién ahí).
- **b)** ✅ **RESUELTO — decisión de Ale (09/09)**: los stats de `coquette.html` (247 piezas / 1840hs / 18kg) **no son verídicos** — la línea no se lanzó, se vendieron cosas aisladas sin datos agregables útiles. **No tocar los números.** Única acción válida futura: si aparecen fotos o propuestas de producto reales, tratarlo como contenido/imágenes, no como estadística a calcular.
- **c)** ✅ **RESUELTO — decisión de Ale (09/09)**: el contenido de `vuelo-certero.html` es **intencional**, no un bug. Es una línea de nicho alta-performance pensada como desprendimiento de Magnitud 19 (público de excelencia/altas capacidades) — **no reemplazar por los SKU VC-* reales**. Sí vale explorar en un futuro ciclo (bajo prioridad, no urgente) alguna relación visual/de navegación entre Vuelo Certero y Magnitud 19 en el hub, ya que conceptualmente se desprende de ahí — pero eso es una mejora de diseño, no una corrección.

### 🟡 Pendientes ya identificados en la auditoría del 09/09 (fotos + v17)
- **d)** Mover fotos: Batman/Darth Vader (14 archivos en `static/productos/sin_clasificar/`) → `static/productos/ip_restringida/`. Portacelular 360 → `static/productos/avp/`.
- **e)** ⚠️ **PARCIAL (24/09, sesión de retoma)** — `migrations/migration_v17.sql` creada, pero solo con los 2 mapeos sin ambigüedad, confirmados **visualmente** (se abrieron las fotos con el visor de imágenes): `perrito_globo_1.jpg` → `OA-LPG-U` (Llavero Perrito Globo), `soporte_comedero.jpg` → `OA-SCP-U` (Soporte Comedero **Patita** — la foto muestra una huella de pata, no un hueso). `soporte_comedero_cruz.jpg` resultó ser una foto de la pata/soporte de ese mismo producto (grabada "OASIS ANIMAL"), no un producto distinto — no se mapea aparte. **Siguen sin resolver, necesitan decisión de Ale/Agustina:**
  - `chapas_poncho.jpg` — son chapitas grabadas con el nombre "PONCHO" (una mascota real, personalización de un pedido). No hay ningún SKU actual de tipo "chapa" que calce claramente (el más cercano, `OA-GTG-U` "Guardian Tag QR Emergencia", es un tag distinto). ¿Se usa como foto genérica del producto (mostrando el nombre de un cliente real) o hay que pedir/generar una versión sin personalizar?
  - `clip_dispensador_A.jpg` / `_B.jpg` — dispensador de bolsitas con el logo "OASIS ANIMAL". **No existe ningún SKU para este producto** en el catálogo actual (10 SKU: EEA, EEI, GTG, KIT-C/E/P, LPG, MLI, SCH, SCP). ¿Es un producto real que falta dar de alta, o una muestra que no se vende?
  - `OA-SCH-U` (Soporte Comedero **Huesito**) sigue sin ninguna foto.
  - No se pudo regenerar `exports/oasis-animal-catalog.json` (sigue con fecha 10/07, sin `imagen_url`, stock en 0 para las 10 SKU) — sin acceso a Supabase desde esta red (ver memoria `feedback-supabase-red`). **Se resuelve solo** en el próximo deploy si alguien con acceso admin aprieta "🔄 Regenerar TODOS los catálogos" en el dashboard, una vez que `migration_v17` haya corrido.
- **f)** ✅ **HECHO (commit `7eb877c`, 09/09, loop)** — `utils/exports.py`: `imagen_url` agregado a los `SELECT` y a las listas whitelist de `_clean()` (productos_3d, productos_linea, kits). Falta que se regeneren los 9 JSON reales (se hace solo en el próximo deploy vía el botón "Regenerar TODOS los catálogos" o guardado de precios — no se pudo probar en vivo desde esta red, sin acceso a Supabase).
- **f2)** ✅ **HECHO (24/09)** — Hallazgo nuevo: aunque `imagen_url` esté poblado, **ninguna de las 9 páginas públicas renderiza `p.imagen_url` en las cards dinámicas** — el template JS de `oasis-animal.html` (y, revisado como muestra, `sport.html`) siempre mostraba un emoji placeholder fijo, ignorando el campo. Corregido **solo en `oasis-animal.html`**: ahora usa `<img src="${p.imagen_url}">` si existe, con fallback al emoji 🐾 si no. La CSS (`.card-img img{object-fit:cover}`) ya estaba lista para esto, solo faltaba el `<img>` en el JS. **Pendiente replicar en las otras 8 páginas** en un ciclo futuro (no urgente hoy — ninguna otra línea tiene `imagen_url` poblado todavía salvo FSP-* de Sport, que usa fotos fijas hardcodeadas en el hero, no el grid dinámico).
- **g)** M19 subcategoría: evaluar con Ale si vale la pena agregar columna `subcategoria` en `products` para reemplazar el filtro por SKU hardcodeado (`_M19_TABS`) en `magnitud19.html`, o si el mantenimiento manual sigue siendo aceptable dado el volumen bajo de SKUs nuevos.

### 🟢 Deuda técnica menor
- **h)** `elpasaje-app-win/`: decidir con Ale si se documenta como submódulo git real o se descarta — actualmente gitignoreado, sin resolver.
- **i)** Convención de migraciones: confirmar formalmente que `.sql` (vía `utils/migration_runner.py`) es el único estándar desde v17 en adelante — ya es el comportamiento de facto, falta que quede escrito en algún doc o en el propio runner.
- **j)** Revisión de consistencia de diseño repo-wide: correr `Select-String -Pattern "#0E0E10|#0e0e10|#C9A24B|#B87333|#0D1117|#161B22|#21262D|#8B949E|Cormorant|Jost" -Recurse *.py *.html` cada vez que se toque un módulo o página pública — el Ciclo 1 encontró y corrigió residuales que un fix anterior había dejado a medias (`cargar_pedido.py`, `panel_socio.py`) precisamente por no re-verificar después de un cambio.

### 🟢 Deuda técnica — hallazgo nuevo (24/09)
- **n)** `sport.html` tiene un botón "IA" (`callIA()`) que hace `fetch('https://api.anthropic.com/v1/messages', ...)` **directo desde el navegador, sin API key**. Esto significa que el fetch siempre falla (401, falta `x-api-key`) y cae siempre al `catch` → muestra una de las 3-5 frases fijas de `FB{}` (fallback hardcodeado). No hay ninguna clave expuesta (bien, no es un leak de seguridad), pero tampoco hay ninguna llamada real a IA — es una función que aparenta ser generativa y no lo es. Si es un placeholder para conectar más adelante a un proxy propio con la key del lado del servidor, dejarlo documentado así; si no, considerar sacar el fetch muerto y dejar directamente las respuestas fijas (más simple y no promete algo que no hace). No se tocó — es una decisión de producto, no un bug urgente.

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

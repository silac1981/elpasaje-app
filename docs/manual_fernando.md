# Manual de Producción — Fernando
## El Pasaje 3D Studio · Sistema de Gestión Interno
### Versión 3 · Mayo 2026

---

## ¿Qué es este sistema?

Es la herramienta interna del taller. Desde acá vas a ver todos los pedidos que llegan, registrar cada pieza que fabricás, controlar el stock de materiales y consultar a Mike (el asistente IA) cuando necesitás ayuda.

**Acceso:** `elpasaje.streamlit.app`
**Tu usuario:** `fer_produccion`
**Contraseña:** (te la da Alejandra)

---

## Lo que SÍ ves y lo que NO

| Ves | No ves |
|-----|--------|
| Nombre de la línea (Oasis Animal, Coquette, etc.) | Nombre del cliente final |
| Estado del pedido | Precios de costo ni márgenes |
| Gramos del producto | Datos de facturación |
| Stock de materiales | Información financiera de socios |
| Tu historial de fabricaciones | |

> Esto es intencional. Vos te enfocás en fabricar bien — el resto lo maneja Alejandra.

---

## Las pestañas del sistema

Cuando entrás, ves 6 pestañas arriba:

```
🛠️ Mi Panel  |  📦 Cargar Fabricacion  |  🧵 Materiales  |  📋 Cola de Pedidos  |  🤖 Mike  |  💹 Finanzas CFO
```

---

## 🛠️ Mi Panel — Tu vista principal

Es lo primero que ves al entrar. Tiene dos partes:

### Los 4 números de arriba

| Métrica | Qué significa |
|---------|---------------|
| ⏳ **Pendientes** | Pedidos esperando que los empieces |
| 🆕 **Hoy** | Pedidos que entraron hoy |
| ✅ **Fabricadas** | Total de piezas que registraste en el sistema |
| ⚠️ **Críticos** | Materiales con stock por debajo del mínimo |

### La cola activa

Debajo de los números ves los pedidos en estado **Pendiente** o **En Proceso**.

Cada pedido muestra:
- Número de pedido y nombre de la pieza
- **Línea** del socio (nunca el nombre del cliente)
- Gramos estimados y fecha de entrega
- Un selectbox para cambiar el estado manualmente

**Al final de esta sección**: un acordeón **"📦 Materiales para esta semana"** que te muestra de un vistazo qué materiales necesitás para fabricar todos los pedidos activos:

```
🟢 PLA Negro     → Necesario: 180g  · Disponible: 850g  ✅ OK
🔴 PETG Blanco   → Necesario: 220g  · Disponible: 90g   ⚠ FALTA
```

> Si ves 🔴 en algún material, avisale a Alejandra antes de arrancar esa fabricación.

---

## 📋 Cola de Pedidos — Cola inteligente

Acá está el corazón del trabajo diario. Ves todos los pedidos activos en tarjetas.

### Cómo leer cada tarjeta

```
#42 · Soporte para auriculares · 🟢           ← número, pieza, material OK
🏷️ Core Tech  ·  ⚖️ 85g  ·  📅 2026-05-01   ← línea, gramos, fecha
```

### Los indicadores de material

| Indicador | Significado |
|-----------|-------------|
| 🟢 | Hay suficiente filamento para fabricar esta pieza |
| 🔴 | No hay suficiente stock — coordiná con Alejandra antes |

### El banner naranja

Si ves un banner amarillo/naranja arriba de la cola:
```
⚠️ Stock insuficiente para la cola actual: PETG Blanco, ABS Gris
```
Significa que en total la demanda supera el stock. No podés fabricar todo sin reponer antes.

### Badge 🔒

Si una pieza tiene el ícono 🔒 es **solo de uso interno** (licencias restringidas). Fabricala normalmente — solo no la vendas al público.

### Los botones de acción

Cada tarjeta tiene botones según el estado:

**Si el pedido está Pendiente:**
```
[ ▶ Iniciar fabricación ]
```
Tocás este botón cuando empezás a imprimir la pieza. El pedido pasa a "En Proceso".

**Si el pedido está En Proceso:**
```
[ ✅ Marcar listo ]
```
Tocás cuando la pieza salió bien y está lista para entregar.

**Si necesitás otro cambio** (cancelar, etc.):
Usá el selectbox de la derecha y confirmá con el botón "✓ Confirmar".

---

## 📦 Cargar Fabricación — Registrar lo que hiciste

Después de fabricar una pieza, registrala acá. Son **4 campos máximo**:

### Campo 1 — Pedido en proceso
Elegís el pedido que fabricaste. El sistema solo te muestra los que ya están **En Proceso** (los que ya iniciaste desde la Cola).

El label te muestra: `#42 · Soporte para auriculares · Core Tech`

> Si fabricaste algo sin pedido asociado, dejá "Sin pedido" seleccionado.

### Campo 2 — Resultado
```
○ ✅ Éxito      ○ ⚠️ Fallo parcial      ○ ❌ Fallo total
```

| Resultado | Qué pasa automáticamente |
|-----------|--------------------------|
| ✅ Éxito | Aparece checkbox para marcar el pedido como Listo |
| ⚠️ Fallo parcial | Registra el fallo pero el pedido sigue En Proceso |
| ❌ Fallo total | El pedido vuelve automáticamente a Pendiente |

### Campo 3 — Gramos consumidos
Ya viene pre-cargado con el peso del producto del pedido seleccionado. Modificalo si usaste más o menos.

### Campo 4 — Tiempo (horas)
Cuántas horas tardó la impresión. Podés poner 0.5, 1.5, 2, etc.

### Opcionales (colapsados)

- **📎 Importar desde slicer**: Si tenés el archivo .gcode o .3mf, podés subirlo y pre-llena gramos, tiempo y material automáticamente (Bambu Studio, PrusaSlicer, Cura).
- **📝 Notas**: Para dejar observaciones (color que quedó distinto, necesita lijado, etc.)

### Al guardar
- Los gramos se descuentan automáticamente del stock del material
- Si marcaste Éxito + "Marcar como Listo": el pedido cambia a Listo solo
- Si fue Fallo total: el pedido vuelve a Pendiente para que Alejandra lo reprograme

---

## 🧵 Materiales — Control de stock

Acá ves todos los filamentos y materiales disponibles.

### Cómo leer cada material

Cada uno tiene un acordeón que muestra:
- **Stock actual** en gramos
- **Precio/kg** para el cálculo de costos
- **Consumido este mes** (cuánto usaste en el mes)
- **Días de stock estimados** al ritmo de consumo actual
- Una barra de progreso visual (verde 🟢 / amarillo ⚠️ / rojo 🔴)

### Registrar una compra de filamento

Cuando comprás un rollo nuevo, abrí el acordeón del material y completá:
1. **Gramos comprados** (ej: 1000 para un kilo)
2. **Precio pagado** (opcional — actualiza el costo/kg automáticamente)
3. Tocá **"Registrar compra"**

El stock se actualiza solo.

---

## 🖥️ Integración con Fusion 360 y Programas de Diseño

### El flujo completo de diseño a producción

```
Fusion 360 / Diseño CAD
        ↓
  Exportar STL o 3MF
        ↓
  Slicer (Bambu Studio / PrusaSlicer / Cura)
        ↓
  Exportar .gcode o .3mf con configuración de impresión
        ↓
  Creality K2 Plus CFS — Fabricación
        ↓
  El Pasaje Sistema — Cargar Fabricación (importar archivo)
        ↓
  Gramos, tiempo y material detectados automáticamente
```

### Cómo exportar desde Fusion 360

**Para imprimir directamente:**
1. Abrí el modelo en Fusion 360
2. Menú **File → Export**
3. Elegí formato **STL** (para piezas simples) o **3MF** (recomendado — preserva más información)
4. Guardá con el nombre del pedido: `OE-BDA-U_v2.stl`

**Para enviar al socio con especificaciones:**
- Exportá como **3MF** desde **File → 3D Print → Export to 3MF**
- El 3MF incluye colores, materiales y metadatos del modelo

### Slicer: cuál usar con el K2 Plus CFS

| Slicer | Compatible K2 Plus | Detección en sistema | Recomendado |
|--------|--------------------|----------------------|-------------|
| **Bambu Studio** | ✅ Perfil nativo | ✅ Gramos exactos + tiempo + color | ⭐ Principal |
| **PrusaSlicer** | ✅ Con perfil manual | ✅ Gramos exactos + tiempo | ✅ Alternativa |
| **Cura** | ✅ Con perfil manual | ⚠️ Solo gramos (parcial) | Para casos específicos |
| **Creality Print** | ✅ Nativo K2 | ❌ No soportado aún | Solo impresora |

> Para el K2 Plus CFS (multicolor), usá siempre **Bambu Studio** — tiene el perfil CFS integrado y la detección del sistema es exacta.

### Configuración recomendada K2 Plus CFS

| Parámetro | PLA | PETG | ABS |
|-----------|-----|------|-----|
| Temp. boquilla | 220°C | 240°C | 250°C |
| Temp. cama | 55°C | 70°C | 100°C |
| Velocidad | 150 mm/s | 120 mm/s | 100 mm/s |
| Relleno | 15% (decorativo) / 30% (funcional) | 20-30% | 25% |
| Capas perímetro | 3 | 3-4 | 4 |

### Cómo exportar el archivo para importar al sistema

#### Bambu Studio (recomendado)

**Opción A — Proyecto .3mf completo (más información):**
1. Configurá la impresión en Bambu Studio
2. **File → Save Project** → guardá como `.3mf`
3. En el sistema, sección **📎 Importar desde slicer**, subí ese `.3mf`
4. El sistema detecta: gramos, tiempo estimado, tipo de material, color (si es Bambu)

**Opción B — .gcode generado:**
1. Hacé slice del modelo
2. **Export → Export plate sliced file** → `.gcode`
3. Subí el `.gcode` al sistema — detecta gramos y tiempo

#### PrusaSlicer

1. Configurá el modelo y hacé slice
2. **File → Export → Export G-code** → `.gcode`
3. En el campo de notas del header del archivo quedan: peso, tiempo estimado y filamento usado
4. El sistema los lee automáticamente

#### Cura

1. Slice el modelo normalmente
2. **Save to File** → `.gcode`
3. El sistema detecta gramos del comentario `;Filament used`

### Flujo completo: Fusion 360 → Sistema, paso a paso

```
1. Diseñás la pieza en Fusion 360

2. Exportás como STL o 3MF

3. Abrís Bambu Studio → importás el archivo

4. Seleccionás el filamento correcto del pedido
   (fijate en las notas del pedido: color y material pedido)

5. Configurás infill según el uso del producto

6. Slice → revisás el tiempo y gramos estimados

7. Guardás como .3mf o exportás el .gcode

8. Mandás a imprimir en el K2 Plus CFS

9. Mientras imprime, vas al sistema:
   Cargar Fabricación → 📎 Importar desde slicer
   Subís el archivo → los campos se llenan solos

10. Cuando la pieza termina:
    Indicás el resultado y guardás
```

### Qué detecta el sistema automáticamente

| Campo | .3mf Bambu | .gcode Bambu | .gcode Prusa | .gcode Cura |
|-------|-----------|-------------|-------------|------------|
| Gramos | ✅ Exacto | ✅ Exacto | ✅ Exacto | ✅ Exacto |
| Tiempo | ✅ Exacto | ✅ Exacto | ✅ Exacto | ⚠️ Aprox. |
| Material | ✅ Nombre | ✅ Nombre | ✅ Nombre | ⚠️ Genérico |
| Color | ✅ Hex | ❌ | ❌ | ❌ |

> Si el sistema no detecta algún campo, completalo vos manualmente — siempre podés corregir antes de guardar.

### Tus propios diseños (ej: OE-BDA-U Bandeja Damero)

Para piezas que vos diseñaste y están en desarrollo:

1. Nombrás el archivo con el SKU oficial: `OE-BDA-U_v1.stl`
2. Cuando hacés la primera prueba de impresión, registrás la fabricación con pedido "Sin pedido" y resultado ⚠️ Fallo parcial o ✅ Éxito
3. En las notas del sistema escribís: *"Primera prueba — prototipo. Gramos reales: Xg. Tiempo: Xh"*
4. Ese dato queda en el historial y Alejandra lo usa para cargar el precio final del producto

> Si el diseño cambia entre versiones (v1, v2, v3), podés agregar la versión en las notas para que el historial sea rastreable.

### Problemas frecuentes con la integración del slicer

| Situación | Solución |
|-----------|----------|
| El sistema no lee el .3mf | Verificá que sea exportado con "Save Project" de Bambu Studio, no solo "Export STL" |
| Detectó 0 gramos | El archivo no tiene metadatos de slice — hacé el slice completo antes de exportar |
| Tiempo detectado muy diferente al real | Usá el tiempo real al cargar — el estimado es referencia, no obligatorio |
| No encuentra el material en la lista | Escribí el material manualmente — si el nombre es nuevo, avisale a Alejandra para que lo agregue |
| El K2 Plus CFS no lee el .gcode | Usá Bambu Studio o exportá directamente desde Creality Print para el K2 |

---

## 🤖 Mike — Tu asistente de IA

Mike es un asistente inteligente que conoce el taller: los pedidos, el stock, tu historial de fabricación y los materiales. Podés preguntarle cualquier cosa relacionada con la producción.

### Preguntas rápidas (botones de una sola pulsación)

```
📋 Prioridades de hoy     🧵 Días de stock
🔴 Analizar fallos        💰 Mejor margen
🛒 Qué comprar            📊 Estado del taller
```

Tocás uno y Mike responde directo, con contexto real del taller.

### Chat libre

También podés escribirle libremente:
- *"Tengo el pedido #38 pero me quedé sin PETG, ¿qué hago?"*
- *"Rompí 3 piezas esta semana, ¿cuál puede ser la causa?"*
- *"¿Qué fabrico primero hoy?"*

Mike tiene acceso a:
- El estado actual de todos los pedidos
- El stock de cada material
- Tu historial de fabricaciones y tasa de fallos
- Las alertas activas del sistema

### Alertas automáticas

Encima del chat Mike te muestra las alertas activas (stock crítico, pedidos demorados, etc.). Para cada alerta hay un botón **"Preguntarle a Mike →"** que le manda el problema directo y te da una respuesta específica.

### Limpiar el chat

El botón **"Limpiar chat"** borra el historial de la sesión. El contexto del taller (pedidos, stock) siempre está actualizado aunque lo limpies.

---

## Flujo de trabajo típico de un día

```
1. Entrás al sistema → 🛠️ Mi Panel
   → Mirás los 4 números
   → Revisás "📦 Materiales para esta semana"
   → Si hay 🔴 en algún material → avisás a Alejandra

2. Vas a 📋 Cola de Pedidos
   → Leés las tarjetas en orden
   → Verificás que el material sea 🟢
   → Tocás "▶ Iniciar fabricación" en el primer pedido

3. Fabricás la pieza

4. Vas a 📦 Cargar Fabricación
   → Seleccionás el pedido
   → Indicás el resultado (Éxito / Fallo parcial / Fallo total)
   → Confirmás gramos y tiempo
   → Guardás

5. Si fue Éxito y marcaste "Listo"
   → El pedido desaparece de la cola activa automáticamente

6. Repetís con el siguiente pedido

7. Si tenés dudas → 🤖 Mike
```

---

## 📁 Repositorio de Archivos — Guardar y recuperar tus archivos de impresión

Desde la pestaña **📁 Archivos** podés guardar todos tus archivos de impresión (.gcode, .3mf, .stl) vinculados al sistema.

### Para qué sirve

- Tener en un solo lugar todos los archivos validados por SKU
- Cuando llega un nuevo pedido de un producto que ya fabricaste, bajás el archivo directamente sin buscarlo en el disco
- Sabés exactamente qué versión (v1, v2...) se usó para cada fabricación
- Alejandra puede ver qué archivos existen para cada producto

### Cómo subir un archivo

1. Abrí el acordeón **➕ Subir nuevo archivo** (viene expandido por defecto)
2. Seleccioná el **SKU del producto** — si es un archivo nuevo sin producto aún, dejá "sin SKU / libre"
3. Si el archivo corresponde a un pedido en curso, ponés el número de pedido (opcional)
4. Subís el archivo (.gcode, .3mf o .stl)
5. Podés agregar una nota: *"v2 · 15% infill · PETG Blanco · tiempo real 2h20"*
6. Tocás **Guardar archivo** — queda vinculado al SKU en la DB

### Cómo recuperar un archivo para imprimir

1. Filtrás por SKU del producto que necesitás
2. Ves todos los archivos guardados para ese SKU con fecha y notas
3. Tocás **⬇ Descargar** — el archivo se descarga a tu dispositivo
4. Lo abrís en Bambu Studio o lo mandás directamente a la impresora

### Indicador 📁 en la Cola

En la **📋 Cola de Pedidos**, si un producto tiene archivos guardados aparece el badge **📁** junto al nombre. Es tu señal de que no necesitás generar el .gcode de cero.

### Tamaño máximo recomendado

| Tipo | Tamaño típico | Recomendación |
|------|--------------|---------------|
| .3mf (Bambu) | 1–5 MB | ✅ Ideal — incluye todo |
| .gcode (simple) | 5–30 MB | ✅ OK |
| .gcode (multicolor CFS) | 30–100 MB | ⚠️ Pesado — preferí .3mf si podés |
| .stl | 0.5–5 MB | ✅ Para referencia de modelo |

---

## 📊 Cómo leer las estadísticas de Mike (para Alejandra)

> Esta sección es referencia para entender qué buscar en cada número de la pestaña 🤖 Mike del dashboard de Alejandra.

### A · Estado del Ecosistema

| Métrica | Verde (bien) | Rojo (acción) | Qué hacer si está en rojo |
|---------|-------------|--------------|--------------------------|
| Pedidos demorados | 0 | Más de 2 | Revisar si Fer tiene sobrecarga o falta stock |
| Líneas inactivas | 0 | 1 o más | Llamar al socio — puede haber algo no reportado |
| Materiales bajo mínimo | 0 | 1 o más | Hacer el pedido al proveedor ese mismo día |

### C · Top 5 Productos

Lo que buscás acá:
- **Si el #1 domina con el triple**: es un producto estrella. Asegurate de que su material nunca falte y que esté siempre en la cola de Fer con prioridad.
- **Si todos tienen números similares**: demanda distribuida — saludable, pero requiere más stock variado.
- **Si un producto desapareció del ranking que antes estaba**: puede ser un problema de stock o que el socio dejó de ofrecerlo. Vale la pena consultar.

### D · Señales de Mercado

Orden de lectura recomendado:
1. **Primero los 🔴 riesgo** — requieren acción inmediata (faltante de insumo, queja, proveedor)
2. **Luego los 🟢 demanda** — oportunidades de nuevos productos o variantes
3. **Por último 🔵 tendencia** — información de mediano plazo para planificar el catálogo

### E · Historial de Precios

Cuándo mirar esto:
- Antes de hablar con un socio sobre precios: revisás el historial completo de sus productos
- Cuando el costo de un filamento sube: verificás qué productos usan ese material y cuánto ajustaste la última vez
- Si hay muchos aumentos juntos en el mismo período: es señal de que hay que revisar todos los márgenes

---

## Errores frecuentes y soluciones

| Situación | Qué hacer |
|-----------|-----------|
| No aparece el pedido en "Cargar Fabricación" | Primero iniciarlo desde la Cola (botón ▶) |
| El stock de un material quedó negativo | Avisale a Alejandra para que lo corrija |
| Registré el resultado equivocado | Avisale a Alejandra (no podés editarlo vos) |
| Mike no responde | Problema de conexión con la IA — intentá de nuevo en 1 minuto |
| La app se cerró en el celular | Volvé a entrar con el mismo usuario, el estado se guarda en la DB |

---

## Resumen de lo que podés hacer vs. lo que no

### ✅ Podés

- Ver y actualizar estados de pedidos
- Registrar fabricaciones con resultado, gramos y tiempo
- Registrar compras de materiales
- Consultar stock y consumo por material
- Pedirle ayuda a Mike
- Exportar historial desde la pestaña Finanzas
- Subir y descargar archivos de impresión (.gcode, .3mf, .stl) vinculados a SKUs

### ❌ No podés (por diseño)

- Ver precios de venta ni márgenes
- Ver el nombre del cliente final (solo la línea)
- Editar pedidos ya registrados
- Modificar productos del catálogo
- Acceder al panel de socios ni al dashboard de Alejandra

---

## Contacto

Cualquier problema con el sistema o pedido que no cierra bien:

**Alejandra Gomez Aguilera** — Administración El Pasaje 3D Studio

---

*El Pasaje 3D Studio · Manual interno · v3 · Mayo 2026*
*Este documento es de uso interno — no compartir fuera del taller.*

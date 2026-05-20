# Reporte Técnico — El Pasaje 3D Studio
### Para: Fernando (Fer) — Responsable de Producción
### Preparado por: Alejandra Gomez Aguilera + Mike (Agente IA)
### Fecha: Mayo 2026 · v1.0

---

## 1. ¿Qué es el sistema?

**El Pasaje 3D Studio** tiene un sistema de gestión operativa construido en Python + Streamlit, corriendo en la nube (Streamlit Cloud). Es accesible desde cualquier navegador, en cualquier dispositivo, sin instalar nada.

El sistema centraliza en un solo lugar:

| Módulo | Para quién | Qué hace |
|---|---|---|
| Dashboard Alejandra | Admin | Inteligencia de negocio: márgenes, stock, ganancia por línea |
| Inventario Pro | Admin | Control de stock detallado por SKU |
| **Centro de Fabricación (Fer)** | **Vos** | Cola de pedidos, registro de fabricación, materiales, Mike |
| Panel de Socios | Admin | Vista del ecosistema completo, pedidos en curso por línea |
| Panel de Socio | Olivia / Constan / Fran / Agustina | Sus propios productos, pedidos, métricas |
| Clientes | Admin | Señales de mercado, comportamiento |

**Base de datos:** SQLite (`elpasaje_v2.db`) con 8+ tablas relacionadas que se actualizan en tiempo real cada vez que alguien usa el sistema.

---

## 2. Tu panel — Centro de Fabricación

### Cómo accedés
1. Entrás a la URL del sistema (Streamlit Cloud)
2. Email + contraseña de producción
3. El sistema te lleva directo a tu panel oscuro

### Las 5 pestañas del panel

#### 🛠️ Mi Panel
Tu dashboard de producción en tiempo real:
- **4 KPIs** en la parte superior: pedidos pendientes, nuevos hoy, total piezas fabricadas, materiales críticos
- **Cola activa**: todos los pedidos Pendiente / En Proceso con cliente, producto, gramos estimados y fecha de entrega
- Desde acá podés cambiar el estado de un pedido directamente (Pendiente → En Proceso → Listo)
- **Estado vacío inteligente**: cuando no hay pedidos activos, te muestra tus métricas históricas (total fabricado, material más usado, última fabricación)

#### 📦 Cargar Fabricación
El formulario principal de tu día a día:
1. **Importar desde slicer** (ver Sección 4 abajo): arrastrás el archivo `.gcode` o `.3mf` de Bambu Studio, PrusaSlicer o Cura y los gramos, tiempo y material se llenan automáticamente
2. Seleccionás el pedido asociado (o "Sin pedido" para fabricación libre sin orden)
3. SKU, material, gramos consumidos, tiempo real, resultado (ok / fallo / reimpresión)
4. Si hubo fallo: campo de descripción
5. Al guardar: descuenta los gramos del stock de materiales y actualiza el estado del pedido

#### 🧵 Materiales
Vista de cada material (filamento) con:
- Stock actual en gramos, barra de nivel visual
- Consumo del mes, días de stock estimados al ritmo actual
- Costo/kg y valor en stock
- **Formulario de compra**: gramos comprados + precio pagado → actualiza stock y recalcula el costo/kg automáticamente (promedio ponderado, no reemplaza el histórico)

#### 📋 Cola de Pedidos
Vista completa de todos los pedidos del sistema con filtro por estado. Podés cambiar estados directamente desde acá también.

#### 🤖 Mike
Tu asistente IA (ver Sección 3 abajo).

---

## 3. Mike — Tu Asistente de Producción

### Qué es Mike
Mike es un agente de inteligencia artificial construido sobre Claude (Anthropic), el mismo modelo que usan herramientas como GitHub Copilot. **No es un chatbot genérico** — conoce en detalle:

- Las reglas de negocio de El Pasaje (estructura de costos, markup, líneas)
- El estado actual de tu base de datos (pedidos, materiales, fabricaciones)
- Tu historial de producción
- Las alertas activas en tiempo real

### Qué hace Mike automáticamente (sin que vos hagas nada)

Cada 2 minutos verifica 4 tipos de alertas:

| Alerta | Ejemplo |
|---|---|
| **Stock crítico** | "PLA Blanco: 120g restantes · mínimo 200g · ~4 días de stock" |
| **Pedido urgente** | "Pedido #12 vence en 1 día — Oasis Animal · En Proceso" |
| **Tasa de fallos alta** | "34% de fallos esta semana (3 de 9 fabricaciones)" |
| **Socio inactivo** | "Core Tech sin pedir hace 28 días — ciclo normal: 14 días" |

Las alertas aparecen en dos lugares:
1. **Sidebar** (barra lateral): siempre visible con el resumen y color de criticidad
2. **Tab 🤖 Mike**: detalle completo con acción sugerida y botón "Preguntarle a Mike →"

### Preguntas rápidas disponibles
Desde el tab Mike, con un click enviás preguntas prearmadas:

- 📋 **Prioridades de hoy** — qué pedidos fabricar primero y por qué
- 🧵 **Días de stock** — cuántos días te queda de cada material al ritmo actual
- 🔴 **Analizar fallos** — causas probables y cómo prevenirlos
- 💰 **Mejor margen** — qué piezas fabricar para maximizar el margen
- 🛒 **Qué comprar** — qué materiales comprar esta semana y en qué cantidad
- 📊 **Estado del taller** — diagnóstico completo del estado actual

### El chat libre
También podés escribirle cualquier cosa en lenguaje natural:
> "Tuve 3 fallos seguidos con PETG gris, la capa no adhiere bien. ¿Qué temperatura me recomendás?"

> "¿Cuánto material necesito para fabricar todos los pedidos activos?"

> "Oliva me mandó un pedido nuevo de porta-macetas de 150g, ¿me alcanza el PETG?"

Mike responde con **números exactos del sistema**, no con respuestas genéricas.

---

## 4. Vinculación con Fusion 360, Bambu Studio y otros sistemas 3D

### Lo que ya está funcionando hoy

#### Parser de slicer (🟢 activo)
Cuando terminás de laminar en cualquier slicer, arrastrás el archivo a la pestaña 📦 Cargar Fabricación y el sistema extrae automáticamente:

| Slicer | Formato | Extrae |
|---|---|---|
| Bambu Studio | `.3mf` | Peso exacto del `slice_info.config` interno, tiempo en segundos, tipo de material (PLA/PETG), color hex |
| Bambu Studio | `.gcode` | Mismos campos del header |
| PrusaSlicer | `.gcode` | Gramos, tiempo `2h 14m`, filament_type |
| Cura | `.gcode` | Gramos (si configurado), tiempo, tipo |

**Resultado:** los gramos en tu historial de fabricación son exactos (del slicer), no estimaciones manuales. Esto mejora directamente las predicciones de Mike.

---

### Lo que viene — Integraciones en el roadmap

#### Bambu Lab API local (🟡 próximo — estimado: 2-4 semanas)
Las impresoras Bambu tienen una API local por WiFi (protocolo MQTT) que permite:
- Ver en tiempo real: % de progreso de la impresión actual, temperatura de boquilla y cama, material restante en el AMS
- Recibir el gramaje **real final consumido** cuando termina la impresión
- Detectar errores (spaghetti detection, jam del AMS)

**Impacto:** el sistema sabría automáticamente cuándo terminó una impresión y con qué resultado, sin que vos tengas que registrar nada manualmente.

**Requisito:** la PC o servidor que corre el sistema debe estar en la misma red WiFi que la impresora. Para Streamlit Cloud (en la nube) se necesitaría un puente local (script en la PC del taller).

#### Fusion 360 (🔵 futuro — 1-3 meses)
Autodesk tiene una API REST (Autodesk Platform Services). Permite:
- Leer el peso estimado del modelo desde el CAD directamente
- Obtener el volumen real de material antes de laminar
- Sincronizar el catálogo de modelos con el inventario del sistema

**Caso de uso:** cuando Constan termina un modelo en Fusion, el sistema ya sabe el peso estimado antes de que llegue a la impresora.

#### Maker World / Bambu Cloud (🔵 futuro)
Bambu Lab tiene una API cloud que permite:
- Ver historial de prints de la cuenta
- Acceder a modelos guardados en la biblioteca
- Estadísticas de uso de materiales por impresora

---

## 5. Las páginas web de los socios — Estado actual y plan

### Estado actual
Existen 14 archivos HTML en el repositorio local, uno por cada línea/canal:

```
coquette.html          → Catálogo Olivia
core-tech.html         → Catálogo Constan
sport.html             → Catálogo Francisco
oasis-animal.html      → Catálogo Oasis Animal (Nando)
oasis-estero.html      → Catálogo Oasis del Estero
pharma-delux.html      → Catálogo Pharma DeLux
aero-tech.html         → Catálogo Aviation Pro
magnitud19.html        → Catálogo Magnitud 19 / Admin
index.html             → Página principal El Pasaje
luminis.html, melomano.html, vuelo-certero.html  → Proyectos en desarrollo
```

**Problema actual:** estos archivos están en la computadora local pero **no están publicados en internet**. Están excluidos del repositorio de GitHub (`*.html` en el .gitignore), lo que significa que no se auto-suben.

### Por qué no se sincronizan con el sistema

Las páginas HTML son estáticas — fueron creadas manualmente y no leen de la base de datos. Si actualizás un precio en el sistema, la página web **no se actualiza sola**.

### El plan para vincularlos — 3 fases

#### Fase 1 — Publicar lo que existe (🟢 1-2 días)
1. Sacar `*.html` del `.gitignore` (o agregar excepciones específicas)
2. Hacer push de los HTML a GitHub
3. Activar **GitHub Pages** en el repositorio → URL pública inmediata: `https://silac1981.github.io/elpasaje-app/`
4. Cada HTML quedaría accesible como: `.../coquette.html`, `.../oasis-animal.html`, etc.
5. **Sin costo** — GitHub Pages es gratuito

#### Fase 2 — Generación automática desde la DB (🟡 1-2 semanas)
Crear un script `generar_paginas.py` que:
1. Lee los productos activos de `elpasaje_v2.db` por línea
2. Genera el HTML de cada socio con precios y stock actualizados
3. Hace commit + push automáticamente

Este script se integraría al backup diario de las 20hs que ya corre Mike. Cada noche:
- Se actualiza el sistema
- Se regeneran los HTML con datos frescos
- Se publican a GitHub Pages automáticamente

#### Fase 3 — Dominio propio + SEO (🔵 1 mes)
- Comprar un dominio (ej: `elpasaje3d.com.ar` — muy económico)
- Apuntar al GitHub Pages o migrar a Netlify/Vercel
- SEO básico para que cada línea aparezca en Google

---

## 6. Proyectos pendientes — Estado y prioridad

### 🔴 Alta prioridad (esta semana)

| # | Tarea | Descripción |
|---|---|---|
| P1 | **Publicar HTML páginas** | Activar GitHub Pages con los catálogos existentes |
| P2 | **Verificar contraste en prod** | Confirmar que el tema oscuro del panel Fer se ve bien en todos los navegadores |
| P3 | **Configurar ANTHROPIC_API_KEY en Streamlit Cloud** | Si Mike da error de conexión, revisar que el secret esté configurado en el dashboard de Streamlit |

### 🟡 Media prioridad (próximas 2 semanas)

| # | Tarea | Descripción |
|---|---|---|
| P4 | **Script generador de páginas web** | Auto-generar HTML desde la DB al hacer backup diario |
| P5 | **Bambu MQTT local** | Conectar la impresora Bambu al sistema para datos en tiempo real |
| P6 | **Panel consulta contextual Mike** | Chat de Mike accesible también desde el formulario de fabricación, no solo desde el tab Mike |
| P7 | **Predicciones de consumo de material** | Mike proyecta cuánto material necesitás en los próximos 30 días según historial |

### 🔵 Largo plazo (1-3 meses)

| # | Tarea | Descripción |
|---|---|---|
| P8 | **Fusion 360 API** | Importar peso estimado de modelos CAD directamente |
| P9 | **Dominio propio** | `elpasaje3d.com.ar` con los catálogos de cada línea |
| P10 | **Notificaciones WhatsApp** | Mike te avisa por WhatsApp cuando un pedido está urgente o el stock cae |
| P11 | **App móvil (PWA)** | Versión mobile-first del panel Fer para usarlo desde el taller sin PC |
| P12 | **Cámara de control de calidad** | Foto de cada pieza terminada vinculada al registro de fabricación |

---

## 7. Cómo colabora Mike con tu día a día — Flujo sugerido

### Mañana al arrancar el taller

```
1. Abrís el sistema en el navegador
2. Ves el sidebar → Mike ya procesó las alertas de la noche
3. Entrás a 🛠️ Mi Panel → ves los pedidos urgentes del día
4. Click en "📋 Prioridades de hoy" en el tab Mike
   → Mike te da el orden exacto de qué fabricar primero
5. Arrancás con el primer pedido
```

### Antes de cada fabricación

```
1. Laminás el modelo en Bambu Studio
2. En 📦 Cargar Fabricación: arrastrás el .3mf al uploader
   → gramos, tiempo y material se llenan automáticamente
3. Seleccionás el pedido asociado (o "Sin pedido")
4. Registrás el resultado al terminar
5. El sistema descuenta el material del stock automáticamente
```

### Cuando comprás material

```
1. Tab 🧵 Materiales → expandís el material que compraste
2. Ponés gramos comprados + precio pagado
3. Click "Registrar compra"
   → Stock actualizado + costo/kg recalculado con promedio ponderado
4. Mike actualiza sus proyecciones de días de stock
```

### Cuando pasa algo raro (fallo, problema con la impresora)

```
1. Tab 🤖 Mike → chat libre
2. Describís el problema en tus palabras
3. Mike analiza el historial de ese material/SKU y te da causas probables
4. Si el fallo se repite → Mike genera una alerta automática de "tasa alta"
```

---

## 8. Arquitectura técnica — Para referencia

```
Internet (Streamlit Cloud)
    │
    ▼
main.py ─────────────────────────────────────────────────────
    │                                                        │
    ├── crear_schema_v3.py    (inicializa la DB al arrancar)  │
    ├── slicer_parser.py      (lee .gcode / .3mf)            │
    └── ep_agente.py ─────────────────────────────────────── │
            │                                                │
            ├── get_alertas_dashboard()   (cada 2 min)      │
            └── analizar_patrones()       (diario 20hs)     │
                                                            │
agent_core.py ─── context_elpasaje.py ─── Claude API        │
    │                    │                                   │
    └── preguntar_mike() └── get_data_context()             │
                                    │                        │
                              elpasaje_v2.db ────────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    ▼                                ▼
              orders / order_items          materials / production_log
              products / tenants            stock_movements / log_agente
              tenant_lineas                 senales_mercado
```

**Backup automático diario (20hs):**
- GitHub (repositorio privado)
- Google Drive (si está montado)
- Disco externo E: (si está conectado)

---

## 9. Preguntas frecuentes

**¿El sistema funciona sin internet?**
No. Está en la nube (Streamlit Cloud). Necesitás conexión para usarlo.

**¿Se puede usar desde el celular?**
Sí, desde el navegador del celular. No está optimizado para móvil todavía (P11 en el roadmap).

**¿Qué pasa si se va la luz mientras registrás una fabricación?**
Si no hiciste click en "Registrar Fabricación", no se guarda nada. Si ya lo guardaste, está en la base de datos y no se pierde.

**¿Mike tiene memoria entre sesiones?**
El chat de Mike se reinicia cuando cerrás sesión. Las alertas y el análisis de patrones se guardan en `log_agente` en la DB y persisten.

**¿Puedo usar Mike desde otro panel (no solo el de Fer)?**
Hoy solo está en el panel de producción. Próximamente estará disponible en el panel de Alejandra también.

---

## 10. Contacto y soporte

| Consulta | Canal |
|---|---|
| Bug en el sistema / algo no funciona | WhatsApp Alejandra |
| Preguntas sobre cómo usar algo | Tab Mike (él conoce el sistema) |
| Propuesta de mejora | Decírsela a Alejandra en persona |

---

*Reporte generado con asistencia de Mike · El Pasaje 3D Studio · Mayo 2026*

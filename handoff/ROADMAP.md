# Roadmap — El Pasaje 3D Studio
## EPCC v2 · Sistema v3.0 · Mayo 2026

---

## Estado actual: Fases 1–4 completadas

### ✅ Fase 1 — Cimientos (EPCC v2 Core)
*Estado: Completa*

- Auth multi-rol (admin / produccion / socio / socio_multi)
- Schema DB v3 con 13 tablas base
- Dashboard Alejandra con métricas y alertas
- Panel socios básico (Mi Panel + Cargar Pedido)
- Agente Mike nocturno (ep_agente.py) con email
- Seguridad: SHA-256 passwords, SQL parameterizado, aislamiento por client_id
- Backup multi-destino (GitHub + Drive + disco)

---

### ✅ Fase 2 — Inteligencia Mike
*Estado: Completa*

- `modules/panel_mike.py` — 5 secciones de análisis ecosistema
- Sección A: Estado del ecosistema (pedidos demorados, líneas inactivas, materiales críticos)
- Sección B: Alertas activas con niveles (critico / atencion / info)
- Sección C: Top 5 productos últimos 30 días
- Sección D: Señales de mercado con filtro por tipo
- Sección E: Historial de precios con delta visual
- Explicaciones de analytics en acordeón ℹ️ por sección
- Tab Mike embebido en dashboard admin (`dashboard_admin.py`)
- Alertas Mike en sidebar (mini-resumen con conteo por nivel)

---

### ✅ Fase 3 — Centro de Producción Fernando
*Estado: Completa*

- `modules/panel_fer.py` — 7 tabs completos
- Cola Inteligente: cards con indicador 🟢/🔴 por material, badges IP 🔒 y archivo 📁
- Botones de acción mobile-first (▶ Iniciar / ✅ Listo)
- Cargar Fabricación: 4 campos simplificados + importación desde slicer (.gcode/.3mf)
- Materiales: stock + consumo mensual + días estimados + registrar compra
- Mi Panel: 4 KPIs + cola activa + "Materiales para esta semana"
- Tab Archivos: repositorio BLOB de .gcode/.3mf/.stl por SKU
- Integración con slicer_parser.py (Bambu Studio, PrusaSlicer, Cura)
- Privacidad: Fernando ve línea, nunca cliente final ni precios
- Migración v6: tabla `archivos_produccion`

---

### ✅ Fase 4 — Canales y Conversión (EPCC v2 Fase 4)
*Estado: Completa*

- `utils/whatsapp.py` — generador de deep links wa.me por número de línea
- `modules/panel_socio.py` — 8 tabs completos:
  - **Mi Tienda**: catálogo con botones WA por producto, badges IP, validación de número configurado
  - **Presupuestador**: Paso 1 (armar presupuesto) → Paso 2 (texto copyable + link WA)
  - **Pedidos**: historial con badge de estado de pago (💳 pendiente / ✅ acreditado / ↩️ devuelto)
  - **Mi Línea (⚙️)**: configuración de número WhatsApp
- `modules/cargar_pedido.py` — método de pago integrado + registro en tabla `pagos`
- Miniaturas de productos en cards (socios) y cola (Fer)
- Migración v5: tabla `pagos`
- Migración v5b: tabla `lineas_config` con seed de 11 líneas

---

## Pendiente — Fase 5: Pagos y automatización

**Prioridad: Alta**

- [ ] **MercadoPago checkout real** — hoy está como "próximamente". Requiere cuenta vendedor MP y credenciales API.
  - Webhook de confirmación → UPDATE pagos SET estado='acreditado'
  - QR / link de pago generado al confirmar pedido

- [ ] **Acreditación de pagos desde el admin** — Alejandra marca pedidos como acreditados desde el dashboard sin ir directo a la DB.

- [ ] **Notificaciones WhatsApp automáticas** — Cuando un pedido cambia a "Listo", enviar mensaje WA al número del socio.
  - Requiere: WhatsApp Business API o Twilio

- [ ] **Upload de imágenes de productos** — Alejandra sube fotos desde el admin, se guardan en Cloudinary/Drive y se actualiza `imagen_url` en products.
  - Actualmente: `imagen_url` soporta URLs externas pero no hay UI de upload.

---

## Pendiente — Fase 6: Escala y externos

**Prioridad: Media**

- [ ] **Portal cliente externo** — Clientes finales (no socios) pueden ver el estado de su pedido con un link único. Sin login completo.

- [ ] **B2B bulk orders** — Formulario especial para pedidos de múltiples items a la vez (ej: Nando pide 20 unidades de 5 productos distintos).

- [ ] **Catálogo público** — Una vista de solo lectura del catálogo de cada línea, accesible sin login, compartible por link.

- [ ] **SMS / Push notifications** — Alertas a Alejandra cuando hay pedidos demorados o stock crítico, sin tener que abrir la app.

---

## Deuda técnica

| Item | Impacto | Esfuerzo |
|------|---------|---------|
| `_tenant_map` cargado en panel_fer.py pero no usado | Bajo | 1 línea |
| `LINEAS` dict en utils/lineas.py no incluye `fer_produccion` (está solo en migration_v5b) | Bajo | Agregar entrada al dict |
| `migration_v5.py` puede imprimir `[SKIP]` engañoso si la tabla no existe | Bajo | Ajustar mensaje de error |
| Imágenes en `cargar_pedido.py` usan `<img>` en HTML pero Streamlit puede bloquear XSS | Medio | Migrar a `st.image()` |
| `CONTEXTO_PROYECTO.md` desactualizado (referencia main.py como v2.6) | Bajo | Actualizar versión y tablas |
| Los archivos `.py` de raíz tienen ~30 scripts de migración/utilidad sin documentar | Bajo | Agregar README en raíz |

---

## Decisiones de arquitectura tomadas (y por qué)

| Decisión | Alternativa considerada | Por qué se eligió |
|----------|------------------------|-------------------|
| SQLite como DB | PostgreSQL / Supabase | Sin servidor, sin costo, suficiente para el volumen actual. Si escala, migrar a Postgres es directo con SQLAlchemy. |
| Archivos como BLOB en SQLite | Filesystem local / S3 | Evita dependencias externas para una feature nueva. Si Streamlit Cloud redeploya, el filesystem se pierde — el BLOB sobrevive. |
| Imágenes como URL externa | BLOB / base64 | Mantiene la DB liviana. Las URLs son de CDN externo (Cloudinary, Drive). |
| LINEAS dict + lineas_config DB | Solo DB | El dict es fallback de UI rápido; la DB es la fuente de verdad mutable. Evita migración si no se tiene la tabla. |
| Migraciones como scripts independientes | Alembic | Más simple para un equipo de 1 persona. Alembic agrega overhead sin beneficio real a esta escala. |
| Multi-rol en una sola app (main.py) | Apps separadas por rol | Simplifica deploy y mantenimiento. El aislamiento se hace vía session_state role + WHERE client_id. |

---

## Historial de versiones

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| v1.0 | Ene 2026 | Primera versión monolítica (`elpasaje_v1.py`) |
| v2.0 | Feb 2026 | Refactor a arquitectura modular (`main.py` + `modules/`) |
| v2.6 | Abr 2026 | Fix SQL injection, segmentación tenants, agente Mike reconectado |
| v3.0 | May 2026 | EPCC v2 Fases 1-4 completas: Mike panel, Fer centro completo, canales WA, pagos, archivos |

---

*El Pasaje 3D Studio · Roadmap v3.0 · Mayo 2026*

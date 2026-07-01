# AUDITORÍA ECOSISTEMA — El Pasaje 3D Studio
**Fecha:** 2026-07-01  
**Modelo:** Claude Sonnet 4.6 (loop autónomo v1)  
**Repo:** silac1981/elpasaje-app  

---

## SEMÁFORO GENERAL

| Área | Estado | Detalle |
|------|--------|---------|
| Código / Modularización | 🟢 | Bien estructurado |
| Base de datos / Schema | 🟡 | Schema OK, datos operativos vacíos |
| **Seguridad** | **🔴** | **CRÍTICO: Fer ve finanzas + credenciales hardcodeadas** |
| Web pública | 🟡 | 3/7 páginas con catálogo dinámico; exports/ vacía |
| Mike / Agente | 🟡 | Conectado, credenciales expuestas |
| Deploy | 🟡 | No hay secrets.toml; en Streamlit Cloud = crash |

---

## ÁREA 1 — CÓDIGO / MODULARIZACIÓN 🟢

**main.py:** Router limpio (25KB). Maneja auth, sidebar, routing por rol. No monolítico.

**modules/** (existentes):
- `dashboard_admin.py` — 46KB
- `panel_fer.py` — 71KB ← VER SECCIÓN SEGURIDAD
- `panel_mike.py` — 15KB
- `panel_socio.py` — 124KB
- `panel_socios.py` — 8KB
- `clientes.py`, `inventario.py`, `cargar_pedido.py`, `impacto.py`

**utils/** (existentes):
- `db.py` — SQLAlchemy engine con os.path.abspath ✅
- `lineas.py` — constantes + helpers (LINEAS dict duplica lineas_config de DB)
- `pricing.py` — fórmula Ale: costo=(gr×1.10×$2350)/1000; precio=costo×4 ✅
- `exports.py` — generador JSON catálogo por línea ✅
- `mike.py` — wrapper para ep_agente + chat Anthropic ✅
- `whatsapp.py` — templates WhatsApp ✅

**Observación:** LINEAS dict en utils/lineas.py es una duplicación de lineas_config en DB. No es crítico (ambos sincronizados), pero lineas_config tiene más campos (whatsapp_numero, fin_solidario).

---

## ÁREA 2 — BASE DE DATOS 🟡

**Archivo:** `elpasaje_v2.db` (180KB activo + WAL)  
**Última migración:** v11 (agrega `precio_socio` a products)

| Tabla | Filas | Estado |
|-------|-------|--------|
| lineas_config | 11 | 🟢 Poblada (10 líneas + admin) |
| products | 100 | 🟢 Distribuidos por línea |
| materials | 41 | 🟡 Stock seed (25kg por material, no real) |
| tenants | 11 | 🟢 Todos los usuarios cargados |
| orders | 3 | 🟡 Solo datos de prueba |
| order_items | 6 | 🟡 Solo datos de prueba |
| pagos | 5 | 🟡 Solo datos de prueba |
| price_history | 4 | 🔴 No se pobla automáticamente en cambios |
| stock_movements | 0 | 🔴 Sistema de movimientos sin uso |
| production_log | 0 | 🔴 Fabricaciones no registradas |
| senales_mercado | 0 | 🔴 Sin señales cargadas |
| tenant_lineas | 4 | 🟢 Relaciones multi-línea OK |
| kit_components | 0 | 🟡 Sin kits configurados |
| donations | 0 | 🟡 Fin solidario sin datos |

**Productos por línea:**
- admin: 17 | aviation: 13 | oasis_del_estero: 15 | oasis_animal: 10
- francisco_sport: 10 | vkhome_cliente: 9 | olivia_coquette: 7
- fer_produccion: 7 | constantino_tech: 6 | pharma_delux: 6

**IP Restringida en DB:** ✅ NINGÚN producto con keywords IP (deadpool, marshall, hello kitty, pokeball, ferrari, baby yoda). Safe.

---

## ÁREA 3 — SEGURIDAD 🔴 CRÍTICO

### 🔴 CRÍTICO-1: Fer ve Finanzas (Regla Inmutable violada)
**Archivo:** `modules/panel_fer.py`, línea 63 + línea 821-938  
**Tab visible para Fer:** `"💹 Finanzas CFO"`  
**Lo que ve:** márgenes por producto, costo de materiales, costos de producción, ganancias brutas, cuota socios, overhead — TODO lo que Fer no debe ver bajo ninguna circunstancia.  
**Acción requerida:** ELIMINAR tab_stats del panel_fer. Pasar ese contenido al dashboard_admin.

### 🔴 CRÍTICO-2: Credenciales Gmail hardcodeadas en repo público
**Archivo:** `ep_agente.py`, líneas 34-37  
**Expuesto:** `app_password: "[REDACTADO]"` + email origen  
**Riesgo:** Las credenciales están en el repo GitHub (silac1981/elpasaje-app). Cualquiera puede verlas.  
**Acción requerida:** Mover a `.streamlit/secrets.toml` + env var fallback.

### 🔴 CRÍTICO-3: No existe .streamlit/secrets.toml
**Consecuencia en Streamlit Cloud:** la app crashea si utils/mike.py (preguntar_mike) intenta leer Anthropic API key desde env sin configurar.  
**Acción requerida:** Crear secrets.toml con template + documentar en README.

---

## ÁREA 4 — WEB PÚBLICA 🟡

| Página | Catálogo dinámico | Fotos propias | WhatsApp by product |
|--------|------------------|--------------|--------------------|
| magnitud19.html | ✅ exports/magnitud19-catalog.json | 🟡 Parcial | ❌ |
| melomano.html | ✅ exports/melomano-catalog.json | 🟡 Parcial | ❌ |
| coquette.html | ✅ exports/coquette-catalog.json | 🟡 Parcial | ❌ |
| sport.html | ❌ Sin carga dinámica | ❌ | ❌ |
| oasis-animal.html | ❌ Sin carga dinámica | 🟡 Tiene fotos | ❌ |
| oasis-estero.html | ❌ Sin carga dinámica | 🟡 Parcial | ❌ |
| aero-tech.html | ❌ Sin carga dinámica | ❌ | ❌ |
| core-tech.html | ❌ Sin carga dinámica | ❌ | ❌ |
| pharma-delux.html | ❌ Sin carga dinámica | ❌ | ❌ |
| index.html (hub) | ❌ Estático | 🟢 Rediseñado | ❌ |

**exports/ folder:** NO EXISTE → Los JSON no se han generado todavía.

---

## ÁREA 5 — MIKE / AGENTE 🟡

- `ep_agente.py`: Agente autónomo completo (análisis, alertas, email diario 20hs) ✅
- `utils/mike.py`: Wrapper conectado al dashboard ✅  
- `preguntar_mike()`: Chat multi-turn con contexto contextual ✅
- `panel_mike.py`: Panel dedicado ✅
- **Problema:** Credenciales hardcodeadas (ver Seguridad CRÍTICO-2)
- **Problema:** Anthropic client creado sin API key explícita → depende de env var ANTHROPIC_API_KEY no configurada en secrets.toml

---

## ÁREA 6 — DEPLOY 🟡

- `requirements.txt`: ✅ LIMPIO (sin sqlite3, sin conflictos)
- `utils/db.py`: ✅ DB_PATH con os.path.abspath correcto
- `.streamlit/secrets.toml`: ❌ NO EXISTE
- `config.toml`: ✅ Existe (theme config)
- Último commit en main: `be20490` (2026-06-18)

---

## ORDEN DE CICLOS (según semáforo)

1. **CICLO 1 → SEGURIDAD** (🔴x3): Eliminar tab Finanzas de Fer + mover credenciales a secrets.toml
2. **CICLO 2 → EXPORTS + WEB**: Crear carpeta exports/, generar JSONs, extender catálogo dinámico a sport/oasis-animal/oasis-estero
3. **CICLO 3 → STOCK + PRODUCTION LOG**: Activar stock_movements y production_log en flujo Fer
4. **CICLO 4 → PRICE HISTORY**: Auto-poblar price_history en cada cambio de precio
5. **CICLO 5 → MIKE DASHBOARD**: Tab Mike consolidado en admin con alertas inteligentes

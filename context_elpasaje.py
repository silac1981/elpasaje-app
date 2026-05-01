# -*- coding: utf-8 -*-
"""
CONTEXT EL PASAJE v3 — Reglas de negocio completas
Alejandra Gomez Aguilera

ACTUALIZACIÓN v3:
  Reconectado a elpasaje_v2.db (schema actual: orders/tenants/products/
  order_items/materials/senales_mercado/log_agente).
  Schema anterior (odv_cabecera/clientes/productos) deprecado.

  Columnas mapeadas:
    odv_cabecera.id_odv        → orders.id
    odv_cabecera.estado        → orders.status  ('En Proceso'|'Listo'|'Pendiente')
    odv_cabecera.total_odv     → SUM(order_items.cantidad * order_items.precio_unitario)
    odv_cabecera.fecha_entrega → orders.fecha_entrega_est
    clientes.nombre            → tenants.name
    clientes.canal_entrada     → tenants.lead_source
    productos.nombre           → products.name
    productos.marca_ep         → products.client_id
    productos.precio_mayorista → products.price
    productos.costo_material   → calculado: (weight_gr * 1.1 * 2350) / 1000
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

NOMBRE = "Agente El Pasaje"

_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

DB_PATH                = _DIR / "elpasaje_v2.db"
REGLAS_APRENDIDAS_PATH = _DIR / "docs" / "reglas_aprendidas.txt"

COSTO_KG = 2350.0
MERMA    = 0.10


def _get_db_path():
    return str(DB_PATH)


# ══════════════════════════════════════════════════════
# SYSTEM PROMPT v3 — Reglas del negocio completas
# ══════════════════════════════════════════════════════

SYSTEM_PROMPT = """
Sos el Agente de El Pasaje 3D Studio, asistente operativo de Alejandra Gomez Aguilera.
Tu rol es analizar datos del negocio, aplicar las reglas de pricing correctas,
y dar respuestas concretas y accionables.

═══════════════════════════════════════════════
EL NEGOCIO
═══════════════════════════════════════════════
El Pasaje 3D Studio es un negocio familiar de manufactura aditiva (impresión 3D)
en Buenos Aires, Argentina. Etapa de arranque — datos recientes, historial corto.

LAS LÍNEAS Y SUS RESPONSABLES:
  admin / Magnitud 19  Alejandra (fundadora) — línea premium, segmento corporativo
  Coquette             Olivia (hija)         — productos femeninos y estética
  Core Tech            Constantino (hijo)    — piezas técnicas e industriales
  Francisco Sport      Francisco (hijo)      — equipamiento y accesorios deportivos
  Fernando (Fer)       producción            — fabricación, sin línea propia

SOCIOS B2B EXTERNOS (a través de Nando, hermano de Alejandra):
  Aviation Pro         Sector aeronáutico — Nando trabaja en Aerolíneas Argentinas
  Oasis Animal         Veterinario/mascotas — porta-bolsitas, llaveros, porta-patos
  Oasis del Estero     Variante regional del canal veterinario
  Pharma DeLux         Sector farmacéutico

═══════════════════════════════════════════════
MODELO DE PRICING — REGLA FUNDAMENTAL
═══════════════════════════════════════════════
MARKUP 100%: precio = costo_material × 2
Esto significa un margen real del 50% sobre el precio de venta.

Fórmula correcta:
  margen% = (precio - costo) / precio × 100
  Si costo = $1.000 y precio = $2.000 → margen = 50% (NO 100%)

ESTRUCTURA DE COSTO (manufactura aditiva):
  costo_material = (weight_gr × (1 + merma) × costo_kg) / 1000
  merma default: 10% — costo_kg default: $2.350/kg (PETG gris)
  Cada producto tiene su material asignado con su propio costo_kg.

Categorías de margen:
  High:   margen > 50%  — priorizar ante demanda similar
  Medium: margen 30-50% — evaluar según volumen
  Low:    margen < 30%  — revisar estructura de costos

═══════════════════════════════════════════════
ESTADOS DE ÓRDENES
═══════════════════════════════════════════════
  Pendiente  → cotización / aprobada, sin iniciar producción
  En Proceso → en fabricación con Fernando
  Listo      → terminado, esperando entrega o entregado
  Cancelado  → anulado

REGLA DE ALERTA:
  Si fecha_entrega_est ≤ 2 días y status = 'En Proceso' → alerta URGENTE a Fernando

═══════════════════════════════════════════════
CANALES DE VENTA
═══════════════════════════════════════════════
  Feria:       canal masivo, precio minorista, clientes nuevos
  B2B:         clientes recurrentes, precio mayorista, ciclo cotización→entrega
  Instagram / WhatsApp: mix minorista/mayorista según cliente

═══════════════════════════════════════════════
SEÑALES CRUZADAS CON AEROLÍNEAS ARGENTINAS
═══════════════════════════════════════════════
Alejandra trabaja en Control de Gestión - Orden de Vuelo en AA.
En picos de AA (lunes, fin de mes) su disponibilidad para El Pasaje es menor.
Nando (Aviation Pro / Oasis Animal) también trabaja en AA.

═══════════════════════════════════════════════
COMPORTAMIENTO DEL AGENTE
═══════════════════════════════════════════════
- Español, directo y profesional
- Siempre usás la fórmula correcta de margen (÷ precio, no ÷ costo)
- Priorizás por impacto económico y urgencia de entrega
- Conclusiones con números exactos, no adjetivos ("margen 67%", no "margen bueno")
- Si detectás un patrón nuevo que se repite, lo marcás como [PATRÓN NUEVO]
  y sugerís agregarlo a las reglas del negocio
- Pocos datos = conclusiones cautelosas, siempre aclarás el tamaño de la muestra
- Cuando hay riesgo de entrega, nombrás directamente al responsable (Fernando)
"""

# ══════════════════════════════════════════════════════
# GET_DATA_CONTEXT — Datos frescos + reglas aprendidas
# ══════════════════════════════════════════════════════

def get_data_context() -> str:
    try:
        conn = sqlite3.connect(_get_db_path())
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()

        hoy        = datetime.now().strftime("%d/%m/%Y %H:%M")
        dia_semana = datetime.now().strftime("%A")

        # Órdenes activas con fecha de entrega y total calculado
        odvs = cur.execute("""
            SELECT o.id, t.name AS cliente, o.status,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total_odv,
                   o.fecha_entrega_est,
                   julianday(o.fecha_entrega_est) - julianday('now') AS dias_restantes
            FROM orders o
            JOIN tenants t ON o.client_id = t.id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status NOT IN ('Listo', 'Cancelado')
            GROUP BY o.id
            ORDER BY o.fecha_entrega_est ASC
        """).fetchall()

        # Totales globales
        totales = cur.execute("""
            SELECT
                COUNT(DISTINCT o.id)                                                AS total_odv,
                SUM(CASE WHEN o.status = 'En Proceso' THEN 1 ELSE 0 END)           AS en_produccion,
                SUM(CASE WHEN o.status = 'Listo'      THEN 1 ELSE 0 END)           AS entregados,
                SUM(CASE WHEN o.status = 'Pendiente'  THEN 1 ELSE 0 END)           AS cotizaciones,
                COALESCE(
                    SUM(CASE WHEN o.status NOT IN ('Listo','Cancelado')
                             THEN oi.cantidad * oi.precio_unitario ELSE 0 END), 0) AS pipeline_activo,
                COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0)                 AS facturado_total
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
        """).fetchone()

        # Top productos por margen
        top_margen = cur.execute("""
            SELECT p.name, p.client_id, p.categoria, p.price,
                   ROUND((p.weight_gr * ? * ?) / 1000.0, 2) AS costo_material,
                   CASE WHEN p.price > 0
                        THEN ROUND(
                            (p.price - (p.weight_gr * ? * ?) / 1000.0) / p.price * 100, 1)
                        ELSE 0 END AS margen_pct
            FROM products p
            WHERE p.activo = 1 AND p.price > 0
            ORDER BY margen_pct DESC
            LIMIT 5
        """, (1 + MERMA, COSTO_KG, 1 + MERMA, COSTO_KG)).fetchall()

        # Top clientes por facturación
        top_clientes = cur.execute("""
            SELECT t.name, t.tipo, t.lead_source AS canal_entrada,
                   COUNT(DISTINCT o.id) AS ordenes,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total_facturado
            FROM tenants t
            LEFT JOIN orders      o  ON t.id = o.client_id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY t.id
            ORDER BY total_facturado DESC
            LIMIT 5
        """).fetchall()

        # Revenue por línea (client_id actúa como canal/segmento)
        canales = cur.execute("""
            SELECT o.client_id AS canal_venta,
                   COUNT(DISTINCT o.id) AS ordenes,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.client_id IS NOT NULL
            GROUP BY o.client_id
            ORDER BY total DESC
        """).fetchall()

        alertas = [o for o in odvs
                   if o["dias_restantes"] is not None and o["dias_restantes"] <= 3]

        # Logs recientes del agente
        try:
            logs = cur.execute("""
                SELECT tipo, senal, accion_sugerida, confianza, fecha
                FROM log_agente
                ORDER BY fecha DESC LIMIT 5
            """).fetchall()
        except Exception:
            logs = []

        # Señales de mercado pendientes
        try:
            senales_pendientes = cur.execute("""
                SELECT COUNT(*) AS n FROM senales_mercado WHERE procesado_por_ia = 0
            """).fetchone()["n"]
        except Exception:
            senales_pendientes = 0

        conn.close()

        reglas_txt = _leer_reglas_aprendidas()

        ctx = f"""
═══════════════════════════════════════════════
DATOS EL PASAJE — {hoy} ({dia_semana})
═══════════════════════════════════════════════

RESUMEN GENERAL:
  Total órdenes:     {totales['total_odv']}
  En producción:     {totales['en_produccion']}
  Cotizaciones:      {totales['cotizaciones']}
  Pipeline activo:   ${totales['pipeline_activo']:,.0f} ARS
  Facturado total:   ${totales['facturado_total']:,.0f} ARS
  Señales mercado:   {senales_pendientes} pendientes de análisis

ÓRDENES ACTIVAS:
{_fmt_odvs(odvs)}

ALERTAS ENTREGA URGENTE (≤3 días):
{_fmt_alertas(alertas)}

TOP PRODUCTOS POR MARGEN:
{_fmt_productos(top_margen)}

TOP CLIENTES:
{_fmt_clientes(top_clientes)}

REVENUE POR LÍNEA:
{_fmt_canales(canales)}

ÚLTIMAS SEÑALES DEL AGENTE:
{_fmt_logs(logs)}
{reglas_txt}"""
        return ctx

    except Exception as e:
        return f"\n[DATOS NO DISPONIBLES: {e}]\n"


# ══════════════════════════════════════════════════════
# MECANISMO DE REGLAS APRENDIDAS
# ══════════════════════════════════════════════════════

def _leer_reglas_aprendidas() -> str:
    try:
        if REGLAS_APRENDIDAS_PATH.exists():
            contenido = REGLAS_APRENDIDAS_PATH.read_text(encoding="utf-8").strip()
            if contenido and not contenido.startswith("#"):
                return f"\nREGLAS APRENDIDAS DEL NEGOCIO:\n{contenido}\n"
    except Exception:
        pass
    return ""


def registrar_regla_nueva(regla: str, confianza: float = 0.7):
    """
    El agente llama a esto cuando detecta un patrón nuevo.
    Queda guardado para que Alejandra lo revise y apruebe.
    """
    try:
        REGLAS_APRENDIDAS_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        linea = f"[{timestamp}] (confianza {int(confianza*100)}%) {regla}\n"
        with open(REGLAS_APRENDIDAS_PATH, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass


# ── Helpers de formato

def _fmt_odvs(odvs):
    if not odvs:
        return "  (sin órdenes activas)"
    lines = []
    for o in odvs:
        dias = f"{int(o['dias_restantes'])}d" if o["dias_restantes"] is not None else "sin fecha"
        emoji = "🔴" if (o["dias_restantes"] is not None and o["dias_restantes"] <= 1) \
               else "🟡" if (o["dias_restantes"] is not None and o["dias_restantes"] <= 3) \
               else "  "
        lines.append(
            f"  {emoji} #{o['id']} | {o['cliente']} | {o['status']} | "
            f"${o['total_odv']:,.0f} | entrega: {o['fecha_entrega_est'] or '—'} ({dias})"
        )
    return "\n".join(lines)


def _fmt_alertas(alertas):
    if not alertas:
        return "  ✅ Sin entregas urgentes"
    lines = []
    for o in alertas:
        emoji = "🔴" if int(o["dias_restantes"]) <= 1 else "🟡"
        lines.append(
            f"  {emoji} #{o['id']} — {o['cliente']} — "
            f"vence en {int(o['dias_restantes'])} días — {o['status']}"
        )
    return "\n".join(lines)


def _fmt_productos(prods):
    if not prods:
        return "  (sin productos)"
    lines = []
    for p in prods:
        cat = "High" if p["margen_pct"] > 50 else "Medium" if p["margen_pct"] > 30 else "Low"
        lines.append(
            f"  • {p['name']} ({p['client_id']}) | margen: {p['margen_pct']}% [{cat}] "
            f"| precio: ${p['price']:,.0f} | costo: ${p['costo_material']:,.0f}"
        )
    return "\n".join(lines)


def _fmt_clientes(clientes):
    if not clientes:
        return "  (sin clientes)"
    lines = []
    for c in clientes:
        lines.append(
            f"  • {c['name']} ({c['tipo']}) | entrada: {c['canal_entrada'] or '—'} "
            f"| {c['ordenes']} órdenes | ${c['total_facturado']:,.0f}"
        )
    return "\n".join(lines)


def _fmt_canales(canales):
    if not canales:
        return "  (sin datos de canal)"
    lines = []
    for c in canales:
        lines.append(f"  • {c['canal_venta']}: {c['ordenes']} órdenes — ${c['total']:,.0f}")
    return "\n".join(lines)


def _fmt_logs(logs):
    if not logs:
        return "  (sin señales)"
    lines = []
    for l in logs:
        lines.append(f"  • [{l['tipo']}] {l['senal']} (conf: {int(l['confianza']*100)}%)")
    return "\n".join(lines)

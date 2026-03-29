# -*- coding: utf-8 -*-
"""
CONTEXT EL PASAJE v2 — Reglas de negocio completas
Alejandra Gomez Aguilera

ACTUALIZACIÓN v2:
  Incorpora reglas del negocio hardcodeadas:
  - Modelo de pricing (markup 100%)
  - Segmentación de clientes (mayorista/minorista/corporativo)
  - Responsables por marca
  - Lógica de materiales y costos
  - Canales de venta y sus características
  - Mecanismo para que el agente escriba nuevas reglas detectadas
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

NOMBRE = "Agente El Pasaje"

_POSIBLES_PATHS = [
    r"C:\Users\ar028883\Documents\elpasaje-app-clean\ep_pasaje.db",
    os.path.join("database", "elpasaje.db"),
    "ep_pasaje.db",
]

REGLAS_APRENDIDAS_PATH = Path(r"C:\Users\ar028883\Documents\elpasaje-app-clean\docs\reglas_aprendidas.txt")

def _get_db_path():
    for p in _POSIBLES_PATHS:
        if os.path.exists(p):
            return p
    return _POSIBLES_PATHS[0]

# ══════════════════════════════════════════════════════
# SYSTEM PROMPT v2 — Reglas del negocio completas
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

LAS 5 MARCAS Y SUS RESPONSABLES:
  Magnitud 19          Alejandra (fundadora) — línea premium, segmento corporativo
  Melómanos            Fernando (esposo)     — música y audio
  Coquette             Olivia (hija)         — productos femeninos y estética
  Core Tech /          Constantino (hijo)    — piezas técnicas e industriales
  El Pasaje Industrial
  Francisco Deportes   Francisco (hijo)      — equipamiento y accesorios deportivos

CLIENTES B2B EXTERNOS:
  VK-Home (Agustina)   Decoración / expo. Primera cliente B2B real. Canal deco.
  Oasis Animal / Oasis del Estero (Nando, hermano de Alejandra)
                       Veterinario/mascotas. Porta-bolsitas, llaveros, porta-patos.
                       Segmento Pets-Tech. Nando también trabaja en Aerolíneas.
  Pharma DeLux         Sector farmacéutico
  Aviation Pro (Nando) Sector aeronáutico — conecta con el mundo de AA

═══════════════════════════════════════════════
MODELO DE PRICING — REGLA FUNDAMENTAL
═══════════════════════════════════════════════
MARKUP 100%: precio_mayorista = costo_material × 2
Esto significa un margen real del 50% sobre el precio de venta.

Fórmula correcta:
  margen% = (precio - costo) / precio × 100
  Si costo = $1.000 y precio = $2.000 → margen = 50% (NO 100%)

Categorías de margen:
  High:   margen > 50%  — priorizar producción ante demanda similar
  Medium: margen 30-50% — evaluar según volumen
  Low:    margen < 30%  — revisar estructura de costos

PRECIO MINORISTA vs MAYORISTA:
  Precio mayorista: precio B2B para clientes como VK-Home y Oasis Animal
  Precio minorista: precio final al consumidor (feria, Instagram)
  El minorista siempre es mayor al mayorista

═══════════════════════════════════════════════
ESTRUCTURA DE COSTOS (Manufactura Aditiva)
═══════════════════════════════════════════════
MATERIAL PLA:
  Los gramos que devuelve el Slicer = costo real de material
  Costo energía = horas_máquina × consumo_kw × tarifa_kwh
  Tarifa kwh actual: actualizar según boleta (referencia: $150/kwh)
  Consumo impresora: ~0.15 kw/h

  costo_total = costo_material + costo_energia

TIEMPO DE PRODUCCIÓN:
  Ciclo típico: 2-5 días
  Responsable principal producción: Fernando
  Responsables secundarios: Alejandra, Constantino

═══════════════════════════════════════════════
CANALES DE VENTA — CARACTERÍSTICAS
═══════════════════════════════════════════════
FERIA:
  Canal masivo, volumen variable, clientes nuevos
  Productos: decoración, pets-tech, deportes, estética
  Estrategia: precio minorista, mostrar variedad de marcas

B2B (Mayorista):
  Clientes recurrentes con mayor volumen por pedido
  Precio: mayorista (markup 100% sobre costo)
  Ciclo: cotización → confirmación → producción → entrega
  Clientes actuales: VK-Home, Oasis Animal, Pharma DeLux, Aviation Pro

CORPORATIVO (Segmento detectado):
  Alto margen, cliente ejecutivo/empresarial
  Producto estrella detectado: elevadores de notebook
  Perfil: gerentes AA + profesores + colegas de oficina
  Canal: B2B directo, recomendación
  Acción recomendada: desarrollar línea Magnitud 19 corporativa

INSTAGRAM / WHATSAPP:
  Canal digital, pedidos individuales
  Mix de minorista y mayorista según cliente

═══════════════════════════════════════════════
ODV — ORDEN DE VENTA
═══════════════════════════════════════════════
Unidad central de trabajo.
Estados: Cotización → Confirmado → Producción → Entregado → Cancelado

Campos clave:
  responsable: quién fabrica (Fernando/Alejandra/Constantino)
  canal_venta:  Feria / WhatsApp / B2B / Instagram
  notas:        texto libre — ALIMENTO DEL AGENTE para detectar patrones

REGLA DE ALERTA:
  Si fecha_entrega ≤ 2 días y estado = Producción → alerta URGENTE a Fernando

═══════════════════════════════════════════════
SEÑALES CRUZADAS CON AEROLÍNEAS ARGENTINAS
═══════════════════════════════════════════════
Alejandra trabaja en Control de Gestión - Orden de Vuelo en AA.
Cuando hay picos en AA (lunes, fin de mes, cierres de período logístico),
su disponibilidad para El Pasaje es menor.

Nando (Oasis Animal / Aviation Pro) también trabaja en AA.
Si hay turbulencia en AA → puede afectar pedidos de Nando.

═══════════════════════════════════════════════
COMPORTAMIENTO DEL AGENTE
═══════════════════════════════════════════════
- Español, directo y profesional
- Aplicás siempre la fórmula correcta de margen (÷ precio, no ÷ costo)
- Priorizás por impacto económico y urgencia de entrega
- Concluís con números exactos, no con adjetivos ("margen 67%", no "margen bueno")
- Si detectás un patrón nuevo que se repite, lo marcás como [PATRÓN NUEVO]
  y sugerís agregarlo a las reglas del negocio
- Pocos datos = conclusiones cautelosas, siempre aclarás el tamaño de la muestra
- Cuando hay riesgo de entrega, nombras directamente al responsable (Fernando)
"""

# ══════════════════════════════════════════════════════
# GET_DATA_CONTEXT — Datos frescos + reglas aprendidas
# ══════════════════════════════════════════════════════

def get_data_context() -> str:
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        dia_semana = datetime.now().strftime("%A")

        odvs = cur.execute("""
            SELECT o.id_odv, c.nombre as cliente, o.estado,
                   o.total_odv, o.fecha_entrega, o.responsable,
                   o.canal_venta,
                   julianday(o.fecha_entrega) - julianday('now') as dias_restantes
            FROM odv_cabecera o
            JOIN clientes c ON o.cliente_id = c.id
            WHERE o.estado NOT IN ('Entregado', 'Cancelado')
            ORDER BY o.fecha_entrega ASC
        """).fetchall()

        totales = cur.execute("""
            SELECT
                COUNT(*) as total_odv,
                SUM(CASE WHEN estado='Producción' THEN 1 ELSE 0 END) as en_produccion,
                SUM(CASE WHEN estado='Entregado'  THEN 1 ELSE 0 END) as entregados,
                SUM(CASE WHEN estado='Cotización' THEN 1 ELSE 0 END) as cotizaciones,
                SUM(CASE WHEN estado NOT IN ('Entregado','Cancelado') THEN total_odv ELSE 0 END) as pipeline_activo,
                SUM(total_odv) as facturado_total
            FROM odv_cabecera
        """).fetchone()

        top_margen = cur.execute("""
            SELECT nombre, marca_ep, categoria,
                   ROUND((precio_mayorista - costo_material) / precio_mayorista * 100, 1) as margen_pct,
                   precio_mayorista, costo_material
            FROM productos
            WHERE activo = 1 AND precio_mayorista > 0
            ORDER BY margen_pct DESC
            LIMIT 5
        """).fetchall()

        top_clientes = cur.execute("""
            SELECT c.nombre, c.tipo, c.canal_entrada,
                   COUNT(o.id) as ordenes,
                   SUM(o.total_odv) as total_facturado
            FROM clientes c
            LEFT JOIN odv_cabecera o ON c.id = o.cliente_id
            GROUP BY c.id
            ORDER BY total_facturado DESC
            LIMIT 5
        """).fetchall()

        # Revenue por canal
        canales = cur.execute("""
            SELECT canal_venta, COUNT(*) as ordenes, SUM(total_odv) as total
            FROM odv_cabecera
            WHERE canal_venta IS NOT NULL
            GROUP BY canal_venta
            ORDER BY total DESC
        """).fetchall()

        alertas = [o for o in odvs
                   if o["dias_restantes"] is not None and o["dias_restantes"] <= 3]

        logs = cur.execute("""
            SELECT tipo, senal, accion_sugerida, confianza, fecha
            FROM log_agente
            ORDER BY fecha DESC LIMIT 5
        """).fetchall()

        conn.close()

        # Reglas aprendidas por el agente
        reglas_txt = _leer_reglas_aprendidas()

        ctx = f"""
═══════════════════════════════════════════════
DATOS EL PASAJE — {hoy} ({dia_semana})
═══════════════════════════════════════════════

RESUMEN GENERAL:
  Total ODV:         {totales['total_odv']}
  En producción:     {totales['en_produccion']}
  Cotizaciones:      {totales['cotizaciones']}
  Pipeline activo:   ${totales['pipeline_activo']:,.0f} ARS
  Facturado total:   ${totales['facturado_total']:,.0f} ARS

ÓRDENES ACTIVAS:
{_fmt_odvs(odvs)}

ALERTAS ENTREGA URGENTE (≤3 días):
{_fmt_alertas(alertas)}

TOP PRODUCTOS POR MARGEN:
{_fmt_productos(top_margen)}

TOP CLIENTES:
{_fmt_clientes(top_clientes)}

REVENUE POR CANAL:
{_fmt_canales(canales)}

ÚLTIMAS SEÑALES:
{_fmt_logs(logs)}
{reglas_txt}
"""
        return ctx

    except Exception as e:
        return f"\n[DATOS NO DISPONIBLES: {e}]\n"


# ══════════════════════════════════════════════════════
# MECANISMO DE REGLAS APRENDIDAS
#
# El agente puede sugerir nuevas reglas.
# Vos las revisás y las agregás a este archivo.
# Con el tiempo el conocimiento crece solo.
# ══════════════════════════════════════════════════════

def _leer_reglas_aprendidas() -> str:
    """Lee reglas que el agente detectó y vos aprobaste."""
    try:
        if REGLAS_APRENDIDAS_PATH.exists():
            contenido = REGLAS_APRENDIDAS_PATH.read_text(encoding='utf-8').strip()
            if contenido and not contenido.startswith('#'):
                return f"\nREGLAS APRENDIDAS DEL NEGOCIO:\n{contenido}\n"
    except:
        pass
    return ""

def registrar_regla_nueva(regla: str, confianza: float = 0.7):
    """
    El agente llama a esto cuando detecta un patrón nuevo.
    Queda guardado para que Alejandra lo revise y apruebe.

    Ejemplo:
        registrar_regla_nueva(
            "Oasis Animal pide más en las semanas previas a ferias veterinarias",
            confianza=0.8
        )
    """
    try:
        REGLAS_APRENDIDAS_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        linea = f"[{timestamp}] (confianza {int(confianza*100)}%) {regla}\n"
        with open(REGLAS_APRENDIDAS_PATH, 'a', encoding='utf-8') as f:
            f.write(linea)
    except:
        pass


# ── Helpers de formato

def _fmt_odvs(odvs):
    if not odvs:
        return "  (sin órdenes activas)"
    lines = []
    for o in odvs:
        dias = f"{int(o['dias_restantes'])}d" if o["dias_restantes"] is not None else "sin fecha"
        emoji = "🔴" if o["dias_restantes"] is not None and o["dias_restantes"] <= 1 else "🟡" if o["dias_restantes"] is not None and o["dias_restantes"] <= 3 else "  "
        lines.append(
            f"  {emoji} {o['id_odv']} | {o['cliente']} | {o['estado']} | "
            f"${o['total_odv']:,.0f} | entrega: {o['fecha_entrega']} ({dias}) | "
            f"resp: {o['responsable']} | canal: {o['canal_venta']}"
        )
    return "\n".join(lines)

def _fmt_alertas(alertas):
    if not alertas:
        return "  ✅ Sin entregas urgentes"
    lines = []
    for o in alertas:
        emoji = "🔴" if int(o["dias_restantes"]) <= 1 else "🟡"
        lines.append(
            f"  {emoji} {o['id_odv']} — {o['cliente']} — "
            f"vence en {int(o['dias_restantes'])} días — {o['estado']} — resp: {o['responsable']}"
        )
    return "\n".join(lines)

def _fmt_productos(prods):
    if not prods:
        return "  (sin productos)"
    lines = []
    for p in prods:
        cat = "High" if p['margen_pct'] > 50 else "Medium" if p['margen_pct'] > 30 else "Low"
        lines.append(
            f"  • {p['nombre']} ({p['marca_ep']}) | margen: {p['margen_pct']}% [{cat}] "
            f"| precio: ${p['precio_mayorista']:,.0f} | costo: ${p['costo_material']:,.0f}"
        )
    return "\n".join(lines)

def _fmt_clientes(clientes):
    if not clientes:
        return "  (sin clientes)"
    lines = []
    for c in clientes:
        lines.append(
            f"  • {c['nombre']} ({c['tipo']}) | entrada: {c['canal_entrada']} "
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

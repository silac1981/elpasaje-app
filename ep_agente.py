"""
╔══════════════════════════════════════════════════════════╗
║         EL PASAJE 3D STUDIO — AGENTE IA                 ║
║         ep_agente.py  v2                                 ║
║         Corre solo. Detecta patrones. Manda resumen.     ║
╚══════════════════════════════════════════════════════════╝

CÓMO CORRER:
  python ep_agente.py            → análisis completo ahora
  python ep_agente.py silencioso → sin email (solo log)

SE ACTIVA AUTOMÁTICAMENTE a las 20hs (configurado en backup_manager.py)

Schema: elpasaje_v2.db — orders / tenants / products / order_items /
        materials / senales_mercado / log_agente
"""

import sys
import os
import smtplib
import sqlite3
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════

_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_secrets() -> dict:
    """Lee credenciales desde env vars, luego desde secrets.toml si existen."""
    secrets = {
        "email_origen":  os.environ.get("EP_EMAIL_ORIGEN",   "elpasaje.3d.studio@gmail.com"),
        "email_destino": os.environ.get("EP_EMAIL_DESTINO",  "elpasaje.3d.studio@gmail.com"),
        "app_password":  os.environ.get("EP_EMAIL_PASSWORD", ""),
    }
    # Intentar leer desde .streamlit/secrets.toml si existe
    _secrets_path = os.path.join(_DIR, ".streamlit", "secrets.toml")
    if not secrets["app_password"] and os.path.exists(_secrets_path):
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                tomllib = None
        if tomllib:
            with open(_secrets_path, "rb") as _f:
                _data = tomllib.load(_f)
            secrets["email_origen"]  = _data.get("email", {}).get("origen",   secrets["email_origen"])
            secrets["email_destino"] = _data.get("email", {}).get("destino",  secrets["email_destino"])
            secrets["app_password"]  = _data.get("email", {}).get("password", "")
    return secrets


_CREDS = _load_secrets()

CONFIG = {
    "email_origen":    _CREDS["email_origen"],
    "email_destino":   _CREDS["email_destino"],
    "app_password":    _CREDS["app_password"],
    "db_path":         os.path.join(_DIR, "elpasaje_v2.db"),
    "modo_silencioso": "--silencioso" in sys.argv or "silencioso" in sys.argv,
}

# Constantes de costo de producción (sincronizadas con main.py)
COSTO_KG = 2350.0
MERMA    = 0.10

# ══════════════════════════════════════════════════════
# CONEXIÓN A LA BASE
# ══════════════════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(CONFIG["db_path"])
    conn.row_factory = sqlite3.Row
    # Crea log_agente si la DB existía antes de agregar esta tabla al schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS log_agente (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto        TEXT DEFAULT 'ElPasaje',
            tipo            TEXT NOT NULL,
            senal           TEXT NOT NULL,
            dato_observado  TEXT,
            accion_sugerida TEXT,
            etiquetas       TEXT,
            confianza       REAL DEFAULT 0.7,
            origen          TEXT DEFAULT 'agente',
            fecha           TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def registrar_log(tipo, senal, dato="", accion="", etiquetas="", confianza=0.7):
    conn = get_conn()
    conn.execute("""
        INSERT INTO log_agente
        (proyecto, tipo, senal, dato_observado, accion_sugerida, etiquetas, confianza, origen)
        VALUES ('ElPasaje',?,?,?,?,?,?,'agente')
    """, (tipo, senal, dato, accion, etiquetas, confianza))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════
# ALERTAS PARA EL DASHBOARD (importable desde main.py)
# ══════════════════════════════════════════════════════

def get_alertas_dashboard() -> list:
    """
    Devuelve lista de alertas actuales para mostrar en la UI de Streamlit.
    Cada alerta: {"nivel": "critico"|"atencion"|"info", "titulo": str, "detalle": str, "accion": str}
    Diseñada para ser llamada con @st.cache_data(ttl=120).
    """
    conn = get_conn()
    cur  = conn.cursor()
    alertas = []
    hoy = datetime.now().date()

    # ── 1. Stock crítico + proyección de días restantes ────────────
    mats = cur.execute("""
        SELECT m.material_id, m.name, m.stock_gr,
               COALESCE(m.stock_minimo_gr, 200) AS stock_minimo_gr,
               COALESCE(c.consumo_30d, 0)       AS consumo_30d
        FROM materials m
        LEFT JOIN (
            SELECT material_id, SUM(gramos_usados) AS consumo_30d
            FROM production_log
            WHERE fecha_fin >= date('now', '-30 days')
            GROUP BY material_id
        ) c ON c.material_id = m.material_id
    """).fetchall()

    for m in mats:
        stock     = m["stock_gr"] or 0
        minimo    = m["stock_minimo_gr"]
        consumo_d = (m["consumo_30d"] or 0) / 30
        if stock <= minimo:
            dias_txt = f"~{int(stock / consumo_d)}d de stock" if consumo_d > 0.5 else "ritmo bajo"
            alertas.append({
                "nivel":   "critico",
                "titulo":  f"⚠️ {m['name']} — stock crítico",
                "detalle": f"{stock:.0f}g restantes · mínimo {minimo:.0f}g · {dias_txt}",
                "accion":  "Reponer ahora",
            })
        elif consumo_d > 0.5:
            dias_stock = stock / consumo_d
            if dias_stock <= 7:
                alertas.append({
                    "nivel":   "atencion",
                    "titulo":  f"🟡 {m['name']} — queda ~{int(dias_stock)} días",
                    "detalle": f"{stock:.0f}g a {consumo_d:.0f}g/día",
                    "accion":  "Planificar compra esta semana",
                })

    # ── 2. Pedidos urgentes (entrega ≤ 2 días) ────────────────────
    urgentes = cur.execute("""
        SELECT id, client_id, status, fecha_entrega_est
        FROM orders
        WHERE status IN ('Pendiente','En Proceso')
          AND fecha_entrega_est IS NOT NULL
          AND julianday(fecha_entrega_est) - julianday('now') <= 2
        ORDER BY fecha_entrega_est ASC
    """).fetchall()

    for u in urgentes:
        try:
            dias = (datetime.strptime(u["fecha_entrega_est"][:10], "%Y-%m-%d").date() - hoy).days
        except Exception:
            continue
        nivel   = "critico" if dias <= 0 else "atencion"
        cuando  = "¡Hoy!" if dias == 0 else ("¡Vencido!" if dias < 0 else f"en {dias} día{'s' if dias != 1 else ''}")
        alertas.append({
            "nivel":   nivel,
            "titulo":  f"{'🚨' if dias <= 0 else '⏰'} Pedido #{u['id']} vence {cuando}",
            "detalle": f"Estado: {u['status']} · Línea: {u['client_id']}",
            "accion":  "Confirmar avance con Fer",
        })

    # ── 3. Tasa de fallos alta esta semana ────────────────────────
    fallos = cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN resultado NOT LIKE 'ok%' THEN 1 ELSE 0 END) AS fallos
        FROM production_log
        WHERE fecha_fin >= date('now', '-7 days')
    """).fetchone()

    if fallos and (fallos["total"] or 0) >= 3:
        tasa = (fallos["fallos"] or 0) / fallos["total"]
        if tasa >= 0.25:
            alertas.append({
                "nivel":   "critico" if tasa >= 0.4 else "atencion",
                "titulo":  f"🔴 Tasa de fallos — {tasa*100:.0f}% esta semana",
                "detalle": f"{fallos['fallos']} fallos de {fallos['total']} fabricaciones",
                "accion":  "Revisar material o calibración de impresora",
            })

    # ── 4. Socios sin pedir hace más de 21 días (con historial) ───
    inactivos = cur.execute("""
        SELECT t.name,
               CAST(julianday('now') - julianday(MAX(o.date)) AS INTEGER) AS dias_sin_pedir
        FROM tenants t
        JOIN orders o ON o.client_id = t.id AND o.status != 'Cancelado'
        WHERE t.id != 'admin'
        GROUP BY t.id
        HAVING COUNT(o.id) >= 2 AND dias_sin_pedir > 21
        ORDER BY dias_sin_pedir DESC
    """).fetchall()

    for t in inactivos:
        alertas.append({
            "nivel":   "info",
            "titulo":  f"💤 {t['name']} — sin pedir hace {t['dias_sin_pedir']} días",
            "detalle": "Superó el umbral de 21 días de inactividad",
            "accion":  "Hacer seguimiento",
        })

    conn.close()

    # Orden: crítico primero, luego atención, luego info
    _orden = {"critico": 0, "atencion": 1, "info": 2}
    alertas.sort(key=lambda a: _orden.get(a["nivel"], 9))
    return alertas


# ══════════════════════════════════════════════════════
# ANÁLISIS DE PATRONES
# ══════════════════════════════════════════════════════

def analizar_patrones():
    """El corazón del agente — busca patrones sin supervisión."""
    conn = get_conn()
    cur  = conn.cursor()
    hallazgos = []

    # 1. Productos con mayor margen
    # Costo real = (weight_gr * (1 + merma) * costo_kg) / 1000  — igual que main.py
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
        LIMIT 3
    """, (1 + MERMA, COSTO_KG, 1 + MERMA, COSTO_KG)).fetchall()

    if top_margen:
        mejor = top_margen[0]
        hallazgos.append({
            "tipo":      "Patrón de Margen",
            "senal":     f"Producto más rentable: {mejor['name']}",
            "dato":      f"Margen {mejor['margen_pct']}% — Línea: {mejor['client_id']}",
            "accion":    f"Priorizar producción de {mejor['name']} ante demanda similar",
            "etiquetas": f"margen_alto|{(mejor['categoria'] or 'general').lower().replace(' ','_')}",
            "confianza": 0.9,
        })

    # 2. Clientes recurrentes vs únicos
    clientes = cur.execute("""
        SELECT t.name, t.tipo,
               COUNT(DISTINCT o.id) AS nro_ordenes,
               COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total_facturado
        FROM tenants t
        LEFT JOIN orders      o  ON t.id = o.client_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY t.id
        ORDER BY total_facturado DESC
    """).fetchall()

    for c in clientes:
        if c["nro_ordenes"] and c["nro_ordenes"] >= 2:
            hallazgos.append({
                "tipo":      "Cliente Recurrente",
                "senal":     f"{c['name']} tiene {c['nro_ordenes']} órdenes — cliente consolidado",
                "dato":      f"Total facturado: ${c['total_facturado']:,.0f}",
                "accion":    "Considerar precio especial por volumen o programa de fidelidad",
                "etiquetas": f"cliente_recurrente|{(c['tipo'] or 'general').lower()}",
                "confianza": 0.85,
            })

    # 3. Órdenes en producción con entrega próxima
    hoy = datetime.now().date()
    proximas = cur.execute("""
        SELECT id, client_id, fecha_entrega_est, status, notas
        FROM orders
        WHERE status IN ('En Proceso', 'Pendiente')
          AND fecha_entrega_est IS NOT NULL
    """).fetchall()

    for p in proximas:
        if p["fecha_entrega_est"]:
            try:
                fecha_e = datetime.strptime(p["fecha_entrega_est"][:10], "%Y-%m-%d").date()
                dias = (fecha_e - hoy).days
                if dias <= 2:
                    hallazgos.append({
                        "tipo":      "Alerta Entrega",
                        "senal":     f"Orden #{p['id']} vence en {dias} días",
                        "dato":      f"Estado: {p['status']} — Entrega: {p['fecha_entrega_est']}",
                        "accion":    "Verificar avance de producción con Fernando",
                        "etiquetas": "entrega_urgente|produccion",
                        "confianza": 1.0,
                    })
            except Exception:
                pass

    # 4. Categorías con más demanda
    cats = cur.execute("""
        SELECT p.categoria,
               COUNT(oi.id) AS pedidos,
               COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_sku = p.sku
        GROUP BY p.categoria
        ORDER BY revenue DESC
    """).fetchall()

    if cats:
        top_cat = cats[0]
        hallazgos.append({
            "tipo":      "Patrón de Demanda",
            "senal":     f"Categoría más demandada: {top_cat['categoria']}",
            "dato":      f"{top_cat['pedidos']} pedidos — ${top_cat['revenue']:,.0f} en revenue",
            "accion":    f"Ampliar catálogo en {top_cat['categoria']} — hay demanda probada",
            "etiquetas": f"demanda|{(top_cat['categoria'] or 'general').lower().replace(' ','_')}",
            "confianza": 0.8,
        })

    # 5. Señales de mercado no procesadas
    senales = cur.execute("""
        SELECT COUNT(*) AS pendientes
        FROM senales_mercado
        WHERE procesado_por_ia = 0
    """).fetchone()

    if senales and senales["pendientes"] > 0:
        hallazgos.append({
            "tipo":      "Señales Pendientes",
            "senal":     f"{senales['pendientes']} señales de mercado sin procesar",
            "dato":      "Registradas en módulo Clientes > Señales de Mercado",
            "accion":    "Revisar señales y actualizar reglas del negocio si corresponde",
            "etiquetas": "señales|mercado",
            "confianza": 0.95,
        })

    conn.close()

    for h in hallazgos:
        registrar_log(h["tipo"], h["senal"], h["dato"], h["accion"], h["etiquetas"], h["confianza"])

    return hallazgos

# ══════════════════════════════════════════════════════
# RESUMEN DEL DÍA
# ══════════════════════════════════════════════════════

def generar_resumen():
    conn = get_conn()
    cur  = conn.cursor()

    # Órdenes activas con total calculado desde order_items
    odvs = cur.execute("""
        SELECT o.id, t.name AS cliente, o.status,
               COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total_odv,
               o.fecha_entrega_est
        FROM orders o
        JOIN tenants t ON o.client_id = t.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id
        ORDER BY o.date DESC
        LIMIT 10
    """).fetchall()

    # Totales globales
    totales = cur.execute("""
        SELECT
            COUNT(DISTINCT o.id)                                                  AS total_odv,
            SUM(CASE WHEN o.status = 'En Proceso' THEN 1 ELSE 0 END)             AS en_produccion,
            SUM(CASE WHEN o.status = 'Listo'      THEN 1 ELSE 0 END)             AS entregados,
            SUM(CASE WHEN o.status = 'Pendiente'  THEN 1 ELSE 0 END)             AS cotizaciones,
            COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0)                    AS facturado_total
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
    """).fetchone()

    # Logs recientes del agente (del día de hoy)
    logs = cur.execute("""
        SELECT tipo, senal, accion_sugerida, confianza
        FROM log_agente
        WHERE DATE(fecha) = DATE('now')
        ORDER BY confianza DESC
        LIMIT 5
    """).fetchall()

    conn.close()
    return dict(totales), [dict(o) for o in odvs], [dict(l) for l in logs]

# ══════════════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════════════

def enviar_email(totales, odvs, hallazgos):
    if CONFIG["modo_silencioso"] or not CONFIG["app_password"]:
        print("📧 Email omitido (modo silencioso o sin contraseña configurada)")
        return

    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    odv_html = ""
    for o in odvs:
        color = {
            "En Proceso": "#F39C12",
            "Listo":      "#27AE60",
            "Pendiente":  "#0071BC",
            "Cancelado":  "#888",
        }.get(o["status"], "#888")
        odv_html += f"""
        <tr>
            <td style='padding:6px;'>#{o['id']}</td>
            <td style='padding:6px;'>{o['cliente']}</td>
            <td style='padding:6px; color:{color}; font-weight:bold;'>{o['status']}</td>
            <td style='padding:6px;'>${o['total_odv']:,.0f}</td>
            <td style='padding:6px;'>{o['fecha_entrega_est'] or '—'}</td>
        </tr>"""

    hallazgos_html = ""
    for h in hallazgos[:5]:
        hallazgos_html += f"""
        <div style='background:#F0F8FF; border-left:4px solid #0071BC;
                    padding:10px; margin:8px 0; border-radius:4px;'>
            <strong>{h['tipo']}</strong> (confianza: {h['confianza']*100:.0f}%)<br>
            📍 {h['senal']}<br>
            💡 <em>{h['accion']}</em>
        </div>"""

    html = f"""
    <html><body style='font-family:Arial; color:#333;'>
    <div style='background:#0071BC; color:white; padding:20px; border-radius:8px;'>
        <h2 style='margin:0;'>🏭 El Pasaje 3D Studio — Resumen del Agente</h2>
        <p style='margin:5px 0 0; opacity:0.8;'>{hoy}</p>
    </div>

    <div style='display:flex; gap:15px; margin:20px 0;'>
        <div style='background:#F5F5F5; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#0071BC;'>{totales['total_odv']}</div>
            <div>Total Órdenes</div>
        </div>
        <div style='background:#FFF3CD; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#F39C12;'>{totales['en_produccion']}</div>
            <div>En Producción</div>
        </div>
        <div style='background:#D4EDDA; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#27AE60;'>{totales['entregados']}</div>
            <div>Listos</div>
        </div>
        <div style='background:#E8F4FD; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#0071BC;'>${totales['facturado_total']:,.0f}</div>
            <div>Facturado Total</div>
        </div>
    </div>

    <h3>📋 Órdenes Activas</h3>
    <table style='width:100%; border-collapse:collapse; background:white;'>
        <tr style='background:#0071BC; color:white;'>
            <th style='padding:8px;'>Orden</th>
            <th style='padding:8px;'>Cliente/Línea</th>
            <th style='padding:8px;'>Estado</th>
            <th style='padding:8px;'>Total</th>
            <th style='padding:8px;'>Entrega estimada</th>
        </tr>
        {odv_html}
    </table>

    <h3>🤖 Patrones detectados hoy</h3>
    {hallazgos_html if hallazgos_html else '<p>Sin nuevos patrones detectados hoy.</p>'}

    <div style='background:#F5F5F5; padding:15px; border-radius:8px; margin-top:20px;
                font-size:12px; color:#888; text-align:center;'>
        Agente El Pasaje 3D Studio — Corriendo automáticamente todos los días a las 20hs
    </div>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[El Pasaje] Resumen del Agente — {datetime.now().strftime('%d/%m/%Y')}"
        msg["From"]    = CONFIG["email_origen"]
        msg["To"]      = CONFIG["email_destino"]
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(CONFIG["email_origen"], CONFIG["app_password"])
            server.sendmail(CONFIG["email_origen"], CONFIG["email_destino"], msg.as_string())

        print("✅ Email enviado correctamente")
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        print("   → Configurá el App Password de Google en CONFIG['app_password']")

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    # Forzar UTF-8 en stdout para emojis en terminales Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"\n{'='*55}")
    print(f"  AGENTE EL PASAJE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  DB: {CONFIG['db_path']}")
    print(f"{'='*55}\n")

    print("🔍 Analizando patrones...")
    hallazgos = analizar_patrones()
    print(f"   → {len(hallazgos)} hallazgos registrados en el log")

    print("\n📊 Generando resumen del día...")
    totales, odvs, logs = generar_resumen()
    print(f"   → {totales['total_odv']} órdenes | {totales['en_produccion']} en producción | ${totales['facturado_total']:,.0f} facturado")

    for h in hallazgos:
        print(f"\n   🔸 [{h['tipo']}] {h['senal']}")
        print(f"      💡 {h['accion']}")

    print("\n📧 Enviando resumen por email...")
    enviar_email(totales, odvs, hallazgos)

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from backup_manager import backup_elpasaje
        backup_elpasaje("Agente El Pasaje — ejecución automática")
    except Exception as e:
        print(f"⚠️  Backup omitido: {e}")

    print(f"\n{'='*55}")
    print(f"  Agente finalizado — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*55}\n")

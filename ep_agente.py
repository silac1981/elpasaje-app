"""
╔══════════════════════════════════════════════════════════╗
║         EL PASAJE 3D STUDIO — AGENTE IA                 ║
║         ep_agente.py                                     ║
║         Corre solo. Detecta patrones. Manda resumen.     ║
╚══════════════════════════════════════════════════════════╝

CÓMO CORRER:
  python ep_agente.py            → análisis completo ahora
  python ep_agente.py silencioso → sin email (solo log)

SE ACTIVA AUTOMÁTICAMENTE a las 20hs (configurado por backup_manager.py programar)
"""

import sys
import os
import json
import smtplib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════

CONFIG = {
    "email_origen":   "elpasaje.3d.studio@gmail.com",
    "email_destino":  "elpasaje.3d.studio@gmail.com",
    "app_password":   "ndguxauofxtedqrr",   # ← completar con App Password de Google (16 caracteres)
    "db_path":        r"C:\Trabajo\ElPasaje\ep_pasaje.db",
    "modo_silencioso": "--silencioso" in sys.argv or "silencioso" in sys.argv,
}

# ══════════════════════════════════════════════════════
# CONEXIÓN A LA BASE
# ══════════════════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(CONFIG["db_path"])
    conn.row_factory = sqlite3.Row
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
# ANÁLISIS DE PATRONES
# ══════════════════════════════════════════════════════

def analizar_patrones():
    """El corazón del agente — busca patrones sin supervisión."""
    conn = get_conn()
    cur = conn.cursor()
    hallazgos = []

    # 1. Productos con mayor margen
    top_margen = cur.execute("""
        SELECT p.nombre, p.marca_ep, p.categoria,
               p.precio_mayorista, p.costo_material,
               CASE WHEN p.precio_mayorista > 0 
                    THEN ROUND((p.precio_mayorista - p.costo_material) / p.precio_mayorista * 100, 1)
                    ELSE 0 END as margen_pct
        FROM productos p
        WHERE p.activo = 1 AND p.precio_mayorista > 0
        ORDER BY margen_pct DESC
        LIMIT 3
    """).fetchall()

    if top_margen:
        mejor = top_margen[0]
        hallazgos.append({
            "tipo": "Patrón de Margen",
            "senal": f"Producto más rentable: {mejor['nombre']}",
            "dato": f"Margen {mejor['margen_pct']}% — Marca: {mejor['marca_ep']}",
            "accion": f"Priorizar producción de {mejor['nombre']} ante demanda similar",
            "etiquetas": f"margen_alto|{mejor['categoria'].lower().replace(' ','_')}",
            "confianza": 0.9
        })

    # 2. Clientes recurrentes vs únicos
    clientes = cur.execute("""
        SELECT c.nombre, c.tipo, c.frecuencia, COUNT(o.id) as nro_ordenes,
               SUM(o.total_odv) as total_facturado
        FROM clientes c
        LEFT JOIN odv_cabecera o ON c.id = o.cliente_id
        GROUP BY c.id
        ORDER BY total_facturado DESC
    """).fetchall()

    for c in clientes:
        if c["nro_ordenes"] and c["nro_ordenes"] >= 2:
            hallazgos.append({
                "tipo": "Cliente Recurrente",
                "senal": f"{c['nombre']} tiene {c['nro_ordenes']} órdenes — cliente consolidado",
                "dato": f"Total facturado: ${c['total_facturado']:,.0f}",
                "accion": "Considerar precio especial por volumen o programa de fidelidad",
                "etiquetas": f"cliente_recurrente|{c['tipo'].lower()}",
                "confianza": 0.85
            })

    # 3. Órdenes en producción con entrega próxima
    hoy = datetime.now().date()
    proximas = cur.execute("""
        SELECT id_odv, cliente_id, fecha_entrega, estado, notas
        FROM odv_cabecera
        WHERE estado IN ('Producción', 'Confirmado')
        AND fecha_entrega IS NOT NULL
    """).fetchall()

    for p in proximas:
        if p["fecha_entrega"]:
            try:
                fecha_e = datetime.strptime(p["fecha_entrega"], "%Y-%m-%d").date()
                dias = (fecha_e - hoy).days
                if dias <= 2:
                    hallazgos.append({
                        "tipo": "Alerta Entrega",
                        "senal": f"ODV {p['id_odv']} vence en {dias} días",
                        "dato": f"Estado: {p['estado']} — Entrega: {p['fecha_entrega']}",
                        "accion": "Verificar avance de producción con Fernando",
                        "etiquetas": "entrega_urgente|produccion",
                        "confianza": 1.0
                    })
            except:
                pass

    # 4. Categorías con más demanda
    cats = cur.execute("""
        SELECT p.categoria, COUNT(d.id) as pedidos, SUM(d.subtotal) as revenue
        FROM odv_detalle d
        JOIN productos p ON d.producto_id = p.id
        GROUP BY p.categoria
        ORDER BY revenue DESC
    """).fetchall()

    if cats:
        top_cat = cats[0]
        hallazgos.append({
            "tipo": "Patrón de Demanda",
            "senal": f"Categoría más demandada: {top_cat['categoria']}",
            "dato": f"{top_cat['pedidos']} pedidos — ${top_cat['revenue']:,.0f} en revenue",
            "accion": f"Ampliar catálogo en {top_cat['categoria']} — hay demanda probada",
            "etiquetas": f"demanda|{top_cat['categoria'].lower().replace(' ','_')}",
            "confianza": 0.8
        })

    conn.close()

    # Guardar hallazgos en el log
    for h in hallazgos:
        registrar_log(h["tipo"], h["senal"], h["dato"], h["accion"], h["etiquetas"], h["confianza"])

    return hallazgos

# ══════════════════════════════════════════════════════
# RESUMEN DEL DÍA
# ══════════════════════════════════════════════════════

def generar_resumen():
    conn = get_conn()
    cur = conn.cursor()

    # ODVs activas
    odvs = cur.execute("""
        SELECT o.id_odv, c.nombre as cliente, o.estado, o.total_odv, o.fecha_entrega
        FROM odv_cabecera o
        JOIN clientes c ON o.cliente_id = c.id
        ORDER BY o.fecha_creacion DESC
        LIMIT 10
    """).fetchall()

    # Totales
    totales = cur.execute("""
        SELECT 
            COUNT(*) as total_odv,
            SUM(CASE WHEN estado='Producción' THEN 1 ELSE 0 END) as en_produccion,
            SUM(CASE WHEN estado='Entregado' THEN 1 ELSE 0 END) as entregados,
            SUM(CASE WHEN estado='Cotización' THEN 1 ELSE 0 END) as cotizaciones,
            SUM(total_odv) as facturado_total
        FROM odv_cabecera
    """).fetchone()

    # Logs recientes del agente
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
        print("📧 Email omitido (modo silencioso o sin contrasena configurada)")
        return

    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Armar cuerpo
    odv_html = ""
    for o in odvs:
        color = {"Producción":"#F39C12", "Entregado":"#27AE60",
                 "Cotización":"#0071BC", "Confirmado":"#8E44AD"}.get(o["estado"], "#888")
        odv_html += f"""
        <tr>
            <td style='padding:6px;'>{o['id_odv']}</td>
            <td style='padding:6px;'>{o['cliente']}</td>
            <td style='padding:6px; color:{color}; font-weight:bold;'>{o['estado']}</td>
            <td style='padding:6px;'>${o['total_odv']:,.0f}</td>
            <td style='padding:6px;'>{o['fecha_entrega'] or '—'}</td>
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
            <div>Total ODV</div>
        </div>
        <div style='background:#FFF3CD; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#F39C12;'>{totales['en_produccion']}</div>
            <div>En Producción</div>
        </div>
        <div style='background:#D4EDDA; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#27AE60;'>{totales['entregados']}</div>
            <div>Entregados</div>
        </div>
        <div style='background:#E8F4FD; padding:15px; border-radius:8px; flex:1; text-align:center;'>
            <div style='font-size:28px; font-weight:bold; color:#0071BC;'>${totales['facturado_total']:,.0f}</div>
            <div>Facturado Total</div>
        </div>
    </div>

    <h3>📋 Órdenes Activas</h3>
    <table style='width:100%; border-collapse:collapse; background:white;'>
        <tr style='background:#0071BC; color:white;'>
            <th style='padding:8px;'>ODV</th>
            <th style='padding:8px;'>Cliente</th>
            <th style='padding:8px;'>Estado</th>
            <th style='padding:8px;'>Total</th>
            <th style='padding:8px;'>Entrega</th>
        </tr>
        {odv_html}
    </table>

    <h3>🤖 Patrones detectados hoy</h3>
    {hallazgos_html if hallazgos_html else '<p>Sin nuevos patrones detectados hoy.</p>'}

    <div style='background:#F5F5F5; padding:15px; border-radius:8px; margin-top:20px;
                font-size:12px; color:#888; text-align:center;'>
        Agente El Pasaje 3D Studio — Corriendo automáticamente todos los días a las 20hs<br>
        Para ver el detalle completo: EPCC Dashboard
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
    print(f"\n{'='*55}")
    print(f"  AGENTE EL PASAJE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}\n")

    print("🔍 Analizando patrones...")
    hallazgos = analizar_patrones()
    print(f"   → {len(hallazgos)} hallazgos registrados en el log")

    print("\n📊 Generando resumen del día...")
    totales, odvs, logs = generar_resumen()
    print(f"   → {totales['total_odv']} ODV | {totales['en_produccion']} en producción | ${totales['facturado_total']:,.0f} facturado")

    for h in hallazgos:
        print(f"\n   🔸 [{h['tipo']}] {h['senal']}")
        print(f"      💡 {h['accion']}")

    print("\n📧 Enviando resumen por email...")
    enviar_email(totales, odvs, hallazgos)

    # Backup automático
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from backup_manager import backup_elpasaje
        backup_elpasaje("Agente El Pasaje — ejecución automática")
    except Exception as e:
        print(f"⚠️  Backup omitido: {e}")

    print(f"\n{'='*55}")
    print(f"  Agente finalizado — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*55}\n")

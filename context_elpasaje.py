# context_elpasaje.py
import sqlite3, os
from datetime import datetime

NOMBRE = "Agente El Pasaje"

DB_PATH = r"C:\Users\ar028883\Documents\elpasaje-app-clean\ep_pasaje.db"

SYSTEM_PROMPT = """Sos el Agente de El Pasaje 3D Studio de Alejandra Gomez Aguilera.
Negocio familiar de impresion 3D en Buenos Aires. 5 marcas: Magnitud 19 (Alejandra), Melomanos (Fernando), Coquette (Olivia), Core Tech (Constantino), Francisco Deportes (Francisco).
Clientes B2B: VK-Home, Oasis Animal, Pharma DeLux, Aviation Pro.
ODV = Orden de Venta. Estados: Cotizacion, Confirmado, Produccion, Entregado, Cancelado.
Margen saludable mayor a 40 por ciento. Respondes en español, directo y concreto."""

def get_data_context():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        totales = cur.execute("""
            SELECT COUNT(*) as total,
            SUM(CASE WHEN estado NOT IN ('Entregado','Cancelado') THEN total_odv ELSE 0 END) as pipeline,
            SUM(CASE WHEN estado='Produccion' THEN 1 ELSE 0 END) as en_prod
            FROM odv_cabecera""").fetchone()
        
        odvs = cur.execute("""
            SELECT o.id_odv, c.nombre, o.estado, o.total_odv, o.fecha_entrega
            FROM odv_cabecera o JOIN clientes c ON o.cliente_id=c.id
            WHERE o.estado NOT IN ('Entregado','Cancelado')
            ORDER BY o.fecha_entrega ASC LIMIT 10""").fetchall()
        
        conn.close()
        
        lineas = [f"DATOS AL {hoy}",
                  f"Total ODV: {totales['total']} | En produccion: {totales['en_prod']} | Pipeline: ${totales['pipeline']:,.0f}",
                  "ORDENES ACTIVAS:"]
        for o in odvs:
            lineas.append(f"  {o['id_odv']} | {o['nombre']} | {o['estado']} | ${o['total_odv']:,.0f} | entrega: {o['fecha_entrega']}")
        return "\n".join(lineas)
    except Exception as e:
        return f"[Base no disponible: {e}]"

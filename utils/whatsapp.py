"""utils/whatsapp.py — Links de WhatsApp para El Pasaje 3D Studio."""
import urllib.parse

NUMERO_DEFAULT = "5491100000000"


def get_numero_linea(client_id: str, db_engine) -> str:
    """Busca whatsapp_numero en lineas_config. Si no hay, usa NUMERO_DEFAULT."""
    try:
        from sqlalchemy import text
        with db_engine.connect() as conn:
            row = conn.execute(
                text("SELECT whatsapp_numero FROM lineas_config WHERE client_id=:cid"),
                {"cid": client_id},
            ).fetchone()
        if row and row[0] and str(row[0]).strip():
            return str(row[0]).strip()
    except Exception:
        pass
    return NUMERO_DEFAULT


def _wa_url(numero: str, mensaje: str) -> str:
    return f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"


def link_producto(nombre: str, sku: str, precio: float,
                  client_id: str, db_engine,
                  precio_override: float = None) -> str:
    """URL wa.me con mensaje pre-cargado para consulta de un producto.
    precio_override: si se pasa y es > 0, reemplaza a precio en el mensaje."""
    numero = get_numero_linea(client_id, db_engine)
    precio_final = precio_override if (precio_override and precio_override > 0) else precio
    msg = (
        f"Hola! Me interesa el {nombre} (SKU: {sku}) — "
        f"Precio: ${precio_final:,.0f}\n¿Está disponible?"
    )
    return _wa_url(numero, msg)


def link_presupuesto(items: list, total: float,
                     client_id: str, db_engine) -> str:
    """URL wa.me con presupuesto multi-ítem pre-cargado.
    Cada item puede traer clave 'precio_reventa' que tiene precedencia sobre 'precio'."""
    numero = get_numero_linea(client_id, db_engine)
    lineas_txt = "\n".join(
        f"• {it['cantidad']}x {it['nombre']} ({it['sku']}) — "
        f"${float(it.get('precio_reventa') or it['precio']) * int(it['cantidad']):,.0f}"
        for it in items
    )
    msg = (
        f"Hola! Quisiera consultar por el siguiente presupuesto:\n"
        f"{lineas_txt}\n"
        f"TOTAL: ${total:,.0f}\n"
        f"¿Podemos coordinar?"
    )
    return _wa_url(numero, msg)


def texto_presupuesto(items: list, total: float,
                      linea_nombre: str = "El Pasaje 3D Studio",
                      numero: str = "") -> str:
    """Texto plano del presupuesto. Usa precio_reventa si está en el item."""
    sep = "─" * 33
    lines = [f"PRESUPUESTO — {linea_nombre}", sep]
    for it in items:
        precio_item = float(it.get("precio_reventa") or it["precio"])
        sub = precio_item * int(it["cantidad"])
        nom = f"{it['cantidad']}x {it['nombre']}"
        lines.append(f"• {nom[:30]}  ${sub:,.0f}")
    lines.append(sep)
    lines.append(f"TOTAL  ${total:,.0f}")
    lines.append("")
    lines.append("Valido por 48 horas - Entrega bajo pedido 48-72hs")
    sig = "El Pasaje 3D Studio"
    if numero and numero != NUMERO_DEFAULT:
        sig += f" - WA: {numero}"
    lines.append(sig)
    return "\n".join(lines)

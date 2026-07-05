"""utils/orders.py — Máquina de estados central para pedidos.

TODOS los cambios de estado de pedidos pasan por avanzar_estado().
Nunca hacer UPDATE orders SET status=... directamente desde los módulos.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from utils.db import engine


# Estados válidos y sus transiciones permitidas
_TRANSICIONES = {
    "Pendiente":  ["En Proceso", "Cancelado"],
    "En Proceso": ["Listo",      "Cancelado"],
    "Listo":      ["Entregado",  "Cancelado"],
    "Entregado":  [],
    "Cancelado":  [],
}


def avanzar_estado(
    pedido_id: int,
    nuevo_estado: str,
    db_path: Optional[str] = None,   # ignorado, mantenido por compatibilidad
    gramos_reales:    Optional[float] = None,
    tiempo_min:       Optional[int]   = None,
    material_id:      Optional[str]   = None,
    resultado:        str             = "Éxito",
    motivo:           Optional[str]   = None,
    gramos_estimados: Optional[float] = None,
) -> dict:
    """
    Avanza el estado de un pedido aplicando TODOS los efectos automáticos.

    Retorna {"ok": True} o {"ok": False, "error": "mensaje"}.

    Efectos por transición:
      → En Proceso : started_at = now()
      → Listo      : INSERT production_log · descuenta filamento · INSERT stock_movements(produccion)
                     Si resultado contiene 'Fallo total' → regresa a Pendiente
      → Entregado  : delivered_at = now() · pagos → pagado · INSERT stock_movements(venta) · monto_venta
      → Cancelado  : motivo_cancelacion registrado
    """
    ahora = datetime.now().isoformat()

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT status, client_id FROM orders WHERE id=:pid"),
                {"pid": pedido_id}
            ).fetchone()
            if not row:
                return {"ok": False, "error": f"Pedido #{pedido_id} no encontrado"}

            estado_actual, client_id = row[0], row[1]

            if nuevo_estado not in _TRANSICIONES.get(estado_actual, []):
                return {
                    "ok": False,
                    "error": f"Transición inválida: {estado_actual} → {nuevo_estado}",
                }

            # ── → EN PROCESO ────────────────────────────────────────────
            if nuevo_estado == "En Proceso":
                conn.execute(
                    text("UPDATE orders SET status='En Proceso', started_at=:t WHERE id=:pid"),
                    {"t": ahora, "pid": pedido_id},
                )

            # ── → LISTO ─────────────────────────────────────────────────
            elif nuevo_estado == "Listo":
                fallo_total = "fallo total" in resultado.lower()

                if fallo_total:
                    conn.execute(
                        text("UPDATE orders SET status='Pendiente' WHERE id=:pid"),
                        {"pid": pedido_id}
                    )
                    if gramos_reales and material_id:
                        conn.execute(text("""
                            INSERT INTO production_log
                                (order_id, product_sku, material_id, gramos_usados, tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                            SELECT :pid, oi.product_sku, :mid, :gr, :tmin, CURRENT_DATE, CURRENT_DATE, :res
                            FROM order_items oi WHERE oi.order_id=:pid LIMIT 1
                        """), {"pid": pedido_id, "mid": material_id, "gr": gramos_reales or 0,
                               "tmin": tiempo_min or 0, "res": resultado})
                    return {"ok": True, "estado_final": "Pendiente", "fallo": True}

                conn.execute(
                    text("UPDATE orders SET status='Listo', completed_at=:t WHERE id=:pid"),
                    {"t": ahora, "pid": pedido_id},
                )

                if gramos_reales and material_id:
                    conn.execute(text("""
                        INSERT INTO production_log
                            (order_id, product_sku, material_id, gramos_usados, tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                        SELECT :pid, oi.product_sku, :mid, :gr, :tmin, CURRENT_DATE, CURRENT_DATE, :res
                        FROM order_items oi WHERE oi.order_id=:pid LIMIT 1
                    """), {"pid": pedido_id, "mid": material_id, "gr": gramos_reales,
                           "tmin": tiempo_min or 0, "res": resultado})
                    conn.execute(
                        text("UPDATE materials SET stock_gr = stock_gr - :gr WHERE material_id=:mid"),
                        {"gr": gramos_reales, "mid": material_id},
                    )
                    qty_row = conn.execute(
                        text("SELECT COALESCE(SUM(cantidad), 1) FROM order_items WHERE order_id=:pid"),
                        {"pid": pedido_id},
                    ).fetchone()
                    qty = qty_row[0] if qty_row else 1
                    sku_row = conn.execute(
                        text("SELECT product_sku FROM order_items WHERE order_id=:pid LIMIT 1"),
                        {"pid": pedido_id},
                    ).fetchone()
                    if sku_row:
                        conn.execute(text("""
                            INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia)
                            VALUES (:sku, 'produccion', :qty, CURRENT_DATE, :ref)
                        """), {"sku": sku_row[0], "qty": qty, "ref": f"order_{pedido_id}"})

            # ── → ENTREGADO ─────────────────────────────────────────────
            elif nuevo_estado == "Entregado":
                pago_row = conn.execute(
                    text("SELECT monto FROM pagos WHERE order_id=:pid AND estado='pendiente' LIMIT 1"),
                    {"pid": pedido_id},
                ).fetchone()
                monto = pago_row[0] if pago_row else 0

                conn.execute(
                    text("UPDATE orders SET status='Entregado', delivered_at=:t, monto_venta=:m WHERE id=:pid"),
                    {"t": ahora, "m": monto, "pid": pedido_id},
                )
                conn.execute(
                    text("UPDATE pagos SET estado='pagado' WHERE order_id=:pid AND estado='pendiente'"),
                    {"pid": pedido_id},
                )
                rows_items = conn.execute(
                    text("SELECT product_sku, cantidad FROM order_items WHERE order_id=:pid"),
                    {"pid": pedido_id},
                ).fetchall()
                for sku, qty in rows_items:
                    conn.execute(text("""
                        INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia)
                        VALUES (:sku, 'venta', :qty, CURRENT_DATE, :ref)
                    """), {"sku": sku, "qty": -qty, "ref": f"order_{pedido_id}"})

            # ── → CANCELADO ─────────────────────────────────────────────
            elif nuevo_estado == "Cancelado":
                conn.execute(
                    text("UPDATE orders SET status='Cancelado', motivo_cancelacion=:m WHERE id=:pid"),
                    {"m": motivo or "", "pid": pedido_id},
                )

        return {"ok": True, "estado_final": nuevo_estado}

    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verificar_material_disponible(pedido_id: int, db_path: Optional[str] = None) -> dict:
    """
    Verifica si hay material suficiente para fabricar un pedido.
    Retorna {"ok": True} o {"ok": False, "faltante_gr": N, "material": "nombre"}.
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT p.material_id, p.weight_gr, oi.cantidad, m.name, m.stock_gr
                FROM order_items oi
                JOIN products p ON p.sku = oi.product_sku
                LEFT JOIN materials m ON m.material_id = p.material_id
                WHERE oi.order_id = :pid
            """), {"pid": pedido_id}).fetchall()

            for mid, wgr, qty, mname, stock in rows:
                if not wgr:
                    continue
                requerido  = float(wgr) * float(qty) * 1.10
                disponible = float(stock or 0)
                if disponible < requerido:
                    return {
                        "ok": False,
                        "faltante_gr":  round(requerido - disponible),
                        "material":     mname or mid,
                        "requerido_gr": round(requerido),
                        "disponible_gr": round(disponible),
                    }
            return {"ok": True}
    except Exception as exc:
        return {"ok": True, "warning": str(exc)}

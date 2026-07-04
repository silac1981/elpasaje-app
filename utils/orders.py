"""utils/orders.py — Máquina de estados central para pedidos.

TODOS los cambios de estado de pedidos pasan por avanzar_estado().
Nunca hacer UPDATE orders SET status=... directamente desde los módulos.
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elpasaje_v2.db")


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
    db_path: Optional[str] = None,
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
    conn = sqlite3.connect(db_path or _DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    ahora = datetime.now().isoformat()

    try:
        conn.execute("BEGIN")

        row = conn.execute(
            "SELECT status, client_id FROM orders WHERE id=?", (pedido_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            conn.close()
            return {"ok": False, "error": f"Pedido #{pedido_id} no encontrado"}

        estado_actual, client_id = row[0], row[1]

        if nuevo_estado not in _TRANSICIONES.get(estado_actual, []):
            conn.rollback()
            conn.close()
            return {
                "ok": False,
                "error": f"Transición inválida: {estado_actual} → {nuevo_estado}",
            }

        # ── → EN PROCESO ────────────────────────────────────────────
        if nuevo_estado == "En Proceso":
            conn.execute(
                "UPDATE orders SET status='En Proceso', started_at=? WHERE id=?",
                (ahora, pedido_id),
            )

        # ── → LISTO ─────────────────────────────────────────────────
        elif nuevo_estado == "Listo":
            fallo_total = "fallo total" in resultado.lower()

            # Si fallo total: regresa a Pendiente sin avanzar
            if fallo_total:
                conn.execute(
                    "UPDATE orders SET status='Pendiente' WHERE id=?", (pedido_id,)
                )
                if gramos_reales and material_id:
                    conn.execute(
                        """INSERT INTO production_log
                           (order_id, product_sku, material_id, gramos_usados,
                            tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                           SELECT ?, oi.product_sku, ?, ?, ?, date('now'), date('now'), ?
                           FROM order_items oi WHERE oi.order_id=? LIMIT 1""",
                        (pedido_id, material_id, gramos_reales or 0,
                         tiempo_min or 0, resultado, pedido_id),
                    )
                conn.commit()
                conn.close()
                return {"ok": True, "estado_final": "Pendiente", "fallo": True}

            # Éxito o fallo parcial → avanza a Listo
            conn.execute(
                "UPDATE orders SET status='Listo', completed_at=? WHERE id=?",
                (ahora, pedido_id),
            )

            # Registrar en production_log
            if gramos_reales and material_id:
                conn.execute(
                    """INSERT INTO production_log
                       (order_id, product_sku, material_id, gramos_usados,
                        tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                       SELECT ?, oi.product_sku, ?, ?, ?, date('now'), date('now'), ?
                       FROM order_items oi WHERE oi.order_id=? LIMIT 1""",
                    (pedido_id, material_id, gramos_reales,
                     tiempo_min or 0, resultado, pedido_id),
                )
                # Descontar filamento real
                conn.execute(
                    "UPDATE materials SET stock_gr = stock_gr - ? WHERE material_id=?",
                    (gramos_reales, material_id),
                )
                # Movimiento de stock (producción terminada)
                qty_row = conn.execute(
                    "SELECT COALESCE(SUM(cantidad), 1) FROM order_items WHERE order_id=?",
                    (pedido_id,),
                ).fetchone()
                qty = qty_row[0] if qty_row else 1
                sku_row = conn.execute(
                    "SELECT product_sku FROM order_items WHERE order_id=? LIMIT 1",
                    (pedido_id,),
                ).fetchone()
                if sku_row:
                    conn.execute(
                        """INSERT INTO stock_movements
                           (product_sku, tipo, cantidad, fecha, referencia)
                           VALUES (?, 'produccion', ?, date('now'), ?)""",
                        (sku_row[0], qty, f"order_{pedido_id}"),
                    )

        # ── → ENTREGADO ─────────────────────────────────────────────
        elif nuevo_estado == "Entregado":
            # Calcular monto desde pagos
            pago_row = conn.execute(
                "SELECT monto FROM pagos WHERE order_id=? AND estado='pendiente' LIMIT 1",
                (pedido_id,),
            ).fetchone()
            monto = pago_row[0] if pago_row else 0

            conn.execute(
                "UPDATE orders SET status='Entregado', delivered_at=?, monto_venta=? WHERE id=?",
                (ahora, monto, pedido_id),
            )
            # Marcar pago como pagado
            conn.execute(
                "UPDATE pagos SET estado='pagado' WHERE order_id=? AND estado='pendiente'",
                (pedido_id,),
            )
            # Movimiento de stock (venta — descuenta producto terminado)
            rows_items = conn.execute(
                "SELECT product_sku, cantidad FROM order_items WHERE order_id=?",
                (pedido_id,),
            ).fetchall()
            for sku, qty in rows_items:
                conn.execute(
                    """INSERT INTO stock_movements
                       (product_sku, tipo, cantidad, fecha, referencia)
                       VALUES (?, 'venta', ?, date('now'), ?)""",
                    (sku, -qty, f"order_{pedido_id}"),
                )

        # ── → CANCELADO ─────────────────────────────────────────────
        elif nuevo_estado == "Cancelado":
            conn.execute(
                "UPDATE orders SET status='Cancelado', motivo_cancelacion=? WHERE id=?",
                (motivo or "", pedido_id),
            )

        conn.commit()
        conn.close()
        return {"ok": True, "estado_final": nuevo_estado}

    except Exception as exc:
        conn.rollback()
        conn.close()
        return {"ok": False, "error": str(exc)}


def verificar_material_disponible(pedido_id: int, db_path: Optional[str] = None) -> dict:
    """
    Verifica si hay material suficiente para fabricar un pedido.
    Retorna {"ok": True} o {"ok": False, "faltante_gr": N, "material": "nombre"}.
    """
    conn = sqlite3.connect(db_path or _DB_PATH)
    try:
        rows = conn.execute(
            """SELECT p.material_id, p.weight_gr, oi.cantidad, m.name, m.stock_gr
               FROM order_items oi
               JOIN products p ON p.sku = oi.product_sku
               LEFT JOIN materials m ON m.material_id = p.material_id
               WHERE oi.order_id = ?""",
            (pedido_id,),
        ).fetchall()

        for mid, wgr, qty, mname, stock in rows:
            if not wgr:
                continue
            requerido = float(wgr) * float(qty) * 1.10  # +10% desperdicio
            disponible = float(stock or 0)
            if disponible < requerido:
                conn.close()
                return {
                    "ok": False,
                    "faltante_gr": round(requerido - disponible),
                    "material": mname or mid,
                    "requerido_gr": round(requerido),
                    "disponible_gr": round(disponible),
                }
        conn.close()
        return {"ok": True}
    except Exception as exc:
        conn.close()
        return {"ok": True, "warning": str(exc)}

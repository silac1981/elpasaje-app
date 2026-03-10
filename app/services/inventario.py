# app/services/inventario.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import ep_core


@dataclass
class MovimientoStockIn:
    producto_id: str
    tipo_movimiento: str  # ENTRADA | SALIDA | AJUSTE
    cantidad: int
    motivo: str
    actor: str = "SYSTEM"
    referencia: Optional[str] = None


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_inventario_schema() -> None:
    """
    Crea tabla de movimientos de inventario si no existe.
    No toca productos ni otras tablas existentes.
    """
    conn = ep_core.get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventario_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            stock_anterior INTEGER NOT NULL,
            stock_nuevo INTEGER NOT NULL,
            motivo TEXT,
            actor TEXT,
            referencia TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_inv_mov_producto_fecha "
        "ON inventario_movimientos(producto_id, created_at)"
    )
    conn.commit()
    conn.close()


def get_producto_by_id(producto_id: str) -> Optional[Dict[str, Any]]:
    conn = ep_core.get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nombre, cliente_id, marca, descripcion, precio, stock, imagen, categoria
        FROM productos
        WHERE id = ?
        """,
        (producto_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "nombre": row[1],
        "cliente_id": row[2],
        "marca": row[3],
        "descripcion": row[4],
        "precio": row[5],
        "stock": row[6],
        "imagen": row[7],
        "categoria": row[8],
    }


def listar_productos() -> List[Dict[str, Any]]:
    conn = ep_core.get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nombre, cliente_id, marca, descripcion, precio, stock, imagen, categoria
        FROM productos
        ORDER BY nombre
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "nombre": r[1],
            "cliente_id": r[2],
            "marca": r[3],
            "descripcion": r[4],
            "precio": r[5],
            "stock": r[6],
            "imagen": r[7],
            "categoria": r[8],
        }
        for r in rows
    ]


def actualizar_stock(producto_id: str, nuevo_stock: int, actor: str = "SYSTEM", motivo: str = "Ajuste manual", referencia: Optional[str] = None) -> Dict[str, Any]:
    """
    Ajuste directo de stock + registro en inventario_movimientos.
    """
    if nuevo_stock < 0:
        raise ValueError("nuevo_stock no puede ser negativo")

    ensure_inventario_schema()

    conn = ep_core.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Producto no encontrado: {producto_id}")

    stock_anterior = int(row[0])
    stock_nuevo = int(nuevo_stock)
    delta = stock_nuevo - stock_anterior

    cur.execute("UPDATE productos SET stock = ? WHERE id = ?", (stock_nuevo, producto_id))
    cur.execute(
        """
        INSERT INTO inventario_movimientos
        (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, actor, referencia, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            producto_id,
            "AJUSTE",
            delta,
            stock_anterior,
            stock_nuevo,
            motivo,
            actor,
            referencia,
            _now_iso(),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "producto_id": producto_id,
        "stock_anterior": stock_anterior,
        "stock_nuevo": stock_nuevo,
        "delta": delta,
        "movimiento_tipo": "AJUSTE",
    }


def registrar_movimiento_stock(data: MovimientoStockIn) -> Dict[str, Any]:
    """
    ENTRADA/SALIDA/AJUSTE con persistencia transaccional en productos + inventario_movimientos.
    """
    tipo = data.tipo_movimiento.upper().strip()
    if tipo not in {"ENTRADA", "SALIDA", "AJUSTE"}:
        raise ValueError("tipo_movimiento inválido. Usar ENTRADA, SALIDA o AJUSTE")
    if data.cantidad <= 0 and tipo in {"ENTRADA", "SALIDA"}:
        raise ValueError("cantidad debe ser > 0 para ENTRADA/SALIDA")

    ensure_inventario_schema()

    conn = ep_core.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT stock FROM productos WHERE id = ?", (data.producto_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Producto no encontrado: {data.producto_id}")

    stock_anterior = int(row[0])

    if tipo == "ENTRADA":
        delta = int(data.cantidad)
        stock_nuevo = stock_anterior + delta
    elif tipo == "SALIDA":
        delta = -int(data.cantidad)
        stock_nuevo = stock_anterior + delta
        if stock_nuevo < 0:
            conn.close()
            raise ValueError("Stock insuficiente para salida")
    else:  # AJUSTE
        # Para AJUSTE interpretamos cantidad como stock final deseado
        stock_nuevo = int(data.cantidad)
        if stock_nuevo < 0:
            conn.close()
            raise ValueError("Stock final no puede ser negativo")
        delta = stock_nuevo - stock_anterior

    cur.execute(
        "UPDATE productos SET stock = ? WHERE id = ?",
        (stock_nuevo, data.producto_id),
    )
    cur.execute(
        """
        INSERT INTO inventario_movimientos
        (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, actor, referencia, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.producto_id,
            tipo,
            delta,
            stock_anterior,
            stock_nuevo,
            data.motivo,
            data.actor,
            data.referencia,
            _now_iso(),
        ),
    )

    conn.commit()
    conn.close()

    return {
        "producto_id": data.producto_id,
        "tipo_movimiento": tipo,
        "stock_anterior": stock_anterior,
        "stock_nuevo": stock_nuevo,
        "delta": delta,
    }


def listar_movimientos_stock(producto_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    ensure_inventario_schema()

    conn = ep_core.get_conn()
    cur = conn.cursor()

    if producto_id:
        cur.execute(
            """
            SELECT id, producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo,
                   motivo, actor, referencia, created_at
            FROM inventario_movimientos
            WHERE producto_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (producto_id, limit),
        )
    else:
        cur.execute(
            """
            SELECT id, producto_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo,
                   motivo, actor, referencia, created_at
            FROM inventario_movimientos
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "producto_id": r[1],
            "tipo_movimiento": r[2],
            "cantidad": r[3],
            "stock_anterior": r[4],
            "stock_nuevo": r[5],
            "motivo": r[6],
            "actor": r[7],
            "referencia": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]
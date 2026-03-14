"""Servicio de Inventario (Enterprise 2.0).

Este módulo NO abre conexiones SQLite directas.
Toda operación de datos se delega al núcleo `ep_core`.
"""

from __future__ import annotations

import pandas as pd

from ep_core import (
    DB_PATH,
    get_movimientos_stock,
    get_productos_export,
    registrar_movimiento_stock,
)


def listar_inventario(db_path: str = DB_PATH) -> pd.DataFrame:
    """Devuelve inventario actual de productos para operación."""
    return get_productos_export(db_path)


def movimientos_stock(limit: int = 100, db_path: str = DB_PATH) -> pd.DataFrame:
    """Devuelve historial de movimientos de stock (desc)."""
    return get_movimientos_stock(limit=limit, db_path=db_path)


def aplicar_movimiento_stock(
    producto_id: str,
    tipo: str,
    cantidad: int,
    motivo: str,
    actor_id: str = "OPS",
    db_path: str = DB_PATH,
) -> None:
    """Registra movimiento y actualiza stock.

    tipo: ENTRADA | SALIDA | AJUSTE
    """
    registrar_movimiento_stock(
        producto_id=producto_id,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo,
        actor_id=actor_id,
        db_path=db_path,
    )

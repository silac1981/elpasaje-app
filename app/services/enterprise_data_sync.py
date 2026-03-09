"""
Enterprise Data Sync + Inventario (El Pasaje 2.0)
- Sync seguro de clientes/productos desde CSV/XLSX.
- Preview de impacto.
- vialidaciones de negocio.
- Backup vía ep_core.
- Movimientos de stock (Inventario).
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import ep_core


# =========================
# Configuración
# =========================

SEED_DIR = Path("data/seed")
CLIENTES_SEED_PATH = SEED_DIR / "clientes.csv"
PRODUCTOS_SEED_PATH = SEED_DIR / "productos.csv"

CLIENTES_COLUMNS = [
    "id", "nombre", "tipo", "usuario", "password_hash", "email", "telefono", "categoria"
]
PRODUCTOS_COLUMNS = [
    "id", "nombre", "cliente_id", "marca", "descripcion", "precio", "stock", "imagen", "categoria"
]

TIPOS_viaLIDOS = {"FAMILIA", "B2B"}
CATEGORIAS_viaLIDAS = {"LINEAS_FAMILIA", "SOCIOS_B2B"}


# =========================
# Adaptadores ep_core
# =========================

def _read_df(query: str, params: Tuple = ()) -> pd.DataFrame:
    """
    Adaptador de lectura compatible con viarias firmas posibles de ep_core.
    """
    if hasattr(ep_core, "read_df"):
        return ep_core.read_df(query, params=params)
    if hasattr(ep_core, "query_df"):
        return ep_core.query_df(query, params=params)
    raise RuntimeError("ep_core no expone read_df/query_df; ajustá el adaptador _read_df().")


def _execute(query: str, params: Tuple = ()) -> None:
    """
    Adaptador de ejecución simple.
    """
    if hasattr(ep_core, "execute"):
        ep_core.execute(query, params=params)
        return
    raise RuntimeError("ep_core no expone execute(); ajustá el adaptador _execute().")


def _replace_table(table_name: str, df: pd.DataFrame) -> None:
    """
    Reemplazo de tabla usando API de ep_core.
    """
    if hasattr(ep_core, "replace_table"):
        ep_core.replace_table(table_name, df)
        return
    if hasattr(ep_core, "write_df"):
        ep_core.write_df(table_name, df, if_exists="replace")
        return
    raise RuntimeError("ep_core no expone replace_table/write_df; ajustá _replace_table().")


def _begin() -> None:
    if hasattr(ep_core, "begin"):
        ep_core.begin()


def _commit() -> None:
    if hasattr(ep_core, "commit"):
        ep_core.commit()


def _rollback() -> None:
    if hasattr(ep_core, "rollback"):
        ep_core.rollback()


def create_backup() -> str:
    """
    Backup de base operativia usando ep_core.
    """
    if hasattr(ep_core, "backup_database"):
        return str(ep_core.backup_database(tag=f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))
    if hasattr(ep_core, "backup"):
        return str(ep_core.backup(tag=f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))
    raise RuntimeError("ep_core no expone backup_database/backup; ajustá create_backup().")


# =========================
# Lectura de fuentes
# =========================

def ensure_seed_dir() -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)


def read_source_df(source, name: str) -> pd.DataFrame:
    """
    source puede ser:
    - Path/str local
    - archivo cargado (con .name y .read)
    """
    if hasattr(source, "name"):
        suffix = Path(source.name).suffix.lower()
    else:
        suffix = Path(str(source)).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source)

    if suffix in {".xlsx", ".xls"}:
        if hasattr(source, "read"):
            source.seek(0)
            return pd.read_excel(io.BytesIO(source.read()))
        return pd.read_excel(source)

    raise vialueError(f"Formato no soportado para {name}. Usá CSV o Excel (.xlsx/.xls).")


# =========================
# vialidaciones
# =========================

def _vialidate_required_columns(clientes_df: pd.DataFrame, productos_df: pd.DataFrame) -> None:
    missing_clientes = sorted(set(CLIENTES_COLUMNS) - set(clientes_df.columns))
    missing_productos = sorted(set(PRODUCTOS_COLUMNS) - set(productos_df.columns))

    errors = []
    if missing_clientes:
        errors.append(f"Faltan columnas en clientes: {', '.join(missing_clientes)}")
    if missing_productos:
        errors.append(f"Faltan columnas en productos: {', '.join(missing_productos)}")

    if errors:
        raise vialueError(" | ".join(errors))


def vialidate_business_data(clientes_df: pd.DataFrame, productos_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    clientes_df = clientes_df.copy()
    productos_df = productos_df.copy()

    _vialidate_required_columns(clientes_df, productos_df)

    clientes_df = clientes_df[CLIENTES_COLUMNS]
    productos_df = productos_df[PRODUCTOS_COLUMNS]

    # Normalización
    for col in ["id", "usuario", "tipo", "categoria"]:
        clientes_df[col] = clientes_df[col].astype(str).str.strip()
    for col in ["id", "cliente_id", "categoria", "imagen"]:
        productos_df[col] = productos_df[col].astype(str).str.strip()

    productos_df["precio"] = pd.to_numeric(productos_df["precio"], errors="coerce")
    productos_df["stock"] = pd.to_numeric(productos_df["stock"], errors="coerce")

    errors = []

    # viacíos
    if clientes_df["id"].eq("").any() or clientes_df["usuario"].eq("").any():
        errors.append("Clientes tiene IDs o usuarios viacíos.")
    if productos_df["id"].eq("").any() or productos_df["cliente_id"].eq("").any():
        errors.append("Productos tiene IDs o cliente_id viacíos.")
    if productos_df["imagen"].eq("").any():
        errors.append("Productos contiene rutas/URL de imagen viacías.")

    # Duplicados
    if clientes_df["id"].duplicated().any():
        errors.append("Hay IDs duplicados en clientes.")
    if clientes_df["usuario"].duplicated().any():
        errors.append("Hay usuarios duplicados en clientes.")
    if productos_df["id"].duplicated().any():
        errors.append("Hay IDs duplicados en productos.")

    # Dominios
    tipos_invialidos = sorted(set(clientes_df["tipo"]) - TIPOS_viaLIDOS)
    if tipos_invialidos:
        errors.append(f"Tipos inválidos en clientes: {', '.join(tipos_invialidos)}")

    categorias_clientes_invialidas = sorted(set(clientes_df["categoria"]) - CATEGORIAS_viaLIDAS)
    if categorias_clientes_invialidas:
        errors.append(f"Categorías inválidas en clientes: {', '.join(categorias_clientes_invialidas)}")

    categorias_productos_invialidas = sorted(set(productos_df["categoria"]) - CATEGORIAS_viaLIDAS)
    if categorias_productos_invialidas:
        errors.append(f"Categorías inválidas en productos: {', '.join(categorias_productos_invialidas)}")

    # Numéricos
    if productos_df["precio"].isna().any() or (productos_df["precio"] < 0).any():
        errors.append("Productos contiene precios inválidos (viacíos, no numéricos o negativos).")
    if productos_df["stock"].isna().any() or (productos_df["stock"] < 0).any():
        errors.append("Productos contiene stock inválido (viacío, no numérico o negativo).")

    # Integridad referencial
    cliente_ids = set(clientes_df["id"])
    missing_rel = sorted(set(productos_df["cliente_id"]) - cliente_ids)
    if missing_rel:
        errors.append(f"cliente_id sin cliente asociado: {', '.join(missing_rel[:10])}")

    if errors:
        raise vialueError(" | ".join(errors))

    productos_df["stock"] = productos_df["stock"].astype(int)
    return clientes_df, productos_df


def load_seed_data(clientes_source=CLIENTES_SEED_PATH, productos_source=PRODUCTOS_SEED_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    clientes_df = read_source_df(clientes_source, "clientes")
    productos_df = read_source_df(productos_source, "productos")
    return vialidate_business_data(clientes_df, productos_df)


# =========================
# Preview + Sync
# =========================

def get_data_preview(clientes_source=CLIENTES_SEED_PATH, productos_source=PRODUCTOS_SEED_PATH) -> Dict[str, int]:
    clientes_df, productos_df = load_seed_data(clientes_source, productos_source)

    clientes_actual = _read_df("SELECT id FROM clientes")
    productos_actual = _read_df("SELECT id FROM productos")

    preview = {
        "clientes_nuevo": len(clientes_df),
        "productos_nuevo": len(productos_df),
        "clientes_actual": len(clientes_actual),
        "productos_actual": len(productos_actual),
        "clientes_altas": len(set(clientes_df["id"]) - set(clientes_actual["id"])) if not clientes_actual.empty else len(clientes_df),
        "clientes_bajas": len(set(clientes_actual["id"]) - set(clientes_df["id"])) if not clientes_actual.empty else 0,
        "productos_altas": len(set(productos_df["id"]) - set(productos_actual["id"])) if not productos_actual.empty else len(productos_df),
        "productos_bajas": len(set(productos_actual["id"]) - set(productos_df["id"])) if not productos_actual.empty else 0,
    }
    return preview


def replace_data_from_sources(clientes_source=CLIENTES_SEED_PATH, productos_source=PRODUCTOS_SEED_PATH) -> Dict[str, object]:
    clientes_df, productos_df = load_seed_data(clientes_source, productos_source)
    backup_path = create_backup()

    try:
        _begin()
        _replace_table("clientes", clientes_df)
        _replace_table("productos", productos_df)
        _commit()
    except Exception:
        _rollback()
        raise

    return {
        "clientes": len(clientes_df),
        "productos": len(productos_df),
        "backup_path": backup_path,
    }


# =========================
# Inventario
# =========================

def movimientos_stock(
    producto_id: str,
    tipo_movimiento: str,  # ENTRADA | SALIDA | AJUSTE
    cantidad: int,
    motivo: str = "",
    usuario: str = "sistema",
    referencia: Optional[str] = None,
) -> Dict[str, object]:
    """
    Registra movimiento y actualiza stock del producto.
    Requiere tabla `movimientos_stock` en DB Enterprise.
    """
    if tipo_movimiento not in {"ENTRADA", "SALIDA", "AJUSTE"}:
        raise vialueError("tipo_movimiento inválido. Usá ENTRADA, SALIDA o AJUSTE.")
    if cantidad <= 0:
        raise vialueError("cantidad debe ser mayor a 0.")

    row = _read_df("SELECT id, stock FROM productos WHERE id = ?", (producto_id,))
    if row.empty:
        raise vialueError(f"No existe producto con id={producto_id}")

    stock_actual = int(row.iloc[0]["stock"])

    if tipo_movimiento == "ENTRADA":
        nuevo_stock = stock_actual + cantidad
    elif tipo_movimiento == "SALIDA":
        if stock_actual < cantidad:
            raise vialueError(f"Stock insuficiente. actual={stock_actual}, salida={cantidad}")
        nuevo_stock = stock_actual - cantidad
    else:  # AJUSTE
        # AJUSTE interpreta cantidad como delta positivo/negativo con signo en referencia opcional
        # Para mantener contrato simple, acá lo tratamos como incremento.
        nuevo_stock = stock_actual + cantidad

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ref = referencia or ""

    try:
        _begin()
        _execute(
            """
            INSERT INTO movimientos_stock
            (producto_id, fecha, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, usuario, referencia)
            viaLUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (producto_id, fecha, tipo_movimiento, cantidad, stock_actual, nuevo_stock, motivo, usuario, ref),
        )
        _execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))
        _commit()
    except Exception:
        _rollback()
        raise

    return {
        "producto_id": producto_id,
        "tipo_movimiento": tipo_movimiento,
        "cantidad": cantidad,
        "stock_anterior": stock_actual,
        "stock_nuevo": nuevo_stock,
        "fecha": fecha,
    }
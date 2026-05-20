"""utils/pricing.py — costo de piezas, carga de productos y materiales."""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db import engine
from utils.lineas import get_linea

COSTO_KG_DEFAULT = 2350.0


def calcular_costo_pieza(weight_gr, cost_kg=COSTO_KG_DEFAULT, merma=0.10, tipo_producto="propio_3d"):
    """Costo de filamento. Solo aplica markup x4 para propio_3d; otros tipos retornan 0."""
    if tipo_producto != "propio_3d":
        return 0.0
    return (weight_gr * (1 + merma) * cost_kg) / 1000


@st.cache_data(ttl=60)
def cargar_productos() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM products", engine)
    # Asegura columnas de Fase 2 con fallback si la migración no corrió aún
    if "tipo_producto" not in df.columns:
        df["tipo_producto"] = "propio_3d"
    if "visibilidad" not in df.columns:
        df["visibilidad"] = "publico"
    df["tipo_producto"] = df["tipo_producto"].fillna("propio_3d")
    df["visibilidad"]   = df["visibilidad"].fillna("publico")

    df["costo_unit"]     = df.apply(
        lambda r: calcular_costo_pieza(r["weight_gr"], tipo_producto=r["tipo_producto"]), axis=1
    ).astype(float)
    df["ganancia_unit"]  = df["price"] - df["costo_unit"]
    df["margen_pct"]     = (
        (df["ganancia_unit"] / df["price"].replace(0, float("nan")) * 100)
        .round(1)
        .fillna(0.0)
    )
    df["valor_stock"]    = df["price"] * df["stock"]
    df["costo_stock"]    = df["costo_unit"] * df["stock"]
    df["ganancia_stock"] = df["ganancia_unit"] * df["stock"]
    df["linea_nombre"]   = df["client_id"].apply(lambda c: get_linea(c)["nombre"])
    df["linea_color"]    = df["client_id"].apply(lambda c: get_linea(c)["color"])
    df["linea_emoji"]    = df["client_id"].apply(lambda c: get_linea(c)["emoji"])
    return df


def cargar_materiales() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM materials", engine)


def calcular_split(sku: str, monto_venta: float) -> dict:
    """Para producto compartido (Tipo C): retorna {linea_id: monto} según revenue_rules."""
    with engine.connect() as conn:
        result = pd.read_sql(
            text("SELECT linea_a, linea_b, split_a, split_b FROM revenue_rules WHERE product_sku=:sku AND activo=1"),
            conn, params={"sku": sku}
        )
    if result.empty:
        return {}
    row = result.iloc[0]
    return {
        row["linea_a"]: round(monto_venta * row["split_a"], 2),
        row["linea_b"]: round(monto_venta * row["split_b"], 2),
    }

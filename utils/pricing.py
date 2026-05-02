"""utils/pricing.py — costo de piezas, carga de productos y materiales."""
import streamlit as st
import pandas as pd
from utils.db import engine
from utils.lineas import get_linea

COSTO_KG_DEFAULT = 2350.0


def calcular_costo_pieza(weight_gr, cost_kg=COSTO_KG_DEFAULT, merma=0.10):
    return (weight_gr * (1 + merma) * cost_kg) / 1000


@st.cache_data(ttl=60)
def cargar_productos() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM products", engine)
    df["costo_unit"]     = df["weight_gr"].apply(lambda w: calcular_costo_pieza(w))
    df["ganancia_unit"]  = df["price"] - df["costo_unit"]
    df["margen_pct"]     = (df["ganancia_unit"] / df["price"] * 100).round(1)
    df["valor_stock"]    = df["price"] * df["stock"]
    df["costo_stock"]    = df["costo_unit"] * df["stock"]
    df["ganancia_stock"] = df["ganancia_unit"] * df["stock"]
    df["linea_nombre"]   = df["client_id"].apply(lambda c: get_linea(c)["nombre"])
    df["linea_color"]    = df["client_id"].apply(lambda c: get_linea(c)["color"])
    df["linea_emoji"]    = df["client_id"].apply(lambda c: get_linea(c)["emoji"])
    return df


def cargar_materiales() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM materials", engine)

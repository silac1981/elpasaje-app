"""utils/lineas.py — constantes de líneas, helpers de UI y cache de usuario."""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db import engine

# ── Configuración de líneas del ecosistema ────────────────────────────────────
LINEAS = {
    "admin":            {"nombre": "Administración",          "color": "#FF4B4B", "emoji": "⚡"},
    "fer_produccion":   {"nombre": "Producción",              "color": "#C9A84C", "emoji": "🛠"},
    "oasis_animal":     {"nombre": "Oasis Animal",            "color": "#F472B6", "emoji": "🐾"},
    "oasis_del_estero": {"nombre": "Oasis del Estero",        "color": "#3E9B53", "emoji": "🌱"},
    "pharma_delux":     {"nombre": "Pharma DeLux",            "color": "#0E7490", "emoji": "💊"},
    "aviation":         {"nombre": "Aviation Pro",            "color": "#1E5A8A", "emoji": "✈"},
    "olivia_coquette":  {"nombre": "Coquette",                "color": "#DB2777", "emoji": "🎀"},
    "francisco_sport":  {"nombre": "F-Zone",                  "color": "#F97316", "emoji": "⚡"},
    "constantino_tech": {"nombre": "Core Tech",               "color": "#0E7E78", "emoji": "⚙"},
    "vkhome_cliente":   {"nombre": "VK-Home",                 "color": "#A78BFA", "emoji": "🏡"},
    "agustina":         {"nombre": "Agustina",                "color": "#6366F1", "emoji": "✨"},
}

_BASE_PAGES = "https://silac1981.github.io/elpasaje-app"

PAGINAS_SOCIOS = {
    "admin":            "magnitud19",
    "fer_produccion":   "melomano",
    "olivia_coquette":  "coquette",
    "francisco_sport":  "sport",
    "constantino_tech": "core-tech",
    "pharma_delux":     "pharma-delux",
    "oasis_animal":     "oasis-animal",
    "oasis_del_estero": "oasis-estero",
    "aviation":         "aero-tech",
    "vkhome_cliente":   None,
    "agustina":         None,
}

# Colores de estado de pedidos, compartidos por todos los paneles
_SC = {
    "Pendiente":  "#F59E0B",
    "En Proceso": "#3B82F6",
    "Listo":      "#10B981",
    "Cancelado":  "#EF4444",
    "Entregado":  "#8B5CF6",
}

# Emojis y configs de estado para panel de producción
_EC = {
    "Pendiente":  {"color": "#F59E0B", "emoji": "⏳"},
    "En Proceso": {"color": "#3B82F6", "emoji": "🖨️"},
    "Listo":      {"color": "#22C55E", "emoji": "✅"},
    "Cancelado":  {"color": "#EF4444", "emoji": "❌"},
}


TIPOS_PRODUCTO = {
    "propio_3d":    {"label": "Propio 3D",          "color": "#3B82F6", "capa": 1},
    "linea_propio": {"label": "Propio de Linea",     "color": "#10B981", "capa": 2},
    "compartido":   {"label": "Compartido (Tipo C)", "color": "#F59E0B", "capa": 2},
    "kit_mixto":    {"label": "Kit Mixto (Tipo D)",  "color": "#8B5CF6", "capa": 2},
}

IP_RESTRINGIDA = ["deadpool", "marshall", "hello kitty", "pokeball", "ferrari", "baby yoda"]


def get_linea(cid: str) -> dict:
    """Retorna la configuración de color/nombre de una línea."""
    return LINEAS.get(cid, {"nombre": cid, "color": "#74798A"})


@st.cache_data(ttl=60)
def get_productos_capa2(client_id: str) -> pd.DataFrame:
    """Retorna productos de Capa 2 (Tipo B/C/D) de una línea, excluyendo propio_3d."""
    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text("SELECT * FROM products WHERE client_id=:cid AND tipo_producto != 'propio_3d'"),
                conn, params={"cid": client_id}
            )
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_lineas_usuario(uid: str) -> list:
    """Retorna las linea_ids visibles para un usuario.
    Para socio_multi lee tenant_lineas; para socio regular devuelve [uid].
    """
    with engine.connect() as _conn:
        rows = pd.read_sql(
            text("SELECT linea_id FROM tenant_lineas WHERE tenant_id=:uid"),
            _conn, params={"uid": uid}
        )
    return rows["linea_id"].tolist() if not rows.empty else [uid]

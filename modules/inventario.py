"""modules/inventario.py — Inventario Pro unificado."""
import streamlit as st


def render():
    from utils.pricing import cargar_productos
    st.markdown("<div class='main-header'><h1>📦 Inventario Unificado</h1><p>Control de stock en tiempo real</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        filtro_linea = st.selectbox("Filtrar por linea", ["Todas"] + sorted(df["linea_nombre"].unique().tolist()))
    with col_f2:
        busqueda = st.text_input("Buscar por SKU o nombre", placeholder="Ej: Kaizen, COQ-TEX...")
    df_f = df.copy()
    if filtro_linea != "Todas":
        df_f = df_f[df_f["linea_nombre"] == filtro_linea]
    if busqueda:
        mask = df_f["name"].str.contains(busqueda, case=False) | df_f["sku"].str.contains(busqueda, case=False)
        df_f = df_f[mask]
    st.caption(f"Mostrando {len(df_f)} productos")
    df_show = df_f[["linea_emoji","linea_nombre","name","sku","price","costo_unit","ganancia_unit","margen_pct","stock","valor_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Precio","Costo","Ganancia","Margen%","Stock","Valor Total"]
    st.dataframe(df_show.style.format({"Precio":"${:,.0f}","Costo":"${:,.0f}","Ganancia":"${:,.0f}","Margen%":"{:.1f}%","Valor Total":"${:,.0f}"}), use_container_width=True, hide_index=True)

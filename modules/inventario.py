"""modules/inventario.py — Inventario Pro con dark theme, filamentos y catálogo."""
import base64
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, get_linea
from utils.pricing import cargar_productos, cargar_materiales

_DARK = "#0D1117"
_CARD = "#161B22"
_BORDER = "#21262D"
_TEXT  = "#E6EDF3"
_MUTED = "#8B949E"
_BLUE  = "#58A6FF"

_TIPO_COLORS = {
    "PLA":  "#3FB950",
    "PETG": "#58A6FF",
    "ABS":  "#F59E0B",
    "TPU":  "#A78BFA",
    "ASA":  "#FB923C",
    "Nylon":"#34D399",
    "otro": "#6B7280",
}


def _dark_css():
    st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#0D1117!important}
.stTabs [data-baseweb="tab-list"]{background:#161B22!important;border-radius:12px!important;padding:4px!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#F0F6FC!important}
[data-testid="stMetricValue"]{color:#E6EDF3!important}
[data-testid="stMetricLabel"]{color:#8B949E!important}
.stMarkdown p,.stMarkdown span{color:#C9D1D9!important}
.stMarkdown strong{color:#F0F6FC!important}
.stTextInput label,.stSelectbox label,.stNumberInput label{color:#8B949E!important;font-weight:500!important}
details{background:#161B22!important;border-radius:12px!important;border:1px solid #21262D!important}
details summary{color:#E6EDF3!important}
[data-testid="stAlert"]{background:#1a2332!important;border-color:#30363D!important}
[data-testid="stFileUploaderDropzone"]{background:#161B22!important;border-color:#30363D!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stSelectbox"] div[data-baseweb="select"] div{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stDateInput"] input{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#6B7280!important}
</style>""", unsafe_allow_html=True)


def _kpi(col, valor, label, sub, color):
    col.markdown(
        f"<div style='background:{_CARD};border-radius:14px;padding:20px 16px;"
        f"border:1px solid {_BORDER};border-top:3px solid {color};text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:800;color:{color};line-height:1;'>{valor}</div>"
        f"<div style='font-size:0.75rem;font-weight:600;color:{_TEXT};margin-top:8px;'>{label}</div>"
        f"<div style='font-size:0.64rem;color:#6B7280;margin-top:4px;'>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def render():
    _dark_css()

    # ── Header ────────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#161B22,#0D1117);border-radius:16px;"
        f"padding:22px 28px;border:1px solid {_BORDER};border-left:4px solid {_BLUE};margin-bottom:16px;'>"
        f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;color:{_BLUE};text-transform:uppercase;'>EL PASAJE 3D STUDIO</div>"
        f"<div style='font-size:1.7rem;font-weight:800;color:{_TEXT};margin-top:6px;'>📦 Inventario Pro</div>"
        f"<div style='font-size:0.78rem;color:{_MUTED};margin-top:4px;'>Stock de filamentos · Catálogo de productos · Gestión de imágenes</div></div>",
        unsafe_allow_html=True,
    )

    mats = cargar_materiales()
    prods = cargar_productos()

    # ── KPIs globales ──────────────────────────────────────────────
    _total_kg   = round(mats["stock_gr"].sum() / 1000, 2) if not mats.empty else 0
    _total_val  = round((mats["stock_gr"] * mats["cost_kg"] / 1000).sum()) if not mats.empty else 0
    _criticos   = int((mats["stock_gr"] <= mats["stock_minimo_gr"]).sum()) if not mats.empty else 0
    _n_prods    = int(prods["activo"].sum()) if not prods.empty and "activo" in prods.columns else len(prods)

    k1, k2, k3, k4 = st.columns(4)
    _kpi(k1, f"{_total_kg:.1f} kg", "Total filamento", "en stock ahora", _BLUE)
    _kpi(k2, f"${_total_val:,.0f}", "Valor del stock", "a precio de costo", "#3FB950")
    _kpi(k3, str(_criticos), "Materiales críticos", "bajo el mínimo", "#EF4444" if _criticos else "#3FB950")
    _kpi(k4, str(_n_prods), "Productos activos", "en el catálogo", "#F59E0B")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    tab_fil, tab_cat = st.tabs(["🧵 Filamentos", "🏷️ Catálogo y Fotos"])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — FILAMENTOS
    # ══════════════════════════════════════════════════════════════
    with tab_fil:
        if mats.empty:
            st.markdown(
                f"<div style='background:{_CARD};border-radius:12px;padding:20px;border:1px solid {_BORDER};"
                f"text-align:center;color:{_MUTED};'>Sin materiales cargados. Agregá el primero desde el panel de Fer.</div>",
                unsafe_allow_html=True,
            )
        else:
            # ── Gráfico resumen por tipo ───────────────────────────
            _tipo_col = "tipo" if "tipo" in mats.columns else None
            if _tipo_col:
                _por_tipo = mats.groupby(_tipo_col)["stock_gr"].sum().reset_index()
                _por_tipo["kg"] = _por_tipo["stock_gr"] / 1000
                _colors_list = [_TIPO_COLORS.get(t, "#6B7280") for t in _por_tipo[_tipo_col]]

                _gc1, _gc2 = st.columns([2, 3])
                with _gc1:
                    fig_donut = go.Figure(go.Pie(
                        labels=_por_tipo[_tipo_col],
                        values=_por_tipo["kg"],
                        hole=0.62,
                        marker=dict(colors=_colors_list, line=dict(color="#0D1117", width=3)),
                        textinfo="none",
                        hovertemplate="<b>%{label}</b><br>%{value:.2f} kg<br>%{percent}<extra></extra>",
                    ))
                    fig_donut.update_layout(
                        paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
                        margin=dict(t=10, b=10, l=10, r=10),
                        showlegend=True,
                        legend=dict(font=dict(color="#C9D1D9", size=11), bgcolor="rgba(0,0,0,0)"),
                        annotations=[dict(
                            text=f"<b>{_total_kg:.1f}</b><br><span style='font-size:10px'>kg</span>",
                            x=0.5, y=0.5, font_size=18, font_color="#E6EDF3",
                            showarrow=False,
                        )],
                        height=260,
                    )
                    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

                with _gc2:
                    fig_bar = go.Figure()
                    for i, row in _por_tipo.iterrows():
                        _tc = _TIPO_COLORS.get(row[_tipo_col], "#6B7280")
                        fig_bar.add_trace(go.Bar(
                            x=[row[_tipo_col]], y=[row["kg"]],
                            marker_color=_tc,
                            marker_line=dict(width=0),
                            name=row[_tipo_col],
                            text=[f"{row['kg']:.2f} kg"],
                            textposition="outside",
                            textfont=dict(color="#C9D1D9", size=11),
                            hovertemplate=f"<b>{row[_tipo_col]}</b><br>{row['kg']:.2f} kg<extra></extra>",
                        ))
                    fig_bar.update_layout(
                        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
                        bargap=0.3, showlegend=False,
                        margin=dict(t=24, b=8, l=0, r=0),
                        height=260,
                        yaxis=dict(gridcolor="#21262D", color="#8B949E", tickformat=".1f", ticksuffix=" kg"),
                        xaxis=dict(color="#8B949E"),
                        font=dict(color="#8B949E"),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

            st.markdown(
                f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
                f"color:{_BLUE};margin:20px 0 12px;'>DETALLE POR MATERIAL</div>",
                unsafe_allow_html=True,
            )

            for _, _mat in mats.iterrows():
                _mid   = _mat["material_id"]
                _stock = float(_mat["stock_gr"])
                _min_g = float(_mat.get("stock_minimo_gr") or 200)
                _ckg   = float(_mat.get("cost_kg") or 0)
                _kg    = _stock / 1000
                _valor = _stock * _ckg / 1000
                _pct   = min(_stock / max(_min_g * 5, 1) * 100, 100)
                _tipo  = str(_mat.get("tipo") or "otro")
                _color_mat = str(_mat.get("color") or "")
                _mc    = "#22C55E" if _stock > _min_g * 2 else ("#F59E0B" if _stock > _min_g else "#EF4444")
                _tc    = _TIPO_COLORS.get(_tipo, "#6B7280")
                _alerta = "⚠️ " if _stock <= _min_g else ""

                with st.expander(f"{_alerta}🧵 {_mat['name']}  ·  {_kg:.2f} kg  ·  ${_valor:,.0f}"):
                    _dc1, _dc2, _dc3, _dc4 = st.columns(4)
                    _dc1.metric("Stock", f"{_stock:.0f} g / {_kg:.2f} kg")
                    _dc2.metric("Precio/kg", f"${_ckg:,.0f}")
                    _dc3.metric("Valor en stock", f"${_valor:,.0f}")
                    _dc4.metric("Mínimo", f"{_min_g:.0f} g")

                    st.markdown(
                        f"<div style='margin:10px 0 4px;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                        f"<span style='font-size:0.72rem;color:{_mc};font-weight:700;'>{_stock:.0f} g de ~{int(_min_g*5)} g referencia</span>"
                        f"<span style='font-size:0.7rem;color:{_tc};font-weight:700;background:{_tc}22;padding:2px 8px;border-radius:99px;'>{_tipo}</span></div>"
                        f"<div style='background:#21262D;border-radius:999px;height:10px;overflow:hidden;'>"
                        f"<div style='width:{_pct:.0f}%;background:{_mc};height:100%;border-radius:999px;transition:width 0.3s;'></div></div>"
                        f"{'<div style=\"font-size:0.7rem;color:#6B7280;margin-top:4px;\">Color: ' + _color_mat + '</div>' if _color_mat else ''}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — CATÁLOGO Y FOTOS
    # ══════════════════════════════════════════════════════════════
    with tab_cat:
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
            f"color:{_BLUE};margin-bottom:12px;'>CATÁLOGO DE PRODUCTOS</div>",
            unsafe_allow_html=True,
        )

        if prods.empty:
            st.caption("Sin productos cargados.")
        else:
            # Filtros
            _if1, _if2, _if3 = st.columns(3)
            with _if1:
                _filt_linea = st.selectbox("Línea", ["Todas"] + sorted(prods["linea_nombre"].unique().tolist()), key="inv_filt_linea")
            with _if2:
                _filt_busq = st.text_input("Buscar", placeholder="SKU o nombre…", key="inv_busq")
            with _if3:
                _filt_sin_img = st.checkbox("Solo sin imagen", key="inv_sin_img")

            _pf = prods.copy()
            if _filt_linea != "Todas":
                _pf = _pf[_pf["linea_nombre"] == _filt_linea]
            if _filt_busq:
                _m = _pf["name"].str.contains(_filt_busq, case=False) | _pf["sku"].str.contains(_filt_busq, case=False)
                _pf = _pf[_m]
            if _filt_sin_img:
                _pf = _pf[_pf["imagen_url"].isna() | (_pf["imagen_url"] == "")]

            st.caption(f"{len(_pf)} productos")

            # Cards
            _cols = st.columns(3)
            for _ci, (_, _pr) in enumerate(_pf.iterrows()):
                _linea_color = _pr.get("linea_color") or "#6366F1"
                _img = str(_pr.get("imagen_url") or "")
                _has_img = bool(_img and (_img.startswith("http") or _img.startswith("data:")))

                with _cols[_ci % 3]:
                    # Imagen o placeholder
                    if _has_img:
                        try:
                            st.image(_img, use_column_width=True)
                        except Exception:
                            _has_img = False
                    if not _has_img:
                        st.markdown(
                            f"<div style='background:linear-gradient(135deg,{_linea_color}33,{_linea_color}11);"
                            f"border-radius:10px;height:80px;display:flex;align-items:center;justify-content:center;"
                            f"border:1px dashed {_linea_color}44;margin-bottom:4px;'>"
                            f"<span style='font-size:1.6rem;'>{_pr.get('linea_emoji','📦')}</span></div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"<div style='background:{_CARD};border-radius:10px;padding:10px 12px;"
                        f"border:1px solid {_BORDER};border-left:3px solid {_linea_color};margin-bottom:4px;'>"
                        f"<div style='font-size:0.6rem;color:{_linea_color};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>{_pr['sku']}</div>"
                        f"<div style='font-size:0.85rem;font-weight:700;color:{_TEXT};margin-top:2px;'>{_pr['name']}</div>"
                        f"<div style='font-size:0.72rem;color:{_MUTED};margin-top:2px;'>{_pr.get('linea_nombre','')} · ${float(_pr['price']):,.0f}</div></div>",
                        unsafe_allow_html=True,
                    )

                    # Upload imagen
                    with st.expander("📷 Subir / cambiar imagen"):
                        _up = st.file_uploader(
                            "Imagen del producto",
                            type=["jpg", "jpeg", "png", "webp"],
                            key=f"inv_img_{_pr['sku']}",
                            label_visibility="collapsed",
                        )
                        if _up is not None:
                            _b64 = base64.b64encode(_up.read()).decode("utf-8")
                            _mime = "image/jpeg" if _up.type == "image/jpeg" else "image/png"
                            _data_uri = f"data:{_mime};base64,{_b64}"
                            if st.button("Guardar imagen", key=f"inv_save_{_pr['sku']}", type="primary", use_container_width=True):
                                with engine.connect() as _conn:
                                    _conn.execute(
                                        text("UPDATE products SET imagen_url=:url WHERE sku=:sku"),
                                        {"url": _data_uri, "sku": _pr["sku"]},
                                    )
                                    _conn.commit()
                                st.success("Imagen guardada ✅")
                                st.rerun()
                        if _has_img:
                            if st.button("🗑 Quitar imagen", key=f"inv_del_{_pr['sku']}", use_container_width=True):
                                with engine.connect() as _conn:
                                    _conn.execute(
                                        text("UPDATE products SET imagen_url=NULL WHERE sku=:sku"),
                                        {"sku": _pr["sku"]},
                                    )
                                    _conn.commit()
                                st.rerun()

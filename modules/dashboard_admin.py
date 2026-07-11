"""modules/dashboard_admin.py — Dashboard principal de Alejandra."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from utils.db import engine
from utils.lineas import get_linea
from utils.orders import avanzar_estado as _avanzar_estado

# ── Design system tokens (deben coincidir con main.py :root) ──────────────────
_BG      = "#EBE6DC"   # --bg
_SURFACE = "#FAF8F3"   # --surface
_INK     = "#16181F"   # --ink
_INK2    = "#3A3E4A"   # --ink-2
_MUTED   = "#74798A"   # --muted
_LINE    = "#DCD5C7"   # --line

_PLOT_LAYOUT = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_SURFACE,
    font=dict(family="Source Sans 3", color=_INK, size=11),
    margin=dict(l=10, r=10, t=10, b=40),
    xaxis=dict(gridcolor=_LINE, linecolor=_LINE, tickcolor=_LINE, zerolinecolor=_LINE),
    yaxis=dict(gridcolor=_LINE, linecolor=_LINE, tickcolor=_LINE, zerolinecolor=_LINE),
)

_LINEA_COLORS = {
    "Administración":   "#FF4B4B",
    "Producción":       "#C9A84C",
    "Oasis Animal":     "#F472B6",
    "Oasis del Estero": "#3E9B53",
    "Pharma DeLux":     "#0E7490",
    "Aviation Pro":     "#1E5A8A",
    "Coquette":         "#DB2777",
    "F-Zone":           "#F97316",
    "Core Tech":        "#0E7E78",
    "VK-Home":          "#A78BFA",
    "Agustina":         "#6366F1",
}


def _dash_main():
    st.markdown("<div class='main-header'><h1>📊 Dashboard de Magnitud</h1><p>Inteligencia de negocios en tiempo real · Ecosistema El Pasaje</p></div>", unsafe_allow_html=True)
    from utils.pricing import cargar_productos, cargar_materiales
    df   = cargar_productos()
    mats = cargar_materiales()
    total_stock    = df["valor_stock"].sum()
    total_costo    = df["costo_stock"].sum()
    total_ganancia = df["ganancia_stock"].sum()
    margen_global  = (total_ganancia / total_stock * 100) if total_stock > 0 else 0
    val_mat        = (mats["stock_gr"] * mats["cost_kg"] / 1000).sum()
    c1, c2, c3, c4 = st.columns(4)
    for col, title, val, sub, color in [
        (c1, "💰 Valor Total Stock",   f"${total_stock:,.0f}",    "Precio venta × unidades",   "#1E3A8A"),
        (c2, "📈 Ganancia Proyectada", f"${total_ganancia:,.0f}", f"Margen: {margen_global:.1f}%", "#059669"),
        (c3, "🏭 Costo Produccion",    f"${total_costo:,.0f}",    "Filamento + merma 10%",     "#DC2626"),
        (c4, "🧵 Stock Materiales",    f"${val_mat:,.0f}",        "Valor bobinas activas",     "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1.6, 1])
    df_linea = df.groupby("linea_nombre").agg(valor_stock=("valor_stock","sum"),ganancia=("ganancia_stock","sum"),costo=("costo_stock","sum")).reset_index().sort_values("valor_stock", ascending=False)
    with col_a:
        st.markdown("<div class='section-title'>💹 Valor de Stock por Linea</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Costo Produccion", x=df_linea["linea_nombre"], y=df_linea["costo"], marker_color="#EF4444", opacity=0.85))
        fig_bar.add_trace(go.Bar(name="Ganancia Neta", x=df_linea["linea_nombre"], y=df_linea["ganancia"], marker_color="#22C55E", opacity=0.85))
        fig_bar.update_layout(**{**_PLOT_LAYOUT, "barmode": "stack", "height": 320,
            "legend": dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color=_INK)),
            "xaxis": dict(**_PLOT_LAYOUT["xaxis"], tickangle=-20),
            "yaxis": dict(**_PLOT_LAYOUT["yaxis"], tickprefix="$", tickformat=",.0f")})
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("<div class='section-title'>🥧 Distribucion del Ecosistema</div>", unsafe_allow_html=True)
        fig_pie = px.pie(df_linea, values="valor_stock", names="linea_nombre",
                         color="linea_nombre", color_discrete_map=_LINEA_COLORS, hole=0.45)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11,
                              textfont_color="white")
        fig_pie.update_layout(showlegend=False, height=320, margin=dict(l=10,r=10,t=10,b=10),
                              paper_bgcolor=_BG, font=dict(color=_INK))
        st.plotly_chart(fig_pie, use_container_width=True)
    col_c, col_d = st.columns([1.6, 1])
    with col_c:
        st.markdown("<div class='section-title'>🎯 Ganancia Neta por Producto</div>", unsafe_allow_html=True)
        df_prod = df.sort_values("ganancia_stock", ascending=True)
        fig_h = go.Figure(go.Bar(x=df_prod["ganancia_stock"], y=df_prod["name"], orientation="h", marker_color=["#22C55E" if g > 0 else "#EF4444" for g in df_prod["ganancia_stock"]], text=[f"${v:,.0f}" for v in df_prod["ganancia_stock"]], textposition="outside"))
        fig_h.update_layout(**{**_PLOT_LAYOUT, "height": 320, "margin": dict(l=10,r=80,t=10,b=10),
            "xaxis": dict(**_PLOT_LAYOUT["xaxis"], tickprefix="$", tickformat=",.0f"),
            "yaxis": dict(**_PLOT_LAYOUT["yaxis"], automargin=True)})
        st.plotly_chart(fig_h, use_container_width=True)
    with col_d:
        st.markdown("<div class='section-title'>🧵 Estado de Materiales</div>", unsafe_allow_html=True)
        for _, mat in mats.iterrows():
            pct = min(mat["stock_gr"] / 1000 * 100, 100)
            color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
            val_m = mat["stock_gr"] * mat["cost_kg"] / 1000
            alerta = " ⚠️ STOCK BAJO" if pct <= 10 else (" ⚡ Atención" if pct <= 30 else "")
            st.markdown(f"<div style='background:{_SURFACE};border-radius:12px;padding:16px;border:1px solid {_LINE};margin-bottom:12px;'><div style='display:flex;justify-content:space-between;margin-bottom:8px;'><b style='color:{_INK}'>{mat['name']}</b><span style='color:{color_m};font-weight:600'>{mat['stock_gr']:.0f}g{alerta}</span></div><div style='background:{_LINE};border-radius:999px;height:8px;overflow:hidden;'><div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div></div><div style='display:flex;justify-content:space-between;margin-top:6px;font-size:0.75rem;color:{_MUTED};'><span>${mat['cost_kg']:,.0f}/kg</span><span>Valor: ${val_m:,.0f}</span></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📋 Analisis Completo por Producto</div>", unsafe_allow_html=True)
    df_show = df[["linea_emoji","linea_nombre","name","sku","weight_gr","costo_unit","price","ganancia_unit","margen_pct","stock","ganancia_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Peso(g)","Costo Unit","Precio Venta","Ganancia Unit","Margen %","Stock","Ganancia Total"]
    def color_margen(val):
        if isinstance(val, (int, float)):
            if val >= 60: return "color:#059669;font-weight:600"
            if val >= 30: return "color:#D97706"
            return "color:#DC2626;font-weight:600"
        return ""
    st.dataframe(df_show.style.format({"Costo Unit":"${:,.0f}","Precio Venta":"${:,.0f}","Ganancia Unit":"${:,.0f}","Ganancia Total":"${:,.0f}","Margen %":"{:.1f}%"}).map(color_margen, subset=["Margen %"]), use_container_width=True, hide_index=True)
    criticos = df[df["stock"] <= 15]
    if not criticos.empty:
        st.markdown("<div class='section-title'>🚨 Alerta Stock Bajo (≤ 15 unidades)</div>", unsafe_allow_html=True)
        for _, row in criticos.iterrows():
            lvl = get_linea(row["client_id"])
            st.markdown(f"<div class='stock-critico'><b>{lvl['emoji']} {row['name']}</b> · SKU: {row['sku']} &nbsp;|&nbsp; Stock: <b style='color:#EF4444'>{int(row['stock'])} uds</b> &nbsp;|&nbsp; Pedido sugerido: 20 uds → ${row['price']*20:,.0f} potencial</div>", unsafe_allow_html=True)

    # ── Facturación real desde órdenes ─────────────────────────
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📅 Facturación Real — Órdenes Completadas</div>", unsafe_allow_html=True)

    # P&L real: costo desde weight_gr, split 50/50
    try:
        _pnl = pd.read_sql("""
            SELECT
                SUM(oi.precio_unitario * oi.cantidad) AS facturado,
                SUM(CASE WHEN p.tipo_producto='propio_3d'
                    THEN p.weight_gr * 1.10 * 2350.0 / 1000.0 * oi.cantidad
                    ELSE 0 END) AS costo_prod,
                COUNT(DISTINCT o.id) AS n_pedidos
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.sku = oi.product_sku
            WHERE o.status IN ('Listo','Entregado')
        """, engine).iloc[0]
        _pnl_fac   = float(_pnl["facturado"] or 0)
        _pnl_cost  = float(_pnl["costo_prod"] or 0)
        _pnl_gb    = _pnl_fac - _pnl_cost
        _pnl_soc   = round(_pnl_gb * 0.5)
        _pnl_ep    = _pnl_gb - _pnl_soc
        _pnl_nped  = int(_pnl["n_pedidos"] or 0)
    except Exception:
        _pnl_fac = _pnl_cost = _pnl_gb = _pnl_soc = _pnl_ep = 0.0
        _pnl_nped = 0

    _pa, _pb, _pc, _pd, _pe = st.columns(5)
    for _pcol, _pv, _pl, _ps, _pcolor in [
        (_pa, f"${_pnl_fac:,.0f}",  "💰 Facturado real",      f"{_pnl_nped} pedidos completados",    "#3B82F6"),
        (_pb, f"${_pnl_cost:,.0f}", "🧵 Costo producción",    "filamento · merma 10% · $2350/kg",    "#F59E0B"),
        (_pc, f"${_pnl_gb:,.0f}",   "📊 Ganancia bruta",      "facturado − costo",                   "#58A6FF"),
        (_pd, f"${_pnl_soc:,.0f}",  "🤝 Cuota socios 50%",   "acumulado todos los socios",           "#A855F7"),
        (_pe, f"${_pnl_ep:,.0f}",   "🏠 Para El Pasaje 50%", "antes de overhead",                   "#22C55E"),
    ]:
        with _pcol:
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:12px;padding:14px 10px;"
                f"border:1px solid {_LINE};border-top:3px solid {_pcolor};"
                f"text-align:center;margin-bottom:14px;'>"
                f"<div style='font-size:1.2rem;font-weight:800;color:{_pcolor};line-height:1;'>{_pv}</div>"
                f"<div style='font-size:0.65rem;font-weight:600;color:{_INK};margin-top:6px;'>{_pl}</div>"
                f"<div style='font-size:0.58rem;color:{_MUTED};margin-top:3px;'>{_ps}</div></div>",
                unsafe_allow_html=True,
            )

    try:
        _df_fac = pd.read_sql("""
            SELECT SUBSTR(o.date, 1, 7) AS mes,
                   o.client_id,
                   COUNT(DISTINCT o.id) AS pedidos,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado,
                   SUM(CASE WHEN p.tipo_producto='propio_3d'
                       THEN p.weight_gr * 1.10 * 2350.0 / 1000.0 * oi.cantidad
                       ELSE 0 END) AS costo_prod
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON p.sku = oi.product_sku
            WHERE o.status = 'Listo'
            GROUP BY mes, o.client_id
            ORDER BY mes
        """, engine)
        _df_fac_mes = pd.read_sql("""
            SELECT SUBSTR(o.date, 1, 7) AS mes,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status = 'Listo'
            GROUP BY mes ORDER BY mes
        """, engine)
    except Exception:
        _df_fac = pd.DataFrame()
        _df_fac_mes = pd.DataFrame()

    _fa, _fb = st.columns([1.6, 1])
    with _fa:
        if not _df_fac_mes.empty:
            _fig_fac = go.Figure()
            _fig_fac.add_trace(go.Bar(x=_df_fac_mes["mes"], y=_df_fac_mes["facturado"],
                marker_color="#3B82F6", name="Facturado"))
            _fig_fac.update_layout(**{**_PLOT_LAYOUT, "height": 280,
                "yaxis": dict(**_PLOT_LAYOUT["yaxis"], tickprefix="$", tickformat=",.0f")})
            st.plotly_chart(_fig_fac, use_container_width=True)
        else:
            st.info("Sin pedidos completados aún.")
    with _fb:
        if not _df_fac.empty:
            _fac_por_linea = _df_fac.groupby("client_id")["facturado"].sum().reset_index()
            _fac_por_linea["linea"] = _fac_por_linea["client_id"].apply(
                lambda c: f"{get_linea(c)['emoji']} {get_linea(c)['nombre']}")
            _fac_por_linea = _fac_por_linea.sort_values("facturado", ascending=False)
            for _, _flr in _fac_por_linea.iterrows():
                _lc = get_linea(_flr["client_id"])
                _lc_color = _lc["color"]
                st.markdown(f"<div style='background:{_SURFACE};border-radius:8px;padding:10px 14px;margin-bottom:6px;border:1px solid {_LINE};display:flex;justify-content:space-between;align-items:center;'><span style='font-weight:600;color:{_INK};'>{_lc['emoji']} {_lc['nombre']}</span><span style='font-weight:800;color:{_lc_color};'>${_flr['facturado']:,.0f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Sin datos de facturación por línea.")

    # ── Canales de contacto y adquisición ─────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🌐 Canales de Contacto y Adquisición</div>", unsafe_allow_html=True)
    try:
        _df_senales = pd.read_sql("""
            SELECT canal, reaccion, linea, COUNT(*) AS total
            FROM senales_mercado
            WHERE canal IS NOT NULL AND canal != ''
            GROUP BY canal, reaccion, linea
            ORDER BY total DESC
        """, engine)
        _df_canal_tot = pd.read_sql("""
            SELECT canal, COUNT(*) AS contactos,
                   SUM(CASE WHEN reaccion IN ('Le encantó','Pidió muestra','Quiere hablar con alguien') THEN 1 ELSE 0 END) AS calientes
            FROM senales_mercado WHERE canal IS NOT NULL AND canal != ''
            GROUP BY canal ORDER BY contactos DESC
        """, engine)
    except Exception:
        _df_senales = pd.DataFrame()
        _df_canal_tot = pd.DataFrame()

    _ca, _cb = st.columns(2)
    with _ca:
        st.markdown("<div style='font-size:0.68rem;color:#6B7280;font-weight:700;letter-spacing:1px;margin-bottom:8px;'>SEÑALES DE MERCADO POR CANAL</div>", unsafe_allow_html=True)
        if not _df_canal_tot.empty:
            _canal_colors = {"Instagram":"#E1306C","TikTok":"#010101","WhatsApp":"#25D366",
                             "Presencial":"#1E3A8A","Email":"#3B82F6","Otro":"#9CA3AF"}
            for _, _cr in _df_canal_tot.iterrows():
                _cc = _canal_colors.get(_cr["canal"], "#6B7280")
                _pct_cal = int(_cr["calientes"] / max(_cr["contactos"],1) * 100)
                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:8px;padding:10px 14px;margin-bottom:6px;border:1px solid {_LINE};'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                    f"<span style='font-weight:700;color:{_INK};'>{_cr['canal']}</span>"
                    f"<span style='color:{_cc};font-weight:700;'>{int(_cr['contactos'])} contactos</span></div>"
                    f"<div style='background:{_LINE};border-radius:999px;height:6px;overflow:hidden;'>"
                    f"<div style='width:{_pct_cal}%;background:{_cc};height:100%;border-radius:999px;'></div></div>"
                    f"<div style='font-size:0.68rem;color:{_MUTED};margin-top:3px;'>{int(_cr['calientes'])} señales calientes ({_pct_cal}%)</div>"
                    f"</div>", unsafe_allow_html=True)
        else:
            st.info("Registrá señales de mercado para ver estadísticas de canal.")
    with _cb:
        st.markdown("<div style='font-size:0.68rem;color:#6B7280;font-weight:700;letter-spacing:1px;margin-bottom:8px;'>TIPO DE REACCIÓN POR CANAL</div>", unsafe_allow_html=True)
        if not _df_senales.empty:
            _fig_react = px.bar(
                _df_senales.groupby(["canal","reaccion"])["total"].sum().reset_index(),
                x="canal", y="total", color="reaccion",
                color_discrete_sequence=px.colors.qualitative.Set2,
                height=280
            )
            _fig_react.update_layout(**{**_PLOT_LAYOUT, "height": 280,
                "legend": dict(orientation="h", yanchor="bottom", y=1.02, font_size=10, font=dict(color=_INK)),
                "xaxis_title": "", "yaxis_title": "Señales"})
            st.plotly_chart(_fig_react, use_container_width=True)
        else:
            st.info("Sin señales registradas aún.")

    # ── Ranking Líneas por Facturación Total ───────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🏆 Ranking Líneas por Facturación Total</div>", unsafe_allow_html=True)
    try:
        _df_rank = pd.read_sql("""
            SELECT o.client_id,
                   COUNT(DISTINCT o.id) AS pedidos_completados,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado_total,
                   MAX(o.date) AS ultimo_pedido
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status = 'Listo'
            GROUP BY o.client_id ORDER BY facturado_total DESC
        """, engine)
    except Exception:
        _df_rank = pd.DataFrame()
    if not _df_rank.empty:
        _rk_cols = st.columns(min(len(_df_rank), 4))
        for _rki, (_, _rkr) in enumerate(_df_rank.head(4).iterrows()):
            _rkl = get_linea(_rkr["client_id"])
            with _rk_cols[_rki]:
                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:14px;padding:16px;border:1px solid {_LINE};text-align:center;border-top:4px solid {_rkl['color']};'>"
                    f"<div style='font-size:1.6rem;'>{_rkl['emoji']}</div>"
                    f"<div style='font-weight:700;color:{_INK};font-size:0.82rem;margin-top:4px;'>{_rkl['nombre']}</div>"
                    f"<div style='font-size:1.3rem;font-weight:800;color:{_rkl['color']};margin-top:6px;'>${_rkr['facturado_total']:,.0f}</div>"
                    f"<div style='font-size:0.68rem;color:{_MUTED};margin-top:2px;'>{int(_rkr['pedidos_completados'])} pedidos · último {str(_rkr['ultimo_pedido'])[:10]}</div>"
                    f"</div>", unsafe_allow_html=True)
    else:
        st.info("Completá pedidos para ver el ranking de facturación.")

    # ── Novedades del ecosistema — últimos 7 días ──────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🆕 Novedades del Ecosistema (últimos 7 días)</div>", unsafe_allow_html=True)
    try:
        _df_nov = pd.read_sql("""
            SELECT sku, name, price, stock, client_id, tipo_producto, visibilidad, fecha_alta
            FROM products
            WHERE tipo_producto != 'propio_3d'
              AND fecha_alta >= date('now', '-7 days')
            ORDER BY fecha_alta DESC
        """, engine)
    except Exception:
        _df_nov = pd.DataFrame()

    _TIPO_LABEL_D = {"linea_propio": "Tipo B", "compartido": "Tipo C", "kit_mixto": "Tipo D"}
    _VIS_C_D      = {"publico": "#10B981", "borrador": "#F59E0B", "pausado": "#6B7280"}
    _VIS_L_D      = {"publico": "Publico",  "borrador": "Borrador",  "pausado": "Pausado"}

    if _df_nov.empty:
        st.markdown(f"<div style='background:{_SURFACE};border-radius:12px;padding:14px 20px;border:1px solid {_LINE};color:{_MUTED};'>Sin productos nuevos de Capa 2 en los últimos 7 días.</div>", unsafe_allow_html=True)
    else:
        _nov_cols = st.columns(3)
        for _ni, (_, _nr) in enumerate(_df_nov.head(6).iterrows()):
            _nl  = get_linea(_nr["client_id"])
            _nvis = _nr.get("visibilidad", "borrador") or "borrador"
            _nvc  = _VIS_C_D.get(_nvis, "#6B7280")
            _nvl  = _VIS_L_D.get(_nvis, _nvis)
            _ntl  = _TIPO_LABEL_D.get(_nr.get("tipo_producto", ""), "Capa 2")
            with _nov_cols[_ni % 3]:
                st.markdown(f"""
<div style='background:{_SURFACE};border-radius:12px;padding:14px 16px;margin-bottom:10px;
     border:1px solid {_LINE};border-top:3px solid {_nl["color"]};'>
  <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
    <div style='font-size:0.75rem;color:{_nl["color"]};font-weight:700;'>{_nl["emoji"]} {_nl["nombre"]}</div>
    <div style='display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end;'>
      <span style='background:{_nvc}18;color:{_nvc};border:1px solid {_nvc}44;border-radius:99px;padding:2px 7px;font-size:0.6rem;font-weight:700;'>{_nvl}</span>
      <span style='background:#EEF2FF;color:#6366F1;border-radius:99px;padding:2px 7px;font-size:0.6rem;font-weight:700;'>{_ntl}</span>
    </div>
  </div>
  <div style='font-size:0.88rem;font-weight:700;color:{_INK};margin-top:6px;'>{_nr['name']}</div>
  <div style='display:flex;justify-content:space-between;margin-top:8px;align-items:center;'>
    <span style='font-size:0.72rem;color:{_MUTED};'>SKU: {_nr.get('sku','')}</span>
    <span style='font-size:0.9rem;font-weight:800;color:{_nl["color"]};'>${float(_nr.get('price', 0) or 0):,.0f}</span>
  </div>
  <div style='font-size:0.63rem;color:{_MUTED};margin-top:2px;'>Alta: {str(_nr.get('fecha_alta', ''))[:10]}</div>
</div>""", unsafe_allow_html=True)

    # ── Gestión de productos — Pausa y Visibilidad ─────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>⚙️ Gestión de Productos — Pausa y Visibilidad</div>", unsafe_allow_html=True)

    _ga, _gb, _gc = st.columns(3)
    with _ga:
        _g_linea = st.selectbox(
            "Filtrar línea",
            ["Todas"] + sorted(df["client_id"].dropna().unique().tolist()),
            format_func=lambda x: "Todas" if x == "Todas" else f"{get_linea(x)['emoji']} {get_linea(x)['nombre']}",
            key="g_linea_filter"
        )
    with _gb:
        _g_tipo = st.selectbox(
            "Tipo de producto",
            ["Todos", "propio_3d", "linea_propio", "compartido", "kit_mixto"],
            format_func=lambda x: "Todos" if x == "Todos" else x.replace("_", " ").title(),
            key="g_tipo_filter"
        )
    with _gc:
        _g_vis = st.selectbox(
            "Visibilidad actual",
            ["Todos", "publico", "borrador", "pausado"],
            format_func=lambda x: "Todos" if x == "Todos" else x.title(),
            key="g_vis_filter"
        )

    df_g = df.copy()
    if _g_linea != "Todas":
        df_g = df_g[df_g["client_id"] == _g_linea]
    if _g_tipo != "Todos" and "tipo_producto" in df_g.columns:
        df_g = df_g[df_g["tipo_producto"] == _g_tipo]
    if _g_vis != "Todos" and "visibilidad" in df_g.columns:
        df_g = df_g[df_g["visibilidad"] == _g_vis]

    if df_g.empty:
        st.info("No hay productos con ese filtro.")
    else:
        df_ed = df_g[["sku","name","linea_nombre","tipo_producto","visibilidad","activo","price","stock"]].copy()
        df_ed = df_ed.rename(columns={
            "name": "Producto", "linea_nombre": "Linea",
            "tipo_producto": "Tipo", "visibilidad": "Visibilidad",
            "activo": "Activo", "price": "Precio", "stock": "Stock"
        }).reset_index(drop=True)

        df_edited = st.data_editor(
            df_ed,
            column_config={
                "sku":         st.column_config.TextColumn("SKU",      disabled=True, width="small"),
                "Producto":    st.column_config.TextColumn("Producto", disabled=True),
                "Linea":       st.column_config.TextColumn("Línea",    disabled=True, width="small"),
                "Tipo":        st.column_config.TextColumn("Tipo",     disabled=True, width="small"),
                "Precio":      st.column_config.NumberColumn("Precio", disabled=False, format="$%d", min_value=0, step=100, width="small"),
                "Stock":       st.column_config.NumberColumn("Stock",  disabled=True, width="small"),
                "Visibilidad": st.column_config.SelectboxColumn("Visibilidad", options=["publico","borrador","pausado"], width="small"),
                "Activo":      st.column_config.CheckboxColumn("Activo", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            key="gestion_editor"
        )
        st.caption("💡 Podés editar Precio, Visibilidad y Activo directamente en la tabla. Guardá al final.")

        if st.button("💾 Guardar cambios de precios / visibilidad", use_container_width=False, type="primary"):
            _changed_mask = (
                (df_edited["Visibilidad"] != df_ed["Visibilidad"]) |
                (df_edited["Activo"].astype(int) != df_ed["Activo"].astype(int)) |
                (df_edited["Precio"].fillna(0) != df_ed["Precio"].fillna(0))
            )
            _changed = df_edited[_changed_mask]
            if _changed.empty:
                st.info("No hay cambios para guardar.")
            else:
                _n_precio = 0
                with engine.begin() as _cn_g:
                    for _, _cr_g in _changed.iterrows():
                        _precio_nuevo = float(_cr_g["Precio"] or 0)
                        _cn_g.execute(
                            text("UPDATE products SET visibilidad=:v, activo=:a, price=:p WHERE sku=:s"),
                            {"v": _cr_g["Visibilidad"], "a": int(_cr_g["Activo"]),
                             "p": _precio_nuevo, "s": _cr_g["sku"]}
                        )
                        _old_row = df_ed[df_ed["sku"] == _cr_g["sku"]]
                        if not _old_row.empty:
                            _precio_ant = float(_old_row.iloc[0]["Precio"] or 0)
                            if _precio_nuevo != _precio_ant:
                                _cn_g.execute(
                                    text("""INSERT INTO price_history
                                            (product_sku, precio_anterior, precio_nuevo, fecha, motivo)
                                            VALUES (:sku, :ant, :nvo, :fecha, :mot)"""),
                                    {"sku": _cr_g["sku"], "ant": _precio_ant,
                                     "nvo": _precio_nuevo,
                                     "fecha": __import__("datetime").date.today().isoformat(),
                                     "mot": "Admin"}
                                )
                                _n_precio += 1
                from utils.pricing import cargar_productos as _cp_dash
                _cp_dash.clear()
                try:
                    from utils.exports import exportar_catalogo_json
                    _lineas_cambiadas = _changed["sku"].apply(
                        lambda s: df_g[df_g["sku"] == s]["client_id"].values[0]
                        if not df_g[df_g["sku"] == s].empty else None
                    ).dropna().unique()
                    for _lc_exp in _lineas_cambiadas:
                        try:
                            exportar_catalogo_json(_lc_exp)
                        except Exception:
                            pass
                except Exception:
                    pass
                _msg = f"{len(_changed)} producto(s) guardados"
                if _n_precio:
                    _msg += f" · {_n_precio} precio(s) actualizado(s) con historial"
                st.success(_msg + " · catálogo web actualizado")
                st.rerun()

    # ── Revenue Sharing — Reglas activas ──────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🤝 Revenue Sharing — Reglas Activas</div>", unsafe_allow_html=True)
    try:
        _df_rev = pd.read_sql("""
            SELECT rr.product_sku, p.name AS producto,
                   rr.linea_a, rr.linea_b, rr.split_a, rr.split_b,
                   rr.notas, rr.activo, rr.created_at
            FROM revenue_rules rr
            LEFT JOIN products p ON p.sku = rr.product_sku
            ORDER BY rr.activo DESC, rr.created_at DESC
        """, engine)
    except Exception:
        _df_rev = pd.DataFrame()

    if _df_rev.empty:
        st.markdown(f"<div style='background:{_SURFACE};border-radius:12px;padding:16px 20px;border:1px solid {_LINE};color:{_MUTED};'>Sin reglas de revenue sharing configuradas. Se agregan al crear un Producto Tipo C (compartido).</div>", unsafe_allow_html=True)
    else:
        _df_rev_show = _df_rev.copy()
        _df_rev_show["linea_a"]    = _df_rev_show["linea_a"].apply(lambda x: f"{get_linea(x)['emoji']} {get_linea(x)['nombre']}")
        _df_rev_show["linea_b"]    = _df_rev_show["linea_b"].apply(lambda x: f"{get_linea(x)['emoji']} {get_linea(x)['nombre']}")
        _df_rev_show["split_a"]    = _df_rev_show["split_a"].apply(lambda x: f"{x*100:.0f}%")
        _df_rev_show["split_b"]    = _df_rev_show["split_b"].apply(lambda x: f"{x*100:.0f}%")
        _df_rev_show["activo"]     = _df_rev_show["activo"].apply(lambda x: "Si" if x else "No")
        _df_rev_show["created_at"] = _df_rev_show["created_at"].astype(str).str[:10]
        st.dataframe(
            _df_rev_show[["product_sku","producto","linea_a","split_a","linea_b","split_b","notas","activo","created_at"]].rename(columns={
                "product_sku": "SKU", "producto": "Producto",
                "linea_a": "Línea A", "split_a": "% A",
                "linea_b": "Línea B", "split_b": "% B",
                "notas": "Notas", "activo": "Activo", "created_at": "Creado"
            }),
            use_container_width=True, hide_index=True
        )


# ── Dialogs de acción de cola (modulo-level para estabilidad de clave) ────────

@st.dialog("Iniciar fabricacion")
def _dlg_iniciar(pid: int):
    st.markdown(f"Iniciar fabricacion del **pedido #{pid}**?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Iniciar", type="primary", use_container_width=True, key="dlg_ini_ok"):
            r = _avanzar_estado(pid, "En Proceso")
            if r["ok"]:
                st.success("Iniciado")
                st.rerun()
            else:
                st.error(r.get("error", "Error"))
    with c2:
        if st.button("Volver", use_container_width=True, key="dlg_ini_no"):
            st.rerun()


@st.dialog("Registrar fabricacion")
def _dlg_fabricar(pid: int):
    st.markdown(f"**Pedido #{pid}** — completar fabricacion")
    with engine.connect() as _c:
        _mats = pd.read_sql(
            text("SELECT material_id, name, stock_gr FROM materials WHERE activo=1 ORDER BY name"), _c
        )
    _mat_opts = {f"{r['name']} ({r['stock_gr']:.0f}g)": r["material_id"] for _, r in _mats.iterrows()}
    if not _mat_opts:
        st.warning("Sin materiales activos en inventario.")
        return
    _mat_sel   = st.selectbox("Material usado", list(_mat_opts.keys()), key="dlg_fab_mat")
    _gramos    = st.number_input("Gramos reales usados", min_value=1, max_value=5000, value=50, key="dlg_fab_gr")
    _tiempo    = st.number_input("Tiempo (minutos)", min_value=1, max_value=2000, value=60, key="dlg_fab_min")
    _resultado = st.selectbox("Resultado", ["Exito", "Fallo parcial (reimpresion necesaria)", "Fallo total"], key="dlg_fab_res")
    if st.button("Registrar", type="primary", use_container_width=True, key="dlg_fab_ok"):
        r = _avanzar_estado(
            pid, "Listo",
            gramos_reales=float(_gramos),
            tiempo_min=int(_tiempo),
            material_id=_mat_opts[_mat_sel],
            resultado=_resultado,
        )
        if r["ok"]:
            _ef = r.get("estado_final", "Listo")
            st.success(f"Registrado — estado: {_ef}")
            st.rerun()
        else:
            st.error(r.get("error", "Error"))


@st.dialog("Confirmar entrega")
def _dlg_entregar(pid: int, monto: float):
    st.markdown(f"**Pedido #{pid}** — marcar como entregado")
    st.markdown(f"Monto a cobrar: **${monto:,.0f}**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar entrega", type="primary", use_container_width=True, key="dlg_ent_ok"):
            r = _avanzar_estado(pid, "Entregado")
            if r["ok"]:
                st.success("Entregado y pago registrado")
                st.rerun()
            else:
                st.error(r.get("error", "Error"))
    with c2:
        if st.button("Volver", use_container_width=True, key="dlg_ent_no"):
            st.rerun()


@st.dialog("Cancelar pedido")
def _dlg_cancelar(pid: int):
    st.markdown(f"**Pedido #{pid}** — cancelar")
    _motivo = st.text_area("Motivo", placeholder="Ej: Cliente no retiro, error de fabricacion...", key="dlg_can_mot")
    if st.button("Cancelar pedido", type="primary", use_container_width=True, key="dlg_can_ok"):
        r = _avanzar_estado(pid, "Cancelado", motivo=_motivo)
        if r["ok"]:
            st.success("Pedido cancelado")
            st.rerun()
        else:
            st.error(r.get("error", "Error"))


def _dash_hoy():
    """Tab Hoy — vista operacional: cola activa + ventas semana + stock critico."""
    from utils.mike import get_alertas_dashboard

    st.markdown(
        "<div class='main-header'><h1>⚡ Vista de Hoy</h1>"
        "<p>Cola activa · ventas recientes · stock critico — todo en una pantalla</p></div>",
        unsafe_allow_html=True,
    )

    # ── KPIs ─────────────────────────────────────────────────
    try:
        _row_sem = pd.read_sql("""
            SELECT COUNT(*) AS pedidos, COALESCE(SUM(monto_venta), 0) AS facturado
            FROM orders WHERE status='Entregado'
              AND delivered_at >= date('now', '-7 days')
        """, engine).iloc[0]
        _ped_sem = int(_row_sem["pedidos"])
        _fac_sem = float(_row_sem["facturado"])
    except Exception:
        _ped_sem = 0; _fac_sem = 0.0

    try:
        _cola_n = int(pd.read_sql(
            "SELECT COUNT(*) AS n FROM orders WHERE status IN ('Pendiente','En Proceso')", engine
        ).iloc[0]["n"])
    except Exception:
        _cola_n = 0

    try:
        _mat_crit = int(pd.read_sql(
            "SELECT COUNT(*) AS n FROM materials WHERE stock_gr < 500 AND activo=1", engine
        ).iloc[0]["n"])
    except Exception:
        _mat_crit = 0

    _alertas = get_alertas_dashboard()
    _n_crit  = sum(1 for a in _alertas if a["nivel"] == "critico")
    _n_atc   = sum(1 for a in _alertas if a["nivel"] == "atencion")

    _k1, _k2, _k3, _k4 = st.columns(4)
    for _kcol, _kv, _kl, _ks, _kc in [
        (_k1, f"${_fac_sem:,.0f}", "Vendido esta semana",    f"{_ped_sem} pedidos entregados",    "#2F9E54"),
        (_k2, str(_cola_n),        "Pedidos en cola",         "Pendiente + En Proceso",             "#E0902A"),
        (_k3, str(_mat_crit),      "Materiales criticos",     "Stock < 500 g",                      "#D7322B" if _mat_crit else "#2F9E54"),
        (_k4, str(_n_crit),        "Alertas Mike",            f"{_n_atc} de atencion",              "#D7322B" if _n_crit else "#2F9E54"),
    ]:
        with _kcol:
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:12px;padding:18px 14px;"
                f"border:1px solid {_LINE};border-top:3px solid {_kc};text-align:center;margin-bottom:16px;'>"
                f"<div style='font-size:1.6rem;font-weight:800;color:{_kc};line-height:1;'>{_kv}</div>"
                f"<div style='font-size:0.58rem;font-weight:700;color:{_INK};margin-top:6px;"
                f"letter-spacing:.05em;text-transform:uppercase;'>{_kl}</div>"
                f"<div style='font-size:0.62rem;color:{_MUTED};margin-top:3px;'>{_ks}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Cola + lateral ────────────────────────────────────────
    _col_cola, _col_lat = st.columns([2, 1])

    with _col_cola:
        st.markdown("<div class='section-title'>⏳ Cola de Produccion Activa</div>", unsafe_allow_html=True)
        try:
            _df_cola = pd.read_sql("""
                SELECT o.id, o.status, o.date, o.notas, o.client_id, o.started_at,
                       oi.cantidad, oi.precio_unitario,
                       p.name AS producto,
                       COALESCE(pg.monto, oi.cantidad * oi.precio_unitario) AS monto_pago
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                JOIN products p ON p.sku = oi.product_sku
                LEFT JOIN pagos pg ON pg.order_id = o.id AND pg.estado='pendiente'
                WHERE o.status IN ('Pendiente','En Proceso','Listo')
                ORDER BY o.date ASC
            """, engine)
        except Exception:
            _df_cola = pd.DataFrame()

        if _df_cola.empty:
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:12px;padding:20px;border:1px solid {_LINE};"
                f"text-align:center;color:{_MUTED};'>Cola vacia — sin pedidos activos</div>",
                unsafe_allow_html=True,
            )
        else:
            for _, _cr in _df_cola.iterrows():
                _pid    = int(_cr["id"])
                _st     = _cr["status"]
                _lcfg   = get_linea(_cr["client_id"])
                _stc    = {"Pendiente": "#E0902A", "En Proceso": "#3B82F6", "Listo": "#2F9E54"}.get(_st, _MUTED)
                _monto  = float(_cr.get("monto_pago") or 0)
                _notas  = str(_cr.get("notas") or "")

                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:12px;padding:14px 16px;"
                    f"border:1px solid {_LINE};border-left:4px solid {_stc};margin-bottom:6px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>"
                    f"<div><span style='font-size:0.58rem;font-weight:700;letter-spacing:.1em;"
                    f"text-transform:uppercase;color:{_lcfg['color']};'>"
                    f"{_lcfg['emoji']} {_lcfg['nombre']}</span>"
                    f"<span style='font-size:0.95rem;font-weight:800;color:{_INK};margin-left:8px;'>"
                    f"#{_pid} — {int(_cr['cantidad'])}× {_cr['producto']}</span></div>"
                    f"<span style='background:{_stc}18;color:{_stc};border-radius:6px;padding:2px 8px;"
                    f"font-size:0.62rem;font-weight:700;'>{_st}</span></div>"
                    f"<div style='font-size:0.68rem;color:{_MUTED};'>"
                    f"${_monto:,.0f} · {str(_cr['date'])[:10]}"
                    + (f" · {_notas[:60]}" if _notas else "")
                    + "</div></div>",
                    unsafe_allow_html=True,
                )

                _b1, _b2, _b3, _b4 = st.columns(4)
                if _st == "Pendiente":
                    with _b1:
                        if st.button("▶ Iniciar", key=f"hoy_ini_{_pid}", use_container_width=True, type="primary"):
                            _dlg_iniciar(_pid)
                    with _b4:
                        if st.button("✕ Cancelar", key=f"hoy_can_{_pid}", use_container_width=True):
                            _dlg_cancelar(_pid)
                elif _st == "En Proceso":
                    with _b1:
                        if st.button("✓ Registrar fab", key=f"hoy_fab_{_pid}", use_container_width=True, type="primary"):
                            _dlg_fabricar(_pid)
                    with _b4:
                        if st.button("✕ Cancelar", key=f"hoy_can_{_pid}", use_container_width=True):
                            _dlg_cancelar(_pid)
                elif _st == "Listo":
                    with _b1:
                        if st.button("📦 Entregar", key=f"hoy_ent_{_pid}", use_container_width=True, type="primary"):
                            _dlg_entregar(_pid, _monto)
                    with _b4:
                        if st.button("✕ Cancelar", key=f"hoy_can_{_pid}", use_container_width=True):
                            _dlg_cancelar(_pid)

        # ── Entregados esta semana ────────────────────────────
        st.markdown("<div class='section-title' style='margin-top:24px;'>✅ Entregados esta semana</div>", unsafe_allow_html=True)
        try:
            _df_rec = pd.read_sql("""
                SELECT o.id, o.client_id, o.delivered_at, o.monto_venta,
                       oi.cantidad, p.name AS producto
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                JOIN products p ON p.sku = oi.product_sku
                WHERE o.status='Entregado' AND o.delivered_at >= date('now','-7 days')
                ORDER BY o.delivered_at DESC
            """, engine)
        except Exception:
            _df_rec = pd.DataFrame()

        if _df_rec.empty:
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:8px;padding:12px 16px;"
                f"border:1px solid {_LINE};color:{_MUTED};'>Sin entregas en los ultimos 7 dias.</div>",
                unsafe_allow_html=True,
            )
        else:
            for _, _rr in _df_rec.iterrows():
                _rl = get_linea(_rr["client_id"])
                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:8px;padding:10px 14px;"
                    f"border:1px solid {_LINE};border-left:3px solid {_rl['color']};margin-bottom:5px;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div><span style='color:{_rl['color']};font-weight:700;font-size:0.75rem;'>"
                    f"{_rl['emoji']} #{int(_rr['id'])}</span>"
                    f" <span style='color:{_INK};font-size:0.82rem;'>"
                    f"{int(_rr['cantidad'])}× {_rr['producto']}</span></div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-weight:800;color:#2F9E54;'>${float(_rr.get('monto_venta') or 0):,.0f}</div>"
                    f"<div style='font-size:0.62rem;color:{_MUTED};'>{str(_rr.get('delivered_at',''))[:10]}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

    with _col_lat:
        # ── Materiales ────────────────────────────────────────
        st.markdown("<div class='section-title'>🧵 Materiales</div>", unsafe_allow_html=True)
        try:
            _df_mats = pd.read_sql(
                "SELECT name, stock_gr FROM materials WHERE activo=1 ORDER BY stock_gr ASC", engine
            )
        except Exception:
            _df_mats = pd.DataFrame()

        for _, _mr in _df_mats.iterrows():
            _mc = "#D7322B" if _mr["stock_gr"] < 200 else ("#E0902A" if _mr["stock_gr"] < 500 else "#2F9E54")
            _ml = "CRITICO" if _mr["stock_gr"] < 200 else ("BAJO" if _mr["stock_gr"] < 500 else "OK")
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:10px;padding:10px 14px;"
                f"border:1px solid {_LINE};border-left:3px solid {_mc};margin-bottom:5px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-size:0.82rem;font-weight:700;color:{_INK};'>{_mr['name']}</span>"
                f"<span style='font-size:0.58rem;font-weight:700;color:{_mc};'>{_ml}</span></div>"
                f"<div style='font-size:0.78rem;color:{_mc};font-weight:600;margin-top:2px;'>"
                f"{_mr['stock_gr']:.0f} g</div></div>",
                unsafe_allow_html=True,
            )

        # ── Alertas Mike ─────────────────────────────────────
        st.markdown("<div class='section-title' style='margin-top:16px;'>🤖 Mike</div>", unsafe_allow_html=True)
        if _alertas:
            for _a in _alertas[:6]:
                _ac = "#D7322B" if _a["nivel"] == "critico" else ("#E0902A" if _a["nivel"] == "atencion" else _MUTED)
                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:8px;padding:8px 12px;"
                    f"border-left:3px solid {_ac};margin-bottom:5px;'>"
                    f"<div style='font-size:0.75rem;font-weight:700;color:{_ac};'>{_a['titulo']}</div>"
                    f"<div style='font-size:0.68rem;color:{_MUTED};margin-top:1px;'>{_a['accion']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"<div style='background:#F0FDF4;border-radius:8px;padding:10px 14px;"
                f"border:1px solid #D1FAE5;font-size:0.75rem;font-weight:600;color:#2F9E54;'>"
                f"Sin alertas — todo en orden</div>",
                unsafe_allow_html=True,
            )


def _dash_m19():
    """Tab Magnitud 19 — panel de linea madre y Vuelo Certero."""
    _LC = "#C9A84C"
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{_LC}22,{_LC}08);border-radius:16px;"
        f"padding:20px 28px;margin-bottom:16px;border:1px solid {_LC}33;'>"
        f"<div style='font-size:0.58rem;font-weight:700;letter-spacing:4px;color:{_LC};text-transform:uppercase;'>EL PASAJE 3D STUDIO · LÍNEA MADRE</div>"
        f"<div style='font-size:1.8rem;font-weight:800;color:#E6EDF3;margin-top:6px;'>⚡ Magnitud 19</div>"
        f"<div style='font-size:0.78rem;color:rgba(240,236,228,0.6);margin-top:4px;'>Ancla tu mente. Expande tu vuelo.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    from utils.pricing import cargar_productos
    from utils.db import engine as _eng_m19
    df_all = cargar_productos()
    df_m19 = df_all[df_all["client_id"] == "admin"].copy()

    if df_m19.empty:
        st.warning("Sin productos para Magnitud 19 en la BD. Corrí migration_v8.py para el seed inicial.")
        if st.button("▶ Correr migration_v8 ahora"):
            try:
                import migration_v8
                migration_v8.run()
                from utils.pricing import cargar_productos as _ccp
                _ccp.clear()
                st.success("migration_v8 OK — recargá la página.")
                st.rerun()
            except Exception as _e:
                st.error(f"Error: {_e}")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    _v_stock   = float(df_m19["valor_stock"].sum())
    _n_prods   = len(df_m19[df_m19["activo"] == 1]) if "activo" in df_m19.columns else len(df_m19)
    _n_cats    = df_m19["categoria"].nunique()
    _n_cero    = int((df_m19["stock"] <= 0).sum())
    _mk1, _mk2, _mk3, _mk4 = st.columns(4)
    for _kc, _kv, _kl, _kcol in [
        (_mk1, f"${_v_stock:,.0f}", "💰 Valor stock",       _LC),
        (_mk2, str(_n_prods),       "📦 Productos activos", _LC),
        (_mk3, str(_n_cats),        "🏷️ Categorías",        "#3B82F6"),
        (_mk4, str(_n_cero),        "⚠️ Sin stock",         "#EF4444"),
    ]:
        with _kc:
            st.markdown(
                f"<div style='background:#161B22;border-radius:12px;padding:14px;border:1px solid #21262D;"
                f"border-top:3px solid {_kcol};text-align:center;margin-bottom:12px;'>"
                f"<div style='font-size:1.4rem;font-weight:800;color:{_kcol};line-height:1;'>{_kv}</div>"
                f"<div style='font-size:0.58rem;color:#8B949E;margin-top:6px;text-transform:uppercase;letter-spacing:0.5px;'>{_kl}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Catálogo por categoría ─────────────────────────────────────────────────
    _cats = sorted(df_m19["categoria"].dropna().unique().tolist())
    if _cats:
        _ctabs = st.tabs(_cats)
        for _ctab, _cat in zip(_ctabs, _cats):
            with _ctab:
                _df_cat = df_m19[df_m19["categoria"] == _cat].sort_values("price", ascending=False)
                _ccols  = st.columns(3)
                for _i, (_, _row) in enumerate(_df_cat.iterrows()):
                    _stk  = int(_row.get("stock", 0) or 0)
                    _sc   = "#10B981" if _stk > 5 else ("#F59E0B" if _stk > 0 else "#EF4444")
                    _desc = str(_row.get("description", "") or "").strip()
                    with _ccols[_i % 3]:
                        st.markdown(
                            f"<div style='background:#161B22;border-radius:12px;padding:16px;"
                            f"border:1px solid #21262D;border-top:2px solid {_LC};margin-bottom:10px;'>"
                            f"<div style='font-size:0.56rem;color:{_LC};letter-spacing:1px;text-transform:uppercase;font-weight:700;'>{_row.get('sku','')}</div>"
                            f"<div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;margin-top:4px;line-height:1.2;'>{_row['name']}</div>"
                            f"<div style='font-size:0.7rem;color:#8B949E;margin-top:4px;line-height:1.4;'>{_desc[:80]}{'…' if len(_desc)>80 else ''}</div>"
                            f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:10px;'>"
                            f"<div style='background:#0D1117;border-radius:6px;padding:7px;text-align:center;'>"
                            f"<div style='font-size:0.5rem;color:#8B949E;margin-bottom:1px;'>PRECIO</div>"
                            f"<div style='font-size:0.82rem;font-weight:700;color:{_LC};'>${float(_row['price']):,.0f}</div></div>"
                            f"<div style='background:#0D1117;border-radius:6px;padding:7px;text-align:center;'>"
                            f"<div style='font-size:0.5rem;color:#8B949E;margin-bottom:1px;'>STOCK</div>"
                            f"<div style='font-size:0.82rem;font-weight:700;color:{_sc};'>{_stk} u</div></div>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )
                        try:
                            from utils.whatsapp import link_producto as _wlp
                            _wa_p = _wlp(str(_row["name"]), str(_row["sku"]), float(_row["price"]), "admin", _eng_m19)
                            st.link_button("📲 Link WA", _wa_p, use_container_width=True)
                        except Exception:
                            pass

    st.markdown("<div style='height:8px;border-top:1px solid #21262D;margin:16px 0;'></div>", unsafe_allow_html=True)

    # ── Presupuestador rápido ──────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:0.58rem;font-weight:700;letter-spacing:3px;color:{_LC};"
        f"text-transform:uppercase;margin-bottom:12px;'>🧮 PRESUPUESTADOR RÁPIDO</div>",
        unsafe_allow_html=True,
    )
    _prod_act = df_m19[df_m19["activo"] == 1][["sku", "name", "price"]].copy() if "activo" in df_m19.columns else df_m19[["sku", "name", "price"]].copy()
    _prod_act["label"] = _prod_act.apply(lambda r: f"{r['name']} — ${float(r['price']):,.0f}", axis=1)
    _sel_m19 = st.multiselect("Productos", options=_prod_act["label"].tolist(), key="m19_presup_sel", label_visibility="collapsed")
    if _sel_m19:
        _items_m19 = []
        _total_m19 = 0.0
        _qty_cols  = st.columns(min(len(_sel_m19), 3))
        for _si, _lbl in enumerate(_sel_m19):
            _rr = _prod_act[_prod_act["label"] == _lbl].iloc[0]
            with _qty_cols[_si % 3]:
                _qty = st.number_input(f"× {_rr['name'][:28]}", min_value=1, value=1, key=f"m19_qty_{_rr['sku']}")
            _items_m19.append({"nombre": _rr["name"], "sku": _rr["sku"], "cantidad": _qty,
                                "precio": float(_rr["price"]), "precio_reventa": 0.0})
            _total_m19 += float(_rr["price"]) * _qty
        st.markdown(
            f"<div style='font-size:1.2rem;font-weight:800;color:{_LC};margin:10px 0;'>Total: ${_total_m19:,.0f}</div>",
            unsafe_allow_html=True,
        )
        try:
            from utils.whatsapp import link_presupuesto as _wlpresup, texto_presupuesto as _wtxt
            _wa_url = _wlpresup(_items_m19, _total_m19, "admin", _eng_m19)
            st.link_button("📲 Enviar presupuesto por WhatsApp", _wa_url, use_container_width=True)
            with st.expander("Ver texto del presupuesto"):
                st.code(_wtxt(_items_m19, _total_m19, linea_nombre="Magnitud 19"), language=None)
        except Exception:
            pass

    st.markdown("<div style='height:8px;border-top:1px solid #21262D;margin:16px 0;'></div>", unsafe_allow_html=True)

    # ── Exportación JSON para web ──────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:0.58rem;font-weight:700;letter-spacing:3px;color:{_LC};"
        f"text-transform:uppercase;margin-bottom:12px;'>📤 EXPORTAR PARA WEB</div>",
        unsafe_allow_html=True,
    )

    _TODAS_LAS_LINEAS_EXPORT = [
        "admin", "fer_produccion", "olivia_coquette", "francisco_sport",
        "constantino_tech", "pharma_delux", "oasis_animal", "oasis_del_estero", "aviation",
    ]

    if st.button("🔄 Regenerar TODOS los catálogos (9 líneas)", use_container_width=True, type="primary"):
        from utils.exports import exportar_catalogo_json, push_exports_to_github
        _ok, _err, _pairs = [], [], []
        for _lid in _TODAS_LAS_LINEAS_EXPORT:
            try:
                _cat, _path = exportar_catalogo_json(_lid)
                _slug = _path.split("/")[-1].split(chr(92))[-1].replace("-catalog.json", "")
                _pairs.append((_slug, _cat))
                _ok.append(_slug)
            except Exception as _e:
                _err.append(f"❌ {_lid}: {_e}")
        if _ok:
            st.success(f"Generados: {len(_ok)}/9 — {', '.join(_ok)}")
        if _err:
            st.error("\n".join(_err))
        if _pairs:
            with st.spinner("Publicando en GitHub Pages..."):
                _pushed, _skipped, _gh_err = push_exports_to_github(_pairs)
            if _pushed:
                st.success(f"GitHub ✅ {len(_pushed)} commiteados: {', '.join(_pushed)}")
            if _skipped:
                st.info(f"GitHub ⏭ {len(_skipped)} sin cambios: {', '.join(_skipped)}")
            if _gh_err:
                st.error("GitHub errores:\n" + "\n".join(_gh_err))

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    _exp_col1, _exp_col2 = st.columns(2)
    with _exp_col1:
        if st.button("📤 Exportar magnitud19-catalog.json", use_container_width=True):
            try:
                from utils.exports import exportar_catalogo_json
                _, _path = exportar_catalogo_json("admin")
                st.success(f"OK: {_path}")
            except Exception as _e:
                st.error(f"Error: {_e}")
    with _exp_col2:
        if st.button("📤 Exportar melomano-catalog.json", use_container_width=True):
            try:
                from utils.exports import exportar_catalogo_json
                _, _path = exportar_catalogo_json("fer_produccion")
                st.success(f"OK: {_path}")
            except Exception as _e:
                st.error(f"Error: {_e}")


def _dash_pagos():
    """Tab 💳 Pagos — acreditación manual de cobros."""
    st.markdown(
        f"<div style='font-size:1.4rem;font-weight:800;color:{_INK};margin-bottom:4px;'>💳 Acreditación de Pagos</div>"
        f"<div style='font-size:0.75rem;color:{_MUTED};margin-bottom:20px;'>Marcá como acreditados los cobros que ya recibiste</div>",
        unsafe_allow_html=True,
    )

    # ── KPI rápido ───────────────────────────────────────────────
    try:
        _kpi = pd.read_sql(
            "SELECT estado, COUNT(*) AS n, SUM(monto) AS total FROM pagos GROUP BY estado",
            engine,
        )
    except Exception:
        _kpi = pd.DataFrame()

    _n_pend  = int(_kpi.loc[_kpi["estado"] == "pendiente",  "n"].sum())     if not _kpi.empty else 0
    _tot_pend = float(_kpi.loc[_kpi["estado"] == "pendiente", "total"].sum()) if not _kpi.empty else 0.0
    _n_acred  = int(_kpi.loc[_kpi["estado"] == "acreditado", "n"].sum())     if not _kpi.empty else 0
    _tot_acred= float(_kpi.loc[_kpi["estado"] == "acreditado","total"].sum()) if not _kpi.empty else 0.0

    _ka, _kb, _kc, _kd = st.columns(4)
    for _col, _val, _lbl, _sub, _color in [
        (_ka, str(_n_pend),          "⏳ Pendientes",   "pagos sin acreditar",        "#F59E0B"),
        (_kb, f"${_tot_pend:,.0f}",  "💵 Monto pend.", "suma de pendientes",         "#EF4444"),
        (_kc, str(_n_acred),         "✅ Acreditados",  "cobros confirmados",          "#22C55E"),
        (_kd, f"${_tot_acred:,.0f}", "💰 Total cobrado","suma acreditada",             "#3B82F6"),
    ]:
        with _col:
            st.markdown(
                f"<div style='background:{_SURFACE};border-radius:12px;padding:14px 10px;"
                f"border:1px solid {_LINE};border-top:3px solid {_color};text-align:center;margin-bottom:16px;'>"
                f"<div style='font-size:1.3rem;font-weight:800;color:{_color};line-height:1;'>{_val}</div>"
                f"<div style='font-size:0.62rem;font-weight:600;color:{_INK};margin-top:6px;'>{_lbl}</div>"
                f"<div style='font-size:0.56rem;color:{_MUTED};margin-top:3px;'>{_sub}</div></div>",
                unsafe_allow_html=True,
            )

    _tp_pend, _tp_hist = st.tabs(["⏳ Pendientes", "✅ Historial"])

    # ── Pendientes ───────────────────────────────────────────────
    with _tp_pend:
        try:
            _df_pend = pd.read_sql(
                """SELECT p.id, p.order_id, COALESCE(t.name, CAST(p.order_id AS TEXT)) AS cliente,
                          p.monto, p.metodo, p.fecha, p.notas, o.status AS estado_pedido
                   FROM pagos p
                   LEFT JOIN orders o ON o.id = p.order_id
                   LEFT JOIN tenants t ON t.id = o.client_id
                   WHERE p.estado = 'pendiente'
                   ORDER BY p.fecha DESC""",
                engine,
            )
        except Exception:
            _df_pend = pd.DataFrame()

        if _df_pend.empty:
            st.success("Sin pagos pendientes.")
        else:
            for _, _row in _df_pend.iterrows():
                _metodo_color = {"efectivo": "#22C55E", "transferencia": "#3B82F6",
                                 "mercadopago": "#009EE3"}.get(str(_row["metodo"]).lower(), "#6B7280")
                st.markdown(
                    f"<div style='background:{_SURFACE};border-radius:12px;padding:16px 20px;"
                    f"border:1px solid {_LINE};border-left:4px solid #F59E0B;margin-bottom:10px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div>"
                    f"<span style='font-weight:700;color:{_INK};font-size:0.9rem;'>{_row['cliente']}</span>"
                    f"<span style='color:{_MUTED};font-size:0.72rem;margin-left:10px;'>Pedido #{int(_row['order_id'])}</span>"
                    f"</div>"
                    f"<div style='font-size:1.1rem;font-weight:800;color:#F59E0B;'>${float(_row['monto']):,.0f}</div>"
                    f"</div>"
                    f"<div style='margin-top:6px;display:flex;gap:12px;flex-wrap:wrap;'>"
                    f"<span style='font-size:0.68rem;background:{_metodo_color}22;color:{_metodo_color};"
                    f"border:1px solid {_metodo_color}44;border-radius:99px;padding:2px 8px;font-weight:700;'>"
                    f"{str(_row['metodo']).capitalize()}</span>"
                    f"<span style='font-size:0.68rem;color:{_MUTED};'>{str(_row['fecha'])[:16]}</span>"
                    f"{'<span style=\"font-size:0.68rem;color:' + _MUTED + ';\">' + str(_row['notas']) + '</span>' if _row['notas'] else ''}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                with st.form(key=f"acred_form_{int(_row['id'])}"):
                    _nota_acred = st.text_input(
                        "Nota (opcional)", value="",
                        placeholder="Ej: transferencia 14/6, CBU confirmado…",
                        label_visibility="collapsed",
                        key=f"nota_inp_{int(_row['id'])}",
                    )
                    if st.form_submit_button("✅ Acreditar pago", type="primary", use_container_width=False):
                        try:
                            with engine.begin() as _cn:
                                _cn.execute(
                                    text("""UPDATE pagos
                                             SET estado = 'acreditado',
                                                 notas  = CASE WHEN notas IS NULL OR notas = ''
                                                               THEN :nota
                                                               ELSE :nota || ' | ' || notas END
                                           WHERE id = :pid"""),
                                    {"nota": _nota_acred.strip() or f"Acreditado {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}",
                                     "pid": int(_row["id"])},
                                )
                            st.success(f"Pago #{int(_row['id'])} acreditado.")
                            st.rerun()
                        except Exception as _e:
                            st.error(f"Error: {_e}")

    # ── Historial ────────────────────────────────────────────────
    with _tp_hist:
        try:
            _df_hist = pd.read_sql(
                """SELECT p.id, p.order_id, COALESCE(t.name, CAST(p.order_id AS TEXT)) AS cliente,
                          p.monto, p.metodo, p.estado, p.fecha, p.notas
                   FROM pagos p
                   LEFT JOIN orders o ON o.id = p.order_id
                   LEFT JOIN tenants t ON t.id = o.client_id
                   ORDER BY p.fecha DESC""",
                engine,
            )
        except Exception:
            _df_hist = pd.DataFrame()

        if _df_hist.empty:
            st.info("Sin pagos registrados.")
        else:
            _df_hist_show = _df_hist.rename(columns={
                "id": "#", "order_id": "Pedido", "cliente": "Cliente",
                "monto": "Monto", "metodo": "Método",
                "estado": "Estado", "fecha": "Fecha", "notas": "Notas",
            })
            _df_hist_show["Monto"] = _df_hist_show["Monto"].apply(lambda x: f"${float(x):,.0f}")
            _df_hist_show["Fecha"] = _df_hist_show["Fecha"].astype(str).str[:16]
            _df_hist_show["Estado"] = _df_hist_show["Estado"].apply(
                lambda x: "✅ Acreditado" if x == "acreditado" else "⏳ Pendiente"
            )
            st.dataframe(_df_hist_show, use_container_width=True, hide_index=True)


def render():
    _tab_hoy, _tab_dash, _tab_mike, _tab_m19, _tab_pagos = st.tabs(["⚡ Hoy", "📊 Dashboard", "🤖 Mike", "⚡ Magnitud 19", "💳 Pagos"])
    with _tab_hoy:
        _dash_hoy()
    with _tab_dash:
        _dash_main()
    with _tab_mike:
        from modules.panel_mike import render as _mike_render
        _mike_render()
    with _tab_m19:
        _dash_m19()
    with _tab_pagos:
        _dash_pagos()

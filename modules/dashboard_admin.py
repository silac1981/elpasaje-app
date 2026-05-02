"""modules/dashboard_admin.py — Dashboard principal de Alejandra."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from utils.db import engine
from utils.lineas import get_linea


def render():
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
        fig_bar.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(l=10,r=10,t=10,b=40), legend=dict(orientation="h",yanchor="bottom",y=1.02), xaxis=dict(tickangle=-20), yaxis=dict(tickprefix="$",tickformat=",.0f"))
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("<div class='section-title'>🥧 Distribucion del Ecosistema</div>", unsafe_allow_html=True)
        fig_pie = px.pie(df_linea, values="valor_stock", names="linea_nombre", color_discrete_sequence=px.colors.qualitative.Set2, hole=0.45)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
        fig_pie.update_layout(showlegend=False, height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig_pie, use_container_width=True)
    col_c, col_d = st.columns([1.6, 1])
    with col_c:
        st.markdown("<div class='section-title'>🎯 Ganancia Neta por Producto</div>", unsafe_allow_html=True)
        df_prod = df.sort_values("ganancia_stock", ascending=True)
        fig_h = go.Figure(go.Bar(x=df_prod["ganancia_stock"], y=df_prod["name"], orientation="h", marker_color=["#22C55E" if g > 0 else "#EF4444" for g in df_prod["ganancia_stock"]], text=[f"${v:,.0f}" for v in df_prod["ganancia_stock"]], textposition="outside"))
        fig_h.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(l=10,r=80,t=10,b=10), xaxis=dict(tickprefix="$",tickformat=",.0f"), yaxis=dict(automargin=True))
        st.plotly_chart(fig_h, use_container_width=True)
    with col_d:
        st.markdown("<div class='section-title'>🧵 Estado de Materiales</div>", unsafe_allow_html=True)
        for _, mat in mats.iterrows():
            pct = min(mat["stock_gr"] / 1000 * 100, 100)
            color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
            val_m = mat["stock_gr"] * mat["cost_kg"] / 1000
            alerta = " ⚠️ STOCK BAJO" if pct <= 10 else (" ⚡ Atención" if pct <= 30 else "")
            st.markdown(f"<div style='background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:12px;'><div style='display:flex;justify-content:space-between;margin-bottom:8px;'><b style='color:#1a1a2e'>{mat['name']}</b><span style='color:{color_m};font-weight:600'>{mat['stock_gr']:.0f}g{alerta}</span></div><div style='background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;'><div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div></div><div style='display:flex;justify-content:space-between;margin-top:6px;font-size:0.75rem;color:#6B7280;'><span>${mat['cost_kg']:,.0f}/kg</span><span>Valor: ${val_m:,.0f}</span></div></div>", unsafe_allow_html=True)
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
    try:
        _df_fac = pd.read_sql("""
            SELECT strftime('%Y-%m', o.date) AS mes,
                   o.client_id,
                   COUNT(DISTINCT o.id) AS pedidos,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado,
                   SUM(oi.cantidad * oi.precio_unitario * 0.25) AS costo_aprox
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status = 'Listo'
            GROUP BY mes, o.client_id
            ORDER BY mes
        """, engine)
        _df_fac_mes = pd.read_sql("""
            SELECT strftime('%Y-%m', o.date) AS mes,
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
            _fig_fac.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280,
                margin=dict(l=10,r=10,t=10,b=40), yaxis=dict(tickprefix="$",tickformat=",.0f"))
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
                st.markdown(f"<div style='background:white;border-radius:8px;padding:10px 14px;margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,0.06);display:flex;justify-content:space-between;align-items:center;'><span style='font-weight:600;color:#1a1a2e;'>{_lc['emoji']} {_lc['nombre']}</span><span style='font-weight:800;color:#1E3A8A;'>${_flr['facturado']:,.0f}</span></div>", unsafe_allow_html=True)
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
                    f"<div style='background:white;border-radius:8px;padding:10px 14px;margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,0.06);'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                    f"<span style='font-weight:700;color:#1a1a2e;'>{_cr['canal']}</span>"
                    f"<span style='color:{_cc};font-weight:700;'>{int(_cr['contactos'])} contactos</span></div>"
                    f"<div style='background:#F3F4F6;border-radius:999px;height:6px;overflow:hidden;'>"
                    f"<div style='width:{_pct_cal}%;background:{_cc};height:100%;border-radius:999px;'></div></div>"
                    f"<div style='font-size:0.68rem;color:#6B7280;margin-top:3px;'>{int(_cr['calientes'])} señales calientes ({_pct_cal}%)</div>"
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
            _fig_react.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=10,r=10,t=10,b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font_size=10),
                xaxis_title="", yaxis_title="Señales")
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
                    f"<div style='background:white;border-radius:14px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.07);text-align:center;border-top:4px solid {_rkl['color']};'>"
                    f"<div style='font-size:1.6rem;'>{_rkl['emoji']}</div>"
                    f"<div style='font-weight:700;color:#1a1a2e;font-size:0.82rem;margin-top:4px;'>{_rkl['nombre']}</div>"
                    f"<div style='font-size:1.3rem;font-weight:800;color:{_rkl['color']};margin-top:6px;'>${_rkr['facturado_total']:,.0f}</div>"
                    f"<div style='font-size:0.68rem;color:#6B7280;margin-top:2px;'>{int(_rkr['pedidos_completados'])} pedidos · último {str(_rkr['ultimo_pedido'])[:10]}</div>"
                    f"</div>", unsafe_allow_html=True)
    else:
        st.info("Completá pedidos para ver el ranking de facturación.")

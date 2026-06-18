"""modules/panel_socios.py — Panel de socios (vista admin consolidada)."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import engine
from utils.lineas import get_linea


def render():
    st.markdown("<div class='main-header'><h1>🤝 Panel de Socios</h1><p>Ecosistema El Pasaje · Familia + B2B · Visión consolidada</p></div>", unsafe_allow_html=True)
    from utils.pricing import cargar_productos
    df = cargar_productos()
    tenants = pd.read_sql("SELECT * FROM tenants WHERE id != 'admin'", engine)
    B2B_IDS = {"oasis_animal","oasis_del_estero","pharma_delux","aviation"}
    try:
        all_orders = pd.read_sql("SELECT * FROM orders", engine)
    except Exception:
        all_orders = pd.DataFrame()
    ids_socios = tenants["id"].tolist()
    df_socios = df[df["client_id"].isin(ids_socios)]
    total_val = df_socios["valor_stock"].sum()
    total_gan = df_socios["ganancia_stock"].sum()
    n_socios = len(tenants)
    pedidos_activos = len(all_orders[all_orders["status"].isin(["Pendiente","En Proceso"])]) if not all_orders.empty and "status" in all_orders.columns else 0
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    for col, title, val, sub, color in [
        (kpi1, "🤝 Socios Activos",      str(n_socios),         "líneas en el ecosistema",   "#1E3A8A"),
        (kpi2, "💰 Stock Consolidado",   f"${total_val:,.0f}",  "valor precio venta",        "#059669"),
        (kpi3, "📈 Ganancia Total",       f"${total_gan:,.0f}",  "potencial del ecosistema",  "#7C3AED"),
        (kpi4, "🏭 Pedidos Activos",      str(pedidos_activos),  "en producción ahora",       "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
    chart_rows = []
    for _, t in tenants.iterrows():
        cfg = get_linea(t["id"])
        prod = df[df["client_id"] == t["id"]]
        chart_rows.append({"Socio": cfg["nombre"], "Costo": prod["costo_stock"].sum(), "Ganancia": prod["ganancia_stock"].sum(), "valor_total": prod["valor_stock"].sum(), "Color": cfg["color"]})
    df_chart = pd.DataFrame(chart_rows).sort_values("Ganancia", ascending=True)
    col_a, col_b = st.columns([1.6, 1])
    with col_a:
        st.markdown("<div class='section-title'>📊 Stock por Línea</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Costo Producción", x=df_chart["Costo"], y=df_chart["Socio"], orientation="h", marker_color="#EF4444", opacity=0.85))
        fig_bar.add_trace(go.Bar(name="Ganancia Neta", x=df_chart["Ganancia"], y=df_chart["Socio"], orientation="h", marker_color="#22C55E", opacity=0.85))
        fig_bar.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(l=10,r=60,t=10,b=30), legend=dict(orientation="h",yanchor="bottom",y=1.02), xaxis=dict(tickprefix="$",tickformat=",.0f"))
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("<div class='section-title'>🥧 Participación</div>", unsafe_allow_html=True)
        color_map = {r["Socio"]: r["Color"] for _, r in df_chart.iterrows()}
        fig_pie = px.pie(df_chart, values="valor_total", names="Socio", color="Socio", color_discrete_map=color_map, hole=0.5)
        fig_pie.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
        fig_pie.update_layout(showlegend=True, height=300, margin=dict(l=0,r=0,t=10,b=10), paper_bgcolor="white", legend=dict(font=dict(size=10)))
        st.plotly_chart(fig_pie, use_container_width=True)
    for grupo_label, grupo_df in [
        ("👨‍👩‍👧‍👦 Familia El Pasaje", tenants[~tenants["id"].isin(B2B_IDS)]),
        ("🤝 Socios B2B · Nando",  tenants[tenants["id"].isin(B2B_IDS)]),
    ]:
        if grupo_df.empty:
            continue
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:#6B7280;margin:28px 0 14px;border-bottom:1px solid #E5E7EB;padding-bottom:8px;'>{grupo_label}</div>", unsafe_allow_html=True)
        tenant_list = list(grupo_df.iterrows())
        for i in range(0, len(tenant_list), 2):
            pair = tenant_list[i:i+2]
            cols_g = st.columns(2)
            for col_g, (_, t) in zip(cols_g, pair):
                cfg = get_linea(t["id"])
                prod = df[df["client_id"] == t["id"]]
                val = prod["valor_stock"].sum()
                gan = prod["ganancia_stock"].sum()
                n_sku = len(prod)
                margen_avg = prod["margen_pct"].mean() if n_sku > 0 else 0.0
                color = cfg["color"]
                ped_activos = 0
                if not all_orders.empty and "client_id" in all_orders.columns and "status" in all_orders.columns:
                    ped_socio = all_orders[all_orders["client_id"] == t["id"]]
                    ped_activos = len(ped_socio[ped_socio["status"].isin(["Pendiente","En Proceso"])])
                m_color = "#059669" if margen_avg >= 50 else ("#D97706" if margen_avg >= 30 else "#EF4444")
                badge_ped = f"<div style='margin-top:12px;display:inline-block;background:{color}1a;color:{color};padding:4px 12px;border-radius:99px;font-size:0.72rem;font-weight:700;'>🏭 {ped_activos} pedido{'s' if ped_activos != 1 else ''} en curso</div>" if ped_activos > 0 else ""
                badge_tipo = "B2B" if t["id"] in B2B_IDS else "Familia"
                with col_g:
                    st.markdown(f"<div style='background:#FAF8F3;border-radius:16px;overflow:hidden;border:1px solid #DCD5C7;margin-bottom:16px;'><div style='background:{color};padding:16px 20px 14px;display:flex;align-items:center;gap:12px;'><div style='font-size:2rem;line-height:1;'>{cfg['emoji']}</div><div><div style='font-family:\"Bricolage Grotesque\",sans-serif;font-size:1.15rem;font-weight:800;color:white;line-height:1.1;letter-spacing:-.02em;'>{t['name']}</div><div style='font-family:\"Source Sans 3\",sans-serif;font-size:10px;font-weight:600;color:rgba(255,255,255,0.75);letter-spacing:.1em;text-transform:uppercase;margin-top:3px;'>{badge_tipo}</div></div></div><div style='padding:16px 20px 18px;'><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;'><div><div style='font-family:\"Source Sans 3\",sans-serif;font-size:10px;font-weight:600;color:#74798A;text-transform:uppercase;letter-spacing:.08em;'>Stock</div><div style='font-family:\"Bricolage Grotesque\",sans-serif;font-size:1.2rem;font-weight:800;color:#16181F;letter-spacing:-.02em;'>${val:,.0f}</div></div><div><div style='font-family:\"Source Sans 3\",sans-serif;font-size:10px;font-weight:600;color:#74798A;text-transform:uppercase;letter-spacing:.08em;'>Ganancia</div><div style='font-family:\"Bricolage Grotesque\",sans-serif;font-size:1.2rem;font-weight:800;color:#2F9E54;letter-spacing:-.02em;'>${gan:,.0f}</div></div><div><div style='font-family:\"Source Sans 3\",sans-serif;font-size:10px;font-weight:600;color:#74798A;text-transform:uppercase;letter-spacing:.08em;'>SKUs</div><div style='font-family:\"Bricolage Grotesque\",sans-serif;font-size:1.2rem;font-weight:800;color:#16181F;letter-spacing:-.02em;'>{n_sku}</div></div></div><div style='margin-top:14px;'><div style='display:flex;justify-content:space-between;font-family:\"Source Sans 3\",sans-serif;font-size:11px;color:#74798A;margin-bottom:5px;'><span>Margen promedio</span><span style='color:{m_color};font-weight:700;'>{margen_avg:.1f}%</span></div><div style='background:#E4DECF;border-radius:999px;height:6px;overflow:hidden;'><div style='width:{min(margen_avg,100):.0f}%;background:{m_color};height:100%;border-radius:999px;'></div></div></div>{badge_ped}</div></div>", unsafe_allow_html=True)
                    if not prod.empty:
                        with st.expander(f"📦 Ver productos · {cfg['nombre']} ({n_sku} SKUs)"):
                            st.dataframe(prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={"name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen %"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen %":"{:.1f}%"}), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Sin productos cargados en esta línea.")

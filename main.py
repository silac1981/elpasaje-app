import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime

st.set_page_config(
    page_title="El Pasaje - Sistema Integral",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  ESTILOS GLOBALES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

.stApp { background-color: #F0F2F6; }
.stSidebar { background-color: #1a1a2e !important; }
.stSidebar * { color: white !important; }

.metric-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07);
    border-top: 5px solid;
    transition: transform 0.2s;
    height: 100%;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.12); }
.metric-title { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; color: #6B7280; margin-bottom: 8px; }
.metric-value { font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 700;
                color: #1a1a2e; line-height: 1; }
.metric-sub   { font-size: 12px; color: #9CA3AF; margin-top: 6px; }

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white; padding: 28px 36px; border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin-bottom: 28px;
}
.main-header h1 { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem;
                  margin: 0; letter-spacing: 2px; }
.main-header p  { font-family: 'Inter', sans-serif; font-size: 0.85rem;
                  color: #94a3b8; margin: 6px 0 0; }

.section-title {
    font-family: 'Cormorant Garamond', serif; font-size: 1.5rem;
    color: #1a1a2e; border-bottom: 2px solid #e5e7eb;
    padding-bottom: 8px; margin: 28px 0 16px;
}

.stock-critico { background: #FEF2F2; border-left: 5px solid #EF4444;
                 border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONEXION Y HELPERS
# ─────────────────────────────────────────────
import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

LINEAS = {
    "admin":            {"nombre": "Administracion",   "color": "#1E3A8A", "emoji": "🏛️"},
    "oasis_animal":     {"nombre": "Oasis Animal",     "color": "#F472B6", "emoji": "🐾"},
    "oasis_del_estero": {"nombre": "Oasis del Estero", "color": "#34D399", "emoji": "🌱"},
    "pharma_delux":     {"nombre": "Pharma DeLux",     "color": "#FBBF24", "emoji": "💊"},
    "aviation":         {"nombre": "Aviation Pro",     "color": "#0F3460", "emoji": "✈️"},
    "olivia_coquette":  {"nombre": "Coquette",         "color": "#F9A8D4", "emoji": "🎀"},
    "francisco_sport":  {"nombre": "Sport (Francisco)","color": "#F97316", "emoji": "⚽"},
    "constantino_tech": {"nombre": "Core Tech (Constantino)", "color": "#64748B", "emoji": "⚙️"},
}

COSTO_KG_DEFAULT = 2350.0

def get_linea(cid):
    return LINEAS.get(cid, {"nombre": cid, "color": "#6B7280", "emoji": "📦"})

def calcular_costo_pieza(weight_gr, cost_kg=COSTO_KG_DEFAULT, merma=0.10):
    return (weight_gr * (1 + merma) * cost_kg) / 1000

def cargar_productos():
    df = pd.read_sql("SELECT * FROM products", engine)
    df["costo_unit"]    = df["weight_gr"].apply(lambda w: calcular_costo_pieza(w))
    df["ganancia_unit"] = df["price"] - df["costo_unit"]
    df["margen_pct"]    = (df["ganancia_unit"] / df["price"] * 100).round(1)
    df["valor_stock"]   = df["price"] * df["stock"]
    df["costo_stock"]   = df["costo_unit"] * df["stock"]
    df["ganancia_stock"]= df["ganancia_unit"] * df["stock"]
    df["linea_nombre"]  = df["client_id"].apply(lambda c: get_linea(c)["nombre"])
    df["linea_color"]   = df["client_id"].apply(lambda c: get_linea(c)["color"])
    df["linea_emoji"]   = df["client_id"].apply(lambda c: get_linea(c)["emoji"])
    return df

def cargar_materiales():
    return pd.read_sql("SELECT * FROM materials", engine)

# ─────────────────────────────────────────────
#  AUTENTICACION
# ─────────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})

if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='background:white;border-radius:20px;padding:40px;
                    box-shadow:0 20px 50px rgba(0,0,0,0.1);margin-top:60px;'>
            <h2 style='font-family:Cormorant Garamond,serif;text-align:center;
                       color:#1a1a2e;font-size:2rem;margin-bottom:4px;'>🏛️ El Pasaje</h2>
            <p style='text-align:center;color:#9CA3AF;font-size:0.85rem;margin-bottom:28px;'>
                Sistema de Gestion Integral · v2.6</p>
        </div>
        """, unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="tu@elpasaje.com")
        pwd   = st.text_input("Contrasena", type="password")
        if st.button("INGRESAR AL SISTEMA", use_container_width=True, type="primary"):
            row = pd.read_sql(
                f"SELECT * FROM tenants WHERE email='{email.strip().lower()}' AND password='{pwd.strip()}'",
                engine
            )
            if not row.empty:
                uid  = row["id"].iloc[0]
                role = "admin" if uid == "admin" else "socio"
                st.session_state.update({
                    "auth": True, "user": row["name"].iloc[0],
                    "role": role, "uid": uid
                })
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    linea_cfg = get_linea(st.session_state["uid"])
    st.markdown(f"""
        <div style='text-align:center;padding:20px 0 10px;'>
            <div style='font-size:2.5rem;'>{linea_cfg['emoji']}</div>
            <div style='font-size:1rem;font-weight:600;margin-top:6px;'>{st.session_state['user']}</div>
            <div style='font-size:0.75rem;color:#94a3b8;margin-top:2px;'>
                {"Administracion" if st.session_state["role"] == "admin" else "Socio"}</div>
        </div>
        <hr style='border-color:#ffffff22;margin:0 0 16px;'/>
    """, unsafe_allow_html=True)

    if st.session_state["role"] == "admin":
        menu = st.radio("", [
            "📊 Dashboard Alejandra",
            "📦 Inventario Pro",
            "🛠️ Produccion (Fer)",
            "🤝 Socios",
            "🌱 Impacto Social",
        ], label_visibility="collapsed")
    else:
        menu = st.radio("", [
            "📈 Mi Panel",
            "🛒 Cargar Pedido",
        ], label_visibility="collapsed")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesion", use_container_width=True):
        st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})
        st.rerun()
    st.markdown(
        f"<div style='font-size:0.7rem;color:#4B5563;text-align:center;margin-top:20px;'>"
        f"v2.6 · {datetime.now().strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
#  DASHBOARD ALEJANDRA
# ─────────────────────────────────────────────
if menu == "📊 Dashboard Alejandra":

    st.markdown("""
    <div class='main-header'>
        <h1>📊 Dashboard de Magnitud</h1>
        <p>Inteligencia de negocios en tiempo real · Ecosistema El Pasaje</p>
    </div>
    """, unsafe_allow_html=True)

    df   = cargar_productos()
    mats = cargar_materiales()

    total_stock    = df["valor_stock"].sum()
    total_costo    = df["costo_stock"].sum()
    total_ganancia = df["ganancia_stock"].sum()
    margen_global  = (total_ganancia / total_stock * 100) if total_stock > 0 else 0
    val_mat        = (mats["stock_gr"] * mats["cost_kg"] / 1000).sum()

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "💰 Valor Total Stock",   f"${total_stock:,.0f}",    "Precio venta × unidades",   "#1E3A8A"),
        (c2, "📈 Ganancia Proyectada", f"${total_ganancia:,.0f}", f"Margen: {margen_global:.1f}%", "#059669"),
        (c3, "🏭 Costo Produccion",    f"${total_costo:,.0f}",    "Filamento + merma 10%",     "#DC2626"),
        (c4, "🧵 Stock Materiales",    f"${val_mat:,.0f}",        "Valor bobinas activas",     "#D97706"),
    ]
    for col, title, val, sub, color in cards:
        with col:
            st.markdown(f"""
            <div class='metric-card' style='border-top-color:{color}'>
                <div class='metric-title'>{title}</div>
                <div class='metric-value'>{val}</div>
                <div class='metric-sub'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1.6, 1])

    df_linea = df.groupby("linea_nombre").agg(
        valor_stock=("valor_stock","sum"),
        ganancia=("ganancia_stock","sum"),
        costo=("costo_stock","sum")
    ).reset_index().sort_values("valor_stock", ascending=False)

    with col_a:
        st.markdown("<div class='section-title'>💹 Valor de Stock por Linea</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Costo Produccion", x=df_linea["linea_nombre"], y=df_linea["costo"],
            marker_color="#EF4444", opacity=0.85
        ))
        fig_bar.add_trace(go.Bar(
            name="Ganancia Neta", x=df_linea["linea_nombre"], y=df_linea["ganancia"],
            marker_color="#22C55E", opacity=0.85
        ))
        fig_bar.update_layout(
            barmode="stack", plot_bgcolor="white", paper_bgcolor="white",
            height=320, margin=dict(l=10, r=10, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(tickangle=-20),
            yaxis=dict(tickprefix="$", tickformat=",.0f")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.markdown("<div class='section-title'>🥧 Distribucion del Ecosistema</div>", unsafe_allow_html=True)
        fig_pie = px.pie(
            df_linea, values="valor_stock", names="linea_nombre",
            color_discrete_sequence=px.colors.qualitative.Set2, hole=0.45
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
        fig_pie.update_layout(
            showlegend=False, height=320,
            margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    col_c, col_d = st.columns([1.6, 1])

    with col_c:
        st.markdown("<div class='section-title'>🎯 Ganancia Neta por Producto</div>", unsafe_allow_html=True)
        df_prod = df.sort_values("ganancia_stock", ascending=True)
        colors  = ["#22C55E" if g > 0 else "#EF4444" for g in df_prod["ganancia_stock"]]
        fig_h = go.Figure(go.Bar(
            x=df_prod["ganancia_stock"], y=df_prod["name"],
            orientation="h", marker_color=colors,
            text=[f"${v:,.0f}" for v in df_prod["ganancia_stock"]],
            textposition="outside"
        ))
        fig_h.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=320, margin=dict(l=10, r=80, t=10, b=10),
            xaxis=dict(tickprefix="$", tickformat=",.0f"),
            yaxis=dict(automargin=True)
        )
        st.plotly_chart(fig_h, use_container_width=True)

    with col_d:
        st.markdown("<div class='section-title'>🧵 Estado de Materiales</div>", unsafe_allow_html=True)
        for _, mat in mats.iterrows():
            pct     = min(mat["stock_gr"] / 1000 * 100, 100)
            color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
            val_m   = mat["stock_gr"] * mat["cost_kg"] / 1000
            alerta  = " ⚠️ STOCK BAJO" if pct <= 10 else (" ⚡ Atención" if pct <= 30 else "")
            st.markdown(f"""
            <div style='background:white;border-radius:12px;padding:16px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:12px;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                    <b style='color:#1a1a2e'>{mat['name']}</b>
                    <span style='color:{color_m};font-weight:600'>{mat['stock_gr']:.0f}g{alerta}</span>
                </div>
                <div style='background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;'>
                    <div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div>
                </div>
                <div style='display:flex;justify-content:space-between;margin-top:6px;
                            font-size:0.75rem;color:#6B7280;'>
                    <span>${mat['cost_kg']:,.0f}/kg</span>
                    <span>Valor: ${val_m:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>📋 Analisis Completo por Producto</div>", unsafe_allow_html=True)
    df_show = df[[
        "linea_emoji","linea_nombre","name","sku",
        "weight_gr","costo_unit","price","ganancia_unit","margen_pct","stock","ganancia_stock"
    ]].copy()
    df_show.columns = [
        "","Linea","Producto","SKU",
        "Peso(g)","Costo Unit","Precio Venta","Ganancia Unit","Margen %","Stock","Ganancia Total"
    ]

    def color_margen(val):
        if isinstance(val, (int, float)):
            if val >= 60:  return "color:#059669;font-weight:600"
            if val >= 30:  return "color:#D97706"
            return "color:#DC2626;font-weight:600"
        return ""

    styled = (
        df_show.style
        .format({
            "Costo Unit":    "${:,.0f}",
            "Precio Venta":  "${:,.0f}",
            "Ganancia Unit": "${:,.0f}",
            "Ganancia Total":"${:,.0f}",
            "Margen %":      "{:.1f}%",
        })
        .map(color_margen, subset=["Margen %"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    criticos = df[df["stock"] <= 15]
    if not criticos.empty:
        st.markdown("<div class='section-title'>🚨 Alerta Stock Bajo (≤ 15 unidades)</div>",
                    unsafe_allow_html=True)
        for _, row in criticos.iterrows():
            lvl = get_linea(row["client_id"])
            st.markdown(f"""
            <div class='stock-critico'>
                <b>{lvl['emoji']} {row['name']}</b> · SKU: {row['sku']}
                &nbsp;|&nbsp; Stock: <b style='color:#EF4444'>{int(row['stock'])} uds</b>
                &nbsp;|&nbsp; Pedido sugerido: 20 uds → ${row['price']*20:,.0f} potencial
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  INVENTARIO PRO
# ─────────────────────────────────────────────
elif menu == "📦 Inventario Pro":
    st.markdown("""
    <div class='main-header'>
        <h1>📦 Inventario Unificado</h1>
        <p>Control de stock en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)
    df = cargar_productos()

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        lineas_disp  = ["Todas"] + sorted(df["linea_nombre"].unique().tolist())
        filtro_linea = st.selectbox("Filtrar por linea", lineas_disp)
    with col_f2:
        busqueda = st.text_input("Buscar por SKU o nombre", placeholder="Ej: Kaizen, COQ-TEX...")

    df_f = df.copy()
    if filtro_linea != "Todas":
        df_f = df_f[df_f["linea_nombre"] == filtro_linea]
    if busqueda:
        mask = (df_f["name"].str.contains(busqueda, case=False) |
                df_f["sku"].str.contains(busqueda, case=False))
        df_f = df_f[mask]

    st.caption(f"Mostrando {len(df_f)} productos")
    df_show = df_f[["linea_emoji","linea_nombre","name","sku","price","costo_unit",
                     "ganancia_unit","margen_pct","stock","valor_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Precio","Costo","Ganancia","Margen%","Stock","Valor Total"]
    st.dataframe(
        df_show.style.format({
            "Precio":"${:,.0f}","Costo":"${:,.0f}",
            "Ganancia":"${:,.0f}","Margen%":"{:.1f}%","Valor Total":"${:,.0f}"
        }),
        use_container_width=True, hide_index=True
    )

# ─────────────────────────────────────────────
#  PRODUCCION FER
# ─────────────────────────────────────────────
elif menu == "🛠️ Produccion (Fer)":
    st.markdown("""
    <div class='main-header'>
        <h1>🛠️ Centro de Produccion</h1>
        <p>Gestion de materiales, insumos y cola de pedidos</p>
    </div>
    """, unsafe_allow_html=True)
    mats = cargar_materiales()

    st.markdown("<div class='section-title'>📋 Cola de Pedidos</div>", unsafe_allow_html=True)

    ESTADO_CONFIG = {
        "Pendiente":  {"color": "#F59E0B", "emoji": "⏳"},
        "En Proceso": {"color": "#3B82F6", "emoji": "🖨️"},
        "Listo":      {"color": "#22C55E", "emoji": "✅"},
        "Cancelado":  {"color": "#EF4444", "emoji": "❌"},
    }

    try:
        todos_pedidos = pd.read_sql("""
            SELECT o.id, o.client_id, o.status, o.date, o.notas,
                   oi.product_sku, oi.cantidad, oi.precio_unitario,
                   p.name as product_name
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN products p ON p.sku = oi.product_sku
            WHERE o.status != 'Cancelado'
            ORDER BY o.date DESC
        """, engine)
    except:
        todos_pedidos = pd.DataFrame()

    if todos_pedidos.empty:
        st.info("No hay pedidos pendientes. 🎉")
    else:
        rc1, rc2, rc3 = st.columns(3)
        for col, estado, ecfg in [
            (rc1, "Pendiente",  ESTADO_CONFIG["Pendiente"]),
            (rc2, "En Proceso", ESTADO_CONFIG["En Proceso"]),
            (rc3, "Listo",      ESTADO_CONFIG["Listo"]),
        ]:
            cant = len(todos_pedidos[todos_pedidos["status"] == estado])
            with col:
                st.markdown(f"""
                <div style='background:white;border-radius:12px;padding:16px;text-align:center;
                            border-top:4px solid {ecfg["color"]};
                            box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:16px;'>
                    <div style='font-size:1.8rem;'>{ecfg["emoji"]}</div>
                    <div style='font-size:2rem;font-weight:700;color:{ecfg["color"]};'>{cant}</div>
                    <div style='font-size:0.8rem;color:#6B7280;'>{estado}</div>
                </div>
                """, unsafe_allow_html=True)

        tenants_df = pd.read_sql("SELECT id, name FROM tenants", engine)
        tenant_map = dict(zip(tenants_df["id"], tenants_df["name"]))

        for _, p in todos_pedidos.iterrows():
            estado   = p.get("status", "Pendiente")
            ecfg     = ESTADO_CONFIG.get(estado, ESTADO_CONFIG["Pendiente"])
            socio    = tenant_map.get(p["client_id"], p["client_id"])
            fecha    = str(p.get("date",""))[:10]
            pid      = p["id"]

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div style='background:white;border-radius:12px;padding:14px 20px;
                            border-left:5px solid {ecfg["color"]};
                            box-shadow:0 2px 8px rgba(0,0,0,0.05);'>
                    <div style='font-weight:700;color:#1a1a2e;'>
                        {ecfg["emoji"]} {p["product_name"]}</div>
                    <div style='font-size:0.8rem;color:#6B7280;margin-top:3px;'>
                        👤 {socio} · 📅 {fecha} ·
                        <span style='background:{ecfg["color"]}22;color:{ecfg["color"]};
                                     padding:2px 8px;border-radius:99px;font-weight:600;'>
                            {estado}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                nuevo_estado = st.selectbox(
                    "Estado",
                    ["Pendiente", "En Proceso", "Listo", "Cancelado"],
                    index=["Pendiente","En Proceso","Listo","Cancelado"].index(estado),
                    key=f"estado_{pid}",
                    label_visibility="collapsed"
                )
                if nuevo_estado != estado:
                    if st.button("Actualizar", key=f"btn_{pid}", type="primary"):
                        with engine.connect() as conn:
                            conn.execute(text(
                                f"UPDATE orders SET status='{nuevo_estado}' WHERE id={pid}"
                            ))
                            conn.commit()
                        st.success(f"✅ Pedido #{pid} → {nuevo_estado}")
                        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🧵 Stock de Filamentos</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, (_, mat) in enumerate(mats.iterrows()):
        pct     = min(mat["stock_gr"] / 1000 * 100, 100)
        color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
        col     = c1 if i == 0 else c2
        with col:
            st.markdown(f"""
            <div class='metric-card' style='border-top-color:{color_m}'>
                <div class='metric-title'>🧵 {mat['name']}</div>
                <div class='metric-value'>{mat['stock_gr']:.0f} g</div>
                <div class='metric-sub'>${mat['cost_kg']:,.0f}/kg · Valor: ${mat['stock_gr']*mat['cost_kg']/1000:,.2f}</div>
                <div style='background:#F3F4F6;border-radius:999px;height:10px;overflow:hidden;margin-top:12px;'>
                    <div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div>
                </div>
                <div style='font-size:0.75rem;color:#6B7280;margin-top:4px;'>{pct:.0f}% de 1kg de referencia</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    with st.expander("➕ Reponer Filamento"):
        mat_sel = st.selectbox("Material", mats["name"].tolist())
        gramos  = st.number_input("Gramos a agregar", min_value=100, max_value=5000, step=100)
        if st.button("Registrar Reposicion", type="primary"):
            with engine.connect() as conn:
                conn.execute(text(
                    f"UPDATE materials SET stock_gr = stock_gr + {gramos} WHERE name = '{mat_sel}'"
                ))
                conn.commit()
            st.success(f"✅ +{gramos}g agregados a {mat_sel}")
            st.rerun()

    st.markdown("<div class='section-title'>⚙️ Calculadora de Insumos</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        peso_g   = st.number_input("Peso de pieza (gramos)", min_value=1.0, value=100.0, step=5.0)
        mat_cal  = st.selectbox("Material", mats["name"].tolist(), key="calc_mat")
    with c2:
        merma    = st.slider("% Merma estimada", 5, 25, 10)
        precio_v = st.number_input("Precio de venta ($)", min_value=0.0, value=5000.0, step=100.0)

    costo_kg_sel = mats.loc[mats["name"] == mat_cal, "cost_kg"].iloc[0]
    costo_calc   = calcular_costo_pieza(peso_g, costo_kg_sel, merma / 100)
    ganancia     = precio_v - costo_calc
    margen       = (ganancia / precio_v * 100) if precio_v > 0 else 0

    st.markdown(f"""
    <div style='background:white;border-radius:16px;padding:20px;
                box-shadow:0 4px 12px rgba(0,0,0,0.06);margin-top:12px;'>
        <div style='display:flex;gap:32px;flex-wrap:wrap;'>
            <div>
                <div class='metric-title'>💰 Costo Pieza</div>
                <div style='font-size:2rem;font-weight:700;color:#DC2626;'>${costo_calc:,.2f}</div>
            </div>
            <div>
                <div class='metric-title'>📈 Ganancia</div>
                <div style='font-size:2rem;font-weight:700;color:#059669;'>${ganancia:,.2f}</div>
            </div>
            <div>
                <div class='metric-title'>📊 Margen</div>
                <div style='font-size:2rem;font-weight:700;color:#1E3A8A;'>{margen:.1f}%</div>
            </div>
            <div>
                <div class='metric-title'>✅ Precio Regla x3</div>
                <div style='font-size:2rem;font-weight:700;color:#7C3AED;'>${costo_calc * 3:,.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SOCIOS  ·  Panel rediseñado v2
# ─────────────────────────────────────────────
elif menu == "🤝 Socios":
    st.markdown("""
    <div class='main-header'>
        <h1>🤝 Panel de Socios</h1>
        <p>Ecosistema El Pasaje · Familia + B2B · Visión consolidada</p>
    </div>
    """, unsafe_allow_html=True)

    df      = cargar_productos()
    tenants = pd.read_sql("SELECT * FROM tenants WHERE id != 'admin'", engine)

    B2B_IDS = {"oasis_animal", "oasis_del_estero", "pharma_delux", "aviation"}

    try:
        all_orders = pd.read_sql("SELECT * FROM orders", engine)
    except Exception:
        all_orders = pd.DataFrame()

    ids_socios    = tenants["id"].tolist()
    df_socios     = df[df["client_id"].isin(ids_socios)]
    total_val     = df_socios["valor_stock"].sum()
    total_gan     = df_socios["ganancia_stock"].sum()
    n_socios      = len(tenants)
    pedidos_activos = (
        len(all_orders[all_orders["status"].isin(["Pendiente", "En Proceso"])])
        if not all_orders.empty and "status" in all_orders.columns else 0
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpis = [
        (kpi1, "🤝 Socios Activos",   str(n_socios),          "líneas en el ecosistema",     "#1E3A8A"),
        (kpi2, "💰 Stock Consolidado", f"${total_val:,.0f}",   "valor precio venta",          "#059669"),
        (kpi3, "📈 Ganancia Total",    f"${total_gan:,.0f}",   "potencial del ecosistema",    "#7C3AED"),
        (kpi4, "🏭 Pedidos Activos",   str(pedidos_activos),   "en producción ahora",         "#D97706"),
    ]
    for col, title, val, sub, color in kpis:
        with col:
            st.markdown(f"""
            <div class='metric-card' style='border-top-color:{color}'>
                <div class='metric-title'>{title}</div>
                <div class='metric-value'>{val}</div>
                <div class='metric-sub'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1.6, 1])

    chart_rows = []
    for _, t in tenants.iterrows():
        cfg  = get_linea(t["id"])
        prod = df[df["client_id"] == t["id"]]
        chart_rows.append({
            "Socio":       cfg["nombre"],
            "Costo":       prod["costo_stock"].sum(),
            "Ganancia":    prod["ganancia_stock"].sum(),
            "valor_total": prod["valor_stock"].sum(),
            "Color":       cfg["color"],
        })
    df_chart = pd.DataFrame(chart_rows).sort_values("Ganancia", ascending=True)

    with col_a:
        st.markdown("<div class='section-title'>📊 Stock por Línea (costo + ganancia)</div>",
                    unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Costo Producción", x=df_chart["Costo"], y=df_chart["Socio"],
            orientation="h", marker_color="#EF4444", opacity=0.85
        ))
        fig_bar.add_trace(go.Bar(
            name="Ganancia Neta", x=df_chart["Ganancia"], y=df_chart["Socio"],
            orientation="h", marker_color="#22C55E", opacity=0.85
        ))
        fig_bar.update_layout(
            barmode="stack", plot_bgcolor="white", paper_bgcolor="white",
            height=300, margin=dict(l=10, r=60, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(tickprefix="$", tickformat=",.0f"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.markdown("<div class='section-title'>🥧 Participación en el Ecosistema</div>",
                    unsafe_allow_html=True)
        color_map = {r["Socio"]: r["Color"] for _, r in df_chart.iterrows()}
        fig_pie = px.pie(
            df_chart, values="valor_total", names="Socio",
            color="Socio", color_discrete_map=color_map, hole=0.5
        )
        fig_pie.update_traces(
            textposition="inside", textinfo="percent", textfont_size=10
        )
        fig_pie.update_layout(
            showlegend=True, height=300,
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="white",
            legend=dict(font=dict(size=10))
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    grupos = [
        ("👨‍👩‍👧‍👦 Familia El Pasaje", tenants[~tenants["id"].isin(B2B_IDS)]),
        ("🤝 Socios B2B · Nando",   tenants[ tenants["id"].isin(B2B_IDS)]),
    ]

    for grupo_label, grupo_df in grupos:
        if grupo_df.empty:
            continue

        st.markdown(f"""
        <div style='font-family:Inter,sans-serif;font-size:0.78rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:2px;color:#6B7280;
                    margin:28px 0 14px;border-bottom:1px solid #E5E7EB;padding-bottom:8px;'>
            {grupo_label}
        </div>
        """, unsafe_allow_html=True)

        tenant_list = list(grupo_df.iterrows())
        for i in range(0, len(tenant_list), 2):
            pair   = tenant_list[i : i + 2]
            cols_g = st.columns(2)
            for col_g, (_, t) in zip(cols_g, pair):

                cfg   = get_linea(t["id"])
                prod  = df[df["client_id"] == t["id"]]
                val   = prod["valor_stock"].sum()
                gan   = prod["ganancia_stock"].sum()
                n_sku = len(prod)
                margen_avg = prod["margen_pct"].mean() if n_sku > 0 else 0.0
                color = cfg["color"]

                ped_activos = 0
                if not all_orders.empty and "client_id" in all_orders.columns and "status" in all_orders.columns:
                    ped_socio   = all_orders[all_orders["client_id"] == t["id"]]
                    ped_activos = len(ped_socio[ped_socio["status"].isin(["Pendiente", "En Proceso"])])

                m_color = (
                    "#059669" if margen_avg >= 50 else
                    "#D97706" if margen_avg >= 30 else
                    "#EF4444"
                )
                badge_ped = (
                    f"<div style='margin-top:12px;display:inline-block;"
                    f"background:{color}1a;color:{color};"
                    f"padding:4px 12px;border-radius:99px;"
                    f"font-size:0.72rem;font-weight:700;'>"
                    f"🏭 {ped_activos} pedido{'s' if ped_activos != 1 else ''} en curso</div>"
                    if ped_activos > 0 else ""
                )
                badge_tipo = "B2B" if t["id"] in B2B_IDS else "Familia"

                with col_g:
                    st.markdown(f"""
                    <div style='background:white;border-radius:20px;overflow:hidden;
                                box-shadow:0 4px 24px rgba(0,0,0,0.08);margin-bottom:16px;'>
                        <div style='background:{color};padding:18px 22px 16px;
                                    display:flex;align-items:center;gap:14px;'>
                            <div style='font-size:2.4rem;line-height:1;'>{cfg["emoji"]}</div>
                            <div>
                                <div style='font-family:Cormorant Garamond,serif;
                                            font-size:1.3rem;font-weight:700;color:white;
                                            line-height:1.1;'>{t["name"]}</div>
                                <div style='font-size:0.68rem;color:rgba(255,255,255,0.72);
                                            letter-spacing:1.5px;text-transform:uppercase;
                                            margin-top:4px;'>{badge_tipo}</div>
                            </div>
                        </div>
                        <div style='padding:18px 22px 20px;'>
                            <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;'>
                                <div>
                                    <div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;
                                                text-transform:uppercase;letter-spacing:0.8px;'>Stock</div>
                                    <div style='font-family:Cormorant Garamond,serif;
                                                font-size:1.3rem;font-weight:700;color:#1a1a2e;'>
                                        ${val:,.0f}</div>
                                </div>
                                <div>
                                    <div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;
                                                text-transform:uppercase;letter-spacing:0.8px;'>Ganancia</div>
                                    <div style='font-family:Cormorant Garamond,serif;
                                                font-size:1.3rem;font-weight:700;color:#059669;'>
                                        ${gan:,.0f}</div>
                                </div>
                                <div>
                                    <div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;
                                                text-transform:uppercase;letter-spacing:0.8px;'>SKUs</div>
                                    <div style='font-family:Cormorant Garamond,serif;
                                                font-size:1.3rem;font-weight:700;color:#1a1a2e;'>
                                        {n_sku}</div>
                                </div>
                            </div>
                            <div style='margin-top:14px;'>
                                <div style='display:flex;justify-content:space-between;
                                            font-size:0.7rem;color:#6B7280;margin-bottom:4px;'>
                                    <span>Margen promedio</span>
                                    <span style='color:{m_color};font-weight:700;'>
                                        {margen_avg:.1f}%</span>
                                </div>
                                <div style='background:#F3F4F6;border-radius:999px;
                                            height:7px;overflow:hidden;'>
                                    <div style='width:{min(margen_avg, 100):.0f}%;
                                                background:{m_color};height:100%;
                                                border-radius:999px;'></div>
                                </div>
                            </div>
                            {badge_ped}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if not prod.empty:
                        with st.expander(f"📦 Ver productos · {cfg['nombre']} ({n_sku} SKUs)"):
                            st.dataframe(
                                prod[["name","sku","price","stock",
                                      "ganancia_unit","margen_pct"]].rename(columns={
                                    "name":         "Producto",
                                    "sku":          "SKU",
                                    "price":        "Precio",
                                    "stock":        "Stock",
                                    "ganancia_unit":"Ganancia Unit",
                                    "margen_pct":   "Margen %",
                                }).style.format({
                                    "Precio":        "${:,.0f}",
                                    "Ganancia Unit": "${:,.0f}",
                                    "Margen %":      "{:.1f}%",
                                }),
                                use_container_width=True,
                                hide_index=True,
                            )
                    else:
                        st.caption("Sin productos cargados en esta línea.")

# ─────────────────────────────────────────────
#  MI PANEL (Socio)
# ─────────────────────────────────────────────
elif menu == "📈 Mi Panel":
    uid = st.session_state["uid"]
    cfg = get_linea(uid)
    st.markdown(f"""
    <div class='main-header' style='background:linear-gradient(135deg,{cfg["color"]}cc,{cfg["color"]}88);'>
        <h1>{cfg['emoji']} Panel {cfg['nombre']}</h1>
        <p>Bienvenido/a, {st.session_state['user']}</p>
    </div>
    """, unsafe_allow_html=True)

    df   = cargar_productos()
    prod = df[df["client_id"] == uid]
    val  = prod["valor_stock"].sum()
    gan  = prod["ganancia_stock"].sum()

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("💰 Capital en Stock",    f"${val:,.0f}")
    cc2.metric("📈 Ganancia Proyectada", f"${gan:,.0f}")
    cc3.metric("📦 Productos Activos",   f"{len(prod)} SKUs")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🏭 Mis Pedidos en Fábrica</div>", unsafe_allow_html=True)

    try:
        pedidos = pd.read_sql(
            f"SELECT * FROM orders WHERE client_id='{uid}' ORDER BY date DESC LIMIT 10",
            engine
        )
    except:
        pedidos = pd.DataFrame()

    ESTADO_CONFIG = {
        "Pendiente":   {"color": "#F59E0B", "emoji": "⏳", "label": "Esperando a Fer"},
        "En Proceso":  {"color": "#3B82F6", "emoji": "🖨️", "label": "Imprimiendo ahora"},
        "Listo":       {"color": "#22C55E", "emoji": "✅", "label": "Listo para retirar"},
        "Cancelado":   {"color": "#EF4444", "emoji": "❌", "label": "Cancelado"},
    }

    if pedidos.empty:
        st.markdown(f"""
        <div style='background:white;border-radius:14px;padding:24px;text-align:center;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);color:#9CA3AF;'>
            <div style='font-size:2rem;'>🏭</div>
            <div style='margin-top:8px;'>No tenés pedidos en curso todavía.</div>
            <div style='font-size:0.8rem;margin-top:4px;'>
                Usá "Cargar Pedido" para solicitar producción a Fer.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if "status" in pedidos.columns:
            estados = pedidos["status"].value_counts()
            cols_e = st.columns(len(ESTADO_CONFIG))
            for col, (estado, ecfg) in zip(cols_e, ESTADO_CONFIG.items()):
                cant = estados.get(estado, 0)
                with col:
                    st.markdown(f"""
                    <div style='background:white;border-radius:12px;padding:14px;text-align:center;
                                border-top:4px solid {ecfg["color"]};
                                box-shadow:0 2px 8px rgba(0,0,0,0.05);'>
                        <div style='font-size:1.5rem;'>{ecfg["emoji"]}</div>
                        <div style='font-size:1.6rem;font-weight:700;color:{ecfg["color"]};'>{cant}</div>
                        <div style='font-size:0.75rem;color:#6B7280;'>{ecfg["label"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            for _, p in pedidos.iterrows():
                estado  = p.get("status", "Pendiente")
                ecfg    = ESTADO_CONFIG.get(estado, ESTADO_CONFIG["Pendiente"])
                fecha   = str(p.get("date",""))[:10]
                producto = p.get("product_name", "—")
                st.markdown(f"""
                <div style='background:white;border-radius:12px;padding:16px 20px;
                            margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);
                            border-left:5px solid {ecfg["color"]};
                            display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <div style='font-weight:700;color:#1a1a2e;font-size:0.95rem;'>
                            {ecfg["emoji"]} {producto}</div>
                        <div style='font-size:0.78rem;color:#9CA3AF;margin-top:3px;'>
                            Pedido el {fecha}</div>
                    </div>
                    <div style='background:{ecfg["color"]}22;color:{ecfg["color"]};
                                padding:4px 12px;border-radius:99px;font-size:0.8rem;
                                font-weight:700;white-space:nowrap;'>
                        {estado}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>📦 Mis Productos</div>", unsafe_allow_html=True)
    if prod.empty:
        st.info("Aun no tenes productos cargados en tu linea.")
    else:
        st.dataframe(
            prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={
                "name":"Producto","sku":"SKU","price":"Precio",
                "stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen%"
            }).style.format({
                "Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen%":"{:.1f}%"
            }),
            use_container_width=True, hide_index=True
        )

# ─────────────────────────────────────────────
#  CARGAR PEDIDO (Socio)
# ─────────────────────────────────────────────
elif menu == "🛒 Cargar Pedido":
    uid = st.session_state["uid"]
    cfg = get_linea(uid)
    st.markdown(f"""
    <div class='main-header'>
        <h1>🛒 Nuevo Pedido · {cfg['nombre']}</h1>
        <p>Solicita produccion a Fer de forma digital</p>
    </div>
    """, unsafe_allow_html=True)

    prods_admin = pd.read_sql("SELECT name, sku FROM products WHERE client_id='admin'", engine)
    producto    = st.selectbox("Producto", prods_admin["name"].tolist())
    cantidad    = st.number_input("Cantidad", min_value=1, max_value=100, value=1)
    notas       = st.text_area("Notas para Fer (color, urgencia, etc.)", height=80)

    if st.button("Confirmar Pedido", type="primary"):
        with engine.connect() as conn:
            result = conn.execute(text(
                f"INSERT INTO orders (client_id, status, date, notas, color_pedido) "
                f"VALUES ('{uid}', 'Pendiente', '{datetime.now().isoformat()}', "
                f"'{notas.strip()}', '') "
            ))
            order_id = result.lastrowid
            precio_unit = pd.read_sql(
                f"SELECT price FROM products WHERE name='{producto}'", engine
            )["price"].iloc[0]
            conn.execute(text(
                f"INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) "
                f"SELECT {order_id}, sku, {cantidad}, {precio_unit} "
                f"FROM products WHERE name='{producto}'"
            ))
            conn.commit()
        st.success(f"✅ Pedido registrado: {cantidad}x {producto}")
        st.balloons()

elif menu == "🌱 Impacto Social":
    st.markdown("<div class='main-header'><h1>🌱 Impacto Social</h1><p>Transparencia total · Fondos solidarios</p></div>", unsafe_allow_html=True)

    FONDOS = {
        "refugio_oasis":     {"nombre": "Refugio Oasis Animal", "emoji": "🐾", "color": "#F472B6", "meta": 50000},
        "mentes_brillantes": {"nombre": "Mentes Brillantes",    "emoji": "🧠", "color": "#818CF8", "meta": 40000},
        "fondo_general":     {"nombre": "Fondo General",        "emoji": "❤️",  "color": "#FB7185", "meta": 30000},
    }

    try:
        dons = pd.read_sql("SELECT * FROM donations ORDER BY fecha DESC", engine)
    except:
        dons = pd.DataFrame()

    cols = st.columns(3)
    for col, (fondo_id, f) in zip(cols, FONDOS.items()):
        recaudado = dons[dons["fondo"] == fondo_id]["monto"].sum() if not dons.empty else 0
        pct = min(recaudado / f["meta"] * 100, 100)
        faltan = max(f["meta"] - recaudado, 0)
        with col:
            st.markdown(f"""
            <div style='background:white;border-radius:18px;padding:24px;
                        box-shadow:0 4px 20px rgba(0,0,0,0.08);
                        border-top:5px solid {f["color"]};margin-bottom:16px;'>
                <div style='font-size:2rem;'>{f["emoji"]}</div>
                <div style='font-size:1rem;font-weight:700;color:#1a1a2e;margin:8px 0 2px;'>
                    {f["nombre"]}</div>
                <div style='font-size:2rem;font-weight:700;color:{f["color"]};
                            font-family:Cormorant Garamond,serif;'>${recaudado:,.0f}</div>
                <div style='font-size:0.78rem;color:#9CA3AF;margin-bottom:12px;'>
                    Meta mensual: ${f["meta"]:,.0f}</div>
                <div style='background:#F3F4F6;border-radius:999px;height:14px;overflow:hidden;'>
                    <div style='width:{pct:.0f}%;background:{f["color"]};height:100%;
                                border-radius:999px;'></div>
                </div>
                <div style='font-size:0.75rem;color:#6B7280;margin-top:6px;'>
                    {"🎉 ¡Meta alcanzada!" if faltan == 0 else f"Faltan ${faltan:,.0f}"}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### ➕ Registrar Donacion Manual")
    dc1, dc2, dc3, dc4 = st.columns([1.5, 1, 1, 1.5])
    with dc1:
        fondo_sel = st.selectbox("Fondo destino",
            list(FONDOS.keys()),
            format_func=lambda x: f"{FONDOS[x]['emoji']} {FONDOS[x]['nombre']}")
    with dc2:
        tipo_don = st.selectbox("Tipo", ["urna","qr","redondeo"],
            format_func=lambda x: {"urna":"🏺 Urna","qr":"📱 QR","redondeo":"🔄 Redondeo"}[x])
    with dc3:
        monto_don = st.number_input("Monto ($)", min_value=1.0, step=50.0, value=500.0)
    with dc4:
        desc_don = st.text_input("Descripcion", placeholder="Ej: Urna fin de semana")

    if st.button("💚 REGISTRAR DONACION", type="primary"):
        with engine.connect() as conn:
            conn.execute(text(
                f"INSERT INTO donations (fondo, monto, tipo, descripcion, fecha) "
                f"VALUES ('{fondo_sel}', {monto_don}, '{tipo_don}', '{desc_don}', '{datetime.now().date()}')"
            ))
            conn.commit()
        st.success(f"✅ ${monto_don:,.0f} registrados en {FONDOS[fondo_sel]['nombre']} 💚")
        st.rerun()

    st.markdown("### 📋 Historial de Donaciones")
    if dons.empty:
        st.info("Aun no hay donaciones. ¡La primera puede ser hoy! 💚")
    else:
        TIPO_ICON = {"urna":"🏺","qr":"📱","redondeo":"🔄","producto":"🌱"}
        for _, row in dons.head(20).iterrows():
            icon  = TIPO_ICON.get(row["tipo"], "💰")
            finfo = FONDOS.get(row["fondo"], {"nombre": row["fondo"], "emoji":"❓", "color":"#ccc"})
            st.markdown(f"""
            <div style='background:white;border-radius:12px;padding:14px 18px;
                        margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);
                        border-left:4px solid {finfo["color"]};'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <b>{icon} {finfo["emoji"]} {finfo["nombre"]}</b>
                        <span style='margin-left:10px;font-size:0.75rem;color:#6B7280;'>
                            {row["tipo"].upper()} · {row["fecha"]}</span>
                        <div style='font-size:0.78rem;color:#9CA3AF;margin-top:3px;'>
                            {row.get("descripcion","") or ""}</div>
                    </div>
                    <div style='font-size:1.4rem;font-weight:700;color:{finfo["color"]};'>
                        ${row["monto"]:,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
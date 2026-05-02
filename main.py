import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import hashlib

st.set_page_config(
    page_title="El Pasaje - Sistema Integral",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── APP ── */
.stApp { background-color: #F0F2F6; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] { background-color: #1a1a2e !important; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #FFFFFF !important; }
/* Radio buttons en sidebar */
[data-testid="stSidebar"] [data-baseweb="radio"] label p { 
    color: #FFFFFF !important; font-size: 0.9rem !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] [data-checked="true"] label p { 
    color: #C9A84C !important; font-weight: 700 !important;
}
/* Version label */
[data-testid="stSidebar"] .version-label { color: #94a3b8 !important; }
/* Botón cerrar sesión */
[data-testid="stSidebar"] button { 
    background: rgba(255,255,255,0.1) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] button:hover { 
    background: rgba(201,168,76,0.2) !important;
    border-color: #C9A84C !important;
}

/* ── CARDS ── */
.metric-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.07); border-top: 5px solid; transition: transform 0.2s; height: 100%; }
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.12); }
.metric-title { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #6B7280; margin-bottom: 8px; }
.metric-value { font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 700; color: #1a1a2e; line-height: 1; }
.metric-sub   { font-size: 12px; color: #9CA3AF; margin-top: 6px; }

/* ── HEADER ── */
.main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 28px 36px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin-bottom: 28px; }
.main-header h1 { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; margin: 0; letter-spacing: 2px; color: white !important; }
.main-header p  { font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #94a3b8; margin: 6px 0 0; }

/* ── TITULOS ── */
.section-title { font-family: 'Cormorant Garamond', serif; font-size: 1.5rem; color: #1a1a2e; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin: 28px 0 16px; }
.stock-critico { background: #FEF2F2; border-left: 5px solid #EF4444; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }

/* ── FORMULARIOS ── */
.stExpander { background: white !important; }
.stTextInput label, .stSelectbox label, .stTextArea label, 
.stCheckbox label, .stNumberInput label { 
    color: #1a1a2e !important; font-weight: 600 !important; font-size: 0.85rem !important;
}
.stForm { background: white; border-radius: 16px; padding: 20px; }
div[data-testid="stFormSubmitButton"] button { margin-top: 12px; }
.stExpander details { background: white !important; }
.stExpander summary p { color: #1a1a2e !important; font-weight: 600 !important; }
.stMarkdown p, .stMarkdown span { color: #1a1a2e !important; }
.stTabs [data-baseweb="tab"] { color: #1a1a2e !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

from crear_schema_v3 import init_schema as _init_schema
_init_schema()

LINEAS = {
    "admin":            {"nombre": "Administracion",     "color": "#1E3A8A", "emoji": "🏛️"},
    "oasis_animal":     {"nombre": "Oasis Animal",       "color": "#F472B6", "emoji": "🐾"},
    "oasis_del_estero": {"nombre": "Oasis del Estero",   "color": "#34D399", "emoji": "🌱"},
    "pharma_delux":     {"nombre": "Pharma DeLux",       "color": "#FBBF24", "emoji": "💊"},
    "aviation":         {"nombre": "Aviation Pro",       "color": "#0F3460", "emoji": "✈️"},
    "olivia_coquette":  {"nombre": "Coquette",           "color": "#F9A8D4", "emoji": "🎀"},
    "francisco_sport":  {"nombre": "Sport (Francisco)",  "color": "#F97316", "emoji": "⚽"},
    "constantino_tech": {"nombre": "Core Tech (Constantino)", "color": "#64748B", "emoji": "⚙️"},
    "vkhome_cliente":   {"nombre": "VK-Home",            "color": "#A78BFA", "emoji": "🏡"},
    "agustina":         {"nombre": "Agustina",           "color": "#6366F1", "emoji": "✨"},
}
COSTO_KG_DEFAULT = 2350.0

def get_linea(cid):
    return LINEAS.get(cid, {"nombre": cid, "color": "#6B7280", "emoji": "📦"})

@st.cache_data(ttl=60)
def get_lineas_usuario(uid: str) -> list[str]:
    """Retorna las linea_ids visibles para un usuario.
    Para socio_multi: lee tenant_lineas. Para socio regular: [uid].
    Genérico — cualquier futuro socio_multi solo necesita filas en tenant_lineas."""
    with engine.connect() as _conn:
        rows = pd.read_sql(
            text("SELECT linea_id FROM tenant_lineas WHERE tenant_id=:uid"),
            _conn, params={"uid": uid}
        )
    return rows["linea_id"].tolist() if not rows.empty else [uid]

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

# AUTENTICACION
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})

if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;background:white;border-radius:20px;padding:36px 40px 28px;box-shadow:0 20px 50px rgba(0,0,0,0.12);margin-top:60px;'>
          <svg width="130" height="130" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto 16px;">
            <circle cx="80" cy="80" r="74" fill="white"/>
            <circle cx="80" cy="80" r="75" fill="none" stroke="#1a1a2e" stroke-width="3"/>
            <circle cx="80" cy="80" r="67" fill="none" stroke="#C9A84C" stroke-width="2.5"/>
            <circle cx="80" cy="80" r="59" fill="none" stroke="#1a1a2e" stroke-width="1.5"/>
            <text x="80" y="97" font-family="Georgia,'Times New Roman',serif" font-size="42" font-weight="700" fill="#1a1a2e" text-anchor="middle" letter-spacing="-1">EP</text>
            <polygon points="80,2 85,11 80,20 75,11"   fill="#C9A84C"/>
            <polygon points="80,158 85,149 80,140 75,149" fill="#C9A84C"/>
            <polygon points="158,80 149,85 140,80 149,75" fill="#C9A84C"/>
            <polygon points="2,80 11,85 20,80 11,75"   fill="#C9A84C"/>
            <circle cx="121" cy="39" r="3" fill="#C9A84C"/>
            <circle cx="121" cy="121" r="3" fill="#C9A84C"/>
            <circle cx="39"  cy="121" r="3" fill="#C9A84C"/>
            <circle cx="39"  cy="39"  r="3" fill="#C9A84C"/>
          </svg>
          <div style='font-family:Cormorant Garamond,Georgia,serif;font-size:1.4rem;font-weight:700;letter-spacing:6px;color:#1a1a2e;text-transform:uppercase;'>El Pasaje</div>
          <div style='font-size:0.6rem;font-weight:600;letter-spacing:4px;color:#C9A84C;text-transform:uppercase;margin-top:4px;'>3 D &nbsp; S T U D I O</div>
        </div>
        """, unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="tu@elpasaje.com")
        pwd   = st.text_input("Contrasena", type="password")
        if st.button("INGRESAR AL SISTEMA", use_container_width=True, type="primary"):
            hashed_pwd = hashlib.sha256(pwd.strip().encode()).hexdigest()
            with engine.connect() as _conn:
                row = pd.read_sql(
                    text("SELECT * FROM tenants WHERE email=:email AND password=:pwd"),
                    _conn,
                    params={"email": email.strip().lower(), "pwd": hashed_pwd}
                )
            if not row.empty:
                uid  = row["id"].iloc[0]
                tipo = row["tipo"].iloc[0] if "tipo" in row.columns else "socio"
                role = "admin" if uid == "admin" else ("produccion" if tipo == "produccion" else ("socio_multi" if tipo == "socio_multi" else "socio"))
                st.session_state.update({"auth": True, "user": row["name"].iloc[0], "role": role, "uid": uid})
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        st.markdown("""
        <div style='text-align:center;margin-top:16px;'>
          <a href='https://wa.me/5491165497234' target='_blank'
             style='display:inline-flex;align-items:center;gap:6px;text-decoration:none;
                    color:#25D366;font-size:0.78rem;font-weight:500;'>
            <svg width='16' height='16' viewBox='0 0 24 24' fill='#25D366'>
              <path d='M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z'/>
            </svg>
            Consultas por WhatsApp
          </a>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# SIDEBAR
with st.sidebar:
    linea_cfg = get_linea(st.session_state["uid"])
    st.markdown(f"""
        <div style='text-align:center;padding:20px 0 10px;'>
            <div style='font-size:2.5rem;'>{linea_cfg['emoji']}</div>
            <div style='font-size:1rem;font-weight:600;margin-top:6px;'>{st.session_state['user']}</div>
            <div style='font-size:0.75rem;color:#94a3b8;margin-top:2px;'>{"Administracion" if st.session_state["role"] == "admin" else ("Produccion" if st.session_state["role"] == "produccion" else "Socio")}</div>
        </div>
        <hr style='border-color:#ffffff22;margin:0 0 16px;'/>
    """, unsafe_allow_html=True)
    if st.session_state["role"] == "admin":
        menu = st.radio("", ["📊 Dashboard Alejandra","📦 Inventario Pro","🛠️ Produccion (Fer)","🤝 Socios","👥 Clientes","🌱 Impacto Social"], label_visibility="collapsed")
    elif st.session_state["role"] == "produccion":
        menu = st.radio("", ["🛠️ Produccion (Fer)"], label_visibility="collapsed")
    elif st.session_state["role"] == "socio_multi":
        _lids = get_lineas_usuario(st.session_state["uid"])
        _nombre_a_id = {LINEAS[l]["nombre"]: l for l in _lids if l in LINEAS}
        _opciones = ["Todas"] + list(_nombre_a_id.keys())
        _sel = st.selectbox("Línea", _opciones, key="linea_sel")
        st.session_state["linea_filtro"] = _lids if _sel == "Todas" else [_nombre_a_id[_sel]]
        menu = st.radio("", ["📈 Mi Panel","🛒 Cargar Pedido"], label_visibility="collapsed")
    else:
        menu = st.radio("", ["📈 Mi Panel","🛒 Cargar Pedido"], label_visibility="collapsed")
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesion", use_container_width=True):
        st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})
        st.rerun()
    st.markdown(f"<div style='font-size:0.7rem;color:#94a3b8;text-align:center;margin-top:20px;'>v2.6 · {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

# DASHBOARD ALEJANDRA
if menu == "📊 Dashboard Alejandra":
    st.markdown("<div class='main-header'><h1>📊 Dashboard de Magnitud</h1><p>Inteligencia de negocios en tiempo real · Ecosistema El Pasaje</p></div>", unsafe_allow_html=True)
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

elif menu == "📦 Inventario Pro":
    st.markdown("<div class='main-header'><h1>📦 Inventario Unificado</h1><p>Control de stock en tiempo real</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        filtro_linea = st.selectbox("Filtrar por linea", ["Todas"] + sorted(df["linea_nombre"].unique().tolist()))
    with col_f2:
        busqueda = st.text_input("Buscar por SKU o nombre", placeholder="Ej: Kaizen, COQ-TEX...")
    df_f = df.copy()
    if filtro_linea != "Todas": df_f = df_f[df_f["linea_nombre"] == filtro_linea]
    if busqueda:
        mask = df_f["name"].str.contains(busqueda, case=False) | df_f["sku"].str.contains(busqueda, case=False)
        df_f = df_f[mask]
    st.caption(f"Mostrando {len(df_f)} productos")
    df_show = df_f[["linea_emoji","linea_nombre","name","sku","price","costo_unit","ganancia_unit","margen_pct","stock","valor_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Precio","Costo","Ganancia","Margen%","Stock","Valor Total"]
    st.dataframe(df_show.style.format({"Precio":"${:,.0f}","Costo":"${:,.0f}","Ganancia":"${:,.0f}","Margen%":"{:.1f}%","Valor Total":"${:,.0f}"}), use_container_width=True, hide_index=True)

elif menu == "🛠️ Produccion (Fer)":
    st.markdown("<div class='main-header'><h1>🛠️ Centro de Produccion</h1><p>Cola de pedidos · Fabricacion · Materiales</p></div>", unsafe_allow_html=True)
    _EC = {"Pendiente":{"color":"#F59E0B","emoji":"⏳"},"En Proceso":{"color":"#3B82F6","emoji":"🖨️"},"Listo":{"color":"#22C55E","emoji":"✅"},"Cancelado":{"color":"#EF4444","emoji":"❌"}}
    _hoy_str = datetime.now().strftime("%Y-%m-%d")
    # ── Cargar datos comunes ──────────────────────────────
    mats = cargar_materiales()
    try:
        _pedidos_all = pd.read_sql("""
            SELECT o.id, o.client_id, o.status, o.date, o.notas, o.fecha_entrega_est,
                   oi.product_sku, oi.cantidad,
                   p.name AS product_name, p.weight_gr, p.material_id
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN products p ON p.sku = oi.product_sku
            ORDER BY o.date DESC
        """, engine)
    except Exception:
        _pedidos_all = pd.DataFrame()
    try:
        _tenant_map = dict(pd.read_sql("SELECT id, name FROM tenants", engine).values)
    except Exception:
        _tenant_map = {}
    _pedidos_activos = _pedidos_all[_pedidos_all["status"].isin(["Pendiente","En Proceso"])] if not _pedidos_all.empty else pd.DataFrame()
    tab_panel, tab_fab, tab_mats, tab_cola = st.tabs(["🛠️ Mi Panel", "📦 Cargar Fabricacion", "🧵 Materiales", "📋 Cola de Pedidos"])

    # ══════════════════════════════════════════════════════
    # TAB 1 — MI PANEL PRODUCCION
    # ══════════════════════════════════════════════════════
    with tab_panel:
        try:
            _fab_total = pd.read_sql("SELECT COUNT(*) AS n FROM production_log", engine).iloc[0]["n"]
        except Exception:
            _fab_total = 0
        _criticos = len(mats[mats["stock_gr"] <= mats["stock_minimo_gr"]]) if not mats.empty else 0
        _nuevos_hoy = len(_pedidos_all[_pedidos_all["date"].astype(str).str.startswith(_hoy_str)]) if not _pedidos_all.empty else 0
        _n_pendientes = len(_pedidos_all[_pedidos_all["status"] == "Pendiente"]) if not _pedidos_all.empty else 0
        k1, k2, k3, k4 = st.columns(4)
        for _col, _title, _val, _sub, _color in [
            (k1, "⏳ Pendientes",       str(_n_pendientes), "en espera de produccion", "#F59E0B"),
            (k2, "🆕 Nuevos Hoy",       str(_nuevos_hoy),   "pedidos del dia",         "#3B82F6"),
            (k3, "✅ Piezas Fabricadas", str(_fab_total),    "registradas en log",      "#22C55E"),
            (k4, "⚠️ Mat. Criticos",    str(_criticos),     "bajo stock minimo",       "#EF4444"),
        ]:
            with _col:
                st.markdown(f"<div class='metric-card' style='border-top-color:{_color}'><div class='metric-title'>{_title}</div><div class='metric-value'>{_val}</div><div class='metric-sub'>{_sub}</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-title' style='margin-top:20px;'>📋 Cola Activa</div>", unsafe_allow_html=True)
        if _pedidos_activos.empty:
            st.success("No hay pedidos activos ahora mismo.")
        else:
            for _, _p in _pedidos_activos.iterrows():
                _ecfg   = _EC.get(_p["status"], _EC["Pendiente"])
                _socio  = _tenant_map.get(_p["client_id"], _p["client_id"])
                _fecha  = str(_p["date"])[:10]
                _pid    = _p["id"]
                _prod   = _p.get("product_name") or "—"
                _gramos = f"{_p['weight_gr']:.0f} g" if pd.notna(_p.get("weight_gr")) else "—"
                _entrega = _p.get("fecha_entrega_est") or "—"
                with st.expander(f"{_ecfg['emoji']} Pedido #{_pid} · {_prod} · {_socio}"):
                    _c1, _c2, _c3, _c4 = st.columns(4)
                    _c1.metric("Cliente", _socio)
                    _c2.metric("Gramos estimados", _gramos)
                    _c3.metric("Entrega est.", _entrega)
                    _c4.metric("Cargado", _fecha)
                    if _p.get("notas"):
                        st.caption(f"Notas: {_p['notas']}")
                    _nuevo_est = st.selectbox("Cambiar estado", ["Pendiente","En Proceso","Listo","Cancelado"],
                                              index=["Pendiente","En Proceso","Listo","Cancelado"].index(_p["status"]),
                                              key=f"panel_est_{_pid}")
                    if _nuevo_est != _p["status"]:
                        if st.button("Confirmar cambio", key=f"panel_btn_{_pid}", type="primary"):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE orders SET status=:s WHERE id=:id"), {"s": _nuevo_est, "id": _pid})
                                _conn.commit()
                            st.success(f"Pedido #{_pid} → {_nuevo_est}")
                            st.rerun()

    # ══════════════════════════════════════════════════════
    # TAB 2 — CARGAR FABRICACION
    # ══════════════════════════════════════════════════════
    with tab_fab:
        st.markdown("<div class='section-title'>Registrar produccion de una pieza</div>", unsafe_allow_html=True)
        if _pedidos_activos.empty:
            st.info("No hay pedidos activos para registrar fabricacion.")
        else:
            _ops_pedido = {f"#{r['id']} · {r.get('product_name','—')} · {_tenant_map.get(r['client_id'],r['client_id'])}": r["id"]
                           for _, r in _pedidos_activos.drop_duplicates("id").iterrows()}
            _sel_label  = st.selectbox("Pedido asociado", list(_ops_pedido.keys()), key="fab_pedido")
            _sel_oid    = _ops_pedido[_sel_label]
            _pedido_row = _pedidos_activos[_pedidos_activos["id"] == _sel_oid].iloc[0]
            _sku_auto   = _pedido_row.get("product_sku") or ""
            _mid_auto   = _pedido_row.get("material_id") or ""
            _fc1, _fc2  = st.columns(2)
            with _fc1:
                _fab_sku   = st.text_input("SKU del producto", value=_sku_auto, key="fab_sku")
                _fab_grams = st.number_input("Gramos consumidos", min_value=1.0, max_value=2000.0, value=max(float(_pedido_row.get("weight_gr") or 50), 1.0), step=5.0, key="fab_grams")
                _fab_res   = st.selectbox("Resultado", ["ok","fallo","reimpresion"], key="fab_res")
            with _fc2:
                _mat_nombres = mats["name"].tolist() if not mats.empty else []
                _mat_ids     = mats["material_id"].tolist() if not mats.empty else []
                _mid_idx     = _mat_ids.index(_mid_auto) if _mid_auto in _mat_ids else 0
                _fab_mat_nom = st.selectbox("Material usado", _mat_nombres, index=_mid_idx, key="fab_mat")
                _fab_tiempo  = st.number_input("Tiempo real (minutos)", min_value=1, max_value=600, value=30, key="fab_tiempo")
            _fab_desc = ""
            if _fab_res != "ok":
                _fab_desc = st.text_area("Descripcion del fallo/problema", height=60, key="fab_desc")
            if st.button("Registrar Fabricacion", type="primary", key="fab_submit"):
                _fab_mid = mats.loc[mats["name"] == _fab_mat_nom, "material_id"].iloc[0] if not mats.empty else ""
                with engine.connect() as _conn:
                    _conn.execute(text("""
                        INSERT INTO production_log
                        (order_id, product_sku, material_id, gramos_usados, tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                        VALUES (:oid, :sku, :mid, :grams, :tiempo, :fi, :ff, :res)
                    """), {"oid": int(_sel_oid), "sku": _fab_sku, "mid": _fab_mid,
                           "grams": _fab_grams, "tiempo": _fab_tiempo,
                           "fi": _hoy_str, "ff": _hoy_str,
                           "res": _fab_res + (f" — {_fab_desc}" if _fab_desc else "")})
                    _conn.execute(text("UPDATE materials SET stock_gr = stock_gr - :g WHERE material_id = :mid"),
                                  {"g": _fab_grams, "mid": _fab_mid})
                    if _fab_res == "ok":
                        _conn.execute(text("UPDATE orders SET status='Listo' WHERE id=:id"), {"id": int(_sel_oid)})
                    _conn.commit()
                st.success(f"Fabricacion registrada · {_fab_grams}g de {_fab_mat_nom} descontados del stock")
                st.rerun()
        st.markdown("<div class='section-title' style='margin-top:24px;'>Ultimas 20 fabricaciones</div>", unsafe_allow_html=True)
        try:
            _hist = pd.read_sql("""
                SELECT pl.id, pl.order_id, pl.product_sku, m.name AS material,
                       pl.gramos_usados, pl.tiempo_real_min, pl.fecha_fin, pl.resultado
                FROM production_log pl
                LEFT JOIN materials m ON m.material_id = pl.material_id
                ORDER BY pl.id DESC LIMIT 20
            """, engine)
            if _hist.empty:
                st.caption("Sin fabricaciones registradas todavia.")
            else:
                st.dataframe(_hist.rename(columns={"id":"#","order_id":"Pedido","product_sku":"SKU","material":"Material","gramos_usados":"Gramos","tiempo_real_min":"Min","fecha_fin":"Fecha","resultado":"Resultado"}), use_container_width=True, hide_index=True)
        except Exception as _e:
            st.caption(f"Sin datos: {_e}")

    # ══════════════════════════════════════════════════════
    # TAB 3 — MATERIALES (mejorado)
    # ══════════════════════════════════════════════════════
    with tab_mats:
        if mats.empty:
            st.info("No hay materiales cargados.")
        else:
            _mes_inicio = datetime.now().strftime("%Y-%m-01")
            try:
                _consumo_mes = pd.read_sql("""
                    SELECT material_id, SUM(gramos_usados) AS consumido
                    FROM production_log
                    WHERE fecha_fin >= :mes
                    GROUP BY material_id
                """, engine, params={"mes": _mes_inicio})
                _consumo_map = dict(zip(_consumo_mes["material_id"], _consumo_mes["consumido"]))
            except Exception:
                _consumo_map = {}
            try:
                _lineas_mat = pd.read_sql("""
                    SELECT material_id, GROUP_CONCAT(DISTINCT client_id) AS lineas
                    FROM products WHERE activo=1 GROUP BY material_id
                """, engine)
                _lineas_map = dict(zip(_lineas_mat["material_id"], _lineas_mat["lineas"]))
            except Exception:
                _lineas_map = {}
            for _, _mat in mats.iterrows():
                _mid      = _mat["material_id"]
                _stock    = _mat["stock_gr"]
                _min_g    = _mat.get("stock_minimo_gr") or 200
                _ckg      = _mat["cost_kg"]
                _valor    = _stock * _ckg / 1000
                _consumido= _consumo_map.get(_mid, 0) or 0
                _dias_est = f"{int(_stock / (_consumido / 30))}" if _consumido > 0 else "—"
                _lineas_r = _lineas_map.get(_mid, "")
                _lineas_nombres = " · ".join([LINEAS.get(l, {}).get("nombre", l) for l in (_lineas_r.split(",") if _lineas_r else [])])
                _pct      = min(_stock / max(_min_g * 5, 1) * 100, 100)
                _mc       = "#22C55E" if _stock > _min_g * 2 else ("#F59E0B" if _stock > _min_g else "#EF4444")
                _alerta   = " ⚠️" if _stock <= _min_g else ""
                with st.expander(f"🧵 {_mat['name']}{_alerta} · {_stock:.0f} g restantes"):
                    _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                    _mc1.metric("Precio/kg", f"${_ckg:,.0f}")
                    _mc2.metric("Valor en stock", f"${_valor:,.0f}")
                    _mc3.metric("Consumido este mes", f"{_consumido:.0f} g")
                    _mc4.metric("Dias de stock est.", _dias_est)
                    _bar_html = (f"<div style='background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;margin:10px 0 6px;'>"
                                 f"<div style='width:{_pct:.0f}%;background:{_mc};height:100%;border-radius:999px;'></div></div>"
                                 f"<div style='font-size:0.72rem;color:#6B7280;'>{_stock:.0f} g de ~{int(_min_g*5)} g referencia · Stock mínimo: {_min_g:.0f} g</div>")
                    if _lineas_nombres:
                        _bar_html += f"<div style='font-size:0.72rem;color:#6B7280;margin-top:4px;'>Usado en: {_lineas_nombres}</div>"
                    if _mat.get("fecha_compra"):
                        _bar_html += f"<div style='font-size:0.72rem;color:#6B7280;margin-top:2px;'>Ultima compra: {_mat['fecha_compra']}</div>"
                    st.markdown(_bar_html, unsafe_allow_html=True)
                    st.markdown("**Compra rápida**")
                    _rep_col1, _rep_col2 = st.columns([2, 1])
                    with _rep_col1:
                        _gramos_rep = st.number_input("Gramos a reponer", min_value=100, max_value=5000, step=100, value=1000, key=f"rep_{_mid}")
                    with _rep_col2:
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                        if st.button("Reponer", key=f"repbtn_{_mid}", type="primary"):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE materials SET stock_gr = stock_gr + :g, fecha_compra = :f WHERE material_id = :mid"),
                                              {"g": _gramos_rep, "f": _hoy_str, "mid": _mid})
                                _conn.commit()
                            st.success(f"+{_gramos_rep}g agregados a {_mat['name']}")
                            st.rerun()

    # ══════════════════════════════════════════════════════
    # TAB 4 — COLA DE PEDIDOS (completa)
    # ══════════════════════════════════════════════════════
    with tab_cola:
        _filtro_est = st.radio("Filtrar por estado", ["Todos","Pendiente","En Proceso","Listo","Cancelado"],
                               horizontal=True, key="cola_filtro")
        if _pedidos_all.empty:
            st.info("No hay pedidos registrados aun.")
        else:
            _df_cola = _pedidos_all if _filtro_est == "Todos" else _pedidos_all[_pedidos_all["status"] == _filtro_est]
            _df_cola = _df_cola.drop_duplicates("id")
            if _df_cola.empty:
                st.info(f"No hay pedidos con estado '{_filtro_est}'.")
            else:
                for _, _p in _df_cola.iterrows():
                    _ecfg  = _EC.get(_p["status"], _EC["Pendiente"])
                    _socio = _tenant_map.get(_p["client_id"], _p["client_id"])
                    _fecha = str(_p["date"])[:10]
                    _prod  = _p.get("product_name") or "—"
                    _pid   = _p["id"]
                    _notas_html = f"<div style='font-size:0.75rem;color:#9CA3AF;margin-top:3px;'>{_p['notas']}</div>" if _p.get("notas") else ""
                    _col_card, _col_sel = st.columns([3, 1])
                    with _col_card:
                        st.markdown(
                            f"<div style='background:white;border-radius:12px;padding:12px 18px;"
                            f"border-left:5px solid {_ecfg['color']};box-shadow:0 1px 6px rgba(0,0,0,0.06);'>"
                            f"<div style='font-weight:700;color:#1a1a2e;'>{_ecfg['emoji']} {_prod}</div>"
                            f"<div style='font-size:0.78rem;color:#6B7280;margin-top:3px;'>👤 {_socio} · 📅 {_fecha} · "
                            f"<span style='background:{_ecfg['color']}22;color:{_ecfg['color']};padding:1px 8px;"
                            f"border-radius:99px;font-weight:600;'>{_p['status']}</span></div>"
                            f"{_notas_html}</div>",
                            unsafe_allow_html=True
                        )
                    with _col_sel:
                        _nuevo_est = st.selectbox("", ["Pendiente","En Proceso","Listo","Cancelado"],
                                                  index=["Pendiente","En Proceso","Listo","Cancelado"].index(_p["status"]),
                                                  key=f"cola_est_{_pid}", label_visibility="collapsed")
                        if _nuevo_est != _p["status"]:
                            if st.button("✓", key=f"cola_btn_{_pid}", type="primary"):
                                with engine.connect() as _conn:
                                    _conn.execute(text("UPDATE orders SET status=:s WHERE id=:id"), {"s": _nuevo_est, "id": _pid})
                                    _conn.commit()
                                st.success(f"#{_pid} → {_nuevo_est}")
                                st.rerun()

elif menu == "🤝 Socios":
    st.markdown("<div class='main-header'><h1>🤝 Panel de Socios</h1><p>Ecosistema El Pasaje · Familia + B2B · Visión consolidada</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    tenants = pd.read_sql("SELECT * FROM tenants WHERE id != 'admin'", engine)
    B2B_IDS = {"oasis_animal","oasis_del_estero","pharma_delux","aviation"}
    try:
        all_orders = pd.read_sql("SELECT * FROM orders", engine)
    except:
        all_orders = pd.DataFrame()
    ids_socios = tenants["id"].tolist()
    df_socios = df[df["client_id"].isin(ids_socios)]
    total_val = df_socios["valor_stock"].sum()
    total_gan = df_socios["ganancia_stock"].sum()
    n_socios = len(tenants)
    pedidos_activos = len(all_orders[all_orders["status"].isin(["Pendiente","En Proceso"])]) if not all_orders.empty and "status" in all_orders.columns else 0
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    for col, title, val, sub, color in [(kpi1,"🤝 Socios Activos",str(n_socios),"líneas en el ecosistema","#1E3A8A"),(kpi2,"💰 Stock Consolidado",f"${total_val:,.0f}","valor precio venta","#059669"),(kpi3,"📈 Ganancia Total",f"${total_gan:,.0f}","potencial del ecosistema","#7C3AED"),(kpi4,"🏭 Pedidos Activos",str(pedidos_activos),"en producción ahora","#D97706")]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
    chart_rows = []
    for _, t in tenants.iterrows():
        cfg = get_linea(t["id"])
        prod = df[df["client_id"] == t["id"]]
        chart_rows.append({"Socio":cfg["nombre"],"Costo":prod["costo_stock"].sum(),"Ganancia":prod["ganancia_stock"].sum(),"valor_total":prod["valor_stock"].sum(),"Color":cfg["color"]})
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
        color_map = {r["Socio"]:r["Color"] for _, r in df_chart.iterrows()}
        fig_pie = px.pie(df_chart, values="valor_total", names="Socio", color="Socio", color_discrete_map=color_map, hole=0.5)
        fig_pie.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
        fig_pie.update_layout(showlegend=True, height=300, margin=dict(l=0,r=0,t=10,b=10), paper_bgcolor="white", legend=dict(font=dict(size=10)))
        st.plotly_chart(fig_pie, use_container_width=True)
    for grupo_label, grupo_df in [("👨‍👩‍👧‍👦 Familia El Pasaje", tenants[~tenants["id"].isin(B2B_IDS)]),("🤝 Socios B2B · Nando", tenants[tenants["id"].isin(B2B_IDS)])]:
        if grupo_df.empty: continue
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
                    st.markdown(f"<div style='background:white;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);margin-bottom:16px;'><div style='background:{color};padding:18px 22px 16px;display:flex;align-items:center;gap:14px;'><div style='font-size:2.4rem;line-height:1;'>{cfg['emoji']}</div><div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:white;line-height:1.1;'>{t['name']}</div><div style='font-size:0.68rem;color:rgba(255,255,255,0.72);letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>{badge_tipo}</div></div></div><div style='padding:18px 22px 20px;'><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;'><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>Stock</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#1a1a2e;'>${val:,.0f}</div></div><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>Ganancia</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#059669;'>${gan:,.0f}</div></div><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>SKUs</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#1a1a2e;'>{n_sku}</div></div></div><div style='margin-top:14px;'><div style='display:flex;justify-content:space-between;font-size:0.7rem;color:#6B7280;margin-bottom:4px;'><span>Margen promedio</span><span style='color:{m_color};font-weight:700;'>{margen_avg:.1f}%</span></div><div style='background:#F3F4F6;border-radius:999px;height:7px;overflow:hidden;'><div style='width:{min(margen_avg,100):.0f}%;background:{m_color};height:100%;border-radius:999px;'></div></div></div>{badge_ped}</div></div>", unsafe_allow_html=True)
                    if not prod.empty:
                        with st.expander(f"📦 Ver productos · {cfg['nombre']} ({n_sku} SKUs)"):
                            st.dataframe(prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={"name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen %"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen %":"{:.1f}%"}), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Sin productos cargados en esta línea.")

elif menu == "📈 Mi Panel":
    uid  = st.session_state["uid"]
    role = st.session_state["role"]
    if role == "socio_multi":
        lineas_activas = st.session_state.get("linea_filtro", get_lineas_usuario(uid))
        sel_nombre     = st.session_state.get("linea_sel", "Todas")
        if sel_nombre == "Todas":
            hdr_nombre = "Mis Líneas"
            hdr_emoji  = LINEAS.get(uid, {}).get("emoji", "✨")
            hdr_color  = LINEAS.get(uid, {}).get("color", "#6366F1")
        else:
            lid        = lineas_activas[0] if lineas_activas else uid
            _lc        = LINEAS.get(lid, {"nombre": sel_nombre, "emoji": "●", "color": "#6366F1"})
            hdr_nombre = _lc["nombre"]
            hdr_emoji  = _lc["emoji"]
            hdr_color  = _lc["color"]
    else:
        lineas_activas = [uid]
        sel_nombre     = uid
        cfg            = get_linea(uid)
        hdr_nombre, hdr_emoji, hdr_color = cfg["nombre"], cfg["emoji"], cfg["color"]
    st.markdown(f"<div class='main-header' style='background:linear-gradient(135deg,{hdr_color}cc,{hdr_color}88);'><h1>{hdr_emoji} Panel {hdr_nombre}</h1><p>Bienvenido/a, {st.session_state['user']}</p></div>", unsafe_allow_html=True)
    df   = cargar_productos()
    prod = df[df["client_id"].isin(lineas_activas)]
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("💰 Capital en Stock",    f"${prod['valor_stock'].sum():,.0f}")
    cc2.metric("📈 Ganancia Proyectada", f"${prod['ganancia_stock'].sum():,.0f}")
    cc3.metric("📦 Productos Activos",   f"{len(prod)} SKUs")
    tab_prod, tab_ped = st.tabs(["📦 Mis Productos", "🛒 Mis Pedidos"])
    # ── TAB PRODUCTOS ──
    with tab_prod:
        if role == "socio_multi" and sel_nombre == "Todas" and len(lineas_activas) > 1:
            st.markdown("<div class='section-title'>📊 Por Línea</div>", unsafe_allow_html=True)
            cols_l = st.columns(len(lineas_activas))
            for i, lid in enumerate(lineas_activas):
                lp = prod[prod["client_id"] == lid]
                lc = LINEAS.get(lid, {"nombre": lid, "emoji": "●", "color": "#6366F1"})
                with cols_l[i]:
                    st.markdown(f"<div class='metric-card' style='border-top-color:{lc['color']}'><div class='metric-title'>{lc['emoji']} {lc['nombre']}</div><div class='metric-value'>${lp['valor_stock'].sum():,.0f}</div><div class='metric-sub'>{len(lp)} productos</div></div>", unsafe_allow_html=True)
        if prod.empty:
            st.info("Aun no tenes productos cargados en tu linea.")
        else:
            if role == "socio_multi" and sel_nombre == "Todas":
                _disp = prod[["client_id","name","sku","price","stock","ganancia_unit","margen_pct"]].copy()
                _disp["client_id"] = _disp["client_id"].map(lambda x: LINEAS.get(x, {}).get("nombre", x))
                st.dataframe(_disp.rename(columns={"client_id":"Línea","name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen%"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen%":"{:.1f}%"}), use_container_width=True, hide_index=True)
            else:
                st.dataframe(prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={"name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen%"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen%":"{:.1f}%"}), use_container_width=True, hide_index=True)
    # ── TAB PEDIDOS ──
    with tab_ped:
        _STATUS_COLOR = {"Pendiente": "#F59E0B", "En Proceso": "#3B82F6", "Listo": "#10B981", "Cancelado": "#EF4444"}
        _show_badge   = role == "socio_multi" and len(lineas_activas) > 1
        with engine.connect() as _conn:
            _oframes = [
                pd.read_sql(
                    text("""SELECT o.id, o.client_id, o.status, o.date, o.fecha_entrega_est, o.notas,
                                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total
                            FROM orders o
                            LEFT JOIN order_items oi ON oi.order_id = o.id
                            WHERE o.client_id = :cid
                            GROUP BY o.id ORDER BY o.date DESC"""),
                    _conn, params={"cid": lid}
                ) for lid in lineas_activas
            ]
        pedidos = pd.concat(_oframes, ignore_index=True) if _oframes else pd.DataFrame()
        if not pedidos.empty and len(lineas_activas) > 1:
            pedidos = pedidos.sort_values("date", ascending=False)
        if pedidos.empty:
            st.info("Todavía no tenés pedidos registrados.")
        else:
            for _, row in pedidos.iterrows():
                s_color      = _STATUS_COLOR.get(row["status"], "#9CA3AF")
                lnombre      = LINEAS.get(row["client_id"], {}).get("nombre", row["client_id"])
                lcolor       = LINEAS.get(row["client_id"], {}).get("color", "#6366F1")
                fecha_str    = str(row["date"])[:10] if row["date"] else "—"
                entrega_str  = row["fecha_entrega_est"] or "—"
                notas_html   = f"<div style='font-size:0.78rem;color:#9CA3AF;margin-top:2px;'>{row['notas']}</div>" if row["notas"] else ""
                badge_html   = f"<span style='background:{lcolor}22;color:{lcolor};border:1px solid {lcolor}55;border-radius:999px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{lnombre}</span>" if _show_badge else ""
                st.markdown(
                    f"<div style='background:white;border-radius:12px;padding:14px 18px;margin-bottom:10px;"
                    f"border-left:4px solid {s_color};box-shadow:0 1px 6px rgba(0,0,0,0.06);'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                    f"<div><span style='font-weight:700;font-size:0.95rem;'>#{row['id']}</span>{badge_html}"
                    f"<span style='background:{s_color}22;color:{s_color};border:1px solid {s_color}55;"
                    f"border-radius:999px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{row['status']}</span>"
                    f"<div style='font-size:0.78rem;color:#6B7280;margin-top:5px;'>Cargado: {fecha_str} · Entrega: {entrega_str}</div>"
                    f"{notas_html}</div>"
                    f"<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;font-weight:700;color:#1a1a2e;'>${row['total']:,.0f}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

elif menu == "🛒 Cargar Pedido":
    uid  = st.session_state["uid"]
    role = st.session_state["role"]
    if role == "socio_multi":
        lineas_activas = st.session_state.get("linea_filtro", get_lineas_usuario(uid))
        cfg = LINEAS.get(uid, {"nombre": "Mis Líneas", "emoji": "✨"})
    else:
        lineas_activas = [uid]
        cfg = get_linea(uid)
    st.markdown(f"<div class='main-header'><h1>🛒 Nuevo Pedido · {cfg['nombre']}</h1><p>Solicita produccion a Fer de forma digital</p></div>", unsafe_allow_html=True)
    with engine.connect() as _conn:
        _frames = [
            pd.read_sql(
                text("SELECT name, sku, client_id FROM products WHERE client_id=:uid AND activo=1 ORDER BY name"),
                _conn, params={"uid": lid}
            ) for lid in lineas_activas
        ]
    prods_socio = pd.concat(_frames, ignore_index=True) if _frames else pd.DataFrame()
    if prods_socio.empty:
        st.info("Todavía no tenés productos cargados en tu línea. Pedile a Alejandra que los agregue.")
        st.stop()
    if role == "socio_multi" and len(lineas_activas) > 1:
        prods_socio["display"] = prods_socio.apply(
            lambda r: f"[{LINEAS.get(r['client_id'],{}).get('nombre', r['client_id'])}] {r['name']}", axis=1
        )
    else:
        prods_socio["display"] = prods_socio["name"]
    producto_display = st.selectbox("Producto", prods_socio["display"].tolist())
    cantidad = st.number_input("Cantidad", min_value=1, max_value=100, value=1)
    notas    = st.text_area("Notas para Fer (color, urgencia, etc.)", height=80)
    if st.button("Confirmar Pedido", type="primary"):
        sel_row     = prods_socio[prods_socio["display"] == producto_display].iloc[0]
        linea_pedido = sel_row["client_id"]
        with engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO orders (client_id, status, date, notas, color_pedido) VALUES (:cid, 'Pendiente', :fecha, :notas, '')"),
                {"cid": linea_pedido, "fecha": datetime.now().isoformat(), "notas": notas.strip()}
            )
            order_id  = result.lastrowid
            prod_data = pd.read_sql(
                text("SELECT sku, price FROM products WHERE name=:nombre AND client_id=:cid"),
                conn, params={"nombre": sel_row["name"], "cid": linea_pedido}
            )
            conn.execute(
                text("INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) VALUES (:oid, :sku, :qty, :precio)"),
                {"oid": order_id, "sku": prod_data["sku"].iloc[0], "qty": cantidad, "precio": float(prod_data["price"].iloc[0])}
            )
            conn.commit()
        st.success(f"✅ Pedido registrado: {cantidad}x {sel_row['name']}")
        st.balloons()


elif menu == "👥 Clientes":
    st.markdown("<div class='main-header'><h1>👥 Gestión de Clientes</h1><p>Segmentación · Potencial · Canal de entrada · Señales de mercado</p></div>", unsafe_allow_html=True)

    # ── CARGAR DATOS ──
    try:
        clientes = pd.read_sql("""
            SELECT id, name, email, telefono, tipo, sector,
                   segmento, lead_source, potencial, canal_preferido,
                   ciudad, rubro, notas_agente, es_cliente_real,
                   fecha_primer_contacto, linea_interes, activo
            FROM tenants
            WHERE tipo IN ('cliente_externo', 'b2b', 'socio', 'familia', 'admin')
            ORDER BY fecha_primer_contacto DESC
        """, engine)
    except Exception as e:
        clientes = pd.DataFrame()
        st.warning(f"Error cargando clientes: {e}")

    # ── KPIs ──
    total = len(clientes)
    reales = len(clientes[clientes["es_cliente_real"] == 1]) if not clientes.empty and "es_cliente_real" in clientes.columns else 0
    alto_potencial = len(clientes[clientes["potencial"] == "Alto"]) if not clientes.empty and "potencial" in clientes.columns else 0
    b2b = len(clientes[clientes["segmento"] == "B2B"]) if not clientes.empty and "segmento" in clientes.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    for col, title, val, sub, color in [
        (k1, "👥 Total Contactos",    str(total),         "en el ecosistema",       "#1E3A8A"),
        (k2, "💰 Clientes Reales",    str(reales),        "con compra registrada",  "#059669"),
        (k3, "⭐ Alto Potencial",     str(alto_potencial),"para próximo contacto",  "#7C3AED"),
        (k4, "🤝 Canal B2B",          str(b2b),           "empresas y socios",      "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3 = st.tabs(["📋 Ver Clientes", "➕ Nuevo Cliente", "📡 Señales de Mercado"])

    # ── TAB 1: VER CLIENTES ──
    with tab1:
        if clientes.empty:
            st.info("No hay clientes cargados todavía.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_seg = st.selectbox("Segmento", ["Todos"] + sorted(clientes["segmento"].dropna().unique().tolist()) if "segmento" in clientes.columns else ["Todos"])
            with col_f2:
                filtro_pot = st.selectbox("Potencial", ["Todos", "Alto", "Medio", "Bajo"])
            with col_f3:
                filtro_real = st.selectbox("Estado", ["Todos", "Clientes reales", "Contactos"])

            df_filtrado = clientes.copy()
            if filtro_seg != "Todos" and "segmento" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["segmento"] == filtro_seg]
            if filtro_pot != "Todos" and "potencial" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["potencial"] == filtro_pot]
            if filtro_real == "Clientes reales" and "es_cliente_real" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["es_cliente_real"] == 1]
            elif filtro_real == "Contactos" and "es_cliente_real" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["es_cliente_real"] == 0]

            st.markdown(f"<div style='font-size:0.8rem;color:#6B7280;margin-bottom:12px;'>{len(df_filtrado)} resultado/s</div>", unsafe_allow_html=True)

            for _, row in df_filtrado.iterrows():
                pot_color = {"Alto": "#059669", "Medio": "#D97706", "Bajo": "#EF4444"}.get(row.get("potencial",""), "#6B7280")
                real_badge = "✅ Cliente real" if row.get("es_cliente_real") == 1 else "📞 Contacto"
                real_color = "#059669" if row.get("es_cliente_real") == 1 else "#6B7280"
                with st.expander(f"{row['name']}  ·  {row.get('segmento','')}  ·  {row.get('linea_interes','')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Email:** {row.get('email','—')}")
                        st.markdown(f"**Teléfono:** {row.get('telefono','—')}")
                        st.markdown(f"**Ciudad:** {row.get('ciudad','—')}")
                    with c2:
                        st.markdown(f"**Rubro:** {row.get('rubro','—')}")
                        st.markdown(f"**Canal preferido:** {row.get('canal_preferido','—')}")
                        st.markdown(f"**Fuente:** {row.get('lead_source','—')}")
                    with c3:
                        st.markdown(f"<span style='color:{pot_color};font-weight:700;'>⭐ Potencial: {row.get('potencial','—')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:{real_color};'>🏷️ {real_badge}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Primer contacto:** {row.get('fecha_primer_contacto','—')}")
                    if row.get("notas_agente"):
                        st.markdown(f"<div style='background:#F0F4FF;border-left:3px solid #1E3A8A;padding:10px 14px;border-radius:8px;font-size:0.85rem;margin-top:8px;'>🤖 <b>Nota del agente:</b> {row['notas_agente']}</div>", unsafe_allow_html=True)

    # ── TAB 2: NUEVO CLIENTE ──
    with tab2:
        st.markdown("<div class='section-title'>➕ Cargar nuevo contacto o cliente</div>", unsafe_allow_html=True)
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nc_nombre    = st.text_input("Nombre o Razón Social *")
                nc_email     = st.text_input("Email")
                nc_telefono  = st.text_input("Teléfono / WhatsApp")
                nc_ciudad    = st.text_input("Ciudad", value="Buenos Aires")
                nc_rubro     = st.text_input("Rubro / Sector")
            with c2:
                nc_segmento  = st.selectbox("Segmento *", ["B2C", "B2B", "Corporativo", "Institucional"])
                nc_potencial = st.selectbox("Potencial *", ["Alto", "Medio", "Bajo"])
                nc_canal     = st.selectbox("Canal preferido", ["WhatsApp", "Instagram", "Presencial", "Email", "Recomendación"])
                nc_fuente    = st.text_input("¿Cómo llegó?", placeholder="Ej: Red de Nando, Laura Cava, Feria")
                nc_linea     = st.text_input("Línea de interés", placeholder="Ej: Magnitud 19, Oasis Animal")
            nc_es_real   = st.checkbox("¿Ya realizó una compra?")
            nc_notas     = st.text_area("Notas (para el agente IA)", placeholder="Describí brevemente quién es y qué le interesa")
            submitted = st.form_submit_button("💾 GUARDAR CLIENTE", use_container_width=True, type="primary")

            if submitted:
                if not nc_nombre:
                    st.error("El nombre es obligatorio.")
                else:
                    import uuid, re
                    nc_id = re.sub(r"[^a-z0-9_]", "_", nc_nombre.lower().strip())[:30] + "_" + str(uuid.uuid4())[:6]
                    nc_email_val = nc_email.strip().lower() or f"{nc_id}@noemail.com"
                    hoy_str = datetime.now().strftime("%Y-%m-%d")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO tenants
                                (id, name, email, password, telefono, tipo, sector,
                                 fecha_alta, activo, segmento, lead_source, potencial,
                                 canal_preferido, ciudad, rubro, notas_agente,
                                 es_cliente_real, fecha_primer_contacto, linea_interes)
                                VALUES
                                (:id,:name,:email,:pwd,:tel,:tipo,:sector,
                                 :fecha,:activo,:seg,:source,:pot,
                                 :canal,:ciudad,:rubro,:notas,
                                 :real,:fcontacto,:linea)
                            """), {
                                "id": nc_id, "name": nc_nombre, "email": nc_email_val,
                                "pwd": "pendiente", "tel": nc_telefono, "tipo": nc_segmento.lower(),
                                "sector": nc_rubro, "fecha": hoy_str, "activo": 1,
                                "seg": nc_segmento, "source": nc_fuente, "pot": nc_potencial,
                                "canal": nc_canal, "ciudad": nc_ciudad, "rubro": nc_rubro,
                                "notas": nc_notas, "real": 1 if nc_es_real else 0,
                                "fcontacto": hoy_str, "linea": nc_linea
                            })
                            conn.commit()
                        st.success(f"✅ {nc_nombre} guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── TAB 3: SEÑALES DE MERCADO ──
    with tab3:
        st.markdown("<div class='section-title'>📡 Señales de Mercado</div>", unsafe_allow_html=True)
        st.caption("Registrá acá cualquier comentario, reacción o idea que surja de una conversación con un cliente. El agente IA las va a analizar.")

        with st.form("form_senal", clear_on_submit=True):
            s1, s2 = st.columns(2)
            with s1:
                s_cliente = st.text_input("Cliente / Persona", placeholder="Ej: Laura, Aldana, contacto de Nando")
                s_linea   = st.text_input("Línea relacionada", placeholder="Ej: Magnitud 19, Coquette")
                s_producto= st.text_input("Producto (si aplica)")
            with s2:
                s_reaccion= st.selectbox("Reacción", ["Le encantó", "Preguntó el precio", "Dudó", "Pidió muestra", "No le interesó", "Quiere hablar con alguien"])
                s_canal   = st.selectbox("Canal", ["WhatsApp", "Presencial", "Instagram", "Email", "Otro"])
                s_fuente  = st.text_input("¿Quién lo reporta?", value=st.session_state.get("user",""))
            s_oportunidad = st.text_input("Oportunidad detectada", placeholder="Ej: Le gustan los regalos corporativos para fin de año")
            s_notas   = st.text_area("Notas libres", placeholder="Todo lo que querés que el agente sepa")
            s_submit  = st.form_submit_button("📡 REGISTRAR SEÑAL", use_container_width=True, type="primary")

            if s_submit:
                hoy_str = datetime.now().strftime("%Y-%m-%d")
                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO senales_mercado
                            (fecha, cliente_id, linea, producto, reaccion,
                             oportunidad, fuente, canal, notas, procesado_por_ia)
                            VALUES
                            (:fecha,:cliente,:linea,:producto,:reaccion,
                             :oportunidad,:fuente,:canal,:notas,0)
                        """), {
                            "fecha": hoy_str, "cliente": s_cliente, "linea": s_linea,
                            "producto": s_producto, "reaccion": s_reaccion,
                            "oportunidad": s_oportunidad, "fuente": s_fuente,
                            "canal": s_canal, "notas": s_notas
                        })
                        conn.commit()
                    st.success("✅ Señal registrada. El agente la va a procesar.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        try:
            senales = pd.read_sql("SELECT * FROM senales_mercado ORDER BY fecha DESC LIMIT 20", engine)
            if not senales.empty:
                st.markdown(f"<div style='font-size:0.8rem;color:#6B7280;margin-bottom:10px;'>Últimas {len(senales)} señales registradas</div>", unsafe_allow_html=True)
                st.dataframe(
                    senales[["fecha","cliente_id","linea","reaccion","oportunidad","fuente"]].rename(columns={
                        "fecha":"Fecha","cliente_id":"Cliente","linea":"Línea",
                        "reaccion":"Reacción","oportunidad":"Oportunidad","fuente":"Reportado por"
                    }),
                    use_container_width=True, hide_index=True
                )
        except:
            st.info("No hay señales registradas todavía.")

elif menu == "🌱 Impacto Social":
    st.markdown("<div class='main-header'><h1>🌱 Impacto Social</h1><p>Transparencia total · Fondos solidarios</p></div>", unsafe_allow_html=True)
    FONDOS = {"refugio_oasis":{"nombre":"Refugio Oasis Animal","emoji":"🐾","color":"#F472B6","meta":50000},"mentes_brillantes":{"nombre":"Mentes Brillantes","emoji":"🧠","color":"#818CF8","meta":40000},"fondo_general":{"nombre":"Fondo General","emoji":"❤️","color":"#FB7185","meta":30000}}
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
            st.markdown(f"<div style='background:white;border-radius:18px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,0.08);border-top:5px solid {f['color']};margin-bottom:16px;'><div style='font-size:2rem;'>{f['emoji']}</div><div style='font-size:1rem;font-weight:700;color:#1a1a2e;margin:8px 0 2px;'>{f['nombre']}</div><div style='font-size:2rem;font-weight:700;color:{f['color']};font-family:Cormorant Garamond,serif;'>${recaudado:,.0f}</div><div style='font-size:0.78rem;color:#9CA3AF;margin-bottom:12px;'>Meta mensual: ${f['meta']:,.0f}</div><div style='background:#F3F4F6;border-radius:999px;height:14px;overflow:hidden;'><div style='width:{pct:.0f}%;background:{f['color']};height:100%;border-radius:999px;'></div></div><div style='font-size:0.75rem;color:#6B7280;margin-top:6px;'>{'🎉 ¡Meta alcanzada!' if faltan == 0 else f'Faltan ${faltan:,.0f}'}</div></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### ➕ Registrar Donacion Manual")
    dc1, dc2, dc3, dc4 = st.columns([1.5, 1, 1, 1.5])
    with dc1:
        fondo_sel = st.selectbox("Fondo destino", list(FONDOS.keys()), format_func=lambda x: f"{FONDOS[x]['emoji']} {FONDOS[x]['nombre']}")
    with dc2:
        tipo_don = st.selectbox("Tipo", ["urna","qr","redondeo"], format_func=lambda x: {"urna":"🏺 Urna","qr":"📱 QR","redondeo":"🔄 Redondeo"}[x])
    with dc3:
        monto_don = st.number_input("Monto ($)", min_value=1.0, step=50.0, value=500.0)
    with dc4:
        desc_don = st.text_input("Descripcion", placeholder="Ej: Urna fin de semana")
    if st.button("💚 REGISTRAR DONACION", type="primary"):
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO donations (fondo, monto, tipo, descripcion, fecha) VALUES (:fondo, :monto, :tipo, :desc, :fecha)"),
                {"fondo": fondo_sel, "monto": monto_don, "tipo": tipo_don, "desc": desc_don, "fecha": str(datetime.now().date())}
            )
            conn.commit()
        st.success(f"✅ ${monto_don:,.0f} registrados en {FONDOS[fondo_sel]['nombre']} 💚")
        st.rerun()
    st.markdown("### 📋 Historial de Donaciones")
    if dons.empty:
        st.info("Aun no hay donaciones. ¡La primera puede ser hoy! 💚")
    else:
        TIPO_ICON = {"urna":"🏺","qr":"📱","redondeo":"🔄","producto":"🌱"}
        for _, row in dons.head(20).iterrows():
            icon = TIPO_ICON.get(row["tipo"], "💰")
            finfo = FONDOS.get(row["fondo"], {"nombre":row["fondo"],"emoji":"❓","color":"#ccc"})
            st.markdown(f"<div style='background:white;border-radius:12px;padding:14px 18px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid {finfo['color']};'><div style='display:flex;justify-content:space-between;align-items:center;'><div><b>{icon} {finfo['emoji']} {finfo['nombre']}</b><span style='margin-left:10px;font-size:0.75rem;color:#6B7280;'>{row['tipo'].upper()} · {row['fecha']}</span><div style='font-size:0.78rem;color:#9CA3AF;margin-top:3px;'>{row.get('descripcion','') or ''}</div></div><div style='font-size:1.4rem;font-weight:700;color:{finfo['color']};'>${row['monto']:,.0f}</div></div></div>", unsafe_allow_html=True)


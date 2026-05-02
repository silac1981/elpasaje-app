import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import hashlib
from slicer_parser import parsear_archivo_slicer, match_material_idx
from ep_agente import get_alertas_dashboard as _get_alertas_raw

@st.cache_data(ttl=120)
def get_alertas_dashboard():
    try:
        return _get_alertas_raw()
    except Exception:
        return []

def _preguntar_mike(pregunta: str, contexto_extra: str = "") -> str:
    try:
        from anthropic import Anthropic
        from context_elpasaje import SYSTEM_PROMPT, get_data_context
        _c = Anthropic()
        _sys = SYSTEM_PROMPT + "\n\n" + get_data_context()
        if contexto_extra:
            _sys += f"\n\nCONTEXTO DEL FORMULARIO ACTUAL:\n{contexto_extra}"
        hist = st.session_state.get("mike_history", [])
        hist.append({"role": "user", "content": pregunta})
        r = _c.messages.create(model="claude-sonnet-4-6", max_tokens=800, system=_sys, messages=hist)
        resp = r.content[0].text
        hist.append({"role": "assistant", "content": resp})
        st.session_state["mike_history"] = hist[-20:]
        return resp
    except Exception as e:
        return f"No pude conectarme con Mike ahora mismo ({e})"

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
_BASE_PAGES = "https://silac1981.github.io/elpasaje-app"
PAGINAS_SOCIOS = {
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
    # ── Alertas Mike (admin + produccion) ────────────────────────
    if st.session_state["role"] in ("admin", "produccion"):
        _alertas = get_alertas_dashboard()
        if _alertas:
            _n_crit = sum(1 for a in _alertas if a["nivel"] == "critico")
            _n_atc  = sum(1 for a in _alertas if a["nivel"] == "atencion")
            _resumen = f"{'🔴 ' + str(_n_crit) + ' crítica' + ('s' if _n_crit != 1 else '') + '  ' if _n_crit else ''}{'🟡 ' + str(_n_atc) if _n_atc else ''}".strip()
            st.markdown(f"<div style='margin-top:18px;padding:8px 12px;background:#1e293b;border-radius:10px;border-left:3px solid {'#EF4444' if _n_crit else '#F59E0B'};'><div style='font-size:0.72rem;font-weight:700;color:{'#EF4444' if _n_crit else '#F59E0B'};'>🤖 MIKE · ALERTAS</div><div style='font-size:0.68rem;color:#CBD5E1;margin-top:3px;'>{_resumen}</div></div>", unsafe_allow_html=True)
            for _a in _alertas[:4]:
                _col = "#EF4444" if _a["nivel"] == "critico" else ("#F59E0B" if _a["nivel"] == "atencion" else "#94A3B8")
                st.markdown(f"<div style='margin-top:6px;padding:6px 10px;background:#0f172a;border-radius:8px;border-left:2px solid {_col};'><div style='font-size:0.67rem;color:{_col};font-weight:600;'>{_a['titulo']}</div><div style='font-size:0.63rem;color:#94A3B8;margin-top:2px;'>{_a['accion']}</div></div>", unsafe_allow_html=True)
            if len(_alertas) > 4:
                st.markdown(f"<div style='font-size:0.62rem;color:#64748B;text-align:center;margin-top:4px;'>+{len(_alertas)-4} más · ver tab Mike</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top:18px;padding:8px 12px;background:#1e293b;border-radius:10px;border-left:3px solid #22C55E;'><div style='font-size:0.72rem;font-weight:700;color:#22C55E;'>🤖 MIKE · SIN ALERTAS</div><div style='font-size:0.68rem;color:#CBD5E1;margin-top:3px;'>Todo en orden ✅</div></div>", unsafe_allow_html=True)
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
        _df_lead = pd.read_sql("""
            SELECT lead_source AS canal, COUNT(*) AS clientes
            FROM tenants WHERE lead_source IS NOT NULL AND lead_source != '' AND es_cliente_real = 1
            GROUP BY lead_source ORDER BY clientes DESC
        """, engine)
    except Exception:
        _df_senales = pd.DataFrame()
        _df_canal_tot = pd.DataFrame()
        _df_lead = pd.DataFrame()

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

    # ── Top clientes por facturación ───────────────────────────
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
    st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#0D1117!important}
.stTabs [data-baseweb="tab-list"]{background:#161B22!important;border-radius:12px!important;padding:4px!important;gap:2px!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#F0F6FC!important}
[data-testid="stMetricValue"]{color:#E6EDF3!important}
[data-testid="stMetricLabel"]{color:#8B949E!important}
details{background:#161B22!important;border-radius:12px!important;border:1px solid #21262D!important}
details summary{color:#E6EDF3!important;padding:8px 12px!important}
[data-testid="stChatMessage"]{background:#161B22!important;border-radius:12px!important;margin-bottom:8px!important}
[data-testid="stChatMessageContent"] p{color:#E6EDF3!important}
.stRadio label{color:#8B949E!important}
[data-testid="stFileUploaderDropzone"]{background:#161B22!important;border-color:#30363D!important}
/* ── Overrides del tema global light que chocan con el fondo oscuro ── */
.stMarkdown p,.stMarkdown span{color:#C9D1D9!important}
.stMarkdown strong,.stMarkdown b{color:#F0F6FC!important}
.stNumberInput label,.stTextInput label,.stSelectbox label,.stTextArea label,.stFileUploader label,.stCheckbox label{color:#8B949E!important;font-weight:500!important}
.stExpander summary p{color:#E6EDF3!important;font-weight:600!important}
.stExpander details{background:#161B22!important}
.stCaption p,.stCaption span{color:#6B7280!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div,[data-testid="stAlert"] span{color:#C9D1D9!important}
[data-testid="stAlert"]{background:#1a2332!important;border-color:#30363D!important}
.stDataFrame,[data-testid="stDataFrame"]{background:#161B22!important}
</style>""", unsafe_allow_html=True)
    st.markdown(f"<div style='background:#161B22;border-radius:16px;padding:22px 28px;border:1px solid #21262D;border-left:4px solid #3FB950;margin-bottom:8px;'><div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;color:#3FB950;text-transform:uppercase;'>EL PASAJE 3D STUDIO · PRODUCCION</div><div style='font-size:1.7rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>🖨️ Centro de Fabricacion</div><div style='font-size:0.78rem;color:#8B949E;margin-top:6px;'>Fernando · {datetime.now().strftime('%A %d/%m/%Y')} · {datetime.now().strftime('%H:%M')}</div></div>", unsafe_allow_html=True)
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
    tab_panel, tab_fab, tab_mats, tab_cola, tab_mike, tab_stats = st.tabs(["🛠️ Mi Panel", "📦 Cargar Fabricacion", "🧵 Materiales", "📋 Cola de Pedidos", "🤖 Mike", "💹 Finanzas CFO"])

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
            (k1, "⏳ Pendientes",  str(_n_pendientes), "en espera",       "#F59E0B"),
            (k2, "🆕 Hoy",        str(_nuevos_hoy),   "pedidos del dia", "#3B82F6"),
            (k3, "✅ Fabricadas",  str(_fab_total),    "en el log",       "#22C55E"),
            (k4, "⚠️ Criticos",   str(_criticos),     "bajo minimo",     "#EF4444"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;border:1px solid #21262D;border-top:3px solid {_color};text-align:center;margin-bottom:8px;'><div style='font-size:2.2rem;font-weight:800;color:{_color};line-height:1;'>{_val}</div><div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_title}</div><div style='font-size:0.64rem;color:#6B7280;margin-top:4px;letter-spacing:0.5px;'>{_sub}</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:24px;margin-bottom:12px;font-size:0.68rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>📋 COLA ACTIVA</div>", unsafe_allow_html=True)
        if _pedidos_activos.empty:
            try:
                _mat_mas_usado = pd.read_sql("""
                    SELECT m.name FROM production_log pl
                    JOIN materials m ON m.material_id = pl.material_id
                    GROUP BY pl.material_id ORDER BY SUM(pl.gramos_usados) DESC LIMIT 1
                """, engine)
                _ultima_fab_row = pd.read_sql("SELECT fecha_fin FROM production_log ORDER BY id DESC LIMIT 1", engine)
            except Exception:
                _mat_mas_usado = pd.DataFrame()
                _ultima_fab_row = pd.DataFrame()
            _mat_nom = _mat_mas_usado.iloc[0]["name"] if not _mat_mas_usado.empty else "—"
            _ult_f   = str(_ultima_fab_row.iloc[0]["fecha_fin"])[:10] if not _ultima_fab_row.empty else "—"
            st.markdown("<div style='background:#0D2818;border-radius:16px;padding:20px 24px;border:1px solid #238636;border-left:4px solid #3FB950;margin-bottom:16px;'><div style='font-size:1.05rem;font-weight:700;color:#3FB950;'>Sin pedidos activos — el taller está al día ✅</div><div style='font-size:0.82rem;color:#8B949E;margin-top:6px;'>Podés registrar fabricaciones libres desde la pestaña 📦 Cargar Fabricacion</div></div>", unsafe_allow_html=True)
            _es1, _es2, _es3 = st.columns(3)
            _es1.metric("Piezas fabricadas", _fab_total)
            _es2.metric("Material más usado", _mat_nom)
            _es3.metric("Última fabricación", _ult_f)
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
        # ── Importar desde slicer ──────────────────────────────
        _slicer_up = st.file_uploader(
            "📎 Importar desde slicer (.gcode / .3mf)",
            type=["gcode", "3mf"],
            help="Bambu Studio, PrusaSlicer o Cura — pre-llena gramos, tiempo y material automáticamente",
            key="slicer_upload"
        )
        if _slicer_up is not None:
            _sp = parsear_archivo_slicer(_slicer_up)
            if _sp:
                _mat_nombres_all = mats["name"].tolist() if not mats.empty else []
                if _sp.get("gramos"):
                    st.session_state["fab_grams"] = float(_sp["gramos"])
                if _sp.get("tiempo_min"):
                    st.session_state["fab_tiempo"] = int(_sp["tiempo_min"])
                if _sp.get("material_tipo") and _mat_nombres_all:
                    _mi = match_material_idx(_sp["material_tipo"], _mat_nombres_all)
                    st.session_state["fab_mat"] = _mat_nombres_all[_mi]
                _info_parts = []
                if _sp.get("gramos"):     _info_parts.append(f"**{_sp['gramos']} g**")
                if _sp.get("tiempo_min"): _info_parts.append(f"**{_sp['tiempo_min']} min**")
                if _sp.get("material_tipo"): _info_parts.append(f"**{_sp['material_tipo']}**")
                if _sp.get("color"):      _info_parts.append(f"color {_sp['color']}")
                st.success(f"✅ Slicer cargado — {' · '.join(_info_parts)}")
            else:
                st.warning("No se pudieron leer los datos del archivo. Completá el formulario manualmente.")
        st.markdown("---")
        _ops_pedido = {"Sin pedido": None}
        if not _pedidos_activos.empty:
            for _, _r in _pedidos_activos.drop_duplicates("id").iterrows():
                _lbl = f"#{_r['id']} · {_r.get('product_name','—')} · {_tenant_map.get(_r['client_id'], _r['client_id'])}"
                _ops_pedido[_lbl] = _r["id"]
        _sel_label = st.selectbox("Pedido asociado (opcional)", list(_ops_pedido.keys()), key="fab_pedido")
        _sel_oid   = _ops_pedido[_sel_label]
        if _sel_oid is not None:
            _pedido_row   = _pedidos_activos[_pedidos_activos["id"] == _sel_oid].iloc[0]
            _sku_auto     = _pedido_row.get("product_sku") or ""
            _mid_auto     = _pedido_row.get("material_id") or ""
            _weight_def   = max(float(_pedido_row.get("weight_gr") or 50), 1.0)
        else:
            _sku_auto, _mid_auto, _weight_def = "", "", 50.0
        _fc1, _fc2 = st.columns(2)
        with _fc1:
            _fab_sku   = st.text_input("SKU del producto", value=_sku_auto, key="fab_sku")
            _fab_grams = st.number_input("Gramos consumidos", min_value=1.0, max_value=2000.0, value=_weight_def, step=5.0, key="fab_grams")
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
                """), {"oid": _sel_oid, "sku": _fab_sku or "LIBRE", "mid": _fab_mid,
                       "grams": _fab_grams, "tiempo": _fab_tiempo,
                       "fi": _hoy_str, "ff": _hoy_str,
                       "res": _fab_res + (f" — {_fab_desc}" if _fab_desc else "")})
                _conn.execute(text("UPDATE materials SET stock_gr = stock_gr - :g WHERE material_id = :mid"),
                              {"g": _fab_grams, "mid": _fab_mid})
                if _fab_res == "ok" and _sel_oid is not None:
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
                    st.markdown("**Registrar compra**")
                    _rep_col1, _rep_col2 = st.columns(2)
                    with _rep_col1:
                        _gramos_rep = st.number_input("Gramos comprados", min_value=100, max_value=10000, step=100, value=1000, key=f"rep_{_mid}")
                    with _rep_col2:
                        _precio_rep = st.number_input("Precio pagado ($)", min_value=0.0, step=100.0, value=0.0, key=f"precio_{_mid}")
                    if st.button("Registrar compra", key=f"repbtn_{_mid}", type="primary"):
                        _total_gr = _stock + _gramos_rep
                        if _precio_rep > 0 and _total_gr > 0:
                            _nuevo_ck = round((_stock * (_ckg or 0) + _precio_rep * 1000) / _total_gr, 2)
                        else:
                            _nuevo_ck = _ckg or 0
                        with engine.connect() as _conn:
                            _conn.execute(text("UPDATE materials SET stock_gr = stock_gr + :g, fecha_compra = :f, cost_kg = :ck WHERE material_id = :mid"),
                                          {"g": _gramos_rep, "f": _hoy_str, "ck": _nuevo_ck, "mid": _mid})
                            _conn.commit()
                        _ck_msg = f" · Costo/kg → ${_nuevo_ck:,.0f}" if _precio_rep > 0 else ""
                        st.success(f"+{_gramos_rep}g registrados en {_mat['name']}{_ck_msg}")
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

    # ══════════════════════════════════════════════════════
    # TAB 5 — MIKE (alertas + chat contextual)
    # ══════════════════════════════════════════════════════
    with tab_mike:
        # ── Identity header ──────────────────────────────────
        _alertas_mike = get_alertas_dashboard()
        _n_crit = sum(1 for a in _alertas_mike if a["nivel"] == "critico")
        _n_atc  = sum(1 for a in _alertas_mike if a["nivel"] == "atencion")
        _est_color = "#EF4444" if _n_crit > 0 else ("#F59E0B" if _n_atc > 0 else "#3FB950")
        _est_txt   = f"{_n_crit} crítica{'s' if _n_crit!=1 else ''}" if _n_crit > 0 else ("Todo en orden" if not _n_atc else f"{_n_atc} atención")
        st.markdown(f"""
<div style='background:#161B22;border-radius:16px;padding:20px 24px;border:1px solid #21262D;margin-bottom:4px;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ASISTENTE DE PRODUCCION</div>
  <div style='font-size:1.5rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>🤖 Mike</div>
  <div style='margin-top:10px;'>
    <span style='background:{_est_color}22;color:{_est_color};padding:4px 12px;border-radius:99px;font-weight:700;font-size:0.78rem;border:1px solid {_est_color}44;'>● {_est_txt}</span>
    <span style='color:#6B7280;margin-left:12px;font-size:0.72rem;'>{len(_alertas_mike)} alertas · actualizado ahora</span>
  </div>
</div>""", unsafe_allow_html=True)

        # ── KPIs del taller ───────────────────────────────────
        try:
            _fab_wk = pd.read_sql("SELECT COUNT(*) AS t, SUM(CASE WHEN resultado NOT LIKE 'ok%' THEN 1 ELSE 0 END) AS f FROM production_log WHERE fecha_fin >= date('now','-7 days')", engine).iloc[0]
            _fab_semana, _fallos_semana = int(_fab_wk["t"] or 0), int(_fab_wk["f"] or 0)
        except Exception:
            _fab_semana = _fallos_semana = 0
        _tasa_txt = f"{_fallos_semana/_fab_semana*100:.0f}%" if _fab_semana > 0 else "—"
        _mat_crit_n = len(mats[mats["stock_gr"] <= mats["stock_minimo_gr"]]) if not mats.empty else 0
        _mk1, _mk2, _mk3, _mk4 = st.columns(4)
        for _col, _v, _l, _c in [
            (_mk1, str(len(_pedidos_activos)), "Pedidos activos",  "#3B82F6"),
            (_mk2, str(_fab_semana),           "Fab. esta semana", "#22C55E"),
            (_mk3, _tasa_txt,                  "Tasa de fallos",   "#EF4444" if _fab_semana > 0 and _fallos_semana/_fab_semana >= 0.25 else "#4B5563"),
            (_mk4, str(_mat_crit_n),           "Mat. críticos",   "#F59E0B" if _mat_crit_n > 0 else "#4B5563"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:16px;border:1px solid #21262D;border-top:3px solid {_c};text-align:center;margin-bottom:4px;'><div style='font-size:1.8rem;font-weight:800;color:{_c};line-height:1;'>{_v}</div><div style='font-size:0.64rem;color:#8B949E;margin-top:6px;text-transform:uppercase;letter-spacing:1px;'>{_l}</div></div>", unsafe_allow_html=True)

        # ── Alertas ───────────────────────────────────────────
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ALERTAS ACTIVAS</div>", unsafe_allow_html=True)
        if not _alertas_mike:
            st.markdown("<div style='background:#0D2818;border-radius:12px;padding:14px 20px;border:1px solid #238636;'><span style='color:#3FB950;font-weight:700;font-size:0.88rem;'>✅ Sin alertas</span><span style='color:#8B949E;margin-left:12px;font-size:0.8rem;'>El taller está en orden — buen trabajo.</span></div>", unsafe_allow_html=True)
        else:
            _cm = {"critico":"#EF4444","atencion":"#F59E0B","info":"#58A6FF"}
            _bm = {"critico":"#2D1117","atencion":"#2D2007","info":"#0D1B2E"}
            _dm = {"critico":"#451B1B","atencion":"#3D2B0A","info":"#1B2D4A"}
            for _i, _a in enumerate(_alertas_mike):
                _c  = _cm.get(_a["nivel"], "#8B949E")
                _bg = _bm.get(_a["nivel"], "#161B22")
                _bd = _dm.get(_a["nivel"], "#21262D")
                st.markdown(f"<div style='background:{_bg};border-radius:12px;padding:14px 18px;border:1px solid {_bd};border-left:4px solid {_c};margin-bottom:8px;'><div style='font-size:0.88rem;font-weight:700;color:{_c};'>{_a['titulo']}</div><div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>{_a['detalle']}</div><div style='font-size:0.7rem;color:#6B7280;margin-top:3px;'>→ {_a['accion']}</div></div>", unsafe_allow_html=True)
                if st.button(f"Preguntarle a Mike →", key=f"ask_a_{_i}", help=_a["titulo"]):
                    st.session_state["mike_auto_q"] = f"Tengo esta alerta activa: {_a['titulo']} — {_a['detalle']}. Acción sugerida: {_a['accion']}. ¿Qué me recomendás hacer exactamente y cómo lo soluciono?"

        # ── Preguntas rápidas ─────────────────────────────────
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>PREGUNTAS RÁPIDAS</div>", unsafe_allow_html=True)
        _qs = [
            ("📋 Prioridades de hoy",   "¿Qué pedidos tengo que priorizar hoy y en qué orden los fabrico?"),
            ("🧵 Días de stock",         "¿Cuántos días de stock me queda en cada material al ritmo de consumo actual?"),
            ("🔴 Analizar fallos",       "Tuve fallos de fabricación esta semana. ¿Cuáles son las causas más probables y cómo los prevengo?"),
            ("💰 Mejor margen",          "¿Qué piezas debería fabricar primero para maximizar el margen del taller hoy?"),
            ("🛒 Qué comprar",           "¿Qué materiales necesito comprar esta semana y en qué cantidad para no quedarme sin stock?"),
            ("📊 Estado del taller",     "Haceme un diagnóstico rápido del estado general del taller ahora mismo."),
        ]
        _qc1, _qc2, _qc3 = st.columns(3)
        for _qi, (_ql, _qt) in enumerate(_qs):
            with [_qc1, _qc2, _qc3][_qi % 3]:
                if st.button(_ql, key=f"qs_{_qi}", use_container_width=True):
                    st.session_state["mike_auto_q"] = _qt

        # ── Chat ──────────────────────────────────────────────
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>CHAT CON MIKE</div>", unsafe_allow_html=True)
        if "mike_history" not in st.session_state:
            st.session_state["mike_history"] = []
        for _msg in st.session_state["mike_history"]:
            with st.chat_message("user" if _msg["role"] == "user" else "assistant", avatar="👤" if _msg["role"] == "user" else "🤖"):
                st.markdown(_msg["content"])
        _mike_q    = st.chat_input("Escribile a Mike...", key="mike_chat_input")
        _mike_auto = st.session_state.pop("mike_auto_q", None)
        _pregunta  = _mike_q or _mike_auto
        if _pregunta:
            _mat_stock_str = ", ".join(f"{r['name']} {r['stock_gr']:.0f}g" for _, r in mats.iterrows()) if not mats.empty else "sin datos"
            _ctx = (
                f"Pedidos activos: {len(_pedidos_activos)}\n"
                f"Alertas: {len(_alertas_mike)} ({_n_crit} críticas, {_n_atc} atención)\n"
                f"Fabricaciones esta semana: {_fab_semana} ({_fallos_semana} fallos)\n"
                f"Materiales críticos: {_mat_crit_n}\n"
                f"Stock materiales: {_mat_stock_str}"
            )
            with st.chat_message("user", avatar="👤"):
                st.markdown(_pregunta)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Mike está pensando..."):
                    _resp = _preguntar_mike(_pregunta, contexto_extra=_ctx)
                st.markdown(_resp)
        if st.session_state["mike_history"]:
            if st.button("Limpiar chat", key="mike_clear"):
                st.session_state["mike_history"] = []
                st.rerun()

    # ══════════════════════════════════════════════════════
    # TAB 6 — FINANZAS CFO
    # ══════════════════════════════════════════════════════
    with tab_stats:
        st.markdown("<div style='margin-bottom:8px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>RESUMEN FINANCIERO · TALLER</div>", unsafe_allow_html=True)

        # ── Cargar datos financieros ──────────────────────────
        try:
            _df_ingresos = pd.read_sql("""
                SELECT strftime('%Y-%m', o.date) AS mes,
                       SUM(oi.precio_unitario * oi.cantidad) AS facturado,
                       COUNT(DISTINCT o.id) AS pedidos
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                WHERE o.status = 'Listo'
                GROUP BY mes ORDER BY mes DESC LIMIT 12
            """, engine)
        except Exception:
            _df_ingresos = pd.DataFrame(columns=["mes","facturado","pedidos"])

        try:
            _df_costo_mat = pd.read_sql("""
                SELECT strftime('%Y-%m', pl.fecha_fin) AS mes,
                       SUM(pl.gramos_usados * m.cost_kg / 1000.0) AS costo_mat,
                       SUM(pl.gramos_usados) AS gramos_total
                FROM production_log pl
                JOIN materials m ON m.material_id = pl.material_id
                WHERE pl.fecha_fin IS NOT NULL
                GROUP BY mes ORDER BY mes DESC LIMIT 12
            """, engine)
        except Exception:
            _df_costo_mat = pd.DataFrame(columns=["mes","costo_mat","gramos_total"])

        try:
            _overhead_total = pd.read_sql("SELECT SUM(monto_mensual) AS total FROM overhead WHERE activo=1", engine).iloc[0]["total"] or 0
            _df_overhead = pd.read_sql("SELECT concepto, monto_mensual, categoria FROM overhead WHERE activo=1 ORDER BY monto_mensual DESC", engine)
        except Exception:
            _overhead_total = 0
            _df_overhead = pd.DataFrame()

        try:
            _df_margen_prod = pd.read_sql("""
                SELECT p.sku, p.name, t.name AS socio, p.price,
                       p.weight_gr, m.cost_kg,
                       p.price - (p.weight_gr * m.cost_kg / 1000.0) AS margen_bruto,
                       CASE WHEN p.price > 0 THEN
                            ((p.price - (p.weight_gr * m.cost_kg / 1000.0)) / p.price * 100)
                       ELSE 0 END AS pct_margen
                FROM products p
                JOIN tenants t ON t.id = p.client_id
                LEFT JOIN materials m ON m.material_id = p.material_id
                WHERE p.activo = 1 AND p.price > 0
                ORDER BY margen_bruto DESC
            """, engine)
        except Exception:
            _df_margen_prod = pd.DataFrame()

        try:
            _df_por_socio = pd.read_sql("""
                SELECT t.name AS socio, o.client_id,
                       COUNT(DISTINCT o.id) AS n_pedidos,
                       SUM(oi.precio_unitario * oi.cantidad) AS facturado
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                JOIN tenants t ON t.id = o.client_id
                WHERE o.status = 'Listo'
                GROUP BY o.client_id ORDER BY facturado DESC
            """, engine)
        except Exception:
            _df_por_socio = pd.DataFrame()

        try:
            _df_stock_inv = pd.read_sql("""
                SELECT name, tipo, stock_gr, cost_kg,
                       ROUND(stock_gr * cost_kg / 1000.0, 0) AS valor_stock
                FROM materials WHERE activo=1 ORDER BY valor_stock DESC
            """, engine)
        except Exception:
            _df_stock_inv = pd.DataFrame()

        _fac_total   = float(_df_ingresos["facturado"].sum()) if not _df_ingresos.empty else 0
        _cost_mat_total = float(_df_costo_mat["costo_mat"].sum()) if not _df_costo_mat.empty else 0
        _margen_bruto = _fac_total - _cost_mat_total - _overhead_total
        _n_ped_listo = int(_df_ingresos["pedidos"].sum()) if not _df_ingresos.empty else 0

        # ── KPIs financieros ──────────────────────────────────
        _fk1, _fk2, _fk3, _fk4 = st.columns(4)
        for _fc, _fv, _fl, _fs, _fcolor in [
            (_fk1, f"${_fac_total:,.0f}",    "💰 Facturación Total",    f"{_n_ped_listo} pedidos completados", "#3FB950"),
            (_fk2, f"${_cost_mat_total:,.0f}","🧵 Costo Materiales",     "consumo registrado en log",          "#F59E0B"),
            (_fk3, f"${_overhead_total:,.0f}","⚙️ Overhead Mensual",     "costos fijos del taller",            "#58A6FF"),
            (_fk4, f"${_margen_bruto:,.0f}",  "📈 Margen Bruto Est.",   "facturado − mat − overhead",         "#EF4444" if _margen_bruto < 0 else "#22C55E"),
        ]:
            with _fc:
                st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;border:1px solid #21262D;border-top:3px solid {_fcolor};text-align:center;margin-bottom:8px;'><div style='font-size:1.65rem;font-weight:800;color:{_fcolor};line-height:1;'>{_fv}</div><div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_fl}</div><div style='font-size:0.64rem;color:#6B7280;margin-top:4px;'>{_fs}</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:28px;margin-bottom:12px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>📅 DETALLE MENSUAL</div>", unsafe_allow_html=True)

        # ── Tabla mensual ─────────────────────────────────────
        if not _df_ingresos.empty or not _df_costo_mat.empty:
            _meses_all = sorted(set(
                list(_df_ingresos["mes"].tolist() if not _df_ingresos.empty else []) +
                list(_df_costo_mat["mes"].tolist() if not _df_costo_mat.empty else [])
            ), reverse=True)[:6]
            _rows_mes = []
            for _m in _meses_all:
                _fac = float(_df_ingresos[_df_ingresos["mes"]==_m]["facturado"].sum()) if not _df_ingresos.empty else 0
                _ped = int(_df_ingresos[_df_ingresos["mes"]==_m]["pedidos"].sum()) if not _df_ingresos.empty else 0
                _cm  = float(_df_costo_mat[_df_costo_mat["mes"]==_m]["costo_mat"].sum()) if not _df_costo_mat.empty else 0
                _gr  = float(_df_costo_mat[_df_costo_mat["mes"]==_m]["gramos_total"].sum()) if not _df_costo_mat.empty else 0
                _mg  = _fac - _cm - _overhead_total
                _rows_mes.append({
                    "Mes": _m,
                    "Pedidos": _ped,
                    "Facturado $": f"${_fac:,.0f}",
                    "Costo Mat $": f"${_cm:,.0f}",
                    "Overhead $": f"${_overhead_total:,.0f}",
                    "Margen $": f"${_mg:,.0f}",
                    "Gramos usados": f"{_gr:,.0f} g",
                })
            _df_mes_show = pd.DataFrame(_rows_mes)
            st.dataframe(_df_mes_show, use_container_width=True, hide_index=True)
        else:
            st.info("Sin registros de ventas completadas todavía.")

        # ── Por socio + por producto ──────────────────────────
        _col_soc, _col_prod = st.columns(2)

        with _col_soc:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🤝 FACTURACIÓN POR SOCIO</div>", unsafe_allow_html=True)
            if not _df_por_socio.empty:
                _fac_max = float(_df_por_socio["facturado"].max()) if _df_por_socio["facturado"].max() > 0 else 1
                for _, _sr in _df_por_socio.iterrows():
                    _pct = min(100, float(_sr["facturado"]) / _fac_max * 100)
                    st.markdown(f"""<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:6px;border:1px solid #21262D;'>
<div style='font-size:0.82rem;font-weight:700;color:#E6EDF3;margin-bottom:6px;'>{_sr['socio']} <span style='color:#6B7280;font-weight:400;font-size:0.72rem;'>· {int(_sr['n_pedidos'])} pedidos</span></div>
<div style='background:#21262D;border-radius:4px;height:6px;margin-bottom:4px;'><div style='background:#3FB950;height:6px;border-radius:4px;width:{_pct:.0f}%;'></div></div>
<div style='font-size:0.88rem;font-weight:700;color:#3FB950;'>${float(_sr['facturado']):,.0f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin ventas completadas registradas.")

        with _col_prod:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🏆 TOP PRODUCTOS POR MARGEN</div>", unsafe_allow_html=True)
            if not _df_margen_prod.empty:
                _top10 = _df_margen_prod.head(10)
                _mg_max = float(_top10["margen_bruto"].max()) if _top10["margen_bruto"].max() > 0 else 1
                for _, _pr in _top10.iterrows():
                    _pct = max(0, min(100, float(_pr["margen_bruto"]) / _mg_max * 100))
                    _mc = "#22C55E" if float(_pr["pct_margen"]) >= 50 else ("#F59E0B" if float(_pr["pct_margen"]) >= 25 else "#EF4444")
                    st.markdown(f"""<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:6px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:700;color:#E6EDF3;'>{_pr['name']} <span style='color:#6B7280;font-size:0.68rem;'>{_pr['sku']}</span></div>
<div style='font-size:0.68rem;color:#8B949E;margin-bottom:5px;'>{_pr['socio']} · ${float(_pr['price']):,.0f} PVP</div>
<div style='background:#21262D;border-radius:4px;height:5px;margin-bottom:4px;'><div style='background:{_mc};height:5px;border-radius:4px;width:{_pct:.0f}%;'></div></div>
<div style='font-size:0.8rem;font-weight:700;color:{_mc};'>Margen ${float(_pr['margen_bruto']):,.0f} <span style='font-size:0.7rem;font-weight:400;'>({float(_pr['pct_margen']):.0f}%)</span></div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin datos de productos con material asignado.")

        # ── Stock materiales + Overhead ───────────────────────
        _col_mat2, _col_oh = st.columns(2)

        with _col_mat2:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🧵 CAPITAL EN STOCK DE MATERIALES</div>", unsafe_allow_html=True)
            if not _df_stock_inv.empty:
                _inv_total = float(_df_stock_inv["valor_stock"].sum())
                st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:10px;border:1px solid #21262D;border-left:3px solid #F59E0B;'><span style='color:#F59E0B;font-weight:700;font-size:0.9rem;'>Total invertido en stock: ${_inv_total:,.0f}</span></div>", unsafe_allow_html=True)
                for _, _mr in _df_stock_inv.iterrows():
                    _pct_s = min(100, float(_mr["valor_stock"]) / max(1, _inv_total) * 100)
                    st.markdown(f"""<div style='background:#161B22;border-radius:8px;padding:10px 14px;margin-bottom:5px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:600;color:#C9D1D9;'>{_mr['name']}</div>
<div style='font-size:0.65rem;color:#6B7280;margin-bottom:4px;'>{_mr['stock_gr']:,.0f} g · ${float(_mr['cost_kg']):,.0f}/kg</div>
<div style='background:#21262D;border-radius:3px;height:4px;margin-bottom:3px;'><div style='background:#F59E0B;height:4px;border-radius:3px;width:{_pct_s:.0f}%;'></div></div>
<div style='font-size:0.75rem;color:#F59E0B;font-weight:700;'>${float(_mr['valor_stock']):,.0f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin materiales activos.")

        with _col_oh:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>⚙️ OVERHEAD MENSUAL FIJO</div>", unsafe_allow_html=True)
            if not _df_overhead.empty:
                st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:10px;border:1px solid #21262D;border-left:3px solid #58A6FF;'><span style='color:#58A6FF;font-weight:700;font-size:0.9rem;'>Total mensual: ${_overhead_total:,.0f}</span></div>", unsafe_allow_html=True)
                for _, _ohr in _df_overhead.iterrows():
                    _pct_oh = min(100, float(_ohr["monto_mensual"]) / max(1, _overhead_total) * 100)
                    _cat_color = {"Servicios":"#F59E0B","Maquinaria":"#EF4444","Infraestructura":"#58A6FF","Produccion":"#22C55E"}.get(_ohr.get("categoria",""), "#8B949E")
                    st.markdown(f"""<div style='background:#161B22;border-radius:8px;padding:10px 14px;margin-bottom:5px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:600;color:#C9D1D9;'>{_ohr['concepto']}</div>
<div style='font-size:0.65rem;color:{_cat_color};margin-bottom:4px;'>{_ohr.get('categoria','')}</div>
<div style='background:#21262D;border-radius:3px;height:4px;margin-bottom:3px;'><div style='background:{_cat_color};height:4px;border-radius:3px;width:{_pct_oh:.0f}%;'></div></div>
<div style='font-size:0.75rem;color:#58A6FF;font-weight:700;'>${float(_ohr['monto_mensual']):,.0f}/mes</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin overhead configurado.")

        # ── Links a páginas de socios ─────────────────────────
        st.markdown("<div style='margin-top:32px;margin-bottom:12px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🌐 PÁGINAS WEB DE SOCIOS</div>", unsafe_allow_html=True)
        _BASE_URL = "https://silac1981.github.io/elpasaje-app"
        _paginas = [
            ("Oasis Animal",      "oasis-animal",  "#22C55E", "🐾"),
            ("Oasis del Estero",  "oasis-estero",  "#10B981", "🌿"),
            ("Core Tech",         "core-tech",     "#3B82F6", "⚙️"),
            ("Coquette",          "coquette",      "#EC4899", "🎀"),
            ("Sport",             "sport",         "#F59E0B", "🏃"),
            ("Pharma DeLux",      "pharma-delux",  "#8B5CF6", "💊"),
            ("Aero Tech",         "aero-tech",     "#06B6D4", "✈️"),
            ("Melómano",          "melomano",      "#EF4444", "🎵"),
            ("Luminis",           "luminis",       "#FBBF24", "💡"),
            ("Vuelo Certero",     "vuelo-certero", "#14B8A6", "🎯"),
            ("Magnitud 19",       "magnitud19",    "#6366F1", "🏭"),
            ("El Pasaje",         "index",         "#F0F6FC", "🏠"),
        ]
        _pcols = st.columns(4)
        for _pi, (_pname, _pslug, _pcolor, _picon) in enumerate(_paginas):
            _purl = f"{_BASE_URL}/{_pslug}.html"
            with _pcols[_pi % 4]:
                st.markdown(f"""<a href="{_purl}" target="_blank" style='text-decoration:none;'>
<div style='background:#161B22;border-radius:12px;padding:16px 14px;border:1px solid #21262D;border-left:3px solid {_pcolor};margin-bottom:8px;transition:all 0.2s;cursor:pointer;'>
  <div style='font-size:1.3rem;line-height:1;'>{_picon}</div>
  <div style='font-size:0.8rem;font-weight:700;color:#E6EDF3;margin-top:6px;'>{_pname}</div>
  <div style='font-size:0.62rem;color:#6B7280;margin-top:2px;'>/{_pslug}.html</div>
</div></a>""", unsafe_allow_html=True)

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
    # ── Tema oscuro para el panel de socios ──────────────────
    st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#0D1117!important}
.stTabs [data-baseweb="tab-list"]{background:#161B22!important;border-radius:12px!important;padding:4px!important;gap:2px!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#F0F6FC!important}
[data-testid="stMetricValue"]{color:#E6EDF3!important}
[data-testid="stMetricLabel"]{color:#8B949E!important}
[data-testid="stMetricDelta"]{font-size:0.8rem!important}
.stDataFrame,[data-testid="stDataFrame"]{background:#161B22!important}
.stSelectbox [data-baseweb="select"]{background:#161B22!important;border-color:#30363D!important}
[data-testid="stChatMessage"]{background:#161B22!important;border-radius:12px!important}
[data-testid="stChatMessageContent"] p{color:#E6EDF3!important}
[data-testid="stFileUploaderDropzone"]{background:#161B22!important;border-color:#30363D!important}
.stMarkdown p,.stMarkdown span{color:#C9D1D9!important}
.stMarkdown strong,.stMarkdown b{color:#F0F6FC!important}
.stSelectbox label,.stTextInput label,.stTextArea label{color:#8B949E!important;font-weight:500!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:#C9D1D9!important}
[data-testid="stAlert"]{background:#1a2332!important;border-color:#30363D!important}
/* Charts */
[data-testid="stVegaLiteChart"] canvas,[data-testid="stArrowVegaLiteChart"]{background:#161B22!important}
</style>""", unsafe_allow_html=True)
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
        cfg            = get_linea(uid)
        hdr_nombre, hdr_emoji, hdr_color = cfg["nombre"], cfg["emoji"], cfg["color"]

    _SC = {"Pendiente":"#F59E0B","En Proceso":"#3B82F6","Listo":"#10B981","Cancelado":"#EF4444"}
    _hoy_s = datetime.now().strftime("%Y-%m-%d")
    _mes_s = datetime.now().strftime("%Y-%m")

    # ── Header con branding de línea ──────────────────────────
    st.markdown(f"""
<div style='background:linear-gradient(135deg,{hdr_color}dd,{hdr_color}88);
     border-radius:20px;padding:24px 32px;margin-bottom:4px;
     border:1px solid {hdr_color}44;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;
       text-transform:uppercase;color:rgba(255,255,255,0.7);'>EL PASAJE 3D STUDIO · SOCIO</div>
  <div style='font-size:2rem;font-weight:800;color:white;margin-top:8px;'>{hdr_emoji} {hdr_nombre}</div>
  <div style='font-size:0.8rem;color:rgba(255,255,255,0.75);margin-top:4px;'>
    Bienvenido/a, {st.session_state['user']} · {datetime.now().strftime('%A %d/%m/%Y')}
  </div>
</div>""", unsafe_allow_html=True)

    # ── Cargar datos del socio ─────────────────────────────────
    df_all = cargar_productos()
    prod   = df_all[df_all["client_id"].isin(lineas_activas)].copy()

    _lid_str = "','".join(lineas_activas)
    try:
        _pedidos_s = pd.read_sql(f"""
            SELECT o.id, o.client_id, o.status, o.date, o.fecha_entrega_est, o.notas,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.client_id IN ('{_lid_str}')
            GROUP BY o.id ORDER BY o.date DESC
        """, engine)
    except Exception:
        _pedidos_s = pd.DataFrame()

    try:
        _hist_mes = pd.read_sql(f"""
            SELECT strftime('%Y-%m', o.date) AS mes,
                   COUNT(DISTINCT o.id) AS pedidos,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.client_id IN ('{_lid_str}') AND o.status='Listo'
            GROUP BY mes ORDER BY mes
        """, engine)
    except Exception:
        _hist_mes = pd.DataFrame()

    try:
        _fab_socio = pd.read_sql(f"""
            SELECT pl.product_sku, pl.gramos_usados, pl.resultado, pl.fecha_fin,
                   p.name AS producto
            FROM production_log pl
            JOIN orders o ON o.id = pl.order_id
            JOIN products p ON p.sku = pl.product_sku
            WHERE o.client_id IN ('{_lid_str}')
            ORDER BY pl.fecha_fin DESC
        """, engine)
    except Exception:
        _fab_socio = pd.DataFrame()

    try:
        _prec_hist = pd.read_sql(f"""
            SELECT ph.product_sku, p.name AS producto,
                   ph.precio_anterior, ph.precio_nuevo, ph.fecha, ph.motivo
            FROM price_history ph
            JOIN products p ON p.sku = ph.product_sku
            WHERE p.client_id IN ('{_lid_str}')
            ORDER BY ph.fecha DESC LIMIT 20
        """, engine)
    except Exception:
        _prec_hist = pd.DataFrame()

    # ── KPIs ──────────────────────────────────────────────────
    _cap_stock  = prod["valor_stock"].sum()
    _gan_stock  = prod["ganancia_stock"].sum()
    _n_skus     = len(prod[prod["activo"]==1]) if "activo" in prod.columns else len(prod)
    _n_activos  = len(_pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])]) if not _pedidos_s.empty else 0
    _n_listo    = len(_pedidos_s[_pedidos_s["status"]=="Listo"]) if not _pedidos_s.empty else 0
    _fac_total  = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum()) if not _pedidos_s.empty else 0
    _margen_avg = prod["margen_pct"].mean() if not prod.empty else 0
    _mg_color   = "#10B981" if _margen_avg>=50 else ("#F59E0B" if _margen_avg>=25 else "#EF4444")

    # ── Banner link a página web ──────────────────────────────
    _page_slug_s = PAGINAS_SOCIOS.get(uid if role != "socio_multi" else lineas_activas[0] if len(lineas_activas)==1 else uid)
    if _page_slug_s:
        _page_url_s = f"{_BASE_PAGES}/{_page_slug_s}.html"
        st.markdown(f"""<a href="{_page_url_s}" target="_blank" style="text-decoration:none;">
<div style="background:linear-gradient(90deg,#161B22,{hdr_color}22);border-radius:12px;
     padding:12px 20px;border:1px solid {hdr_color}44;margin-bottom:12px;
     display:flex;align-items:center;gap:12px;">
  <span style="font-size:1.2rem;">🌐</span>
  <div>
    <div style="font-size:0.72rem;font-weight:700;color:{hdr_color};letter-spacing:1px;">TU PÁGINA WEB</div>
    <div style="font-size:0.78rem;color:#8B949E;margin-top:1px;">{_page_url_s}</div>
  </div>
  <div style="margin-left:auto;background:{hdr_color}22;color:{hdr_color};padding:6px 16px;
       border-radius:99px;font-size:0.7rem;font-weight:700;border:1px solid {hdr_color}44;">
    Abrir →
  </div>
</div></a>""", unsafe_allow_html=True)

    _sk1,_sk2,_sk3,_sk4,_sk5 = st.columns(5)
    for _sc,_sv,_sl,_ss,_scolor in [
        (_sk1, f"${_cap_stock:,.0f}",  "💰 Stock",           "valor precio venta",        hdr_color),
        (_sk2, f"${_gan_stock:,.0f}",  "📈 Ganancia Stock",  "margen del inventario",     "#10B981"),
        (_sk3, f"${_fac_total:,.0f}",  "✅ Facturado Total", f"{_n_listo} pedidos listos","#3B82F6"),
        (_sk4, str(_n_activos),        "🏭 En Producción",   "pedidos activos hoy",       "#F59E0B"),
        (_sk5, f"{_margen_avg:.1f}%",  "📊 Margen Prom.",    "promedio de tu catálogo",   _mg_color),
    ]:
        with _sc:
            st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:18px 14px;border:1px solid #21262D;border-top:3px solid {_scolor};text-align:center;margin-bottom:8px;'><div style='font-size:1.5rem;font-weight:800;color:{_scolor};line-height:1;'>{_sv}</div><div style='font-size:0.72rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_sl}</div><div style='font-size:0.62rem;color:#8B949E;margin-top:3px;'>{_ss}</div></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    _t_res, _t_stats, _t_prod, _t_ped, _t_mike = st.tabs([
        "🏠 Resumen", "📊 Estadísticas", "📦 Productos", "🛒 Pedidos", "🤖 Mike"
    ])

    # ══ TAB RESUMEN ══════════════════════════════════════════
    with _t_res:
        _ra, _rb = st.columns([1.4, 1])
        with _ra:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>PEDIDOS ACTIVOS</div>", unsafe_allow_html=True)
            _pact = _pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])] if not _pedidos_s.empty else pd.DataFrame()
            if _pact.empty:
                st.markdown("<div style='background:#0D2818;border-radius:12px;padding:16px 20px;border:1px solid #238636;border-left:4px solid #3FB950;'><span style='color:#3FB950;font-weight:700;'>✅ Sin pedidos en curso</span><br><span style='color:#8B949E;font-size:0.8rem;'>Podés cargar un nuevo pedido desde el menú 🛒</span></div>", unsafe_allow_html=True)
            else:
                for _, _pr in _pact.iterrows():
                    _sc2 = _SC.get(_pr["status"],"#9CA3AF")
                    _fecha2 = str(_pr["date"])[:10] if _pr["date"] else "—"
                    _entrega2 = str(_pr.get("fecha_entrega_est","—") or "—")
                    st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:14px 18px;margin-bottom:8px;border-left:4px solid {_sc2};border:1px solid #21262D;'><div style='font-weight:700;font-size:0.95rem;color:#E6EDF3;'>Pedido #{int(_pr['id'])} <span style='background:{_sc2}22;color:{_sc2};border:1px solid {_sc2}44;border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:600;margin-left:6px;'>{_pr['status']}</span></div><div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>Cargado: {_fecha2} · Entrega: {_entrega2}</div><div style='font-size:0.88rem;font-weight:700;color:{_sc2};margin-top:6px;'>${float(_pr['total']):,.0f}</div></div>", unsafe_allow_html=True)

        with _rb:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>ESTADO DE TU CATÁLOGO</div>", unsafe_allow_html=True)
            if not prod.empty:
                _top3 = prod.sort_values("margen_pct", ascending=False).head(3)
                for _, _p3 in _top3.iterrows():
                    _mc3 = "#10B981" if _p3["margen_pct"]>=50 else ("#F59E0B" if _p3["margen_pct"]>=25 else "#EF4444")
                    st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;margin-bottom:6px;border:1px solid #21262D;'><div style='font-size:0.8rem;font-weight:600;color:#E6EDF3;'>{_p3['name']}</div><div style='background:#21262D;border-radius:3px;height:5px;margin:5px 0;'><div style='background:{_mc3};height:5px;border-radius:3px;width:{min(100,_p3['margen_pct']):.0f}%;'></div></div><div style='font-size:0.72rem;color:{_mc3};font-weight:700;'>{_p3['margen_pct']:.1f}% margen · ${_p3['price']:,.0f}</div></div>", unsafe_allow_html=True)
                _stock_bajo = prod[prod["stock"] <= 2] if "stock" in prod.columns else pd.DataFrame()
                if not _stock_bajo.empty:
                    st.markdown(f"<div style='background:#2D2007;border-radius:10px;padding:10px 14px;border-left:3px solid #F59E0B;margin-top:6px;border:1px solid #3D2B0A;'><span style='color:#F59E0B;font-weight:700;font-size:0.8rem;'>⚠️ Stock bajo: {', '.join(_stock_bajo['name'].tolist()[:3])}</span></div>", unsafe_allow_html=True)

        # Últimas fabricaciones
        if not _fab_socio.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:10px;'>ÚLTIMAS FABRICACIONES</div>", unsafe_allow_html=True)
            _fab_show = _fab_socio.head(5).copy()
            _fab_show["resultado"] = _fab_show["resultado"].fillna("ok")
            _fab_show["fecha_fin"] = _fab_show["fecha_fin"].astype(str).str[:10]
            _fab_show["gramos_usados"] = _fab_show["gramos_usados"].apply(lambda x: f"{x:.0f} g" if pd.notna(x) else "—")
            st.dataframe(
                _fab_show[["fecha_fin","producto","gramos_usados","resultado"]].rename(
                    columns={"fecha_fin":"Fecha","producto":"Producto","gramos_usados":"Gramos","resultado":"Resultado"}
                ), use_container_width=True, hide_index=True
            )

    # ══ TAB ESTADÍSTICAS ═════════════════════════════════════
    with _t_stats:
        _sa, _sb = st.columns(2)
        with _sa:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:8px;'>FACTURACIÓN MENSUAL (pedidos listos)</div>", unsafe_allow_html=True)
            if not _hist_mes.empty and len(_hist_mes) > 0:
                _chart_df = _hist_mes.set_index("mes")[["facturado"]].rename(columns={"facturado":"Facturado $"})
                st.bar_chart(_chart_df, color=hdr_color, height=220)
                # Delta mes actual vs anterior
                _meses_ord = _hist_mes.sort_values("mes")
                if len(_meses_ord) >= 2:
                    _fac_act = float(_meses_ord.iloc[-1]["facturado"])
                    _fac_ant = float(_meses_ord.iloc[-2]["facturado"])
                    _delta   = _fac_act - _fac_ant
                    _delta_s = f"+${_delta:,.0f}" if _delta >= 0 else f"-${abs(_delta):,.0f}"
                    st.metric("Este mes vs mes anterior", f"${_fac_act:,.0f}", _delta_s)
            else:
                st.info("Aún no hay pedidos completados para graficar.")

        with _sb:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:8px;'>MARGEN POR PRODUCTO</div>", unsafe_allow_html=True)
            if not prod.empty:
                _mg_chart = prod.sort_values("margen_pct",ascending=False)[["name","margen_pct"]].head(12).copy()
                _mg_chart["name"] = _mg_chart["name"].str[:22]
                st.bar_chart(_mg_chart.set_index("name")[["margen_pct"]].rename(columns={"margen_pct":"Margen %"}), color="#3FB950", height=220)
            else:
                st.info("Sin productos para analizar.")

        # Estado de pedidos (distribución)
        st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:10px;'>DISTRIBUCIÓN DE PEDIDOS</div>", unsafe_allow_html=True)
        if not _pedidos_s.empty:
            _dist_cols = st.columns(4)
            for _dci, _dst in enumerate(["Pendiente","En Proceso","Listo","Cancelado"]):
                _dn = len(_pedidos_s[_pedidos_s["status"]==_dst])
                _dc = _SC[_dst]
                with _dist_cols[_dci]:
                    st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:16px;border:1px solid #21262D;border-top:3px solid {_dc};text-align:center;'><div style='font-size:1.8rem;font-weight:800;color:{_dc};'>{_dn}</div><div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>{_dst}</div></div>", unsafe_allow_html=True)

        # Historial de precios
        if not _prec_hist.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#6B7280;margin-top:24px;margin-bottom:8px;'>HISTORIAL DE PRECIOS</div>", unsafe_allow_html=True)
            _ph_show = _prec_hist.copy()
            _ph_show["fecha"] = _ph_show["fecha"].astype(str).str[:10]
            _ph_show["precio_anterior"] = _ph_show["precio_anterior"].apply(lambda x: f"${x:,.0f}")
            _ph_show["precio_nuevo"]    = _ph_show["precio_nuevo"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(
                _ph_show[["fecha","producto","precio_anterior","precio_nuevo","motivo"]].rename(
                    columns={"fecha":"Fecha","producto":"Producto","precio_anterior":"Precio Anterior",
                             "precio_nuevo":"Precio Nuevo","motivo":"Motivo"}
                ), use_container_width=True, hide_index=True
            )

        # Top productos por volumen de fabricación
        if not _fab_socio.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:8px;'>PRODUCTOS MÁS FABRICADOS</div>", unsafe_allow_html=True)
            _vol_prod = _fab_socio.groupby("producto").agg(
                fabricaciones=("resultado","count"),
                gramos_total=("gramos_usados","sum")
            ).sort_values("fabricaciones",ascending=False).head(8).reset_index()
            st.dataframe(
                _vol_prod.rename(columns={"producto":"Producto","fabricaciones":"Fabricaciones","gramos_total":"Gramos totales"})
                .style.format({"Gramos totales":"{:.0f} g"}),
                use_container_width=True, hide_index=True
            )

    # ══ TAB PRODUCTOS ════════════════════════════════════════
    with _t_prod:
        def _render_cards_linea(df_p, _col_default):
            _df_act = df_p[df_p["activo"]==1] if "activo" in df_p.columns else df_p
            if _df_act.empty:
                st.info("Sin productos activos en esta línea.")
                return
            _pcols2 = st.columns(3)
            for _pii, (_, _prow) in enumerate(_df_act.sort_values("margen_pct", ascending=False).iterrows()):
                _pmc = "#10B981" if _prow["margen_pct"]>=50 else ("#F59E0B" if _prow["margen_pct"]>=25 else "#EF4444")
                _plincolor = LINEAS.get(_prow["client_id"],{}).get("color", _col_default)
                _pstock_c  = "#10B981" if (_prow.get("stock",0) or 0) > 5 else ("#F59E0B" if (_prow.get("stock",0) or 0) > 0 else "#EF4444")
                _costo_u   = _prow.get("costo_unit", 0) or 0
                _peso_g    = int(_prow.get("weight_gr", 0) or 0)
                with _pcols2[_pii % 3]:
                    st.markdown(f"""<div style='background:#161B22;border-radius:14px;padding:16px;border:1px solid #21262D;margin-bottom:10px;border-top:3px solid {_plincolor};'>
<div style='font-size:0.62rem;color:{_plincolor};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>{_prow.get('sku','')} · {_peso_g}g</div>
<div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;margin-top:4px;line-height:1.2;'>{_prow['name']}</div>
<div style='font-size:0.68rem;color:#8B949E;margin-top:2px;'>{_prow.get('categoria','') or ''}</div>
<div style='margin-top:10px;background:#21262D;border-radius:3px;height:5px;'><div style='background:{_pmc};height:5px;border-radius:3px;width:{min(100,max(0,_prow['margen_pct'])):.0f}%;'></div></div>
<div style='margin-top:8px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;'>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>COSTO EP</div><div style='font-size:0.76rem;font-weight:700;color:#F59E0B;'>${_costo_u:,.0f}</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>PRECIO</div><div style='font-size:0.76rem;font-weight:700;color:#E6EDF3;'>${_prow['price']:,.0f}</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>MARGEN</div><div style='font-size:0.76rem;font-weight:700;color:{_pmc};'>{_prow['margen_pct']:.1f}%</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>STOCK</div><div style='font-size:0.76rem;font-weight:700;color:{_pstock_c};'>{int(_prow.get("stock",0) or 0)} u</div></div>
</div>
</div>""", unsafe_allow_html=True)

        if role == "socio_multi" and len(lineas_activas) > 1:
            _ltab_names = [
                f"{LINEAS.get(l,{}).get('emoji','●')} {LINEAS.get(l,{}).get('nombre',l)}"
                for l in lineas_activas
            ]
            _ltabs = st.tabs(_ltab_names)
            for _ltab, _lid3 in zip(_ltabs, lineas_activas):
                _lp3 = prod[prod["client_id"]==_lid3]
                _lc3 = LINEAS.get(_lid3, {"nombre":_lid3,"emoji":"●","color":"#6366F1"})
                with _ltab:
                    _ls1, _ls2, _ls3 = st.columns(3)
                    _n_act3 = len(_lp3[_lp3["activo"]==1]) if "activo" in _lp3.columns else len(_lp3)
                    _mg3    = _lp3["margen_pct"].mean() if not _lp3.empty else 0
                    with _ls1:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>PRODUCTOS</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>{_n_act3}</div></div>", unsafe_allow_html=True)
                    with _ls2:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>VALOR STOCK</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>${_lp3['valor_stock'].sum():,.0f}</div></div>", unsafe_allow_html=True)
                    with _ls3:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>MARGEN PROM.</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>{_mg3:.1f}%</div></div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    _render_cards_linea(_lp3, _lc3["color"])
        else:
            if prod.empty:
                st.info("Aún no tenés productos cargados en tu línea.")
            else:
                _render_cards_linea(prod, hdr_color)

    # ══ TAB PEDIDOS ══════════════════════════════════════════
    with _t_ped:
        _show_badge = role == "socio_multi" and len(lineas_activas) > 1
        if _pedidos_s.empty:
            st.info("Todavía no tenés pedidos registrados.")
        else:
            # Filtro rápido
            _pf_est = st.selectbox("Filtrar por estado", ["Todos","Pendiente","En Proceso","Listo","Cancelado"], key="ped_filtro_socio")
            _pf_df  = _pedidos_s if _pf_est=="Todos" else _pedidos_s[_pedidos_s["status"]==_pf_est]
            if _pf_df.empty:
                st.info(f"Sin pedidos en estado {_pf_est}.")
            for _, _pr2 in _pf_df.iterrows():
                _sc3    = _SC.get(_pr2["status"],"#9CA3AF")
                _lnom2  = LINEAS.get(_pr2["client_id"],{}).get("nombre","")
                _lcol2  = LINEAS.get(_pr2["client_id"],{}).get("color",hdr_color)
                _fec2   = str(_pr2["date"])[:10] if _pr2["date"] else "—"
                _ent2   = str(_pr2.get("fecha_entrega_est","—") or "—")
                _not2   = f"<div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'><em>{_pr2['notas']}</em></div>" if _pr2.get("notas") else ""
                _badge2 = f"<span style='background:{_lcol2}22;color:{_lcol2};border:1px solid {_lcol2}44;border-radius:99px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{_lnom2}</span>" if _show_badge else ""
                st.markdown(
                    f"<div style='background:#161B22;border-radius:14px;padding:16px 20px;margin-bottom:10px;"
                    f"border-left:4px solid {_sc3};border:1px solid #21262D;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div><span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>#{int(_pr2['id'])}</span>"
                    f"<span style='background:{_sc3}22;color:{_sc3};border:1px solid {_sc3}44;"
                    f"border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:700;margin-left:8px;'>{_pr2['status']}</span>"
                    f"{_badge2}"
                    f"<div style='font-size:0.72rem;color:#8B949E;margin-top:5px;'>📅 {_fec2} → entrega {_ent2}</div>"
                    f"{_not2}</div>"
                    f"<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;font-weight:700;color:#E6EDF3;'>${float(_pr2['total']):,.0f}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
            # Resumen total
            _tot_fac = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum())
            st.markdown(f"<div style='background:#0D1B2E;border-radius:10px;padding:12px 18px;margin-top:6px;border:1px solid #1B2D4A;text-align:right;'><span style='color:#58A6FF;font-weight:700;'>Total facturado (pedidos Listo): ${_tot_fac:,.0f}</span></div>", unsafe_allow_html=True)

    # ══ TAB MIKE ════════════════════════════════════════════
    with _t_mike:
        st.markdown(f"""
<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:16px;
     padding:20px 24px;border:1px solid #0F3460;margin-bottom:12px;'>
  <div style='font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
       color:#58A6FF;'>ASISTENTE IA</div>
  <div style='font-size:1.4rem;font-weight:800;color:white;margin-top:6px;'>🤖 Mike para {hdr_nombre}</div>
  <div style='font-size:0.78rem;color:#8B949E;margin-top:4px;'>
    Mike conoce tu línea, tus productos y tu historial — preguntale lo que quieras.
  </div>
</div>""", unsafe_allow_html=True)

        # Preguntas rápidas contextualizadas
        _mqs = [
            ("📋 Estado de mi línea",    f"Haceme un resumen del estado actual de la línea {hdr_nombre}: pedidos, stock, margen y oportunidades."),
            ("💰 Mis mejores productos", f"¿Cuáles son mis productos con mejor margen en {hdr_nombre} y por qué?"),
            ("📈 Tendencia de ventas",   f"¿Cómo evolucionaron mis ventas en {hdr_nombre} en los últimos meses? ¿Qué me recomendás?"),
            ("🛒 Cuándo pedir",         f"¿Cuándo conviene que haga el próximo pedido de producción en {hdr_nombre} según el stock y la demanda?"),
            ("⚠️ Riesgos",              f"¿Qué riesgos o alertas tengo en mi línea {hdr_nombre} ahora mismo?"),
            ("🚀 Oportunidades",        f"¿Qué oportunidades de crecimiento ves para la línea {hdr_nombre}?"),
        ]
        _mqc1, _mqc2, _mqc3 = st.columns(3)
        for _mqi, (_mql, _mqt) in enumerate(_mqs):
            with [_mqc1, _mqc2, _mqc3][_mqi % 3]:
                if st.button(_mql, key=f"smq_{_mqi}", use_container_width=True):
                    st.session_state["socio_mike_auto"] = _mqt

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

        _smk_key = f"socio_mike_hist_{uid}"
        if _smk_key not in st.session_state:
            st.session_state[_smk_key] = []
        for _smsg in st.session_state[_smk_key]:
            with st.chat_message("user" if _smsg["role"]=="user" else "assistant", avatar="👤" if _smsg["role"]=="user" else "🤖"):
                st.markdown(_smsg["content"])

        _smk_q    = st.chat_input(f"Preguntale a Mike sobre {hdr_nombre}...", key=f"smk_input_{uid}")
        _smk_auto = st.session_state.pop("socio_mike_auto", None)
        _smk_preg = _smk_q or _smk_auto

        if _smk_preg:
            _ctx_socio = (
                f"Línea del socio: {hdr_nombre}\n"
                f"SKUs activos: {_n_skus}\n"
                f"Capital en stock: ${_cap_stock:,.0f}\n"
                f"Ganancia proyectada stock: ${_gan_stock:,.0f}\n"
                f"Margen promedio catálogo: {_margen_avg:.1f}%\n"
                f"Pedidos activos: {_n_activos}\n"
                f"Total facturado histórico: ${_fac_total:,.0f}\n"
                f"Pedidos completados: {_n_listo}\n"
            )
            if not prod.empty:
                _ctx_socio += "Productos: " + ", ".join(f"{r['name']} (${r['price']:,.0f}, {r['margen_pct']:.0f}% margen)" for _,r in prod.iterrows()) + "\n"
            try:
                from anthropic import Anthropic as _Anthropic
                from context_elpasaje import SYSTEM_PROMPT, get_data_context
                _ac = _Anthropic()
                _sys_s = SYSTEM_PROMPT + f"\n\nEres el asistente personal de {hdr_nombre} dentro del ecosistema El Pasaje 3D Studio.\n" + get_data_context()
                _sys_s += f"\n\nCONTEXTO DEL SOCIO:\n{_ctx_socio}"
                _hist_s = st.session_state[_smk_key]
                _hist_s.append({"role":"user","content":_smk_preg})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(_smk_preg)
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Mike está pensando..."):
                        _rr = _ac.messages.create(model="claude-sonnet-4-6",max_tokens=800,system=_sys_s,messages=_hist_s)
                        _resp_s = _rr.content[0].text
                    st.markdown(_resp_s)
                _hist_s.append({"role":"assistant","content":_resp_s})
                st.session_state[_smk_key] = _hist_s[-20:]
            except Exception as _e:
                st.error(f"Mike no pudo conectarse: {_e}")

        if st.session_state.get(_smk_key):
            if st.button("Limpiar chat", key=f"smk_clear_{uid}"):
                st.session_state[_smk_key] = []
                st.rerun()

elif menu == "🛒 Cargar Pedido":
    uid  = st.session_state["uid"]
    role = st.session_state["role"]
    if role == "socio_multi":
        lineas_activas = st.session_state.get("linea_filtro", get_lineas_usuario(uid))
        cfg = LINEAS.get(uid, {"nombre": "Mis Líneas", "emoji": "✨", "color": "#6366F1"})
    else:
        lineas_activas = [uid]
        cfg = get_linea(uid)

    _cp_color = cfg.get("color","#6366F1")

    # ── Tema oscuro en Cargar Pedido ──────────────────────────
    st.markdown(f"""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{background-color:#0D1117!important}}
.stTabs [data-baseweb="tab-list"]{{background:#161B22!important;border-radius:12px!important;padding:4px!important}}
.stTabs [data-baseweb="tab"]{{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}}
.stTabs [aria-selected="true"]{{background:#21262D!important;color:#F0F6FC!important}}
[data-testid="stFileUploaderDropzone"]{{background:#161B22!important;border-color:{_cp_color}44!important}}
.stMarkdown p,.stMarkdown span{{color:#C9D1D9!important}}
.stMarkdown strong,.stMarkdown b{{color:#F0F6FC!important}}
.stSelectbox label,.stTextInput label,.stTextArea label,.stNumberInput label,.stDateInput label,.stFileUploader label{{color:#8B949E!important;font-weight:500!important}}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{{color:#C9D1D9!important}}
[data-testid="stAlert"]{{background:#1a2332!important;border-color:#30363D!important}}
details{{background:#161B22!important;border:1px solid #21262D!important;border-radius:12px!important}}
</style>""", unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────
    st.markdown(f"""
<div style='background:linear-gradient(135deg,{_cp_color}dd,{_cp_color}88);
     border-radius:20px;padding:20px 28px;margin-bottom:16px;border:1px solid {_cp_color}44;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.7);'>EL PASAJE 3D STUDIO</div>
  <div style='font-size:1.6rem;font-weight:800;color:white;margin-top:4px;'>🛒 Nuevo Pedido · {cfg['nombre']}</div>
  <div style='font-size:0.78rem;color:rgba(255,255,255,0.65);margin-top:4px;'>Solicitá producción a Fer — quedará registrado en el sistema</div>
</div>""", unsafe_allow_html=True)

    # ── Cargar productos ──────────────────────────────────────
    with engine.connect() as _conn:
        _frames = [
            pd.read_sql(
                text("SELECT name, sku, price, weight_gr, description, categoria, color, client_id FROM products WHERE client_id=:uid AND activo=1 ORDER BY name"),
                _conn, params={"uid": lid}
            ) for lid in lineas_activas
        ]
    prods_socio = pd.concat(_frames, ignore_index=True) if _frames else pd.DataFrame()

    if prods_socio.empty:
        st.markdown("<div style='background:#161B22;border-radius:12px;padding:20px;border:1px solid #21262D;text-align:center;color:#8B949E;'>Sin productos cargados todavía. Contactá a Alejandra para agregarlos.</div>", unsafe_allow_html=True)
        st.stop()

    # ── Selección visual de producto ──────────────────────────
    st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:12px;'>SELECCIONÁ UN PRODUCTO</div>", unsafe_allow_html=True)

    if "cp_sel_sku" not in st.session_state:
        st.session_state["cp_sel_sku"] = None

    _cp_cols = st.columns(3)
    for _cpi, (_, _cpr) in enumerate(prods_socio.iterrows()):
        _is_sel = st.session_state["cp_sel_sku"] == _cpr["sku"]
        _cpc    = LINEAS.get(_cpr["client_id"],{}).get("color","#6366F1")
        _sel_style = f"border:2px solid {_cpc};background:#1C2128;" if _is_sel else "border:1px solid #21262D;background:#161B22;"
        _sel_badge = f"<div style='background:{_cpc};color:white;font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:99px;display:inline-block;margin-bottom:6px;'>✓ SELECCIONADO</div>" if _is_sel else ""
        with _cp_cols[_cpi % 3]:
            st.markdown(f"""<div style='{_sel_style}border-radius:14px;padding:14px;margin-bottom:8px;cursor:pointer;'>
{_sel_badge}
<div style='font-size:0.6rem;color:{_cpc};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>{_cpr['sku']}</div>
<div style='font-size:0.88rem;font-weight:700;color:#E6EDF3;margin-top:3px;'>{_cpr['name']}</div>
<div style='font-size:0.68rem;color:#8B949E;margin-top:2px;'>{_cpr.get('categoria','') or ''}</div>
<div style='margin-top:8px;font-size:1rem;font-weight:800;color:{_cpc};'>${float(_cpr['price']):,.0f}</div>
<div style='font-size:0.65rem;color:#6B7280;'>{float(_cpr.get('weight_gr',0) or 0):.0f} g · {str(_cpr.get('description','') or '')[:50]}</div>
</div>""", unsafe_allow_html=True)
            if st.button("Seleccionar", key=f"cpbtn_{_cpr['sku']}", use_container_width=True,
                         type="primary" if _is_sel else "secondary"):
                st.session_state["cp_sel_sku"] = _cpr["sku"]
                st.rerun()

    _sel_sku = st.session_state.get("cp_sel_sku")
    _sel_prod = prods_socio[prods_socio["sku"] == _sel_sku].iloc[0] if _sel_sku and not prods_socio[prods_socio["sku"]==_sel_sku].empty else None

    if _sel_prod is None:
        st.markdown("<div style='background:#0D1B2E;border-radius:10px;padding:12px 18px;border:1px solid #1B2D4A;margin-top:8px;'><span style='color:#58A6FF;font-size:0.82rem;'>👆 Seleccioná un producto de los cards de arriba para continuar</span></div>", unsafe_allow_html=True)
        st.stop()

    st.markdown("<div style='border-top:1px solid #21262D;margin:20px 0;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:12px;'>DETALLE DEL PEDIDO · {_sel_prod['name'].upper()}</div>", unsafe_allow_html=True)

    # ── Formulario de detalle ─────────────────────────────────
    _fd1, _fd2 = st.columns(2)
    with _fd1:
        _cp_qty = st.number_input("Cantidad de unidades", min_value=1, max_value=50, value=1, key="cp_qty")
        _cp_fecha = st.date_input("Fecha de entrega deseada (opcional)", value=None, key="cp_fecha")
    with _fd2:
        _cp_color_txt = st.text_input("Color o material preferido (ej: Rosa, Negro mate, PETG gris)", key="cp_color")
        _cp_urgente = st.checkbox("🔴 Urgente", key="cp_urgente", help="Ferr lo prioriza en la cola")

    _cp_notas = st.text_area(
        "Notas adicionales para Fer (medidas especiales, acabado, packaging, etc.)",
        placeholder="Ej: Necesito el moño con cinta integrada, para regalo de 15 años este viernes...",
        height=90, key="cp_notas"
    )

    # ── Subir referencias / archivos ──────────────────────────
    st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:16px;margin-bottom:8px;'>REFERENCIAS E IMÁGENES (opcional)</div>", unsafe_allow_html=True)
    _cp_files = st.file_uploader(
        "Subí fotos de referencia, bocetos, archivos STL, PDFs o cualquier cosa que le ayude a Fer",
        type=["png","jpg","jpeg","pdf","stl","3mf","dxf","svg","docx","txt"],
        accept_multiple_files=True,
        key="cp_files"
    )
    if _cp_files:
        _fnames = [f.name for f in _cp_files]
        st.markdown(f"<div style='background:#0D2818;border-radius:8px;padding:8px 14px;border:1px solid #238636;'><span style='color:#3FB950;font-size:0.8rem;'>📎 {len(_cp_files)} archivo{'s' if len(_cp_files)>1 else ''} adjunto{'s' if len(_cp_files)>1 else ''}: {', '.join(_fnames)}</span></div>", unsafe_allow_html=True)

    # ── Resumen del pedido antes de confirmar ─────────────────
    _total_est = float(_sel_prod["price"]) * _cp_qty
    st.markdown(f"""
<div style='background:#161B22;border-radius:14px;padding:16px 20px;border:1px solid {_cp_color}44;
     border-left:4px solid {_cp_color};margin-top:16px;margin-bottom:16px;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{_cp_color};margin-bottom:8px;'>RESUMEN DEL PEDIDO</div>
  <div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;'>{_cp_qty}x {_sel_prod['name']}</div>
  <div style='font-size:0.75rem;color:#8B949E;margin-top:2px;'>{_cp_color_txt or "Color por defecto"} · {("🔴 URGENTE" if _cp_urgente else "Sin urgencia")}</div>
  <div style='font-size:1.2rem;font-weight:800;color:{_cp_color};margin-top:8px;'>${_total_est:,.0f}</div>
</div>""", unsafe_allow_html=True)

    if st.button("✅ Confirmar Pedido", type="primary", use_container_width=True, key="cp_submit"):
        # Construir notas completas
        _notas_full = []
        if _cp_color_txt: _notas_full.append(f"Color/material: {_cp_color_txt}")
        if _cp_urgente:   _notas_full.append("🔴 URGENTE")
        if _cp_notas.strip(): _notas_full.append(_cp_notas.strip())
        if _cp_files:     _notas_full.append(f"Archivos adjuntos: {', '.join(f.name for f in _cp_files)}")
        _notas_str = " | ".join(_notas_full)
        _fecha_str = _cp_fecha.isoformat() if _cp_fecha else None
        _archivos_str = ", ".join(f.name for f in _cp_files) if _cp_files else None

        linea_pedido = _sel_prod["client_id"]
        with engine.connect() as _conn2:
            result = _conn2.execute(
                text("""INSERT INTO orders (client_id, status, date, notas, color_pedido,
                                           fecha_entrega_solicitada, referencia_archivo)
                        VALUES (:cid, 'Pendiente', :fecha, :notas, :color,
                                :entrega, :archivos)"""),
                {"cid": linea_pedido, "fecha": datetime.now().isoformat(),
                 "notas": _notas_str, "color": _cp_color_txt or "",
                 "entrega": _fecha_str, "archivos": _archivos_str}
            )
            order_id = result.lastrowid
            prod_q = pd.read_sql(
                text("SELECT price FROM products WHERE sku=:sku"),
                _conn2, params={"sku": _sel_sku}
            )
            _conn2.execute(
                text("INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) VALUES (:oid, :sku, :qty, :precio)"),
                {"oid": order_id, "sku": _sel_sku, "qty": _cp_qty,
                 "precio": float(prod_q["price"].iloc[0]) if not prod_q.empty else float(_sel_prod["price"])}
            )
            _conn2.commit()

        st.session_state.pop("cp_sel_sku", None)
        st.success(f"✅ Pedido #{order_id} enviado a Fer — {_cp_qty}x {_sel_prod['name']} · ${_total_est:,.0f}")
        if _cp_urgente:
            st.warning("🔴 Marcado como urgente — Fer lo verá al tope de su cola.")
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


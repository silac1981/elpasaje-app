"""main.py — Router principal + auth + sidebar. Lógica de paneles en modules/."""
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
from sqlalchemy import text

from utils.db import engine
from utils.lineas import LINEAS, get_linea, get_lineas_usuario
from utils.mike import get_alertas_dashboard

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
[data-testid="stSidebar"] [data-baseweb="radio"] label p {
    color: #FFFFFF !important; font-size: 0.9rem !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] [data-checked="true"] label p {
    color: #C9A84C !important; font-weight: 700 !important;
}
[data-testid="stSidebar"] .version-label { color: #94a3b8 !important; }
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

# ── DB + Schema init ───────────────────────────────────────────────────────
from crear_schema_v3 import init_schema as _init_schema
_init_schema()

# ── Autenticación ──────────────────────────────────────────────────────────
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

# ── Sidebar ────────────────────────────────────────────────────────────────
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
    st.markdown(f"<div style='font-size:0.7rem;color:#94a3b8;text-align:center;margin-top:20px;'>v3.0 · {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

# ── Router ─────────────────────────────────────────────────────────────────
if menu == "📊 Dashboard Alejandra":
    from modules.dashboard_admin import render
    render()

elif menu == "📦 Inventario Pro":
    from modules.inventario import render
    render()

elif menu == "🛠️ Produccion (Fer)":
    from modules.panel_fer import render
    render()

elif menu == "🤝 Socios":
    from modules.panel_socios import render
    render()

elif menu == "📈 Mi Panel":
    from modules.panel_socio import render
    render()

elif menu == "🛒 Cargar Pedido":
    from modules.cargar_pedido import render
    render()

elif menu == "👥 Clientes":
    from modules.clientes import render
    render()

elif menu == "🌱 Impacto Social":
    from modules.impacto import render
    render()

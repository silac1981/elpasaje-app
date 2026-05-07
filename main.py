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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Jost:wght@300;400;500&display=swap');

/* ══════════════════════════════════════════════════════
   BASE — fondo negro, herencia de color claro
   ══════════════════════════════════════════════════════ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main  { background-color: #0e0e0e !important; color: #f0ece4 !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; }

/* ══════════════════════════════════════════════════════
   TEXTO GENÉRICO — cubre todos los casos de Streamlit
   ══════════════════════════════════════════════════════ */
.stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp h5, .stApp small, .stApp strong, .stApp em,
.stApp td, .stApp th, .stApp caption,
.stApp [class*="css"] { color: #f0ece4; }

/* div sin inline-style: hereda; con inline-style: la inline gana */
.stApp div { color: inherit; }

/* Forzar en contenedores Streamlit específicos */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stText"],
[data-testid="stCaptionContainer"] { color: #f0ece4 !important; }

.stMarkdown p, .stMarkdown li, .stMarkdown h1,
.stMarkdown h2, .stMarkdown h3 { color: #f0ece4 !important; }

/* Caption / ayuda */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * { color: rgba(240,236,228,0.70) !important; }
.stApp small { color: rgba(240,236,228,0.70) !important; }

/* ══════════════════════════════════════════════════════
   WIDGETS — labels y valores en claro
   ══════════════════════════════════════════════════════ */
/* Labels generales */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stTextArea label,
.stCheckbox label, .stRadio label,
.stMultiSelect label, .stSlider label,
.stDateInput label, .stTimeInput label,
.stFileUploader label {
    color: rgba(184,115,51,0.85) !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}
/* Radio / checkbox opciones */
.stRadio p, .stRadio div, .stRadio span,
.stCheckbox p, .stCheckbox div, .stCheckbox span {
    color: #f0ece4 !important;
}
/* Help tooltip */
.stTooltipContent, .stTooltipContent * { color: #f0ece4 !important; }

/* ── TEXT INPUT ── */
.stTextInput input, .stTextInput textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 0.5px solid rgba(184,115,51,0.3) !important;
    border-radius: 4px !important;
    color: #f0ece4 !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput input:focus, .stTextInput textarea:focus {
    border-color: #B87333 !important;
    box-shadow: none !important;
}
/* TEXT AREA */
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 0.5px solid rgba(184,115,51,0.3) !important;
    color: #f0ece4 !important;
}
/* NUMBER INPUT */
.stNumberInput input { color: #f0ece4 !important; background: rgba(255,255,255,0.04) !important; }
.stNumberInput [data-baseweb="button"],
.stNumberInput button { background: rgba(255,255,255,0.06) !important; color: #f0ece4 !important; }
/* SELECT */
.stSelectbox [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] div,
.stSelectbox [data-baseweb="select"] span {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(184,115,51,0.3) !important;
    color: #f0ece4 !important;
}
/* SELECT DROPDOWN popup */
[data-baseweb="popover"], [data-baseweb="menu"],
[data-baseweb="menu"] * {
    background: #1a1a1a !important;
    color: #f0ece4 !important;
}
[data-baseweb="option"]:hover { background: rgba(184,115,51,0.2) !important; }
/* MULTISELECT */
.stMultiSelect [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] * { background: rgba(255,255,255,0.04) !important; color: #f0ece4 !important; }
[data-baseweb="tag"] { background: rgba(184,115,51,0.25) !important; }
[data-baseweb="tag"] span { color: #f0ece4 !important; }

/* ══════════════════════════════════════════════════════
   BOTONES
   ══════════════════════════════════════════════════════ */
.stButton > button, .stDownloadButton > button,
.stFormSubmitButton > button, .stLinkButton > a {
    background: transparent !important;
    border: 0.5px solid rgba(184,115,51,0.45) !important;
    border-radius: 4px !important;
    color: #B87333 !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    background: rgba(184,115,51,0.15) !important;
    border-color: #B87333 !important;
    color: #f0ece4 !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: #B87333 !important;
    color: #0e0e0e !important;
    border-color: #B87333 !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: #cc8c45 !important;
}

/* ══════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 0.5px solid rgba(184,115,51,0.15) !important;
}
[data-testid="stSidebar"] * { color: #f0ece4 !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] label p,
[data-testid="stSidebar"] [data-baseweb="radio"] label span {
    font-family: 'Jost', sans-serif !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: rgba(240,236,228,0.55) !important;
}
[data-testid="stSidebar"] [data-checked="true"] label p,
[data-testid="stSidebar"] [data-checked="true"] label span { color: #B87333 !important; }
[data-testid="stSidebar"] button {
    background: rgba(184,115,51,0.1) !important;
    border: 0.5px solid rgba(184,115,51,0.3) !important;
    color: rgba(240,236,228,0.8) !important;
}
[data-testid="stSidebar"] button:hover { background: rgba(184,115,51,0.22) !important; }
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"],
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] * {
    background: rgba(255,255,255,0.05) !important;
    color: #f0ece4 !important;
}

/* ══════════════════════════════════════════════════════
   TABS
   ══════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 0.5px solid rgba(184,115,51,0.2) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(240,236,228,0.55) !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #B87333 !important;
    border-bottom: 2px solid #B87333 !important;
    background: transparent !important;
}

/* ══════════════════════════════════════════════════════
   MÉTRICAS
   ══════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03) !important;
    border: 0.5px solid rgba(184,115,51,0.15) !important;
    border-radius: 6px !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    color: rgba(184,115,51,0.75) !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 10px !important; letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    color: #f0ece4 !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 26px !important;
}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
    color: #f0ece4 !important; font-size: 0.78rem !important;
}

/* ══════════════════════════════════════════════════════
   ALERTAS / INFO / WARNING / ERROR / SUCCESS
   ══════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(184,115,51,0.3) !important;
    border-radius: 6px !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span,
[data-testid="stAlert"] * { color: #f0ece4 !important; }

/* ══════════════════════════════════════════════════════
   EXPANDER
   ══════════════════════════════════════════════════════ */
.stExpander { background: rgba(255,255,255,0.02) !important; border-color: rgba(184,115,51,0.15) !important; }
.stExpander details { background: rgba(255,255,255,0.02) !important; }
.stExpander summary, .stExpander summary p,
.stExpander summary span, .stExpander summary svg { color: #f0ece4 !important; }

/* ══════════════════════════════════════════════════════
   DATAFRAME / TABLA
   ══════════════════════════════════════════════════════ */
.stDataFrame, [data-testid="stDataFrame"],
[data-testid="stDataFrame"] * {
    background: rgba(255,255,255,0.02) !important;
    color: #f0ece4 !important;
}
.stDataFrame th { background: rgba(184,115,51,0.12) !important; color: #B87333 !important; }

/* ══════════════════════════════════════════════════════
   CODE BLOCK
   ══════════════════════════════════════════════════════ */
.stCode, .stCode *, pre, code {
    background: rgba(255,255,255,0.05) !important;
    color: #f0ece4 !important;
}

/* ══════════════════════════════════════════════════════
   FORM
   ══════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.02) !important;
    border: 0.5px solid rgba(184,115,51,0.12) !important;
    border-radius: 6px !important;
}

/* ══════════════════════════════════════════════════════
   HEADINGS
   ══════════════════════════════════════════════════════ */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Cormorant Garamond', serif !important;
    color: #f0ece4 !important;
    font-weight: 300 !important;
    letter-spacing: 2px !important;
}

/* ══════════════════════════════════════════════════════
   CUSTOM CLASSES (admin / inventario)
   ══════════════════════════════════════════════════════ */
.main-header {
    background: linear-gradient(135deg,#1a0e00,#2a1a00) !important;
    border: 0.5px solid rgba(184,115,51,0.3) !important;
    border-radius: 8px !important;
    padding: 28px 36px !important; margin-bottom: 28px !important;
}
.main-header h1, .main-header * { color: #f0ece4 !important; }
.metric-card {
    background: rgba(255,255,255,0.03) !important;
    border: 0.5px solid rgba(184,115,51,0.15) !important;
    border-radius: 6px !important; padding: 20px !important;
}
.metric-card * { color: #f0ece4 !important; }
.section-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.4rem !important; color: #f0ece4 !important;
    border-bottom: 0.5px solid rgba(184,115,51,0.2) !important;
    padding-bottom: 6px !important; margin: 24px 0 14px !important;
}
.stock-critico { background: rgba(239,68,68,0.1) !important; border-left: 3px solid #EF4444 !important; }
.stock-critico * { color: #f0ece4 !important; }

/* ══════════════════════════════════════════════════════
   FILE UPLOADER
   ══════════════════════════════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,0.03) !important;
    border-color: rgba(184,115,51,0.3) !important;
}
[data-testid="stFileUploaderDropzone"] * { color: #f0ece4 !important; }

</style>
""", unsafe_allow_html=True)

# ── DB + Schema init ───────────────────────────────────────────────────────
from crear_schema_v3 import init_schema as _init_schema
_init_schema()
from migration_v7 import run as _migration_v7
_migration_v7()

# ── Autenticación ──────────────────────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})

if not st.session_state["auth"]:
    # Ocultar sidebar en la pantalla de login
    st.markdown("<style>[data-testid='stSidebar']{display:none!important}</style>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
<div style="max-width:420px;margin:4vh auto 2rem;text-align:center;">
  <div style="width:72px;height:72px;border-radius:50%;border:1.5px solid #B87333;
              display:flex;align-items:center;justify-content:center;margin:0 auto 1.2rem;">
    <span style="font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;
                 font-weight:600;color:#B87333;letter-spacing:2px;">EP</span>
  </div>
  <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:300;
            color:#f0ece4;letter-spacing:7px;text-transform:uppercase;margin:0 0 4px;">El Pasaje</p>
  <p style="font-size:10px;font-weight:300;color:#B87333;letter-spacing:5px;
            text-transform:uppercase;margin:0 0 2rem;">3 D &nbsp; S T U D I O</p>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:2rem;">
    <div style="flex:1;height:0.5px;background:rgba(184,115,51,0.25);"></div>
    <div style="width:6px;height:6px;background:#B87333;transform:rotate(45deg);opacity:0.6;"></div>
    <div style="flex:1;height:0.5px;background:rgba(184,115,51,0.25);"></div>
  </div>
</div>""", unsafe_allow_html=True)

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
<div style="display:flex;justify-content:center;gap:6px;flex-wrap:wrap;
            margin-top:1.5rem;padding-top:1.5rem;
            border-top:0.5px solid rgba(184,115,51,0.1);">
  <div style="width:6px;height:6px;border-radius:50%;background:#B87333;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#9C6B3C;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#FFB6C1;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#F472B6;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#166534;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#1e3a5f;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#F97316;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#D4A574;opacity:.5;"></div>
  <div style="width:6px;height:6px;border-radius:50%;background:#4ade80;opacity:.5;"></div>
</div>
<div style="text-align:center;margin-top:1.2rem;">
  <a href="https://wa.me/5491165497234" target="_blank"
     style="color:rgba(184,115,51,0.6);font-size:10px;letter-spacing:2px;
            text-transform:uppercase;text-decoration:none;">
    Consultas &nbsp;·&nbsp; WhatsApp
  </a>
</div>""", unsafe_allow_html=True)
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    linea_cfg   = get_linea(st.session_state["uid"])
    _sb_color   = linea_cfg["color"]
    _sb_nombre  = linea_cfg["nombre"]
    _sb_rol_map = {"admin": "Administración", "produccion": "Producción", "socio_multi": "Multi-Línea", "socio": "Socio"}
    _sb_rol     = _sb_rol_map.get(st.session_state["role"], "Socio")
    st.markdown(f"""
<div style="padding:1.4rem 0 1rem;border-bottom:0.5px solid rgba(184,115,51,0.15);margin-bottom:1rem;">
  <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:20px;font-weight:300;
            color:#f0ece4;letter-spacing:4px;text-transform:uppercase;margin:0 0 4px;">EP</p>
  <p style="font-size:10px;letter-spacing:2px;text-transform:uppercase;
            color:{_sb_color};margin:0 0 8px;font-family:'Jost',sans-serif;">{_sb_nombre}</p>
  <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:15px;font-weight:300;
            color:rgba(240,236,228,0.75);letter-spacing:1px;margin:0;">
    Bienvenida,&nbsp;{st.session_state['user']}</p>
  <p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;
            color:rgba(184,115,51,0.45);margin:2px 0 0;font-family:'Jost',sans-serif;">{_sb_rol}</p>
</div>""", unsafe_allow_html=True)
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

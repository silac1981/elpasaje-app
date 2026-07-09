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

st.html("""
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;700;800&family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* TOKENS */
:root {
  --bg:#EBE6DC; --surface:#FAF8F3; --surface-2:#F2EEE5; --raise:#FFFFFF;
  --line:#DCD5C7; --ink:#16181F; --ink-2:#3A3E4A; --muted:#74798A; --track:#E4DECF;
  --ep:#FF4B4B; --ok:#2F9E54; --warn:#E0902A; --danger:#D7322B; --wa:#25D366;
  --disp:"Bricolage Grotesque",sans-serif;
  --text:"Source Sans 3",sans-serif;
  --mono:"Source Code Pro",monospace;
  --accent:#FF4B4B;
}

/* ── BASE ───────────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background-color: var(--bg) !important; color: var(--ink) !important; font-family: var(--text) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; }

/* ── TEXTO ──────────────────────────────────────────────── */
.stApp p, .stApp li, .stApp td, .stApp th, .stApp caption,
.stApp small, .stApp strong, .stApp em { color: var(--ink); }
.stApp div { color: inherit; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stText"] { color: var(--ink) !important; }
.stMarkdown p, .stMarkdown li { color: var(--ink) !important; }
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * { color: var(--muted) !important; }

/* ── TITULARES ──────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6,
.stApp h1, .stApp h2, .stApp h3 {
    font-family: var(--disp) !important;
    color: var(--ink) !important;
    font-weight: 700 !important;
    letter-spacing: -.02em !important;
}

/* ── WIDGETS ────────────────────────────────────────────── */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stTextArea label,
.stCheckbox label, .stRadio label,
.stMultiSelect label, .stSlider label,
.stDateInput label, .stTimeInput label,
.stFileUploader label {
    color: var(--muted) !important;
    font-family: var(--text) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: .04em !important;
    text-transform: uppercase !important;
}
.stRadio p, .stRadio span, .stCheckbox p, .stCheckbox span { color: var(--ink) !important; }
.stTooltipContent, .stTooltipContent * { color: var(--ink) !important; }

/* TEXT INPUT / TEXTAREA */
.stTextInput input, .stTextInput textarea, .stTextArea textarea {
    background: var(--raise) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
    font-family: var(--text) !important;
    font-size: 13.5px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(255,75,75,0.15) !important;
}

/* NUMBER INPUT */
.stNumberInput input { color: var(--ink) !important; background: var(--raise) !important; border: 1px solid var(--line) !important; border-radius: 8px !important; }
.stNumberInput [data-baseweb="button"], .stNumberInput button { background: var(--surface-2) !important; color: var(--ink) !important; }

/* SELECT */
.stSelectbox [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] div,
.stSelectbox [data-baseweb="select"] span {
    background: var(--raise) !important;
    border-color: var(--line) !important;
    color: var(--ink) !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="menu"] * {
    background: var(--surface) !important;
    color: var(--ink) !important;
}
[data-baseweb="option"]:hover { background: var(--surface-2) !important; }

/* MULTISELECT */
.stMultiSelect [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] * { background: var(--raise) !important; color: var(--ink) !important; }
[data-baseweb="tag"] { background: rgba(255,75,75,0.15) !important; }
[data-baseweb="tag"] span { color: var(--ink) !important; }

/* ── BOTONES ─────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button,
.stFormSubmitButton > button, .stLinkButton > a {
    background: var(--raise) !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
    color: var(--ink) !important;
    font-family: var(--text) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: .04em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #fff !important;
    border-color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    filter: brightness(1.08) !important;
}

/* ── SIDEBAR ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] label p,
[data-testid="stSidebar"] [data-baseweb="radio"] label span {
    font-family: var(--text) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: .04em !important;
    color: var(--ink-2) !important;
}
[data-testid="stSidebar"] [data-checked="true"] label p,
[data-testid="stSidebar"] [data-checked="true"] label span { color: var(--accent) !important; }
[data-testid="stSidebar"] button {
    background: var(--surface-2) !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
}
[data-testid="stSidebar"] button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"],
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] * {
    background: var(--raise) !important;
    color: var(--ink) !important;
}

/* ── TABS ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--line) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    font-family: var(--text) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: .04em !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

/* ── MÉTRICAS ────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    color: var(--muted) !important;
    font-family: var(--text) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: .06em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    color: var(--ink) !important;
    font-family: var(--disp) !important;
    font-weight: 700 !important;
    font-size: 30px !important;
    letter-spacing: -.03em !important;
}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
    font-size: 0.78rem !important;
}

/* ── ALERTAS ─────────────────────────────────────────────── */
[data-testid="stAlert"] {
    background: var(--surface) !important;
    border-color: var(--line) !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span { color: var(--ink) !important; }

/* ── EXPANDER ────────────────────────────────────────────── */
.stExpander { background: var(--surface) !important; border-color: var(--line) !important; border-radius: 10px !important; }
.stExpander details { background: var(--surface) !important; }
.stExpander summary, .stExpander summary p,
.stExpander summary span { color: var(--ink) !important; font-weight: 600 !important; }

/* ── DATAFRAME ───────────────────────────────────────────── */
.stDataFrame, [data-testid="stDataFrame"],
[data-testid="stDataFrame"] * {
    background: var(--surface) !important;
    color: var(--ink) !important;
}
.stDataFrame td, [data-testid="stDataFrame"] td {
    font-family: var(--mono) !important;
    font-variant-numeric: tabular-nums !important;
}
.stDataFrame th { background: var(--surface-2) !important; color: var(--ink-2) !important; font-weight: 600 !important; }

/* ── FORM ────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
}

/* ── FILE UPLOADER ───────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface) !important;
    border-color: var(--line) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] * { color: var(--ink) !important; }

/* ── CODE BLOCK ──────────────────────────────────────────── */
.stCode, .stCode *, pre, code {
    background: var(--surface-2) !important;
    color: var(--ink-2) !important;
    font-family: var(--mono) !important;
}

/* ── CUSTOM CLASSES ──────────────────────────────────────── */
.main-header {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-left: 4px solid var(--accent) !important;
    border-radius: 12px !important;
    padding: 24px 32px !important;
    margin-bottom: 24px !important;
}
.main-header h1, .main-header * { color: var(--ink) !important; }
.metric-card {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    padding: 20px !important;
}
.metric-card * { color: var(--ink) !important; }
.section-title {
    font-family: var(--disp) !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    border-bottom: 1px solid var(--line) !important;
    padding-bottom: 6px !important;
    margin: 24px 0 14px !important;
}
.stock-critico {
    background: rgba(215,50,43,0.08) !important;
    border-left: 3px solid var(--danger) !important;
}
.stock-critico * { color: var(--ink) !important; }
</style>
""")

# ── DB + Schema init — corre UNA vez por sesión de servidor ───────────────
@st.cache_resource
def _run_migrations():
    from crear_schema_v3 import init_schema as _init_schema
    _init_schema()
    from migration_v7 import run as _migration_v7
    _migration_v7()
    from migration_v8 import run as _migration_v8
    _migration_v8()
    from migration_v9 import run as _migration_v9
    _migration_v9()
    from migration_v10 import run as _migration_v10
    _migration_v10()
    from migration_v11 import run as _migration_v11
    _migration_v11()
    from migration_v12 import run as _migration_v12
    _migration_v12()
    from migration_v13 import run as _migration_v13
    _migration_v13()
    from migration_v14 import run as _migration_v14
    _migration_v14()

_run_migrations()

# ── Autenticación ──────────────────────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})

def _set_accent(hex_color: str):
    st.html(f"<style>:root{{--accent:{hex_color};}}</style>")

if not st.session_state["auth"]:
    st.html("<style>[data-testid='stSidebar']{display:none!important}</style>")
    _, col2, _ = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
<div style="max-width:400px;margin:6vh auto 2rem;text-align:center;">
  <div style="width:68px;height:68px;border-radius:50%;
              background:#FAF8F3;border:2px solid #FF4B4B;
              display:flex;align-items:center;justify-content:center;margin:0 auto 1.4rem;">
    <span style="font-family:'Bricolage Grotesque',sans-serif;font-size:20px;
                 font-weight:800;color:#FF4B4B;letter-spacing:-1px;">EP</span>
  </div>
  <p style="font-family:'Bricolage Grotesque',sans-serif;font-size:28px;font-weight:800;
            color:#16181F;letter-spacing:-.03em;margin:0 0 2px;">El Pasaje</p>
  <p style="font-family:'Source Sans 3',sans-serif;font-size:11px;font-weight:600;
            color:#74798A;letter-spacing:.18em;text-transform:uppercase;margin:0 0 2rem;">
    3D Studio
  </p>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:2rem;">
    <div style="flex:1;height:1px;background:#DCD5C7;"></div>
    <div style="width:6px;height:6px;background:#FF4B4B;border-radius:50%;opacity:.7;"></div>
    <div style="flex:1;height:1px;background:#DCD5C7;"></div>
  </div>
</div>""", unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="tu@elpasaje.com")
        pwd   = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al sistema", use_container_width=True, type="primary"):
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
                role = "admin" if (uid == "admin" or tipo == "admin") else ("socio_multi" if tipo == "socio_multi" else "socio")
                st.session_state.update({"auth": True, "user": row["name"].iloc[0], "role": role, "uid": uid})
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

        st.markdown("""
<div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap;
            margin-top:2rem;padding-top:1.5rem;border-top:1px solid #DCD5C7;">
  <div style="width:8px;height:8px;border-radius:50%;background:#3E9B53;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#F472B6;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#DB2777;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#F97316;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#C9A84C;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#1E5A8A;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#0E7E78;"></div>
  <div style="width:8px;height:8px;border-radius:50%;background:#0E7490;"></div>
</div>
<div style="text-align:center;margin-top:1.2rem;">
  <a href="https://wa.me/5491165497234" target="_blank"
     style="color:#74798A;font-family:'Source Sans 3',sans-serif;font-size:11px;
            font-weight:600;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;">
    Consultas · WhatsApp
  </a>
</div>""", unsafe_allow_html=True)
    st.stop()

# ── Accent por rol ─────────────────────────────────────────────────────────
_linea_cfg  = get_linea(st.session_state["uid"])
_accent     = "#FF4B4B" if st.session_state["role"] == "admin" else _linea_cfg["color"]
_set_accent(_accent)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    _sb_nombre  = _linea_cfg["nombre"]
    _sb_rol_map = {"admin": "Administración", "socio_multi": "Multi-Línea", "socio": "Socio"}
    _sb_rol     = _sb_rol_map.get(st.session_state["role"], "Socio")

    st.html(f"""<style>
[data-testid="stSidebar"] [data-baseweb="radio"] {{
    gap: 2px !important;
}}
[data-testid="stSidebar"] [data-baseweb="radio"] label {{
    padding: 8px 10px !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 8px 8px 0 !important;
    transition: all 0.15s !important;
}}
[data-testid="stSidebar"] [data-checked="true"] label {{
    border-left-color: {_accent} !important;
    background: rgba(0,0,0,0.05) !important;
}}
[data-testid="stSidebar"] [data-checked="true"] label p,
[data-testid="stSidebar"] [data-checked="true"] label span {{
    color: {_accent} !important;
    font-weight: 700 !important;
}}
</style>""")

    st.markdown(f"""
<div style="padding:1.2rem 0 1rem;border-bottom:1px solid #DCD5C7;margin-bottom:1rem;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
    <div style="width:36px;height:36px;border-radius:50%;background:#FAF8F3;
                border:2px solid {_accent};display:flex;align-items:center;
                justify-content:center;flex-shrink:0;">
      <span style="font-family:'Bricolage Grotesque',sans-serif;font-size:13px;
                   font-weight:800;color:{_accent};">EP</span>
    </div>
    <div>
      <p style="font-family:'Bricolage Grotesque',sans-serif;font-size:15px;
                font-weight:800;color:#16181F;letter-spacing:-.02em;margin:0 0 1px;">
        El Pasaje</p>
      <p style="font-family:'Source Sans 3',sans-serif;font-size:10px;font-weight:600;
                color:{_accent};letter-spacing:.12em;text-transform:uppercase;margin:0;">
        {_sb_nombre}</p>
    </div>
  </div>
  <p style="font-family:'Source Sans 3',sans-serif;font-size:13px;font-weight:600;
            color:#3A3E4A;margin:0 0 2px;">
    Bienvenida, {st.session_state['user']}</p>
  <p style="font-family:'Source Sans 3',sans-serif;font-size:10px;font-weight:600;
            color:#74798A;letter-spacing:.1em;text-transform:uppercase;margin:0;">
    {_sb_rol}</p>
</div>""", unsafe_allow_html=True)

    if st.session_state["role"] == "admin":
        menu = st.radio("", ["Control", "Venta", "Taller", "Stock", "Líneas", "CRM", "Impacto", "Mike"], label_visibility="collapsed")
    elif st.session_state["role"] == "socio_multi":
        _lids = get_lineas_usuario(st.session_state["uid"])
        _nombre_a_id = {LINEAS[l]["nombre"]: l for l in _lids if l in LINEAS}
        _opciones = ["Todas"] + list(_nombre_a_id.keys())
        _sel = st.selectbox("Ver línea", _opciones, key="linea_sel")
        st.session_state["linea_filtro"] = _lids if _sel == "Todas" else [_nombre_a_id[_sel]]
        menu = st.radio("", ["Mi Línea", "Pedido"], label_visibility="collapsed")
    else:
        menu = st.radio("", ["Mi Línea", "Pedido"], label_visibility="collapsed")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})
        st.rerun()

    if st.session_state["role"] == "admin":
        _alertas = get_alertas_dashboard()
        if _alertas:
            _n_crit = sum(1 for a in _alertas if a["nivel"] == "critico")
            _n_atc  = sum(1 for a in _alertas if a["nivel"] == "atencion")
            _borde  = "#D7322B" if _n_crit else "#E0902A"
            _resumen = f"{_n_crit} crítica{'s' if _n_crit != 1 else ''}" if _n_crit else ""
            if _n_atc:
                _resumen += f"{'  ' if _resumen else ''}{_n_atc} atención"
            st.markdown(f"""
<div style='margin-top:16px;padding:10px 12px;background:#FAF8F3;border-radius:10px;
            border:1px solid #DCD5C7;border-left:3px solid {_borde};'>
  <div style='font-family:"Source Sans 3",sans-serif;font-size:10px;font-weight:700;
              color:{_borde};letter-spacing:.1em;text-transform:uppercase;'>Mike · Alertas</div>
  <div style='font-family:"Source Code Pro",monospace;font-size:11px;color:#3A3E4A;
              margin-top:3px;'>{_resumen}</div>
</div>""", unsafe_allow_html=True)
            for _a in _alertas[:4]:
                _col = "#D7322B" if _a["nivel"] == "critico" else ("#E0902A" if _a["nivel"] == "atencion" else "#74798A")
                st.markdown(f"""
<div style='margin-top:5px;padding:7px 10px;background:#FAF8F3;border-radius:8px;
            border-left:3px solid {_col};'>
  <div style='font-family:"Source Sans 3",sans-serif;font-size:11px;
              font-weight:700;color:{_col};'>{_a['titulo']}</div>
  <div style='font-family:"Source Sans 3",sans-serif;font-size:11px;
              color:#74798A;margin-top:2px;'>{_a['accion']}</div>
</div>""", unsafe_allow_html=True)
            if len(_alertas) > 4:
                st.markdown(f"<div style='font-family:\"Source Sans 3\",sans-serif;font-size:11px;color:#74798A;text-align:center;margin-top:4px;'>+{len(_alertas)-4} más · ver tab Mike</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style='margin-top:16px;padding:10px 12px;background:#FAF8F3;border-radius:10px;
            border:1px solid #DCD5C7;border-left:3px solid #2F9E54;'>
  <div style='font-family:"Source Sans 3",sans-serif;font-size:10px;font-weight:700;
              color:#2F9E54;letter-spacing:.1em;text-transform:uppercase;'>Mike · Sin alertas</div>
  <div style='font-family:"Source Sans 3",sans-serif;font-size:11px;color:#74798A;
              margin-top:3px;'>Todo en orden</div>
</div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='font-family:\"Source Code Pro\",monospace;font-size:10px;color:#74798A;text-align:center;margin-top:20px;'>v3.0 · {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

# ── Router ─────────────────────────────────────────────────────────────────
if menu == "Control":
    from modules.dashboard_admin import render
    render()

elif menu == "Venta":
    from modules.nueva_venta import render
    render()

elif menu == "Stock":
    from modules.inventario import render
    render()

elif menu == "Taller":
    from modules.panel_fer import render
    render()

elif menu == "Líneas":
    from modules.panel_socios import render
    render()

elif menu == "Mi Línea":
    from modules.panel_socio import render
    render()

elif menu == "Pedido":
    from modules.cargar_pedido import render
    render()

elif menu == "CRM":
    from modules.clientes import render
    render()

elif menu == "Impacto":
    from modules.impacto import render
    render()

elif menu == "Mike":
    from modules.panel_mike import render
    render()

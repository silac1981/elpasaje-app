 """
EL PASAJE CONTROL CENTER v1.0
Sistema de Gestion Integral para Manufactura 3D
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import hashlib
import json
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="EPCC v1.0 | El Pasaje 3D Studio",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

VERSION = "1.0 Enterprise"
FECHA_SISTEMA = datetime.now().strftime("%d/%m/%Y %H:%M")

COLORES = {
    'oro_viejo': '#B8860B',
    'oro_brillante': '#DAA520',
    'negro_carbon': '#1A1A1A',
}

IMG_PASAJE = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Pasaje_La_Piedad.JPG/1024px-Pasaje_La_Piedad.JPG"
IMG_OASIS = "https://images.unsplash.com/photo-1544568100-847a948585b9?auto=format&fit=crop&q=80&w=1600"
IMG_HIDROPONIA = "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?auto=format&fit=crop&q=80&w=1600"
IMG_TURNTABLE = "https://images.unsplash.com/photo-1603048588665-791ca8aea617?auto=format&fit=crop&q=80&w=1600"
IMG_PHARMA = "https://images.unsplash.com/photo-1587854692152-cbe660dbbb88?auto=format&fit=crop&q=80&w=1600"

LOGO_HTML = '<div style="text-align:center; padding:50px;"><h1 style="color:#B8860B; font-family:Cormorant Garamond, serif; font-size:82px; letter-spacing:25px; margin:0; text-shadow:2px 2px 4px rgba(0,0,0,0.3);">EL PASAJE</h1><p style="color:#666; font-size:22px; letter-spacing:10px; margin:15px 0 0 0; font-weight:600;">3D STUDIO</p><div style="width:80px; height:3px; background:linear-gradient(90deg, #B8860B, #DAA520); margin:20px auto;"></div></div>'

def inject_custom_css():
    st.markdown(f'''
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap");
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{IMG_PASAJE}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .glass-card {{
        background: rgba(255, 255, 255, 0.97);
        border-radius: 30px;
        padding: 50px;
        border: 2px solid {COLORES['oro_viejo']};
        box-shadow: 0 30px 80px rgba(0,0,0,0.5);
        backdrop-filter: blur(15px);
    }}
    .metric-card {{
        background: linear-gradient(135deg, {COLORES['oro_viejo']}, {COLORES['oro_brillante']});
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }}
    .metric-card h2 {{
        margin: 0;
        font-size: 42px;
        color: white !important;
        font-weight: bold;
    }}
    .metric-card h4 {{
        margin: 0 0 10px 0;
        font-size: 15px;
        color: white !important;
        opacity: 0.9;
    }}
    .stButton>button {{
        background: linear-gradient(135deg, {COLORES['oro_viejo']}, {COLORES['oro_brillante']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 14px 40px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        letter-spacing: 2px !important;
        transition: all 0.3s !important;
    }}
    .stButton>button:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 10px 30px rgba(212, 175, 55, 0.5) !important;
    }}
    h1, h2, h3 {{
        color: {COLORES['oro_viejo']} !important;
        font-family: "Cormorant Garamond", serif !important;
    }}
    </style>
    ''', unsafe_allow_html=True)

DB_PATH = 'database/elpasaje.db'

def init_database():
    os.makedirs('database', exist_ok=True)
    os.makedirs('uploads_clientes', exist_ok=True)
    os.makedirs('uploads_proyectos', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id_cliente TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        tipo TEXT DEFAULT 'B2B',
        usuario TEXT UNIQUE,
        password_hash TEXT,
        email TEXT,
        telefono TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activo BOOLEAN DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS productos_frecuentes (
        id_producto TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        cliente_id TEXT,
        categoria TEXT,
        descripcion TEXT,
        precio_base REAL,
        gramos_material REAL,
        tiempo_impresion_min INTEGER,
        colores_disponibles TEXT,
        stock_actual INTEGER DEFAULT 0,
        imagen_url TEXT,
        activo BOOLEAN DEFAULT 1,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido TEXT PRIMARY KEY,
        cliente_id TEXT,
        fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'Pendiente',
        total REAL,
        metodo_pago TEXT,
        pagado BOOLEAN DEFAULT 0,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_materiales (
        id_material INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_material TEXT,
        color TEXT,
        precio_kg REAL,
        stock_actual_kg REAL,
        stock_minimo_kg REAL DEFAULT 0.5
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS proyectos_stl (
        id_proyecto TEXT PRIMARY KEY,
        cliente_id TEXT,
        nombre_archivo TEXT,
        gramos_brutos REAL,
        precio_calculado REAL,
        fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente)
    )''')
    
    conn.commit()
    conn.close()

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM clientes")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    clientes = [
        ('EP-2026-001', 'Oasis Animal', 'B2B', 'oasis', hashlib.sha256('perros'.encode()).hexdigest(), 'contacto@oasisanimal.com', '+54 9 11 5555-0001'),
        ('EP-2026-002', 'Oasis del Estero', 'B2B', 'estero', hashlib.sha256('plantas'.encode()).hexdigest(), 'contacto@oasisestero.com', '+54 9 11 5555-0002'),
        ('EP-2026-003', 'Pharma DeLux', 'B2B', 'pharmadelux', hashlib.sha256('medicina'.encode()).hexdigest(), 'lucas@pharmadelux.com', '+54 9 11 5555-0003'),
        ('EP-2026-004', 'Aviation & Audio', 'B2B', 'aviation', hashlib.sha256('fernando'.encode()).hexdigest(), 'fernando@aviationaudio.com', '+54 9 11 5555-0004'),
    ]
    c.executemany("INSERT INTO clientes (id_cliente, nombre, tipo, usuario, password_hash, email, telefono) VALUES (?,?,?,?,?,?,?)", clientes)
    
    productos = [
        ('PROD-2026-001', 'Llavero Porta-Bolsas Premium', 'EP-2026-001', 'Oasis Animal', 'Llavero ergonomico para bolsas biodegradables', 450.00, 15.0, 25, '["Negro", "Verde", "Azul", "Rosa"]', 50, IMG_OASIS, 1),
        ('PROD-2026-002', 'Base Elevada Comedero', 'EP-2026-001', 'Oasis Animal', 'Soporte elevado ajustable', 1200.00, 85.0, 180, '["Blanco", "Gris", "Negro"]', 15, IMG_OASIS, 1),
        ('PROD-2026-003', 'Maceta Hidroponica Modular', 'EP-2026-002', 'Oasis del Estero', 'Sistema de cultivo hidroponico', 2800.00, 220.0, 480, '["Blanco", "Verde", "Terracota"]', 8, IMG_HIDROPONIA, 1),
        ('PROD-2026-004', 'Soporte LP-Display', 'EP-2026-004', 'Aviation & Audio', 'Exhibidor para vinilos', 1500.00, 95.0, 210, '["Negro", "Blanco", "Madera"]', 12, IMG_TURNTABLE, 1),
        ('PROD-2026-005', 'Organizador Medico', 'EP-2026-003', 'Pharma DeLux', 'Sistema organizador medico', 3200.00, 180.0, 360, '["Blanco", "Azul"]', 5, IMG_PHARMA, 1),
    ]
    c.executemany("INSERT INTO productos_frecuentes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", productos)
    
    materiales = [
        ('PLA', 'Blanco', 4500.00, 5.2, 0.5),
        ('PLA', 'Negro', 4500.00, 3.8, 0.5),
        ('PLA', 'Verde Oasis', 5200.00, 2.1, 0.5),
        ('PLA', 'Rosa Coquette', 5200.00, 0.3, 0.5),
        ('PETG', 'Transparente', 6800.00, 1.2, 0.5),
    ]
    c.executemany("INSERT INTO inventario_materiales (tipo_material, color, precio_kg, stock_actual_kg, stock_minimo_kg) VALUES (?,?,?,?,?)", materiales)
    
    conn.commit()
    conn.close()

def verificar_credenciales(usuario, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if usuario == 'admin' and password == 'piedad2024':
        conn.close()
        return {'logged': True, 'role': 'Admin', 'name': 'Direccion Arcano (Alejandra)', 'id': 'ADMIN'}
    
    if usuario == 'operaciones' and password == 'fer2024':
        conn.close()
        return {'logged': True, 'role': 'Admin', 'name': 'Operaciones Tecnicas (Fernando)', 'id': 'OPERATIONS'}
    
    c.execute("SELECT id_cliente, nombre, tipo, password_hash FROM clientes WHERE usuario=? AND activo=1", (usuario,))
    result = c.fetchone()
    conn.close()
    
    if result:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if result[3] == password_hash:
            return {'logged': True, 'role': 'B2B', 'name': result[1], 'id': result[0]}
    
    return None

inject_custom_css()
init_database()
seed_data()

if 'auth' not in st.session_state:
    st.session_state.auth = {'logged': False}
if 'view' not in st.session_state:
    st.session_state.view = None

if not st.session_state.auth['logged']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2.5, 1])
    
    with col2:
        st.markdown(f'<div class="glass-card">{LOGO_HTML}', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #888; font-size:14px;'>Sistema v{VERSION}</p>", unsafe_allow_html=True)
        
        perfil = st.selectbox("Protocolo de Acceso", ["Invitado de Honor", "Socio Estrategico B2B", "Direccion Arcano"], label_visibility="collapsed")
        
        if perfil == "Direccion Arcano":
            st.caption("**Usuarios:** admin / operaciones")
            with st.form("admin_login"):
                usuario = st.text_input("Usuario", placeholder="admin")
                password = st.text_input("Contrasena", type="password", placeholder="•••••")
                submit = st.form_submit_button("🔓 Activar Gobierno", use_container_width=True)
                
                if submit:
                    auth = verificar_credenciales(usuario, password)
                    if auth:
                        st.session_state.auth = auth
                        st.rerun()
                    else:
                        st.error("❌ Credenciales invalidas")
        
        elif perfil == "Socio Estrategico B2B":
            st.caption("**Usuarios:** oasis / estero / pharmadelux / aviation")
            with st.form("b2b_login"):
                usuario = st.text_input("Socio", placeholder="oasis")
                password = st.text_input("Clave", type="password", placeholder="•••••")
                submit = st.form_submit_button("🤝 Vincular Cuenta", use_container_width=True)
                
                if submit:
                    auth = verificar_credenciales(usuario, password)
                    if auth:
                        st.session_state.auth = auth
                        st.rerun()
                    else:
                        st.error("❌ Credenciales invalidas")
        else:
            st.info("👁️ Modo Publico: Acceso al catalogo institucional")
            if st.button("🏛️ Explorar El Pasaje", use_container_width=True):
                st.session_state.auth = {'logged': True, 'role': 'Public', 'name': 'Invitado', 'id': 'PUBLIC'}
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("© 2026 El Pasaje 3D Studio | Bartolome Mitre 1500, Buenos Aires")

else:
    with st.sidebar:
        st.markdown(LOGO_HTML, unsafe_allow_html=True)
        st.markdown(f"### 👤 {st.session_state.auth['name']}")
        st.caption(f"**Sistema:** EPCC v{VERSION}")
        st.caption(f"**Fecha:** {FECHA_SISTEMA}")
        
        if st.button("🚪 Cerrar Sesion", use_container_width=True):
            st.session_state.auth = {'logged': False}
            st.session_state.view = None
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.auth['role'] == 'Admin':
            menu = ["📊 Dashboard Financiero", "📦 Inventario & Stock", "📋 Gestion de Pedidos", "🎨 Proyectos STL", "🛍️ Catalogo El Pasaje", "👥 Gestion de Clientes"]
            selected = st.radio("Panel", menu, label_visibility="collapsed")
            st.session_state.view = selected
    
    if st.session_state.auth['role'] == 'Admin':
        st.title(f"🏛️ {st.session_state.view if st.session_state.view else 'Panel Principal'}")
        
        if "Dashboard" in str(st.session_state.view):
            conn = sqlite3.connect(DB_PATH)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                ingresos = pd.read_sql("SELECT COALESCE(SUM(total), 0) as total FROM pedidos WHERE pagado=1", conn)['total'][0]
                st.markdown(f'<div class="metric-card"><h4>💰 Ingresos</h4><h2>${ingresos:,.0f}</h2></div>', unsafe_allow_html=True)
            
            with col2:
                pedidos = pd.read_sql("SELECT COUNT(*) as cnt FROM pedidos WHERE estado!='Completado'", conn)['cnt'][0]
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #4682B4, #5F9EA0);"><h4>📦 Pedidos</h4><h2>{pedidos}</h2></div>', unsafe_allow_html=True)
            
            with col3:
                alertas = pd.read_sql("SELECT COUNT(*) as cnt FROM inventario_materiales WHERE stock_actual_kg < stock_minimo_kg", conn)['cnt'][0]
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #dc3545, #c82333);"><h4>⚠️ Alertas</h4><h2>{alertas}</h2></div>', unsafe_allow_html=True)
            
            with col4:
                proyectos = pd.read_sql("SELECT COUNT(*) as cnt FROM proyectos_stl", conn)['cnt'][0]
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #28a745, #218838);"><h4>🎨 Proyectos</h4><h2>{proyectos}</h2></div>', unsafe_allow_html=True)
            
            conn.close()
            st.markdown("---")
            st.success("✅ El Pasaje 3D Studio - Sistema operativo")
            st.info("📊 Base de datos: elpasaje.db | IDs: EP-2026-XXX")
        
        elif "Inventario" in str(st.session_state.view):
            st.subheader("📦 Control de Inventario")
            conn = sqlite3.connect(DB_PATH)
            stock_bajo = pd.read_sql("SELECT tipo_material, color, stock_actual_kg, stock_minimo_kg FROM inventario_materiales WHERE stock_actual_kg < stock_minimo_kg", conn)
            
            if not stock_bajo.empty:
                st.warning(f"⚠️ {len(stock_bajo)} material(es) bajo stock minimo")
                st.dataframe(stock_bajo, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Todos los materiales con stock suficiente")
            
            st.markdown("---")
            inventario = pd.read_sql("SELECT * FROM inventario_materiales", conn)
            st.dataframe(inventario, use_container_width=True, hide_index=True)
            conn.close()
        
        else:
            st.info(f"✨ Modulo: {st.session_state.view}")
            st.write("Funcionalidad en desarrollo")
    
    elif st.session_state.auth['role'] == 'B2B':
        st.title(f"🤝 Portal de Socios - {st.session_state.auth['name']}")
        st.success("✅ Acceso B2B habilitado")
        conn = sqlite3.connect(DB_PATH)
        productos = pd.read_sql(f"SELECT nombre, descripcion, precio_base, stock_actual FROM productos_frecuentes WHERE cliente_id = '{st.session_state.auth['id']}'", conn)
        
        if not productos.empty:
            st.subheader("🛍️ Tus Productos")
            st.dataframe(productos, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No hay productos asignados")
        conn.close()
    
    else:
        st.title("🏛️ El Pasaje 3D Studio")
        st.caption("Manufactura Aditiva de Alta Precision | Bartolome Mitre 1500, Buenos Aires")
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image(IMG_OASIS, use_container_width=True)
            st.markdown("### 🐾 Oasis Animal")
            st.caption("Productos Premium para Mascotas")
        
        with col2:
            st.image(IMG_HIDROPONIA, use_container_width=True)
            st.markdown("### 🌱 Oasis del Estero")
            st.caption("Hidroponia Tecnica")
        
        with col3:
            st.image(IMG_TURNTABLE, use_container_width=True)
            st.markdown("### ✈️ Aviation & Audio")
            st.caption("Modelismo & Audio Elite")
        
        st.markdown("---")
        st.info("🔐 Inicia sesion para acceder al sistema completo")

if st.session_state.auth.get('logged'):
    st.markdown("---")
    st.caption(f"© 2026 El Pasaje 3D Studio | EPCC v{VERSION}")
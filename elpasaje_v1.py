"""
EL PASAJE 3D STUDIO - Sistema de Gestión Empresarial v2.0
Bartolomé Mitre 1500, Buenos Aires
"""

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import logging
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="El Pasaje 3D Studio | EPCC v2.0",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

VERSION = "2.0 Enterprise"
FECHA = datetime.now().strftime("%d/%m/%Y")

COLORES = {
    'oro_viejo': '#B8860B',
    'oro_brillante': '#DAA520',
    'negro': '#1A1A1A',
    'blanco': '#FFFFF0'
}

# Logo EP oficial (del HTML)
LOGO_EP = '''<svg width="100%" height="220" viewBox="0 0 600 700" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 8px 20px rgba(0,0,0,0.4));">
<defs>
<linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" style="stop-color:#DAA520;stop-opacity:1" />
<stop offset="50%" style="stop-color:#F9E498;stop-opacity:1" />
<stop offset="100%" style="stop-color:#B8860B;stop-opacity:1" />
</linearGradient>
<radialGradient id="depthCenter">
<stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />
<stop offset="70%" style="stop-color:#F5F5F5;stop-opacity:1" />
<stop offset="100%" style="stop-color:#E8E8E8;stop-opacity:1" />
</radialGradient>
<filter id="shadow">
<feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
<feOffset dx="2" dy="2" result="offsetblur"/>
<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>
<circle cx="300" cy="260" r="200" fill="url(#depthCenter)"/>
<circle cx="300" cy="260" r="195" fill="none" stroke="#1A1A1A" stroke-width="9" filter="url(#shadow)"/>
<circle cx="300" cy="260" r="175" fill="none" stroke="url(#goldGrad)" stroke-width="5"/>
<line x1="300" y1="75" x2="300" y2="445" stroke="#B8B8B8" stroke-width="3"/>
<line x1="115" y1="260" x2="485" y2="260" stroke="#B8B8B8" stroke-width="3"/>
<g filter="url(#shadow)">
<path d="M 300 70 L 310 110 L 300 122 L 290 110 Z" fill="#1A1A1A"/>
<path d="M 300 70 L 310 110 L 300 105 L 290 110 Z" fill="#B8860B"/>
</g>
<g transform="translate(300, 260)" filter="url(#shadow)">
<path d="M -52 -54 L -12 -54 L -12 -42 L -38 -42 L -38 -8 L -18 -8 L -18 4 L -38 4 L -38 44 L -12 44 L -12 56 L -52 56 Z" fill="#1A1A1A"/>
<path d="M 12 -54 L 12 56 L 20 56 L 20 2 L 50 2 Q 70 2 70 -27 Q 70 -54 50 -54 Z M 20 -48 L 48 -48 Q 64 -48 64 -27 Q 64 -4 48 -4 L 20 -4 Z" fill="#1A1A1A"/>
</g>
<circle cx="300" cy="260" r="12" fill="#B8860B" filter="url(#shadow)"/>
<circle cx="300" cy="260" r="4" fill="#1A1A1A"/>
<text x="300" y="540" font-family="Georgia, serif" font-size="64" font-weight="400" fill="#1A1A1A" text-anchor="middle" letter-spacing="15">EL PASAJE</text>
<text x="300" y="585" font-family="Arial, sans-serif" font-size="18" font-weight="600" fill="url(#goldGrad)" text-anchor="middle" letter-spacing="10">3D STUDIO</text>
</svg>'''

DB_PATH = 'database/elpasaje.db'
ALLOWED_ID_TABLES = {'clientes', 'productos', 'proyectos_stl'}

ADMIN_USER = os.getenv('EP_ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('EP_ADMIN_PASSWORD', 'piedad2024')
OPS_USER = os.getenv('EP_OPS_USER', 'operaciones')
OPS_PASSWORD = os.getenv('EP_OPS_PASSWORD', 'fer2024')

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/elpasaje.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger('elpasaje')

def inject_css():
    st.markdown(f'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap');
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Pasaje_La_Piedad.JPG/1920px-Pasaje_La_Piedad.JPG");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .glass-card {{
        background: rgba(255,255,255,0.98);
        padding: 60px 50px;
        border-radius: 30px;
        border: 3px solid {COLORES['oro_viejo']};
        box-shadow: 0 40px 100px rgba(0,0,0,0.7);
        backdrop-filter: blur(25px);
    }}
    .metric-gold {{
        background: linear-gradient(135deg, {COLORES['oro_viejo']}, {COLORES['oro_brillante']});
        color: white;
        padding: 35px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 20px 50px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }}
    .metric-gold h2 {{
        margin: 0;
        font-size: 52px;
        color: white !important;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .metric-gold h4 {{
        margin: 0 0 15px 0;
        font-size: 16px;
        color: white !important;
        opacity: 0.95;
        letter-spacing: 2px;
    }}
    .stButton>button {{
        background: linear-gradient(135deg, {COLORES['oro_viejo']}, {COLORES['oro_brillante']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 16px 50px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 30px rgba(184, 134, 11, 0.4) !important;
    }}
    .stButton>button:hover {{
        transform: scale(1.08) translateY(-3px) !important;
        box-shadow: 0 20px 50px rgba(184, 134, 11, 0.6) !important;
    }}
    h1, h2, h3 {{
        color: {COLORES['oro_viejo']} !important;
        font-family: 'Cormorant Garamond', serif !important;
        letter-spacing: 3px !important;
    }}
    .producto-card {{
        background: white;
        border: 2px solid #e8e8e8;
        border-radius: 25px;
        padding: 30px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        height: 100%;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }}
    .producto-card:hover {{
        border-color: {COLORES['oro_viejo']};
        transform: translateY(-12px);
        box-shadow: 0 25px 50px rgba(184, 134, 11, 0.35);
    }}
    .categoria-header {{
        background: linear-gradient(135deg, {COLORES['oro_viejo']}, {COLORES['oro_brillante']});
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        margin: 30px 0 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
    .categoria-header h2 {{
        margin: 0;
        color: white !important;
        font-size: 32px;
        letter-spacing: 5px;
    }}
    </style>
    ''', unsafe_allow_html=True)

def init_db():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id TEXT PRIMARY KEY,
        nombre TEXT,
        tipo TEXT,
        usuario TEXT,
        password_hash TEXT,
        email TEXT,
        telefono TEXT,
        categoria TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS productos (
        id TEXT PRIMARY KEY,
        nombre TEXT,
        cliente_id TEXT,
        marca TEXT,
        descripcion TEXT,
        precio REAL,
        stock INTEGER,
        imagen TEXT,
        categoria TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS movimientos_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id TEXT,
        cambio INTEGER,
        motivo TEXT,
        usuario TEXT,
        fecha TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS proyectos_stl (
        id TEXT PRIMARY KEY,
        cliente_id TEXT,
        nombre TEXT,
        estado TEXT,
        prioridad TEXT,
        fecha_compromiso TEXT,
        notas TEXT,
        creado_en TEXT
    )''')
    
    c.execute("SELECT COUNT(*) FROM clientes")
    if c.fetchone()[0] == 0:
        # FAMILIA EL PASAJE (5)
        clientes_familia = [
            ('EP-FAM-001', 'Fernando Melómanos', 'FAMILIA', 'melomanos', hashlib.sha256('audio2024'.encode()).hexdigest(), 
             'fernando@elpasaje.com', '+54 11 5555-1001', 'LINEAS_FAMILIA'),
            ('EP-FAM-002', 'Olivia Coquette', 'FAMILIA', 'coquette', hashlib.sha256('olivia2024'.encode()).hexdigest(),
             'olivia@elpasaje.com', '+54 11 5555-1002', 'LINEAS_FAMILIA'),
            ('EP-FAM-003', 'Estudio Constantino', 'FAMILIA', 'constantino', hashlib.sha256('tech2024'.encode()).hexdigest(),
             'constantino@elpasaje.com', '+54 11 5555-1003', 'LINEAS_FAMILIA'),
            ('EP-FAM-004', 'Francisco Deportes', 'FAMILIA', 'francisco', hashlib.sha256('sport2024'.encode()).hexdigest(),
             'francisco@elpasaje.com', '+54 11 5555-1004', 'LINEAS_FAMILIA'),
        ]
        
        # SOCIOS B2B (4)
        clientes_b2b = [
            ('EP-B2B-001', 'Oasis Animal', 'B2B', 'oasis', hashlib.sha256('perros'.encode()).hexdigest(),
             'contacto@oasisanimal.com', '+54 11 5555-2001', 'SOCIOS_B2B'),
            ('EP-B2B-002', 'Oasis del Estero', 'B2B', 'estero', hashlib.sha256('plantas'.encode()).hexdigest(),
             'contacto@oasisestero.com', '+54 11 5555-2002', 'SOCIOS_B2B'),
            ('EP-B2B-003', 'Pharma DeLux', 'B2B', 'pharmadelux', hashlib.sha256('medicina'.encode()).hexdigest(),
             'lucas@pharmadelux.com', '+54 11 5555-2003', 'SOCIOS_B2B'),
            ('EP-B2B-004', 'Aviation Pro', 'B2B', 'aviation_pro', hashlib.sha256('nando2024'.encode()).hexdigest(),
             'nando@aviationpro.com', '+54 11 5555-2004', 'SOCIOS_B2B'),
        ]
        
        c.executemany("INSERT INTO clientes VALUES (?,?,?,?,?,?,?,?)", clientes_familia + clientes_b2b)
        
        # Productos ejemplo
        productos = [
            ('PROD-001', 'Soporte LP-Display Premium', 'EP-FAM-001', 'Melómanos',
             'Exhibidor minimalista para vinilos con cable management', 1500.00, 12, 
             'lineas_familia/melomanos/soporte_lp.jpg', 'LINEAS_FAMILIA'),
            
            ('PROD-002', 'Tarjeta QR Coquette Rosa', 'EP-FAM-002', 'Coquette',
             'Tarjeta personalizable con código QR, acabado Silk', 350.00, 100,
             'lineas_familia/coquette/tarjeta_qr.jpg', 'LINEAS_FAMILIA'),
            
            ('PROD-003', 'Soporte Técnico Modular', 'EP-FAM-003', 'Constantino',
             'Sistema de organización para herramientas técnicas', 2200.00, 8,
             'lineas_familia/constantino/soporte_tech.jpg', 'LINEAS_FAMILIA'),
            
            ('PROD-004', 'Llavero Porta-Bolsas', 'EP-B2B-001', 'Oasis Animal',
             'Llavero ergonómico con compartimento para bolsas', 450.00, 50,
             'socios_b2b/oasis/llavero.jpg', 'SOCIOS_B2B'),
            
            ('PROD-005', 'Maceta Hidropónica', 'EP-B2B-002', 'Oasis del Estero',
             'Sistema de cultivo hidropónico modular', 2800.00, 8,
             'socios_b2b/estero/maceta.jpg', 'SOCIOS_B2B'),
        ]
        
        c.executemany("INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?)", productos)
        conn.commit()
    
    conn.close()


def next_id(prefix, table_name):
    if table_name not in ALLOWED_ID_TABLES:
        raise ValueError('Tabla no permitida para generación de IDs')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = c.fetchone()[0] + 1
    conn.close()
    return f"{prefix}-{total:03d}"


def get_clientes(tipo=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT id, nombre, tipo, usuario, email, telefono, categoria FROM clientes"
    params = ()
    if tipo:
        query += " WHERE tipo=?"
        params = (tipo,)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def get_productos(categoria=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT id, nombre, cliente_id, marca, descripcion, precio, stock, imagen, categoria FROM productos"
    params = ()
    if categoria:
        query += " WHERE categoria=?"
        params = (categoria,)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def get_proyectos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        '''SELECT p.id, p.nombre, c.nombre as cliente, p.estado, p.prioridad, p.fecha_compromiso, p.notas, p.creado_en
           FROM proyectos_stl p
           LEFT JOIN clientes c ON p.cliente_id = c.id
           ORDER BY p.creado_en DESC''',
        conn,
    )
    conn.close()
    return df

def login(usuario, password):
    if usuario == ADMIN_USER and password == ADMIN_PASSWORD:
        logger.info('Login admin exitoso para usuario=%s', usuario)
        return {'logged': True, 'role': 'Admin', 'name': 'Dirección Arcano', 'id': 'ADMIN'}
    
    if usuario == OPS_USER and password == OPS_PASSWORD:
        logger.info('Login operaciones exitoso para usuario=%s', usuario)
        return {'logged': True, 'role': 'Admin', 'name': 'Operaciones Técnicas', 'id': 'OPS'}
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nombre, tipo, password_hash, categoria FROM clientes WHERE usuario=?", (usuario,))
    result = c.fetchone()
    conn.close()
    
    if result and result[3] == hashlib.sha256(password.encode()).hexdigest():
        logger.info('Login cliente exitoso para usuario=%s tipo=%s', usuario, result[2])
        return {'logged': True, 'role': result[2], 'name': result[1], 'id': result[0], 'categoria': result[4]}
    logger.warning('Login fallido para usuario=%s', usuario)
    return None

def get_imagen_url(ruta):
    """Retorna URL de imagen (local o fallback)"""
    local_path = Path('assets/productos') / ruta
    if local_path.exists():
        return str(local_path)

    fallbacks = {
        'melomanos': 'https://images.unsplash.com/photo-1603048588665-791ca8aea617?w=800',
        'coquette': 'https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=800',
        'constantino': 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800',
        'francisco': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800',
        'oasis': 'https://images.unsplash.com/photo-1544568100-847a948585b9?w=800',
        'estero': 'https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=800',
        'pharma': 'https://images.unsplash.com/photo-1587854692152-cbe660dbbb88?w=800',
        'aviation': 'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=800'
    }
    
    for key, url in fallbacks.items():
        if key in ruta:
            return url
    
    return 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800'


def save_uploaded_image(uploaded_file, categoria, marca):
    if uploaded_file is None:
        return None

    marca_slug = marca.strip().lower().replace(' ', '_') if marca else 'general'
    carpeta = Path('assets/productos') / categoria.lower() / marca_slug
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / uploaded_file.name
    destino.write_bytes(uploaded_file.getbuffer())
    return str(destino.relative_to('assets/productos'))

inject_css()
init_db()

if 'auth' not in st.session_state:
    st.session_state.auth = {'logged': False}
if 'menu' not in st.session_state:
    st.session_state.menu = '📊 Dashboard'

# LOGIN
if not st.session_state.auth['logged']:
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(LOGO_EP, unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center; color:#888; font-size:16px; letter-spacing:2px;">EPCC v{VERSION} | {FECHA}</p>', 
                   unsafe_allow_html=True)
        
        perfil = st.selectbox("🔐 Protocolo de Acceso", 
                             ["Dirección Arcano", "Líneas Familia", "Socios B2B", "Invitado"],
                             label_visibility="collapsed")
        
        if perfil != "Invitado":
            with st.form("login"):
                if perfil == "Dirección Arcano":
                    st.caption(f"**Usuarios:** {ADMIN_USER} / {OPS_USER}")
                elif perfil == "Líneas Familia":
                    st.caption("**Usuarios:** melomanos / coquette / constantino / francisco")
                else:
                    st.caption("**Usuarios:** oasis / estero / pharmadelux / aviation_pro")
                
                usuario = st.text_input("Usuario", placeholder="admin")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("🔓 Ingresar", use_container_width=True)
                
                if submit:
                    auth = login(usuario, password)
                    if auth:
                        st.session_state.auth = auth
                        st.rerun()
                    else:
                        st.error("❌ Credenciales inválidas")
        else:
            if st.button("🏛️ Explorar Catálogo", use_container_width=True):
                st.session_state.auth = {'logged': True, 'role': 'Public', 'name': 'Invitado', 'id': 'PUBLIC'}
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("© 2026 El Pasaje 3D Studio | Bartolomé Mitre 1500, Buenos Aires")

# APLICACIÓN
else:
    with st.sidebar:
        st.markdown(f'<div style="transform: scale(0.35); margin: -120px -140px -100px -140px;">{LOGO_EP}</div>', 
                   unsafe_allow_html=True)
        st.markdown(f"### 👤 {st.session_state.auth['name']}")
        st.caption(f"**Rol:** {st.session_state.auth['role']}")
        st.caption(f"**Sistema:** EPCC v{VERSION}")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.auth = {'logged': False}
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.auth['role'] == 'Admin':
            st.session_state.menu = st.radio("Navegación", 
                ["📊 Dashboard", "🛍️ Catálogo Completo", "📦 Inventario", "👥 Gestión", "🎨 Proyectos STL"],
                label_visibility="collapsed")
    
    st.title("🏛️ El Pasaje 3D Studio")
    
    if st.session_state.auth['role'] == 'Admin':
        if st.session_state.menu == "📊 Dashboard":
            st.success(f"✅ Bienvenid@, {st.session_state.auth['name']}")

            with st.expander("🚀 Pasos rápidos para operar hoy", expanded=True):
                st.markdown("""
                1. **Gestión** → crear cliente nuevo (tipo FAMILIA o B2B).  
                2. **Inventario** → alta de producto y carga de foto.  
                3. **Inventario** → ajuste de stock con motivo.  
                4. **Proyectos STL** → crear proyecto y mover estado.  
                5. **Catálogo Completo** → verificar cómo se ve publicado.
                """)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div class="metric-gold"><h4>💰 INGRESOS</h4><h2>$0</h2></div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-gold" style="background: linear-gradient(135deg, #4682B4, #5F9EA0);"><h4>📦 PEDIDOS</h4><h2>0</h2></div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-gold" style="background: linear-gradient(135deg, #28a745, #218838);"><h4>🎨 PROYECTOS</h4><h2>0</h2></div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="metric-gold" style="background: linear-gradient(135deg, #dc3545, #c82333);"><h4>⚠️ ALERTAS</h4><h2>0</h2></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            conn = sqlite3.connect(DB_PATH)
            familia = pd.read_sql("SELECT COUNT(*) as total FROM clientes WHERE categoria='LINEAS_FAMILIA'", conn)
            b2b = pd.read_sql("SELECT COUNT(*) as total FROM clientes WHERE categoria='SOCIOS_B2B'", conn)
            conn.close()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"👨‍👩‍👧‍👦 **Líneas Familia:** {familia['total'].values[0]} marcas")
            with col2:
                st.info(f"🤝 **Socios B2B:** {b2b['total'].values[0]} empresas")
            
            st.success("✅ Sistema operativo | Base de datos: elpasaje.db | IDs: EP-XXX-XXX")
            
        elif st.session_state.menu == "🛍️ Catálogo Completo":
            conn = sqlite3.connect(DB_PATH)
            
            st.markdown('<div class="categoria-header"><h2>👨‍👩‍👧‍👦 LÍNEAS FAMILIA EL PASAJE</h2></div>', unsafe_allow_html=True)
            
            productos_familia = pd.read_sql("SELECT * FROM productos WHERE categoria='LINEAS_FAMILIA'", conn)
            
            if not productos_familia.empty:
                for i in range(0, len(productos_familia), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(productos_familia):
                            prod = productos_familia.iloc[i + j]
                            with cols[j]:
                                st.markdown('<div class="producto-card">', unsafe_allow_html=True)
                                st.image(get_imagen_url(prod['imagen']), use_container_width=True)
                                st.markdown(f"### {prod['nombre']}")
                                st.caption(f"🏷️ {prod['marca']}")
                                st.write(prod['descripcion'])
                                st.markdown(f"**💰 ${prod['precio']:,.0f}**")
                                st.caption(f"📦 Stock: {prod['stock']}")
                                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="categoria-header"><h2>🤝 SOCIOS B2B</h2></div>', unsafe_allow_html=True)
            
            productos_b2b = pd.read_sql("SELECT * FROM productos WHERE categoria='SOCIOS_B2B'", conn)
            
            if not productos_b2b.empty:
                for i in range(0, len(productos_b2b), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(productos_b2b):
                            prod = productos_b2b.iloc[i + j]
                            with cols[j]:
                                st.markdown('<div class="producto-card">', unsafe_allow_html=True)
                                st.image(get_imagen_url(prod['imagen']), use_container_width=True)
                                st.markdown(f"### {prod['nombre']}")
                                st.caption(f"🏷️ {prod['marca']}")
                                st.write(prod['descripcion'])
                                st.markdown(f"**💰 ${prod['precio']:,.0f}**")
                                st.caption(f"📦 Stock: {prod['stock']}")
                                st.markdown('</div>', unsafe_allow_html=True)
            
            conn.close()

        elif st.session_state.menu == "📦 Inventario":
            st.subheader("📦 Inventario")
            productos = get_productos()
            st.dataframe(productos, use_container_width=True, hide_index=True)

            st.markdown("### ➕ Alta de producto")
            clientes = get_clientes()
            clientes_map = {f"{row['nombre']} ({row['id']})": row['id'] for _, row in clientes.iterrows()}
            with st.form("alta_producto"):
                nombre = st.text_input("Nombre")
                cliente_sel = st.selectbox("Cliente", list(clientes_map.keys()))
                marca = st.text_input("Marca")
                descripcion = st.text_area("Descripción")
                precio = st.number_input("Precio", min_value=0.0, step=100.0)
                stock = st.number_input("Stock inicial", min_value=0, step=1)
                categoria = st.selectbox("Categoría", ["LINEAS_FAMILIA", "SOCIOS_B2B"])
                imagen_file = st.file_uploader("Foto del producto (opcional)", type=["png", "jpg", "jpeg", "webp"])
                imagen_manual = st.text_input("Ruta imagen manual (opcional)", value="")
                submit_prod = st.form_submit_button("Guardar producto", use_container_width=True)
                if submit_prod and nombre and marca:
                    try:
                        prod_id = next_id("PROD", "productos")
                        imagen = save_uploaded_image(imagen_file, categoria, marca) or imagen_manual or f"{categoria.lower()}/default.jpg"
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO productos VALUES (?,?,?,?,?,?,?,?,?)",
                            (prod_id, nombre, clientes_map[cliente_sel], marca, descripcion, float(precio), int(stock), imagen, categoria),
                        )
                        conn.commit()
                        conn.close()
                        logger.info('Alta producto id=%s cliente=%s', prod_id, clientes_map[cliente_sel])
                        st.success(f"Producto {prod_id} creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo guardar el producto: {e}")

            st.markdown("### 🔄 Ajuste de stock")
            if not productos.empty:
                prod_map = {f"{row['nombre']} ({row['id']})": row['id'] for _, row in productos.iterrows()}
                with st.form("ajuste_stock"):
                    prod_sel = st.selectbox("Producto", list(prod_map.keys()))
                    cambio = st.number_input("Cambio (usar negativo para descontar)", value=0, step=1)
                    motivo = st.text_input("Motivo")
                    submit_stock = st.form_submit_button("Aplicar ajuste", use_container_width=True)
                    if submit_stock and cambio != 0 and motivo:
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute("SELECT stock FROM productos WHERE id=?", (prod_map[prod_sel],))
                            actual = c.fetchone()
                            if not actual:
                                raise ValueError('Producto inexistente')
                            nuevo_stock = int(actual[0]) + int(cambio)
                            if nuevo_stock < 0:
                                raise ValueError('El stock no puede quedar negativo')

                            c.execute("UPDATE productos SET stock = ? WHERE id=?", (nuevo_stock, prod_map[prod_sel]))
                            c.execute(
                                "INSERT INTO movimientos_stock (producto_id, cambio, motivo, usuario, fecha) VALUES (?,?,?,?,?)",
                                (prod_map[prod_sel], int(cambio), motivo, st.session_state.auth['id'], datetime.now().isoformat()),
                            )
                            conn.commit()
                            conn.close()
                            logger.info('Ajuste stock producto=%s cambio=%s usuario=%s', prod_map[prod_sel], int(cambio), st.session_state.auth['id'])
                            st.success("Stock actualizado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo actualizar el stock: {e}")

            conn = sqlite3.connect(DB_PATH)
            movimientos = pd.read_sql("SELECT producto_id, cambio, motivo, usuario, fecha FROM movimientos_stock ORDER BY id DESC LIMIT 20", conn)
            conn.close()
            st.markdown("### 🧾 Últimos movimientos")
            st.dataframe(movimientos, use_container_width=True, hide_index=True)

        elif st.session_state.menu == "👥 Gestión":
            st.subheader("👥 Gestión de clientes")
            tab1, tab2 = st.tabs(["Clientes", "Alta cliente"])
            with tab1:
                tipo_filtro = st.selectbox("Filtrar por tipo", ["TODOS", "FAMILIA", "B2B"])
                df_clientes = get_clientes(None if tipo_filtro == "TODOS" else tipo_filtro)
                st.dataframe(df_clientes, use_container_width=True, hide_index=True)
            with tab2:
                with st.form("alta_cliente"):
                    nombre = st.text_input("Nombre")
                    tipo = st.selectbox("Tipo", ["FAMILIA", "B2B"])
                    usuario = st.text_input("Usuario")
                    password = st.text_input("Contraseña temporal", type="password")
                    email = st.text_input("Email")
                    telefono = st.text_input("Teléfono")
                    categoria = "LINEAS_FAMILIA" if tipo == "FAMILIA" else "SOCIOS_B2B"
                    submit_cliente = st.form_submit_button("Crear cliente", use_container_width=True)
                    if submit_cliente and nombre and usuario and password:
                        try:
                            pref = "EP-FAM" if tipo == "FAMILIA" else "EP-B2B"
                            cliente_id = next_id(pref, "clientes")
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO clientes VALUES (?,?,?,?,?,?,?,?)",
                                (cliente_id, nombre, tipo, usuario, hashlib.sha256(password.encode()).hexdigest(), email, telefono, categoria),
                            )
                            conn.commit()
                            conn.close()
                            logger.info('Alta cliente id=%s tipo=%s usuario=%s', cliente_id, tipo, usuario)
                            st.success(f"Cliente {cliente_id} creado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo crear el cliente: {e}")

        elif st.session_state.menu == "🎨 Proyectos STL":
            st.subheader("🎨 Proyectos STL")
            proyectos = get_proyectos()
            st.dataframe(proyectos, use_container_width=True, hide_index=True)

            clientes = get_clientes()
            if not clientes.empty:
                clientes_map = {f"{row['nombre']} ({row['id']})": row['id'] for _, row in clientes.iterrows()}
                with st.form("alta_proyecto"):
                    nombre = st.text_input("Nombre del proyecto")
                    cliente_sel = st.selectbox("Cliente", list(clientes_map.keys()))
                    prioridad = st.selectbox("Prioridad", ["baja", "media", "alta"])
                    fecha_compromiso = st.date_input("Fecha compromiso")
                    notas = st.text_area("Notas")
                    submit_proy = st.form_submit_button("Crear proyecto", use_container_width=True)
                    if submit_proy and nombre:
                        try:
                            proyecto_id = next_id("STL", "proyectos_stl")
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO proyectos_stl VALUES (?,?,?,?,?,?,?,?)",
                                (proyecto_id, clientes_map[cliente_sel], nombre, "nuevo", prioridad, str(fecha_compromiso), notas, datetime.now().isoformat()),
                            )
                            conn.commit()
                            conn.close()
                            logger.info('Alta proyecto id=%s cliente=%s prioridad=%s', proyecto_id, clientes_map[cliente_sel], prioridad)
                            st.success(f"Proyecto {proyecto_id} creado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo crear el proyecto: {e}")

            if not proyectos.empty:
                estados = ["nuevo", "en_revision", "en_produccion", "entregado"]
                with st.form("actualizar_estado"):
                    proyecto_sel = st.selectbox("Proyecto", proyectos['id'].tolist())
                    nuevo_estado = st.selectbox("Nuevo estado", estados)
                    submit_estado = st.form_submit_button("Actualizar estado", use_container_width=True)
                    if submit_estado:
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute("UPDATE proyectos_stl SET estado=? WHERE id=?", (nuevo_estado, proyecto_sel))
                            conn.commit()
                            conn.close()
                            logger.info('Cambio estado proyecto=%s estado=%s', proyecto_sel, nuevo_estado)
                            st.success("Estado actualizado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo actualizar el estado: {e}")

        else:
            st.info(f"✨ Módulo en desarrollo: {st.session_state.menu}")
    
    elif st.session_state.auth['role'] in ['FAMILIA', 'B2B']:
        st.success(f"✅ Portal: {st.session_state.auth['name']}")
        
        conn = sqlite3.connect(DB_PATH)
        productos = pd.read_sql("SELECT * FROM productos WHERE cliente_id=?", conn, params=(st.session_state.auth['id'],))
        conn.close()
        
        if not productos.empty:
            st.subheader("🛍️ Tus Productos")
            for _, prod in productos.iterrows():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(get_imagen_url(prod['imagen']), use_container_width=True)
                with col2:
                    st.markdown(f"### {prod['nombre']}")
                    st.write(prod['descripcion'])
                    st.markdown(f"**${prod['precio']:,.0f}** | Stock: {prod['stock']}")
        else:
            st.info("📭 No hay productos asignados aún")
    
    else:
        st.caption("Manufactura Aditiva de Alta Precisión | Bartolomé Mitre 1500, Buenos Aires")
        st.info("🔐 Iniciá sesión para acceder al sistema completo")
    
    st.markdown("---")
    st.caption(f"© 2026 El Pasaje 3D Studio | EPCC v{VERSION}")

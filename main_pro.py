import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="El Pasaje - Magnitud Pro", layout="wide")

# Estilo de Vanguardia
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .main-header { color: #2C3E50; font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; border-bottom: 3px solid #3498DB; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #E9ECEF; padding: 15px; border-radius: 12px; }
    .stSidebar { background-color: #F1F3F5; }
    </style>
    """, unsafe_allow_html=True)

engine = create_engine("sqlite:///elpasaje_v2.db")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None})

if not st.session_state['auth']:
    st.markdown("<div class='main-header'>🏛️ El Pasaje - Ecosistema</div>", unsafe_allow_html=True)
    u = st.text_input("Email")
    p = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        user = pd.read_sql(f"SELECT name FROM tenants WHERE email='{u}' AND password='{p}'", engine)
        if not user.empty:
            st.session_state.update({'auth': True, 'user': user['name'].iloc[0]})
            st.rerun()
        else: st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.title(f"👤 {st.session_state['user']}")
menu = st.sidebar.radio("NAVEGACIÓN", ["📊 Dashboard Finanzas", "📦 Inventario Real", "🤝 Línea Solidaria"])

if menu == "📊 Dashboard Finanzas":
    st.markdown("<div class='main-header'>📊 Dashboard de Finanzas</div>", unsafe_allow_html=True)
    df = pd.read_sql("SELECT client_id as Socio, SUM(price * stock) as Valor_Stock FROM products GROUP BY client_id", engine)
    c1, c2 = st.columns([2, 1])
    with c1: st.bar_chart(df.set_index('Socio'))
    with c2: st.write("### Desglose por Línea"); st.dataframe(df, use_container_width=True)

elif menu == "📦 Inventario Real":
    st.markdown("<div class='main-header'>📦 Control de Stock</div>", unsafe_allow_html=True)
    # Aquí aparecen el Organizador Kaizen y el Cubo Infinito rescatados
    df_p = pd.read_sql("SELECT sku, name, price, stock, client_id FROM products", engine)
    st.dataframe(df_p, use_container_width=True)

elif menu == "🤝 Línea Solidaria":
    st.markdown("<div class='main-header'>🤝 Impacto Social</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Oasis Animal", "$ 4.500", "Llaveros Huellita")
    col2.metric("Aviation (Nando)", "En Producción", "Nuevas Maquetas")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.update({'auth': False, 'user': None}); st.rerun()

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="El Pasaje - Ecosistema", layout="wide")
st.markdown("<style>.stApp { background-color: white; color: #31333F; }</style>", unsafe_allow_html=True)

engine = create_engine("sqlite:///elpasaje_v2.db")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None})

if not st.session_state['auth']:
    st.title("🏛️ El Pasaje - Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if (u == "admin" and p == "123") or (u == "admin@elpasaje.com" and p == "admin123"):
            st.session_state.update({'auth': True, 'user': "Admin"})
            st.rerun()
        else: st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.title(f"👤 {st.session_state['user']}")
menu = st.sidebar.radio("Navegación", ["📈 Finanzas", "📦 Stock Real", "🤝 La Solidaria"])

if menu == "📈 Finanzas":
    st.header("📈 Resumen de Magnitud Real")
    try:
        df_inv = pd.read_sql("SELECT client_id as Línea, SUM(price * stock) as Valor_Inventario FROM products GROUP BY client_id", engine)
        if not df_inv.empty:
            st.bar_chart(df_inv.set_index('Línea'))
            st.write("### Valor de Stock por Línea")
            st.dataframe(df_inv, use_container_width=True)
        else: st.warning("No hay productos cargados en la base de datos.")
    except: st.error("Error al conectar con la base de datos.")

elif menu == "📦 Stock Real":
    st.header("📦 Inventario de todas las Líneas")
    try:
        df = pd.read_sql("SELECT sku, name, price, stock, client_id FROM products", engine)
        st.dataframe(df, use_container_width=True)
    except: st.error("Aún no hay datos en la tabla de productos.")

elif menu == "🤝 La Solidaria":
    st.header("🤝 La Solidaria - Impacto Social")
    try:
        prod_sol = pd.read_sql("SELECT * FROM products WHERE client_id='la_solidaria'", engine)
        c1, c2 = st.columns(2)
        c1.metric("Productos Solidarios", len(prod_sol))
        c2.metric("Impacto Social (Est.)", f"$ {prod_sol['price'].sum() * 0.2:.2f}")
        st.write("### Catálogo Solidario (Oasis Animal / Niños)")
        st.dataframe(prod_sol, use_container_width=True)
    except: st.warning("Cargando línea solidaria...")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.update({'auth': False, 'user': None}); st.rerun()

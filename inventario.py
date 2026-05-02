import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

def mostrar_panel():
    engine = create_engine("sqlite:///elpasaje_v2.db")
    st.subheader("📦 Gestión de Inventario Real")
    
    df = pd.read_sql("SELECT sku, name, price, stock, client_id FROM products", engine)
    
    busqueda = st.text_input("🔍 Buscar producto (Kaizen, Cubo, Moño...)")
    if busqueda:
        df = df[df['name'].str.contains(busqueda, case=False)]
    
    st.table(df)

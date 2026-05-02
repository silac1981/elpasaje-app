import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

engine = create_engine("sqlite:///elpasaje_v2.db")

def procesar_venta(sku, nombre, precio, client_id):
    with engine.begin() as conn:
        # 1. Bajamos el stock
        conn.execute(f"UPDATE products SET stock = stock - 1 WHERE sku = '{sku}' AND stock > 0")
        # 2. Registramos la venta
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(f"INSERT INTO sales (sku, product_name, price, client_id, date) VALUES ('{sku}', '{nombre}', {precio}, '{client_id}', '{fecha}')")

# Esta lógica se integra en la pestaña "Inventario Central"
st.markdown("### ⚡ Venta Rápida (Showroom)")
df_v = pd.read_sql("SELECT sku, name, price, stock, client_id FROM products WHERE stock > 0", engine)

for index, row in df_v.iterrows():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"**{row['name']}** ({row['sku']}) - ${row['price']:,.2f}")
    with col2:
        st.write(f"Stock: {row['stock']}")
    with col3:
        if st.button(f"Vender ✅", key=f"btn_{row['sku']}"):
            procesar_venta(row['sku'], row['name'], row['price'], row['client_id'])
            st.toast(f"¡Venta de {row['name']} registrada!")
            st.rerun()

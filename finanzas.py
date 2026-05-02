import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

def mostrar_dashboard():
    engine = create_engine("sqlite:///elpasaje_v2.db")
    st.subheader("📊 Análisis de Magnitud Financiera")
    
    try:
        df = pd.read_sql("SELECT client_id as Socio, SUM(price * stock) as Total FROM products GROUP BY client_id", engine)
        
        # Diccionario para nombres lindos
        nombres = {
            "admin": "Alejandra (Stock Propio)",
            "la_solidaria": "Línea Solidaria (Impacto)",
            "olivia_coquette": "Olivia - Coquette",
            "francisco_sport": "Francisco - Sport"
        }
        df['Socio'] = df['Socio'].map(nombres).fillna(df['Socio'])
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(df.set_index('Socio'))
        with col2:
            st.dataframe(df)
            
        st.success(f"💰 Valor Total del Inventario: ${df['Total'].sum():,.2f}")
    except:
        st.warning("Aún no hay datos para procesar en el dashboard.")

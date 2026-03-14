import streamlit as st
import ep_core as core
import pandas as pd

st.set_page_config(page_title="El Pasaje - Enterprise 2.0", layout="wide")

def main():
    st.title("Plataforma El Pasaje - Gestión B2B")
    st.sidebar.info("Versión: 2.0 Enterprise (Codex-Compliant)")
    
    # Validación de integridad usando el nuevo ep_core
    if core.check_system_integrity():
        st.success("Conectado a la Base de Datos elpasaje.db")
        
        tab1, tab2 = st.tabs(["Inventario", "Proyectos STL"])
        with tab1:
            st.write("Cargando catálogo de materiales...")
            # Aquí irá la lógica de carga masiva de Línea Olivia
    else:
        st.error("Error de integridad: Base de datos no encontrada.")

if __name__ == "__main__":
    main()

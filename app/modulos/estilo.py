import streamlit as st

def aplicar_diseno():
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #2C3E50; }
        .main-header { 
            color: #1E3A8A; 
            font-size: 2.5rem; 
            font-weight: 850; 
            border-bottom: 4px solid #3498DB; 
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .stMetric { 
            background-color: #F0F4F8; 
            border: 1px solid #D1D5DB; 
            padding: 20px; 
            border-radius: 15px; 
            box-shadow: 3px 3px 10px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

def obtener_nombre_lindo(client_id):
    dict_nombres = {
        "admin": "🏛️ Administración (Ale)",
        "olivia_coquette": "🎀 Olivia - Coquette",
        "francisco_sport": "⚽ Francisco - Sport",
        "la_solidaria": "🤝 Línea Solidaria",
        "Aviation.com": "✈️ Aviation (Nando)",
        "Pharma_DeLux.com": "💊 Pharma DeLux (Lucas)",
        "project_hub": "🔧 Project Hub (Desarrollo)"
    }
    return dict_nombres.get(client_id, f"📦 {client_id}")

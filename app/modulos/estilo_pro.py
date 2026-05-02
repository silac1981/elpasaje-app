import streamlit as st

def aplicar_estilo_profesional():
    st.markdown("""
        <style>
        .stApp { background-color: #F4F7FA; }
        .main-header { 
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white; padding: 30px; border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-bottom: 30px;
            text-align: center; font-family: 'Inter', sans-serif;
        }
        .metric-card {
            background: white; padding: 25px; border-radius: 15px;
            border-top: 6px solid #3B82F6; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            text-align: center;
        }
        .stButton>button {
            border-radius: 50px; background: #1E3A8A; color: white;
            font-weight: 600; padding: 10px 25px; border: none;
        }
        </style>
    """, unsafe_allow_html=True)

def get_linea_config(client_id):
    configs = {
        "olivia_coquette": {"nombre": "🎀 Olivia - Coquette", "color": "#FFD1DC"},
        "francisco_sport": {"nombre": "⚽ Francisco - Sport", "color": "#87CEEB"},
        "la_solidaria": {"nombre": "🤝 Línea Solidaria", "color": "#98FB98"},
        "Aviation.com": {"nombre": "✈️ Aviation (Nando)", "color": "#A9A9A9"},
        "Pharma_DeLux.com": {"nombre": "💊 Pharma DeLux (Lucas)", "color": "#FFB347"},
        "admin": {"nombre": "🏛️ Administración", "color": "#1E3A8A"}
    }
    return configs.get(client_id, {"nombre": client_id, "color": "#FFFFFF"})

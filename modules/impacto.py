"""modules/impacto.py — Panel de Impacto Social."""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db import engine


def render():
    st.markdown("<div class='main-header'><h1>🌱 Impacto Social</h1><p>Transparencia total · Fondos solidarios</p></div>", unsafe_allow_html=True)
    from datetime import datetime
    FONDOS = {
        "refugio_oasis":    {"nombre": "Refugio Oasis Animal", "emoji": "🐾", "color": "#F472B6", "meta": 50000},
        "mentes_brillantes":{"nombre": "Mentes Brillantes",    "emoji": "🧠", "color": "#818CF8", "meta": 40000},
        "fondo_general":    {"nombre": "Fondo General",        "emoji": "❤️", "color": "#FB7185", "meta": 30000},
    }
    try:
        dons = pd.read_sql("SELECT * FROM donations ORDER BY fecha DESC", engine)
    except Exception:
        dons = pd.DataFrame()
    cols = st.columns(3)
    for col, (fondo_id, f) in zip(cols, FONDOS.items()):
        recaudado = dons[dons["fondo"] == fondo_id]["monto"].sum() if not dons.empty else 0
        pct = min(recaudado / f["meta"] * 100, 100)
        faltan = max(f["meta"] - recaudado, 0)
        with col:
            st.markdown(f"<div style='background:white;border-radius:18px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,0.08);border-top:5px solid {f['color']};margin-bottom:16px;'><div style='font-size:2rem;'>{f['emoji']}</div><div style='font-size:1rem;font-weight:700;color:#1a1a2e;margin:8px 0 2px;'>{f['nombre']}</div><div style='font-size:2rem;font-weight:700;color:{f['color']};font-family:Cormorant Garamond,serif;'>${recaudado:,.0f}</div><div style='font-size:0.78rem;color:#9CA3AF;margin-bottom:12px;'>Meta mensual: ${f['meta']:,.0f}</div><div style='background:#F3F4F6;border-radius:999px;height:14px;overflow:hidden;'><div style='width:{pct:.0f}%;background:{f['color']};height:100%;border-radius:999px;'></div></div><div style='font-size:0.75rem;color:#6B7280;margin-top:6px;'>{'🎉 ¡Meta alcanzada!' if faltan == 0 else f'Faltan ${faltan:,.0f}'}</div></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### ➕ Registrar Donacion Manual")
    dc1, dc2, dc3, dc4 = st.columns([1.5, 1, 1, 1.5])
    with dc1:
        fondo_sel = st.selectbox("Fondo destino", list(FONDOS.keys()), format_func=lambda x: f"{FONDOS[x]['emoji']} {FONDOS[x]['nombre']}")
    with dc2:
        tipo_don = st.selectbox("Tipo", ["urna","qr","redondeo"], format_func=lambda x: {"urna":"🏺 Urna","qr":"📱 QR","redondeo":"🔄 Redondeo"}[x])
    with dc3:
        monto_don = st.number_input("Monto ($)", min_value=1.0, step=50.0, value=500.0)
    with dc4:
        desc_don = st.text_input("Descripcion", placeholder="Ej: Urna fin de semana")
    if st.button("💚 REGISTRAR DONACION", type="primary"):
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO donations (fondo, monto, tipo, descripcion, fecha) VALUES (:fondo, :monto, :tipo, :desc, :fecha)"),
                {"fondo": fondo_sel, "monto": monto_don, "tipo": tipo_don, "desc": desc_don, "fecha": str(datetime.now().date())}
            )
            conn.commit()
        st.success(f"✅ ${monto_don:,.0f} registrados en {FONDOS[fondo_sel]['nombre']} 💚")
        st.rerun()
    st.markdown("### 📋 Historial de Donaciones")
    if dons.empty:
        st.info("Aun no hay donaciones. ¡La primera puede ser hoy! 💚")
    else:
        TIPO_ICON = {"urna":"🏺","qr":"📱","redondeo":"🔄","producto":"🌱"}
        for _, row in dons.head(20).iterrows():
            icon = TIPO_ICON.get(row["tipo"], "💰")
            finfo = FONDOS.get(row["fondo"], {"nombre": row["fondo"], "emoji": "❓", "color": "#ccc"})
            st.markdown(f"<div style='background:white;border-radius:12px;padding:14px 18px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid {finfo['color']};'><div style='display:flex;justify-content:space-between;align-items:center;'><div><b>{icon} {finfo['emoji']} {finfo['nombre']}</b><span style='margin-left:10px;font-size:0.75rem;color:#6B7280;'>{row['tipo'].upper()} · {row['fecha']}</span><div style='font-size:0.78rem;color:#9CA3AF;margin-top:3px;'>{row.get('descripcion','') or ''}</div></div><div style='font-size:1.4rem;font-weight:700;color:{finfo['color']};'>${row['monto']:,.0f}</div></div></div>", unsafe_allow_html=True)

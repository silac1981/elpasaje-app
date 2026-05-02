"""modules/clientes.py — Gestión de clientes y señales de mercado."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine


def render():
    st.markdown("<div class='main-header'><h1>👥 Gestión de Clientes</h1><p>Segmentación · Potencial · Canal de entrada · Señales de mercado</p></div>", unsafe_allow_html=True)

    try:
        clientes = pd.read_sql("""
            SELECT id, name, email, telefono, tipo, sector,
                   segmento, lead_source, potencial, canal_preferido,
                   ciudad, rubro, notas_agente, es_cliente_real,
                   fecha_primer_contacto, linea_interes, activo
            FROM tenants
            WHERE tipo IN ('cliente_externo', 'b2b', 'socio', 'familia', 'admin')
            ORDER BY fecha_primer_contacto DESC
        """, engine)
    except Exception as e:
        clientes = pd.DataFrame()
        st.warning(f"Error cargando clientes: {e}")

    total = len(clientes)
    reales = len(clientes[clientes["es_cliente_real"] == 1]) if not clientes.empty and "es_cliente_real" in clientes.columns else 0
    alto_potencial = len(clientes[clientes["potencial"] == "Alto"]) if not clientes.empty and "potencial" in clientes.columns else 0
    b2b = len(clientes[clientes["segmento"] == "B2B"]) if not clientes.empty and "segmento" in clientes.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    for col, title, val, sub, color in [
        (k1, "👥 Total Contactos",   str(total),          "en el ecosistema",      "#1E3A8A"),
        (k2, "💰 Clientes Reales",   str(reales),         "con compra registrada", "#059669"),
        (k3, "⭐ Alto Potencial",    str(alto_potencial), "para próximo contacto", "#7C3AED"),
        (k4, "🤝 Canal B2B",         str(b2b),            "empresas y socios",     "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📋 Ver Clientes", "➕ Nuevo Cliente", "📡 Señales de Mercado"])

    with tab1:
        if clientes.empty:
            st.info("No hay clientes cargados todavía.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_seg = st.selectbox("Segmento", ["Todos"] + sorted(clientes["segmento"].dropna().unique().tolist()) if "segmento" in clientes.columns else ["Todos"])
            with col_f2:
                filtro_pot = st.selectbox("Potencial", ["Todos", "Alto", "Medio", "Bajo"])
            with col_f3:
                filtro_real = st.selectbox("Estado", ["Todos", "Clientes reales", "Contactos"])
            df_filtrado = clientes.copy()
            if filtro_seg != "Todos" and "segmento" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["segmento"] == filtro_seg]
            if filtro_pot != "Todos" and "potencial" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["potencial"] == filtro_pot]
            if filtro_real == "Clientes reales" and "es_cliente_real" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["es_cliente_real"] == 1]
            elif filtro_real == "Contactos" and "es_cliente_real" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["es_cliente_real"] == 0]
            st.markdown(f"<div style='font-size:0.8rem;color:#6B7280;margin-bottom:12px;'>{len(df_filtrado)} resultado/s</div>", unsafe_allow_html=True)
            for _, row in df_filtrado.iterrows():
                pot_color = {"Alto": "#059669", "Medio": "#D97706", "Bajo": "#EF4444"}.get(row.get("potencial",""), "#6B7280")
                real_badge = "✅ Cliente real" if row.get("es_cliente_real") == 1 else "📞 Contacto"
                real_color = "#059669" if row.get("es_cliente_real") == 1 else "#6B7280"
                with st.expander(f"{row['name']}  ·  {row.get('segmento','')}  ·  {row.get('linea_interes','')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Email:** {row.get('email','—')}")
                        st.markdown(f"**Teléfono:** {row.get('telefono','—')}")
                        st.markdown(f"**Ciudad:** {row.get('ciudad','—')}")
                    with c2:
                        st.markdown(f"**Rubro:** {row.get('rubro','—')}")
                        st.markdown(f"**Canal preferido:** {row.get('canal_preferido','—')}")
                        st.markdown(f"**Fuente:** {row.get('lead_source','—')}")
                    with c3:
                        st.markdown(f"<span style='color:{pot_color};font-weight:700;'>⭐ Potencial: {row.get('potencial','—')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:{real_color};'>🏷️ {real_badge}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Primer contacto:** {row.get('fecha_primer_contacto','—')}")
                    if row.get("notas_agente"):
                        st.markdown(f"<div style='background:#F0F4FF;border-left:3px solid #1E3A8A;padding:10px 14px;border-radius:8px;font-size:0.85rem;margin-top:8px;'>🤖 <b>Nota del agente:</b> {row['notas_agente']}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-title'>➕ Cargar nuevo contacto o cliente</div>", unsafe_allow_html=True)
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nc_nombre   = st.text_input("Nombre o Razón Social *")
                nc_email    = st.text_input("Email")
                nc_telefono = st.text_input("Teléfono / WhatsApp")
                nc_ciudad   = st.text_input("Ciudad", value="Buenos Aires")
                nc_rubro    = st.text_input("Rubro / Sector")
            with c2:
                nc_segmento  = st.selectbox("Segmento *", ["B2C", "B2B", "Corporativo", "Institucional"])
                nc_potencial = st.selectbox("Potencial *", ["Alto", "Medio", "Bajo"])
                nc_canal     = st.selectbox("Canal preferido", ["WhatsApp", "Instagram", "Presencial", "Email", "Recomendación"])
                nc_fuente    = st.text_input("¿Cómo llegó?", placeholder="Ej: Red de Nando, Laura Cava, Feria")
                nc_linea     = st.text_input("Línea de interés", placeholder="Ej: Magnitud 19, Oasis Animal")
            nc_es_real = st.checkbox("¿Ya realizó una compra?")
            nc_notas   = st.text_area("Notas (para el agente IA)", placeholder="Describí brevemente quién es y qué le interesa")
            submitted  = st.form_submit_button("💾 GUARDAR CLIENTE", use_container_width=True, type="primary")
            if submitted:
                if not nc_nombre:
                    st.error("El nombre es obligatorio.")
                else:
                    import uuid, re
                    nc_id = re.sub(r"[^a-z0-9_]", "_", nc_nombre.lower().strip())[:30] + "_" + str(uuid.uuid4())[:6]
                    nc_email_val = nc_email.strip().lower() or f"{nc_id}@noemail.com"
                    hoy_str = datetime.now().strftime("%Y-%m-%d")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO tenants
                                (id, name, email, password, telefono, tipo, sector,
                                 fecha_alta, activo, segmento, lead_source, potencial,
                                 canal_preferido, ciudad, rubro, notas_agente,
                                 es_cliente_real, fecha_primer_contacto, linea_interes)
                                VALUES
                                (:id,:name,:email,:pwd,:tel,:tipo,:sector,
                                 :fecha,:activo,:seg,:source,:pot,
                                 :canal,:ciudad,:rubro,:notas,
                                 :real,:fcontacto,:linea)
                            """), {
                                "id": nc_id, "name": nc_nombre, "email": nc_email_val,
                                "pwd": "pendiente", "tel": nc_telefono, "tipo": nc_segmento.lower(),
                                "sector": nc_rubro, "fecha": hoy_str, "activo": 1,
                                "seg": nc_segmento, "source": nc_fuente, "pot": nc_potencial,
                                "canal": nc_canal, "ciudad": nc_ciudad, "rubro": nc_rubro,
                                "notas": nc_notas, "real": 1 if nc_es_real else 0,
                                "fcontacto": hoy_str, "linea": nc_linea
                            })
                            conn.commit()
                        st.success(f"✅ {nc_nombre} guardado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab3:
        st.markdown("<div class='section-title'>📡 Señales de Mercado</div>", unsafe_allow_html=True)
        st.caption("Registrá acá cualquier comentario, reacción o idea que surja de una conversación con un cliente. El agente IA las va a analizar.")
        with st.form("form_senal", clear_on_submit=True):
            s1, s2 = st.columns(2)
            with s1:
                s_cliente  = st.text_input("Cliente / Persona", placeholder="Ej: Laura, Aldana, contacto de Nando")
                s_linea    = st.text_input("Línea relacionada", placeholder="Ej: Magnitud 19, Coquette")
                s_producto = st.text_input("Producto (si aplica)")
            with s2:
                s_reaccion = st.selectbox("Reacción", ["Le encantó", "Preguntó el precio", "Dudó", "Pidió muestra", "No le interesó", "Quiere hablar con alguien"])
                s_canal    = st.selectbox("Canal", ["WhatsApp", "Presencial", "Instagram", "Email", "Otro"])
                s_fuente   = st.text_input("¿Quién lo reporta?", value=st.session_state.get("user",""))
            s_oportunidad = st.text_input("Oportunidad detectada", placeholder="Ej: Le gustan los regalos corporativos para fin de año")
            s_notas   = st.text_area("Notas libres", placeholder="Todo lo que querés que el agente sepa")
            s_submit  = st.form_submit_button("📡 REGISTRAR SEÑAL", use_container_width=True, type="primary")
            if s_submit:
                hoy_str = datetime.now().strftime("%Y-%m-%d")
                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO senales_mercado
                            (fecha, cliente_id, linea, producto, reaccion,
                             oportunidad, fuente, canal, notas, procesado_por_ia)
                            VALUES
                            (:fecha,:cliente,:linea,:producto,:reaccion,
                             :oportunidad,:fuente,:canal,:notas,0)
                        """), {
                            "fecha": hoy_str, "cliente": s_cliente, "linea": s_linea,
                            "producto": s_producto, "reaccion": s_reaccion,
                            "oportunidad": s_oportunidad, "fuente": s_fuente,
                            "canal": s_canal, "notas": s_notas
                        })
                        conn.commit()
                    st.success("✅ Señal registrada. El agente la va a procesar.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        try:
            senales = pd.read_sql("SELECT * FROM senales_mercado ORDER BY fecha DESC LIMIT 20", engine)
            if not senales.empty:
                st.markdown(f"<div style='font-size:0.8rem;color:#6B7280;margin-bottom:10px;'>Últimas {len(senales)} señales registradas</div>", unsafe_allow_html=True)
                st.dataframe(
                    senales[["fecha","cliente_id","linea","reaccion","oportunidad","fuente"]].rename(columns={
                        "fecha":"Fecha","cliente_id":"Cliente","linea":"Línea",
                        "reaccion":"Reacción","oportunidad":"Oportunidad","fuente":"Reportado por"
                    }),
                    use_container_width=True, hide_index=True
                )
        except Exception:
            st.info("No hay señales registradas todavía.")

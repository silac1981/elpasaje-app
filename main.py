import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import hashlib

st.set_page_config(
    page_title="El Pasaje - Sistema Integral",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
.stApp { background-color: #F0F2F6; }
.stSidebar { background-color: #1a1a2e !important; }
.stSidebar * { color: white !important; }
.metric-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.07); border-top: 5px solid; transition: transform 0.2s; height: 100%; }
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.12); }
.metric-title { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #6B7280; margin-bottom: 8px; }
.metric-value { font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 700; color: #1a1a2e; line-height: 1; }
.metric-sub   { font-size: 12px; color: #9CA3AF; margin-top: 6px; }
.main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 28px 36px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin-bottom: 28px; }
.main-header h1 { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; margin: 0; letter-spacing: 2px; }
.main-header p  { font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #94a3b8; margin: 6px 0 0; }
.section-title { font-family: 'Cormorant Garamond', serif; font-size: 1.5rem; color: #1a1a2e; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin: 28px 0 16px; }
.stock-critico { background: #FEF2F2; border-left: 5px solid #EF4444; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
.stExpander { background: white !important; }
.stTextInput label, .stSelectbox label, .stTextArea label, 
.stCheckbox label, .stNumberInput label { 
    color: #1a1a2e !important; font-weight: 600 !important; font-size: 0.85rem !important;
}
.stForm { background: white; border-radius: 16px; padding: 20px; }
div[data-testid="stFormSubmitButton"] button { margin-top: 12px; }
.stExpander details { background: white !important; }
.stExpander summary p { color: #1a1a2e !important; font-weight: 600 !important; }
.stMarkdown p, .stMarkdown span { color: #1a1a2e !important; }
.stTabs [data-baseweb="tab"] { color: #1a1a2e !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

LINEAS = {
    "admin":            {"nombre": "Administracion",   "color": "#1E3A8A", "emoji": "🏛️"},
    "oasis_animal":     {"nombre": "Oasis Animal",     "color": "#F472B6", "emoji": "🐾"},
    "oasis_del_estero": {"nombre": "Oasis del Estero", "color": "#34D399", "emoji": "🌱"},
    "pharma_delux":     {"nombre": "Pharma DeLux",     "color": "#FBBF24", "emoji": "💊"},
    "aviation":         {"nombre": "Aviation Pro",     "color": "#0F3460", "emoji": "✈️"},
    "olivia_coquette":  {"nombre": "Coquette",         "color": "#F9A8D4", "emoji": "🎀"},
    "francisco_sport":  {"nombre": "Sport (Francisco)","color": "#F97316", "emoji": "⚽"},
    "constantino_tech": {"nombre": "Core Tech (Constantino)", "color": "#64748B", "emoji": "⚙️"},
}
COSTO_KG_DEFAULT = 2350.0

def get_linea(cid):
    return LINEAS.get(cid, {"nombre": cid, "color": "#6B7280", "emoji": "📦"})

def calcular_costo_pieza(weight_gr, cost_kg=COSTO_KG_DEFAULT, merma=0.10):
    return (weight_gr * (1 + merma) * cost_kg) / 1000

def cargar_productos():
    df = pd.read_sql("SELECT * FROM products", engine)
    df["costo_unit"]    = df["weight_gr"].apply(lambda w: calcular_costo_pieza(w))
    df["ganancia_unit"] = df["price"] - df["costo_unit"]
    df["margen_pct"]    = (df["ganancia_unit"] / df["price"] * 100).round(1)
    df["valor_stock"]   = df["price"] * df["stock"]
    df["costo_stock"]   = df["costo_unit"] * df["stock"]
    df["ganancia_stock"]= df["ganancia_unit"] * df["stock"]
    df["linea_nombre"]  = df["client_id"].apply(lambda c: get_linea(c)["nombre"])
    df["linea_color"]   = df["client_id"].apply(lambda c: get_linea(c)["color"])
    df["linea_emoji"]   = df["client_id"].apply(lambda c: get_linea(c)["emoji"])
    return df

def cargar_materiales():
    return pd.read_sql("SELECT * FROM materials", engine)

# AUTENTICACION
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})

if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='background:white;border-radius:20px;padding:40px;box-shadow:0 20px 50px rgba(0,0,0,0.1);margin-top:60px;'>
            <h2 style='font-family:Cormorant Garamond,serif;text-align:center;color:#1a1a2e;font-size:2rem;margin-bottom:4px;'>🏛️ El Pasaje</h2>
            <p style='text-align:center;color:#9CA3AF;font-size:0.85rem;margin-bottom:28px;'>Sistema de Gestion Integral · v2.6</p>
        </div>
        """, unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="tu@elpasaje.com")
        pwd   = st.text_input("Contrasena", type="password")
        if st.button("INGRESAR AL SISTEMA", use_container_width=True, type="primary"):
            hashed_pwd = hashlib.sha256(pwd.strip().encode()).hexdigest()
            row = pd.read_sql(
                f"SELECT * FROM tenants WHERE email='{email.strip().lower()}' AND password='{hashed_pwd}'",
                engine
            )
            if not row.empty:
                uid  = row["id"].iloc[0]
                tipo = row["tipo"].iloc[0] if "tipo" in row.columns else "socio"
                if uid == "admin":
                    role = "admin"
                elif tipo == "produccion":
                    role = "produccion"
                else:
                    role = "socio"
                st.session_state.update({"auth": True, "user": row["name"].iloc[0], "role": role, "uid": uid})
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# SIDEBAR
with st.sidebar:
    linea_cfg = get_linea(st.session_state["uid"])
    st.markdown(f"""
        <div style='text-align:center;padding:20px 0 10px;'>
            <div style='font-size:2.5rem;'>{linea_cfg['emoji']}</div>
            <div style='font-size:1rem;font-weight:600;margin-top:6px;'>{st.session_state['user']}</div>
            <div style='font-size:0.75rem;color:#94a3b8;margin-top:2px;'>{"Administracion" if st.session_state["role"] == "admin" else ("Produccion" if st.session_state["role"] == "produccion" else "Socio")}</div>
        </div>
        <hr style='border-color:#ffffff22;margin:0 0 16px;'/>
    """, unsafe_allow_html=True)
    if st.session_state["role"] == "admin":
        menu = st.radio("", ["📊 Dashboard Alejandra","📦 Inventario Pro","🛠️ Produccion (Fer)","🤝 Socios","👥 Clientes","🌱 Impacto Social"], label_visibility="collapsed")
    else:
        menu = st.radio("", ["📈 Mi Panel","🛒 Cargar Pedido"], label_visibility="collapsed")
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesion", use_container_width=True):
        st.session_state.update({"auth": False, "user": None, "role": None, "uid": None})
        st.rerun()
    st.markdown(f"<div style='font-size:0.7rem;color:#4B5563;text-align:center;margin-top:20px;'>v2.6 · {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════
# PANEL PRODUCCION — FER
# ══════════════════════════════════════
if st.session_state["role"] == "produccion":
    st.markdown("<div class='main-header'><h1>🛠️ Panel de Producción</h1><p>El Pasaje 3D Studio · Fernando · Lo que fabricás, lo que cuesta, lo que queda</p></div>", unsafe_allow_html=True)

    # ── KPIs de producción ──
    try:
        pedidos = pd.read_sql("SELECT * FROM orders WHERE status IN ('Pendiente','En Proceso') ORDER BY date DESC", engine)
    except:
        pedidos = pd.DataFrame()
    try:
        materiales = pd.read_sql("SELECT * FROM materials WHERE activo=1", engine)
    except:
        materiales = pd.DataFrame()
    try:
        log = pd.read_sql("SELECT * FROM production_log ORDER BY fecha_inicio DESC LIMIT 50", engine)
    except:
        log = pd.DataFrame()

    k1, k2, k3, k4 = st.columns(4)
    pedidos_hoy = len(pedidos[pedidos["date"].str.startswith(datetime.now().strftime("%Y-%m-%d"))]) if not pedidos.empty and "date" in pedidos.columns else 0
    total_pendientes = len(pedidos)
    piezas_fabricadas = len(log) if not log.empty else 0
    mat_criticos = len(materiales[materiales["stock_gr"] < materiales["stock_minimo_gr"]]) if not materiales.empty and "stock_gr" in materiales.columns and "stock_minimo_gr" in materiales.columns else 0

    for col, title, val, sub, color in [
        (k1, "📋 Pedidos Pendientes", str(total_pendientes), "en cola ahora", "#1E3A8A"),
        (k2, "⚡ Nuevos Hoy",         str(pedidos_hoy),     "entrados hoy",  "#D97706"),
        (k3, "✅ Piezas Fabricadas",  str(piezas_fabricadas),"en el historial","#059669"),
        (k4, "⚠️ Materiales Críticos",str(mat_criticos),    "bajo mínimo",   "#EF4444"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if menu == "🛠️ Mi Panel Produccion":
        # Cola de pedidos activos
        st.markdown("<div class='section-title'>📋 Cola de Pedidos Activos</div>", unsafe_allow_html=True)
        if pedidos.empty:
            st.info("🎉 No hay pedidos pendientes. Podés tomarte un descanso, Fer.")
        else:
            for _, p in pedidos.iterrows():
                try:
                    items = pd.read_sql(f"SELECT oi.*, pr.name, pr.weight_gr, pr.tiempo_impresion_min FROM order_items oi JOIN products pr ON oi.product_sku=pr.sku WHERE oi.order_id={p['id']}", engine)
                except:
                    items = pd.DataFrame()
                cliente_row = pd.read_sql(f"SELECT name FROM tenants WHERE id='{p['client_id']}'", engine)
                cliente_nombre = cliente_row["name"].iloc[0] if not cliente_row.empty else p["client_id"]
                status_color = {"Pendiente":"#D97706","En Proceso":"#1E3A8A","Listo":"#059669"}.get(p.get("status",""), "#6B7280")
                total_tiempo = items["tiempo_impresion_min"].sum() if not items.empty and "tiempo_impresion_min" in items.columns else 0
                total_gr = items["weight_gr"].sum() if not items.empty and "weight_gr" in items.columns else 0
                with st.expander(f"Pedido #{p['id']} · {cliente_nombre} · {p.get('status','')} · {total_tiempo//60}h {total_tiempo%60}min estimado"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Cliente:** {cliente_nombre}")
                        st.markdown(f"**Fecha:** {p.get('date','')[:10]}")
                    with c2:
                        st.markdown(f"**Tiempo estimado:** {total_tiempo//60}h {total_tiempo%60}min")
                        st.markdown(f"**Material estimado:** {total_gr:.0f}g")
                    with c3:
                        nuevo_status = st.selectbox(f"Estado #{p['id']}", ["Pendiente","En Proceso","Listo","Cancelado"],
                            index=["Pendiente","En Proceso","Listo","Cancelado"].index(p.get("status","Pendiente")),
                            key=f"status_{p['id']}")
                        if st.button(f"Actualizar #{p['id']}", key=f"btn_{p['id']}"):
                            with engine.connect() as conn_:
                                conn_.execute(text(f"UPDATE orders SET status='{nuevo_status}' WHERE id={p['id']}"))
                                conn_.commit()
                            st.success("✅ Actualizado")
                            st.rerun()
                    if not items.empty:
                        st.dataframe(items[["name","cantidad","weight_gr","tiempo_impresion_min"]].rename(columns={
                            "name":"Producto","cantidad":"Cant","weight_gr":"Gramos","tiempo_impresion_min":"Min"}),
                            use_container_width=True, hide_index=True)
                    if p.get("notas"):
                        st.caption(f"📝 Notas: {p['notas']}")

    elif menu == "📦 Cargar Fabricacion":
        st.markdown("<div class='section-title'>📦 Registrar lo que fabricaste</div>", unsafe_allow_html=True)
        st.caption("Cada registro que cargás acá alimenta el análisis de Mike y ayuda a calcular el costo real de cada pieza.")

        with st.form("form_fabricacion", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                # Pedidos activos para vincular
                try:
                    opts_pedidos = pd.read_sql("SELECT id, client_id, status FROM orders WHERE status IN ('Pendiente','En Proceso')", engine)
                    pedido_opts = ["Sin pedido asociado"] + [f"Pedido #{r['id']} — {r['client_id']}" for _,r in opts_pedidos.iterrows()]
                except:
                    pedido_opts = ["Sin pedido asociado"]
                fab_pedido = st.selectbox("Pedido asociado", pedido_opts)
                fab_sku = st.text_input("SKU del producto", placeholder="Ej: OAS-LLA-001")
                fab_material = st.selectbox("Material usado", ["petg_gris","petg_naranja","pla_seda_azul","pla_seda_gris","pla_rosa","pla_blanco","pla_negro"])
            with c2:
                fab_gramos = st.number_input("Gramos consumidos", min_value=0.0, step=0.5)
                fab_tiempo = st.number_input("Tiempo real (minutos)", min_value=0, step=1)
                fab_resultado = st.selectbox("Resultado", ["ok","fallo","reimpresion"])
            fab_fallo_desc = st.text_input("Si hubo fallo — ¿qué pasó?", placeholder="Ej: Se tapó el hotend, se despegó la base...")
            fab_notas = st.text_area("Notas adicionales", placeholder="Cualquier cosa que quieras que quede registrada")

            if st.form_submit_button("✅ REGISTRAR FABRICACIÓN", use_container_width=True, type="primary"):
                hoy_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                order_id_val = None
                if fab_pedido != "Sin pedido asociado":
                    try:
                        order_id_val = int(fab_pedido.split("#")[1].split("—")[0].strip())
                    except:
                        order_id_val = None
                try:
                    with engine.connect() as conn_:
                        conn_.execute(text("""
                            INSERT INTO production_log
                            (order_id, product_sku, material_id, gramos_usados,
                             tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                            VALUES (:oid,:sku,:mat,:gr,:tiempo,:fi,:ff,:res)
                        """), {
                            "oid": order_id_val, "sku": fab_sku.strip(),
                            "mat": fab_material, "gr": fab_gramos,
                            "tiempo": int(fab_tiempo), "fi": hoy_str, "ff": hoy_str,
                            "res": fab_resultado + (f" — {fab_fallo_desc}" if fab_fallo_desc else "")
                        })
                        # Si hubo fallo, registrar en orders también
                        if order_id_val and fab_resultado != "ok":
                            conn_.execute(text(f"UPDATE orders SET notas=COALESCE(notas,'')||' | FALLO: {fab_fallo_desc}' WHERE id={order_id_val}"))
                        conn_.commit()
                    st.success(f"✅ Fabricación registrada — {fab_sku} — {fab_gramos}g — {fab_tiempo}min — {fab_resultado}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        # Historial reciente
        if not log.empty:
            st.markdown("<div class='section-title'>📋 Últimas fabricaciones</div>", unsafe_allow_html=True)
            st.dataframe(
                log[["fecha_inicio","product_sku","material_id","gramos_usados","tiempo_real_min","resultado"]].rename(columns={
                    "fecha_inicio":"Fecha","product_sku":"SKU","material_id":"Material",
                    "gramos_usados":"Gramos","tiempo_real_min":"Minutos","resultado":"Resultado"
                }).head(20),
                use_container_width=True, hide_index=True
            )

    elif menu == "🧵 Materiales":
        st.markdown("<div class='section-title'>🧵 Stock de Filamentos</div>", unsafe_allow_html=True)

        # Calcular consumo del mes por material desde production_log
        try:
            consumo_mes = pd.read_sql("""
                SELECT material_id, SUM(gramos_usados) as consumido_mes
                FROM production_log
                WHERE fecha_inicio >= date('now','start of month')
                GROUP BY material_id
            """, engine)
        except:
            consumo_mes = pd.DataFrame(columns=["material_id","consumido_mes"])

        # Calcular qué líneas usan cada material
        try:
            uso_lineas = pd.read_sql("""
                SELECT p.material_id, GROUP_CONCAT(DISTINCT t.name) as lineas
                FROM products p
                JOIN tenants t ON p.client_id = t.id
                WHERE p.material_id IS NOT NULL
                GROUP BY p.material_id
            """, engine)
        except:
            uso_lineas = pd.DataFrame(columns=["material_id","lineas"])

        # Historial de compras por material
        try:
            compras = pd.read_sql("""
                SELECT product_sku as material_id, fecha, cantidad, referencia
                FROM stock_movements
                WHERE tipo = 'entrada'
                ORDER BY fecha DESC
            """, engine)
        except:
            compras = pd.DataFrame(columns=["material_id","fecha","cantidad","referencia"])

        if not materiales.empty:
            col_a, col_b = st.columns(2)
            for idx, (_, m) in enumerate(materiales.iterrows()):
                stock = m.get("stock_gr", 0)
                minimo = m.get("stock_minimo_gr", 200)
                pct = min(stock / 1000 * 100, 100)
                color_bar = "#059669" if stock > minimo*2 else ("#D97706" if stock > minimo else "#EF4444")
                alerta = "⚠️ STOCK BAJO" if stock <= minimo else "✅ OK"
                mid = m.get("material_id","")

                # Datos de consumo del mes
                consumo = consumo_mes[consumo_mes["material_id"]==mid]["consumido_mes"].sum() if not consumo_mes.empty else 0
                # Líneas que usan este material
                lineas_txt = uso_lineas[uso_lineas["material_id"]==mid]["lineas"].values[0] if not uso_lineas.empty and mid in uso_lineas["material_id"].values else "Sin asignar"
                # Última compra
                compra_mat = compras[compras["material_id"]==mid].head(1) if not compras.empty else pd.DataFrame()
                ultima_compra = compra_mat["fecha"].values[0] if not compra_mat.empty else m.get("fecha_compra","—")
                ultimo_precio = m.get("cost_kg", 0)
                # Días de stock restante (estimado)
                dias_stock = round(stock / (consumo / 30)) if consumo > 0 else 999

                col = col_a if idx % 2 == 0 else col_b
                with col:
                    with st.expander(f"{'⚠️' if stock <= minimo else '🟢'} {m.get('name','')} — {stock:.0f}g restantes"):
                        # Barra de stock
                        st.markdown(f"""
                        <div style='margin-bottom:12px;'>
                            <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                                <span style='font-size:2rem;font-weight:700;color:{color_bar};'>{stock:.0f}g</span>
                                <span style='font-size:0.8rem;color:#6B7280;padding-top:12px;'>{alerta}</span>
                            </div>
                            <div style='background:#F3F4F6;border-radius:999px;height:10px;'>
                                <div style='width:{pct:.0f}%;background:{color_bar};height:100%;border-radius:999px;'></div>
                            </div>
                            <div style='font-size:0.75rem;color:#9CA3AF;margin-top:4px;'>{pct:.0f}% de 1kg de referencia · Mínimo: {minimo}g</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Grid de datos
                        d1, d2, d3 = st.columns(3)
                        with d1:
                            st.markdown(f"**💰 Precio/kg**")
                            st.markdown(f"${ultimo_precio:,.0f}")
                            st.markdown(f"**📅 Última compra**")
                            st.markdown(f"{ultima_compra}")
                        with d2:
                            st.markdown(f"**🔥 Consumido este mes**")
                            st.markdown(f"{consumo:.0f}g")
                            st.markdown(f"**📊 Stock estimado**")
                            st.markdown(f"{'∞ días' if dias_stock==999 else f'{dias_stock} días'}")
                        with d3:
                            st.markdown(f"**🏭 Usado en líneas**")
                            st.markdown(f"{lineas_txt[:50] if lineas_txt else '—'}")
                            st.markdown(f"**💵 Valor stock**")
                            st.markdown(f"${stock * ultimo_precio / 1000:,.0f}")

                        # Historial de compras de este material
                        hist_mat = compras[compras["material_id"]==mid].head(5) if not compras.empty else pd.DataFrame()
                        if not hist_mat.empty:
                            st.markdown("**📋 Últimas compras:**")
                            st.dataframe(hist_mat[["fecha","cantidad","referencia"]].rename(columns={
                                "fecha":"Fecha","cantidad":"Gramos","referencia":"Detalle"
                            }), use_container_width=True, hide_index=True)

                        # Botón compra rápida
                        st.markdown("---")
                        with st.form(f"compra_rapida_{mid}", clear_on_submit=True):
                            cr1, cr2 = st.columns(2)
                            with cr1:
                                cr_gr = st.number_input("Gramos a cargar", min_value=0, step=250, value=1000, key=f"gr_{mid}")
                            with cr2:
                                cr_precio = st.number_input("Precio pagado ($)", min_value=0.0, step=500.0, key=f"pr_{mid}")
                            if st.form_submit_button("🛒 Registrar compra", use_container_width=True):
                                try:
                                    with engine.connect() as conn_:
                                        nuevo_costo = cr_precio/(cr_gr/1000) if cr_gr > 0 else ultimo_precio
                                        conn_.execute(text(f"UPDATE materials SET stock_gr=stock_gr+{cr_gr}, cost_kg={nuevo_costo} WHERE material_id='{mid}'"))
                                        conn_.execute(text(f"""
                                            INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia)
                                            VALUES ('{mid}','entrada',{cr_gr},'{datetime.now().strftime('%Y-%m-%d')}',
                                            'Compra Fer — ${cr_precio:,.0f} — ${nuevo_costo:,.0f}/kg')
                                        """))
                                        conn_.commit()
                                    st.success(f"✅ +{cr_gr}g registrado a ${nuevo_costo:,.0f}/kg")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

        # Actualizar stock
        st.markdown("<div class='section-title'>🛒 Registrar compra de material</div>", unsafe_allow_html=True)
        with st.form("form_material", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                mat_id = st.selectbox("Material", materiales["material_id"].tolist() if not materiales.empty else [])
            with c2:
                mat_gr = st.number_input("Gramos comprados", min_value=0, step=100, value=1000)
            with c3:
                mat_precio = st.number_input("Precio pagado ($)", min_value=0.0, step=100.0)
            if st.form_submit_button("💾 REGISTRAR COMPRA", use_container_width=True, type="primary"):
                try:
                    with engine.connect() as conn_:
                        conn_.execute(text(f"UPDATE materials SET stock_gr = stock_gr + {mat_gr}, cost_kg = {mat_precio/(mat_gr/1000) if mat_gr > 0 else 0} WHERE material_id='{mat_id}'"))
                        conn_.execute(text(f"""
                            INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia)
                            VALUES ('{mat_id}', 'entrada', {mat_gr}, '{datetime.now().strftime("%Y-%m-%d")}',
                            'Compra registrada por Fer — ${mat_precio:,.0f}')
                        """))
                        conn_.commit()
                    st.success(f"✅ +{mat_gr}g de {mat_id} registrado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    elif menu == "📋 Cola de Pedidos":
        st.markdown("<div class='section-title'>📋 Todos los pedidos</div>", unsafe_allow_html=True)
        try:
            todos_pedidos = pd.read_sql("SELECT * FROM orders ORDER BY date DESC", engine)
        except:
            todos_pedidos = pd.DataFrame()
        if todos_pedidos.empty:
            st.info("No hay pedidos registrados todavía.")
        else:
            filtro_st = st.selectbox("Filtrar por estado", ["Todos","Pendiente","En Proceso","Listo","Cancelado"])
            df_p = todos_pedidos if filtro_st=="Todos" else todos_pedidos[todos_pedidos["status"]==filtro_st]
            st.dataframe(df_p[["id","client_id","status","date","notas"]].rename(columns={
                "id":"#","client_id":"Cliente","status":"Estado","date":"Fecha","notas":"Notas"
            }), use_container_width=True, hide_index=True)

    st.stop()

# DASHBOARD ALEJANDRA
if menu == "📊 Dashboard Alejandra":
    st.markdown("<div class='main-header'><h1>📊 Dashboard de Magnitud</h1><p>Inteligencia de negocios en tiempo real · Ecosistema El Pasaje</p></div>", unsafe_allow_html=True)
    df   = cargar_productos()
    mats = cargar_materiales()
    total_stock    = df["valor_stock"].sum()
    total_costo    = df["costo_stock"].sum()
    total_ganancia = df["ganancia_stock"].sum()
    margen_global  = (total_ganancia / total_stock * 100) if total_stock > 0 else 0
    val_mat        = (mats["stock_gr"] * mats["cost_kg"] / 1000).sum()
    c1, c2, c3, c4 = st.columns(4)
    for col, title, val, sub, color in [
        (c1, "💰 Valor Total Stock",   f"${total_stock:,.0f}",    "Precio venta × unidades",   "#1E3A8A"),
        (c2, "📈 Ganancia Proyectada", f"${total_ganancia:,.0f}", f"Margen: {margen_global:.1f}%", "#059669"),
        (c3, "🏭 Costo Produccion",    f"${total_costo:,.0f}",    "Filamento + merma 10%",     "#DC2626"),
        (c4, "🧵 Stock Materiales",    f"${val_mat:,.0f}",        "Valor bobinas activas",     "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1.6, 1])
    df_linea = df.groupby("linea_nombre").agg(valor_stock=("valor_stock","sum"),ganancia=("ganancia_stock","sum"),costo=("costo_stock","sum")).reset_index().sort_values("valor_stock", ascending=False)
    with col_a:
        st.markdown("<div class='section-title'>💹 Valor de Stock por Linea</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Costo Produccion", x=df_linea["linea_nombre"], y=df_linea["costo"], marker_color="#EF4444", opacity=0.85))
        fig_bar.add_trace(go.Bar(name="Ganancia Neta", x=df_linea["linea_nombre"], y=df_linea["ganancia"], marker_color="#22C55E", opacity=0.85))
        fig_bar.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(l=10,r=10,t=10,b=40), legend=dict(orientation="h",yanchor="bottom",y=1.02), xaxis=dict(tickangle=-20), yaxis=dict(tickprefix="$",tickformat=",.0f"))
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("<div class='section-title'>🥧 Distribucion del Ecosistema</div>", unsafe_allow_html=True)
        fig_pie = px.pie(df_linea, values="valor_stock", names="linea_nombre", color_discrete_sequence=px.colors.qualitative.Set2, hole=0.45)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
        fig_pie.update_layout(showlegend=False, height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
        st.plotly_chart(fig_pie, use_container_width=True)
    col_c, col_d = st.columns([1.6, 1])
    with col_c:
        st.markdown("<div class='section-title'>🎯 Ganancia Neta por Producto</div>", unsafe_allow_html=True)
        df_prod = df.sort_values("ganancia_stock", ascending=True)
        fig_h = go.Figure(go.Bar(x=df_prod["ganancia_stock"], y=df_prod["name"], orientation="h", marker_color=["#22C55E" if g > 0 else "#EF4444" for g in df_prod["ganancia_stock"]], text=[f"${v:,.0f}" for v in df_prod["ganancia_stock"]], textposition="outside"))
        fig_h.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(l=10,r=80,t=10,b=10), xaxis=dict(tickprefix="$",tickformat=",.0f"), yaxis=dict(automargin=True))
        st.plotly_chart(fig_h, use_container_width=True)
    with col_d:
        st.markdown("<div class='section-title'>🧵 Estado de Materiales</div>", unsafe_allow_html=True)
        for _, mat in mats.iterrows():
            pct = min(mat["stock_gr"] / 1000 * 100, 100)
            color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
            val_m = mat["stock_gr"] * mat["cost_kg"] / 1000
            alerta = " ⚠️ STOCK BAJO" if pct <= 10 else (" ⚡ Atención" if pct <= 30 else "")
            st.markdown(f"<div style='background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:12px;'><div style='display:flex;justify-content:space-between;margin-bottom:8px;'><b style='color:#1a1a2e'>{mat['name']}</b><span style='color:{color_m};font-weight:600'>{mat['stock_gr']:.0f}g{alerta}</span></div><div style='background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;'><div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div></div><div style='display:flex;justify-content:space-between;margin-top:6px;font-size:0.75rem;color:#6B7280;'><span>${mat['cost_kg']:,.0f}/kg</span><span>Valor: ${val_m:,.0f}</span></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📋 Analisis Completo por Producto</div>", unsafe_allow_html=True)
    df_show = df[["linea_emoji","linea_nombre","name","sku","weight_gr","costo_unit","price","ganancia_unit","margen_pct","stock","ganancia_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Peso(g)","Costo Unit","Precio Venta","Ganancia Unit","Margen %","Stock","Ganancia Total"]
    def color_margen(val):
        if isinstance(val, (int, float)):
            if val >= 60: return "color:#059669;font-weight:600"
            if val >= 30: return "color:#D97706"
            return "color:#DC2626;font-weight:600"
        return ""
    st.dataframe(df_show.style.format({"Costo Unit":"${:,.0f}","Precio Venta":"${:,.0f}","Ganancia Unit":"${:,.0f}","Ganancia Total":"${:,.0f}","Margen %":"{:.1f}%"}).map(color_margen, subset=["Margen %"]), use_container_width=True, hide_index=True)
    criticos = df[df["stock"] <= 15]
    if not criticos.empty:
        st.markdown("<div class='section-title'>🚨 Alerta Stock Bajo (≤ 15 unidades)</div>", unsafe_allow_html=True)
        for _, row in criticos.iterrows():
            lvl = get_linea(row["client_id"])
            st.markdown(f"<div class='stock-critico'><b>{lvl['emoji']} {row['name']}</b> · SKU: {row['sku']} &nbsp;|&nbsp; Stock: <b style='color:#EF4444'>{int(row['stock'])} uds</b> &nbsp;|&nbsp; Pedido sugerido: 20 uds → ${row['price']*20:,.0f} potencial</div>", unsafe_allow_html=True)

elif menu == "📦 Inventario Pro":
    st.markdown("<div class='main-header'><h1>📦 Inventario Unificado</h1><p>Control de stock en tiempo real</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        filtro_linea = st.selectbox("Filtrar por linea", ["Todas"] + sorted(df["linea_nombre"].unique().tolist()))
    with col_f2:
        busqueda = st.text_input("Buscar por SKU o nombre", placeholder="Ej: Kaizen, COQ-TEX...")
    df_f = df.copy()
    if filtro_linea != "Todas": df_f = df_f[df_f["linea_nombre"] == filtro_linea]
    if busqueda:
        mask = df_f["name"].str.contains(busqueda, case=False) | df_f["sku"].str.contains(busqueda, case=False)
        df_f = df_f[mask]
    st.caption(f"Mostrando {len(df_f)} productos")
    df_show = df_f[["linea_emoji","linea_nombre","name","sku","price","costo_unit","ganancia_unit","margen_pct","stock","valor_stock"]].copy()
    df_show.columns = ["","Linea","Producto","SKU","Precio","Costo","Ganancia","Margen%","Stock","Valor Total"]
    st.dataframe(df_show.style.format({"Precio":"${:,.0f}","Costo":"${:,.0f}","Ganancia":"${:,.0f}","Margen%":"{:.1f}%","Valor Total":"${:,.0f}"}), use_container_width=True, hide_index=True)

elif menu == "🛠️ Produccion (Fer)":
    st.markdown("<div class='main-header'><h1>🛠️ Centro de Produccion</h1><p>Gestion de materiales, insumos y cola de pedidos</p></div>", unsafe_allow_html=True)
    mats = cargar_materiales()
    st.markdown("<div class='section-title'>📋 Cola de Pedidos</div>", unsafe_allow_html=True)
    ESTADO_CONFIG = {"Pendiente":{"color":"#F59E0B","emoji":"⏳"},"En Proceso":{"color":"#3B82F6","emoji":"🖨️"},"Listo":{"color":"#22C55E","emoji":"✅"},"Cancelado":{"color":"#EF4444","emoji":"❌"}}
    try:
        todos_pedidos = pd.read_sql("SELECT o.id, o.client_id, o.status, o.date, o.notas, oi.product_sku, oi.cantidad, oi.precio_unitario, p.name as product_name FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.id LEFT JOIN products p ON p.sku = oi.product_sku WHERE o.status != 'Cancelado' ORDER BY o.date DESC", engine)
    except:
        todos_pedidos = pd.DataFrame()
    if todos_pedidos.empty:
        st.info("No hay pedidos pendientes. 🎉")
    else:
        rc1, rc2, rc3 = st.columns(3)
        for col, estado, ecfg in [(rc1,"Pendiente",ESTADO_CONFIG["Pendiente"]),(rc2,"En Proceso",ESTADO_CONFIG["En Proceso"]),(rc3,"Listo",ESTADO_CONFIG["Listo"])]:
            cant = len(todos_pedidos[todos_pedidos["status"] == estado])
            with col:
                st.markdown(f"<div style='background:white;border-radius:12px;padding:16px;text-align:center;border-top:4px solid {ecfg['color']};box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:16px;'><div style='font-size:1.8rem;'>{ecfg['emoji']}</div><div style='font-size:2rem;font-weight:700;color:{ecfg['color']};'>{cant}</div><div style='font-size:0.8rem;color:#6B7280;'>{estado}</div></div>", unsafe_allow_html=True)
        tenants_df = pd.read_sql("SELECT id, name FROM tenants", engine)
        tenant_map = dict(zip(tenants_df["id"], tenants_df["name"]))
        for _, p in todos_pedidos.iterrows():
            estado = p.get("status","Pendiente")
            ecfg = ESTADO_CONFIG.get(estado, ESTADO_CONFIG["Pendiente"])
            socio = tenant_map.get(p["client_id"], p["client_id"])
            fecha = str(p.get("date",""))[:10]
            pid = p["id"]
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"<div style='background:white;border-radius:12px;padding:14px 20px;border-left:5px solid {ecfg['color']};box-shadow:0 2px 8px rgba(0,0,0,0.05);'><div style='font-weight:700;color:#1a1a2e;'>{ecfg['emoji']} {p['product_name']}</div><div style='font-size:0.8rem;color:#6B7280;margin-top:3px;'>👤 {socio} · 📅 {fecha} · <span style='background:{ecfg['color']}22;color:{ecfg['color']};padding:2px 8px;border-radius:99px;font-weight:600;'>{estado}</span></div></div>", unsafe_allow_html=True)
            with col_btn:
                nuevo_estado = st.selectbox("Estado", ["Pendiente","En Proceso","Listo","Cancelado"], index=["Pendiente","En Proceso","Listo","Cancelado"].index(estado), key=f"estado_{pid}", label_visibility="collapsed")
                if nuevo_estado != estado:
                    if st.button("Actualizar", key=f"btn_{pid}", type="primary"):
                        with engine.connect() as conn:
                            conn.execute(text(f"UPDATE orders SET status='{nuevo_estado}' WHERE id={pid}"))
                            conn.commit()
                        st.success(f"✅ Pedido #{pid} → {nuevo_estado}")
                        st.rerun()
    st.markdown("<div class='section-title'>🧵 Stock de Filamentos</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, (_, mat) in enumerate(mats.iterrows()):
        pct = min(mat["stock_gr"] / 1000 * 100, 100)
        color_m = "#22C55E" if pct > 30 else ("#F59E0B" if pct > 10 else "#EF4444")
        with (c1 if i == 0 else c2):
            st.markdown(f"<div class='metric-card' style='border-top-color:{color_m}'><div class='metric-title'>🧵 {mat['name']}</div><div class='metric-value'>{mat['stock_gr']:.0f} g</div><div class='metric-sub'>${mat['cost_kg']:,.0f}/kg · Valor: ${mat['stock_gr']*mat['cost_kg']/1000:,.2f}</div><div style='background:#F3F4F6;border-radius:999px;height:10px;overflow:hidden;margin-top:12px;'><div style='width:{pct:.0f}%;background:{color_m};height:100%;border-radius:999px;'></div></div><div style='font-size:0.75rem;color:#6B7280;margin-top:4px;'>{pct:.0f}% de 1kg de referencia</div></div>", unsafe_allow_html=True)
    with st.expander("➕ Reponer Filamento"):
        mat_sel = st.selectbox("Material", mats["name"].tolist())
        gramos = st.number_input("Gramos a agregar", min_value=100, max_value=5000, step=100)
        if st.button("Registrar Reposicion", type="primary"):
            with engine.connect() as conn:
                conn.execute(text(f"UPDATE materials SET stock_gr = stock_gr + {gramos} WHERE name = '{mat_sel}'"))
                conn.commit()
            st.success(f"✅ +{gramos}g agregados a {mat_sel}")
            st.rerun()
    st.markdown("<div class='section-title'>⚙️ Calculadora de Insumos</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        peso_g = st.number_input("Peso de pieza (gramos)", min_value=1.0, value=100.0, step=5.0)
        mat_cal = st.selectbox("Material", mats["name"].tolist(), key="calc_mat")
    with c2:
        merma = st.slider("% Merma estimada", 5, 25, 10)
        precio_v = st.number_input("Precio de venta ($)", min_value=0.0, value=5000.0, step=100.0)
    costo_kg_sel = mats.loc[mats["name"] == mat_cal, "cost_kg"].iloc[0]
    costo_calc = calcular_costo_pieza(peso_g, costo_kg_sel, merma / 100)
    ganancia = precio_v - costo_calc
    margen = (ganancia / precio_v * 100) if precio_v > 0 else 0
    st.markdown(f"<div style='background:white;border-radius:16px;padding:20px;box-shadow:0 4px 12px rgba(0,0,0,0.06);margin-top:12px;'><div style='display:flex;gap:32px;flex-wrap:wrap;'><div><div class='metric-title'>💰 Costo Pieza</div><div style='font-size:2rem;font-weight:700;color:#DC2626;'>${costo_calc:,.2f}</div></div><div><div class='metric-title'>📈 Ganancia</div><div style='font-size:2rem;font-weight:700;color:#059669;'>${ganancia:,.2f}</div></div><div><div class='metric-title'>📊 Margen</div><div style='font-size:2rem;font-weight:700;color:#1E3A8A;'>{margen:.1f}%</div></div><div><div class='metric-title'>✅ Precio Regla x3</div><div style='font-size:2rem;font-weight:700;color:#7C3AED;'>${costo_calc * 3:,.2f}</div></div></div></div>", unsafe_allow_html=True)

elif menu == "🤝 Socios":
    st.markdown("<div class='main-header'><h1>🤝 Panel de Socios</h1><p>Ecosistema El Pasaje · Familia + B2B · Visión consolidada</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    tenants = pd.read_sql("SELECT * FROM tenants WHERE id != 'admin'", engine)
    B2B_IDS = {"oasis_animal","oasis_del_estero","pharma_delux","aviation"}
    try:
        all_orders = pd.read_sql("SELECT * FROM orders", engine)
    except:
        all_orders = pd.DataFrame()
    ids_socios = tenants["id"].tolist()
    df_socios = df[df["client_id"].isin(ids_socios)]
    total_val = df_socios["valor_stock"].sum()
    total_gan = df_socios["ganancia_stock"].sum()
    n_socios = len(tenants)
    pedidos_activos = len(all_orders[all_orders["status"].isin(["Pendiente","En Proceso"])]) if not all_orders.empty and "status" in all_orders.columns else 0
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    for col, title, val, sub, color in [(kpi1,"🤝 Socios Activos",str(n_socios),"líneas en el ecosistema","#1E3A8A"),(kpi2,"💰 Stock Consolidado",f"${total_val:,.0f}","valor precio venta","#059669"),(kpi3,"📈 Ganancia Total",f"${total_gan:,.0f}","potencial del ecosistema","#7C3AED"),(kpi4,"🏭 Pedidos Activos",str(pedidos_activos),"en producción ahora","#D97706")]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)
    chart_rows = []
    for _, t in tenants.iterrows():
        cfg = get_linea(t["id"])
        prod = df[df["client_id"] == t["id"]]
        chart_rows.append({"Socio":cfg["nombre"],"Costo":prod["costo_stock"].sum(),"Ganancia":prod["ganancia_stock"].sum(),"valor_total":prod["valor_stock"].sum(),"Color":cfg["color"]})
    df_chart = pd.DataFrame(chart_rows).sort_values("Ganancia", ascending=True)
    col_a, col_b = st.columns([1.6, 1])
    with col_a:
        st.markdown("<div class='section-title'>📊 Stock por Línea</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Costo Producción", x=df_chart["Costo"], y=df_chart["Socio"], orientation="h", marker_color="#EF4444", opacity=0.85))
        fig_bar.add_trace(go.Bar(name="Ganancia Neta", x=df_chart["Ganancia"], y=df_chart["Socio"], orientation="h", marker_color="#22C55E", opacity=0.85))
        fig_bar.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(l=10,r=60,t=10,b=30), legend=dict(orientation="h",yanchor="bottom",y=1.02), xaxis=dict(tickprefix="$",tickformat=",.0f"))
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("<div class='section-title'>🥧 Participación</div>", unsafe_allow_html=True)
        color_map = {r["Socio"]:r["Color"] for _, r in df_chart.iterrows()}
        fig_pie = px.pie(df_chart, values="valor_total", names="Socio", color="Socio", color_discrete_map=color_map, hole=0.5)
        fig_pie.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
        fig_pie.update_layout(showlegend=True, height=300, margin=dict(l=0,r=0,t=10,b=10), paper_bgcolor="white", legend=dict(font=dict(size=10)))
        st.plotly_chart(fig_pie, use_container_width=True)
    for grupo_label, grupo_df in [("👨‍👩‍👧‍👦 Familia El Pasaje", tenants[~tenants["id"].isin(B2B_IDS)]),("🤝 Socios B2B · Nando", tenants[tenants["id"].isin(B2B_IDS)])]:
        if grupo_df.empty: continue
        st.markdown(f"<div style='font-family:Inter,sans-serif;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:#6B7280;margin:28px 0 14px;border-bottom:1px solid #E5E7EB;padding-bottom:8px;'>{grupo_label}</div>", unsafe_allow_html=True)
        tenant_list = list(grupo_df.iterrows())
        for i in range(0, len(tenant_list), 2):
            pair = tenant_list[i:i+2]
            cols_g = st.columns(2)
            for col_g, (_, t) in zip(cols_g, pair):
                cfg = get_linea(t["id"])
                prod = df[df["client_id"] == t["id"]]
                val = prod["valor_stock"].sum()
                gan = prod["ganancia_stock"].sum()
                n_sku = len(prod)
                margen_avg = prod["margen_pct"].mean() if n_sku > 0 else 0.0
                color = cfg["color"]
                ped_activos = 0
                if not all_orders.empty and "client_id" in all_orders.columns and "status" in all_orders.columns:
                    ped_socio = all_orders[all_orders["client_id"] == t["id"]]
                    ped_activos = len(ped_socio[ped_socio["status"].isin(["Pendiente","En Proceso"])])
                m_color = "#059669" if margen_avg >= 50 else ("#D97706" if margen_avg >= 30 else "#EF4444")
                badge_ped = f"<div style='margin-top:12px;display:inline-block;background:{color}1a;color:{color};padding:4px 12px;border-radius:99px;font-size:0.72rem;font-weight:700;'>🏭 {ped_activos} pedido{'s' if ped_activos != 1 else ''} en curso</div>" if ped_activos > 0 else ""
                badge_tipo = "B2B" if t["id"] in B2B_IDS else "Familia"
                with col_g:
                    st.markdown(f"<div style='background:white;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);margin-bottom:16px;'><div style='background:{color};padding:18px 22px 16px;display:flex;align-items:center;gap:14px;'><div style='font-size:2.4rem;line-height:1;'>{cfg['emoji']}</div><div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:white;line-height:1.1;'>{t['name']}</div><div style='font-size:0.68rem;color:rgba(255,255,255,0.72);letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>{badge_tipo}</div></div></div><div style='padding:18px 22px 20px;'><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;'><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>Stock</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#1a1a2e;'>${val:,.0f}</div></div><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>Ganancia</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#059669;'>${gan:,.0f}</div></div><div><div style='font-size:0.65rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.8px;'>SKUs</div><div style='font-family:Cormorant Garamond,serif;font-size:1.3rem;font-weight:700;color:#1a1a2e;'>{n_sku}</div></div></div><div style='margin-top:14px;'><div style='display:flex;justify-content:space-between;font-size:0.7rem;color:#6B7280;margin-bottom:4px;'><span>Margen promedio</span><span style='color:{m_color};font-weight:700;'>{margen_avg:.1f}%</span></div><div style='background:#F3F4F6;border-radius:999px;height:7px;overflow:hidden;'><div style='width:{min(margen_avg,100):.0f}%;background:{m_color};height:100%;border-radius:999px;'></div></div></div>{badge_ped}</div></div>", unsafe_allow_html=True)
                    if not prod.empty:
                        with st.expander(f"📦 Ver productos · {cfg['nombre']} ({n_sku} SKUs)"):
                            st.dataframe(prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={"name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen %"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen %":"{:.1f}%"}), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Sin productos cargados en esta línea.")

elif menu == "📈 Mi Panel":
    uid = st.session_state["uid"]
    cfg = get_linea(uid)
    st.markdown(f"<div class='main-header' style='background:linear-gradient(135deg,{cfg['color']}cc,{cfg['color']}88);'><h1>{cfg['emoji']} Panel {cfg['nombre']}</h1><p>Bienvenido/a, {st.session_state['user']}</p></div>", unsafe_allow_html=True)
    df = cargar_productos()
    prod = df[df["client_id"] == uid]
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("💰 Capital en Stock", f"${prod['valor_stock'].sum():,.0f}")
    cc2.metric("📈 Ganancia Proyectada", f"${prod['ganancia_stock'].sum():,.0f}")
    cc3.metric("📦 Productos Activos", f"{len(prod)} SKUs")
    st.markdown("<div class='section-title'>📦 Mis Productos</div>", unsafe_allow_html=True)
    if prod.empty:
        st.info("Aun no tenes productos cargados en tu linea.")
    else:
        st.dataframe(prod[["name","sku","price","stock","ganancia_unit","margen_pct"]].rename(columns={"name":"Producto","sku":"SKU","price":"Precio","stock":"Stock","ganancia_unit":"Ganancia Unit","margen_pct":"Margen%"}).style.format({"Precio":"${:,.0f}","Ganancia Unit":"${:,.0f}","Margen%":"{:.1f}%"}), use_container_width=True, hide_index=True)

elif menu == "🛒 Cargar Pedido":
    uid = st.session_state["uid"]
    cfg = get_linea(uid)
    st.markdown(f"<div class='main-header'><h1>🛒 Nuevo Pedido · {cfg['nombre']}</h1><p>Solicita produccion a Fer de forma digital</p></div>", unsafe_allow_html=True)
    prods_admin = pd.read_sql("SELECT name, sku FROM products WHERE client_id='admin'", engine)
    producto = st.selectbox("Producto", prods_admin["name"].tolist())
    cantidad = st.number_input("Cantidad", min_value=1, max_value=100, value=1)
    notas = st.text_area("Notas para Fer (color, urgencia, etc.)", height=80)
    if st.button("Confirmar Pedido", type="primary"):
        with engine.connect() as conn:
            result = conn.execute(text(f"INSERT INTO orders (client_id, status, date, notas, color_pedido) VALUES ('{uid}', 'Pendiente', '{datetime.now().isoformat()}', '{notas.strip()}', '')"))
            order_id = result.lastrowid
            precio_unit = pd.read_sql(f"SELECT price FROM products WHERE name='{producto}'", engine)["price"].iloc[0]
            conn.execute(text(f"INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) SELECT {order_id}, sku, {cantidad}, {precio_unit} FROM products WHERE name='{producto}'"))
            conn.commit()
        st.success(f"✅ Pedido registrado: {cantidad}x {producto}")
        st.balloons()


elif menu == "👥 Clientes":
    st.markdown("<div class='main-header'><h1>👥 Gestión de Clientes</h1><p>Segmentación · Potencial · Canal de entrada · Señales de mercado</p></div>", unsafe_allow_html=True)

    # ── CARGAR DATOS ──
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

    # ── KPIs ──
    total = len(clientes)
    reales = len(clientes[clientes["es_cliente_real"] == 1]) if not clientes.empty and "es_cliente_real" in clientes.columns else 0
    alto_potencial = len(clientes[clientes["potencial"] == "Alto"]) if not clientes.empty and "potencial" in clientes.columns else 0
    b2b = len(clientes[clientes["segmento"] == "B2B"]) if not clientes.empty and "segmento" in clientes.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    for col, title, val, sub, color in [
        (k1, "👥 Total Contactos",    str(total),         "en el ecosistema",       "#1E3A8A"),
        (k2, "💰 Clientes Reales",    str(reales),        "con compra registrada",  "#059669"),
        (k3, "⭐ Alto Potencial",     str(alto_potencial),"para próximo contacto",  "#7C3AED"),
        (k4, "🤝 Canal B2B",          str(b2b),           "empresas y socios",      "#D97706"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card' style='border-top-color:{color}'><div class='metric-title'>{title}</div><div class='metric-value'>{val}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3 = st.tabs(["📋 Ver Clientes", "➕ Nuevo Cliente", "📡 Señales de Mercado"])

    # ── TAB 1: VER CLIENTES ──
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

    # ── TAB 2: NUEVO CLIENTE ──
    with tab2:
        st.markdown("<div class='section-title'>➕ Cargar nuevo contacto o cliente</div>", unsafe_allow_html=True)
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nc_nombre    = st.text_input("Nombre o Razón Social *")
                nc_email     = st.text_input("Email")
                nc_telefono  = st.text_input("Teléfono / WhatsApp")
                nc_ciudad    = st.text_input("Ciudad", value="Buenos Aires")
                nc_rubro     = st.text_input("Rubro / Sector")
            with c2:
                nc_segmento  = st.selectbox("Segmento *", ["B2C", "B2B", "Corporativo", "Institucional"])
                nc_potencial = st.selectbox("Potencial *", ["Alto", "Medio", "Bajo"])
                nc_canal     = st.selectbox("Canal preferido", ["WhatsApp", "Instagram", "Presencial", "Email", "Recomendación"])
                nc_fuente    = st.text_input("¿Cómo llegó?", placeholder="Ej: Red de Nando, Laura Cava, Feria")
                nc_linea     = st.text_input("Línea de interés", placeholder="Ej: Magnitud 19, Oasis Animal")
            nc_es_real   = st.checkbox("¿Ya realizó una compra?")
            nc_notas     = st.text_area("Notas (para el agente IA)", placeholder="Describí brevemente quién es y qué le interesa")
            submitted = st.form_submit_button("💾 GUARDAR CLIENTE", use_container_width=True, type="primary")

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

    # ── TAB 3: SEÑALES DE MERCADO ──
    with tab3:
        st.markdown("<div class='section-title'>📡 Señales de Mercado</div>", unsafe_allow_html=True)
        st.caption("Registrá acá cualquier comentario, reacción o idea que surja de una conversación con un cliente. El agente IA las va a analizar.")

        with st.form("form_senal", clear_on_submit=True):
            s1, s2 = st.columns(2)
            with s1:
                s_cliente = st.text_input("Cliente / Persona", placeholder="Ej: Laura, Aldana, contacto de Nando")
                s_linea   = st.text_input("Línea relacionada", placeholder="Ej: Magnitud 19, Coquette")
                s_producto= st.text_input("Producto (si aplica)")
            with s2:
                s_reaccion= st.selectbox("Reacción", ["Le encantó", "Preguntó el precio", "Dudó", "Pidió muestra", "No le interesó", "Quiere hablar con alguien"])
                s_canal   = st.selectbox("Canal", ["WhatsApp", "Presencial", "Instagram", "Email", "Otro"])
                s_fuente  = st.text_input("¿Quién lo reporta?", value=st.session_state.get("user",""))
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
        except:
            st.info("No hay señales registradas todavía.")

elif menu == "🌱 Impacto Social":
    st.markdown("<div class='main-header'><h1>🌱 Impacto Social</h1><p>Transparencia total · Fondos solidarios</p></div>", unsafe_allow_html=True)
    FONDOS = {"refugio_oasis":{"nombre":"Refugio Oasis Animal","emoji":"🐾","color":"#F472B6","meta":50000},"mentes_brillantes":{"nombre":"Mentes Brillantes","emoji":"🧠","color":"#818CF8","meta":40000},"fondo_general":{"nombre":"Fondo General","emoji":"❤️","color":"#FB7185","meta":30000}}
    try:
        dons = pd.read_sql("SELECT * FROM donations ORDER BY fecha DESC", engine)
    except:
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
            conn.execute(text(f"INSERT INTO donations (fondo, monto, tipo, descripcion, fecha) VALUES ('{fondo_sel}', {monto_don}, '{tipo_don}', '{desc_don}', '{datetime.now().date()}')"))
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
            finfo = FONDOS.get(row["fondo"], {"nombre":row["fondo"],"emoji":"❓","color":"#ccc"})
            st.markdown(f"<div style='background:white;border-radius:12px;padding:14px 18px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid {finfo['color']};'><div style='display:flex;justify-content:space-between;align-items:center;'><div><b>{icon} {finfo['emoji']} {finfo['nombre']}</b><span style='margin-left:10px;font-size:0.75rem;color:#6B7280;'>{row['tipo'].upper()} · {row['fecha']}</span><div style='font-size:0.78rem;color:#9CA3AF;margin-top:3px;'>{row.get('descripcion','') or ''}</div></div><div style='font-size:1.4rem;font-weight:700;color:{finfo['color']};'>${row['monto']:,.0f}</div></div></div>", unsafe_allow_html=True)


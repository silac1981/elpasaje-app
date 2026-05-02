"""modules/panel_fer.py — Panel de producción para Fernando."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, _EC
from utils.mike import get_alertas_dashboard, preguntar_mike as _preguntar_mike


def render():
    st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#0D1117!important}
.stTabs [data-baseweb="tab-list"]{background:#161B22!important;border-radius:12px!important;padding:4px!important;gap:2px!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#F0F6FC!important}
[data-testid="stMetricValue"]{color:#E6EDF3!important}
[data-testid="stMetricLabel"]{color:#8B949E!important}
details{background:#161B22!important;border-radius:12px!important;border:1px solid #21262D!important}
details summary{color:#E6EDF3!important;padding:8px 12px!important}
[data-testid="stChatMessage"]{background:#161B22!important;border-radius:12px!important;margin-bottom:8px!important}
[data-testid="stChatMessageContent"] p{color:#E6EDF3!important}
.stRadio label{color:#8B949E!important}
[data-testid="stFileUploaderDropzone"]{background:#161B22!important;border-color:#30363D!important}
.stMarkdown p,.stMarkdown span{color:#C9D1D9!important}
.stMarkdown strong,.stMarkdown b{color:#F0F6FC!important}
.stNumberInput label,.stTextInput label,.stSelectbox label,.stTextArea label,.stFileUploader label,.stCheckbox label{color:#8B949E!important;font-weight:500!important}
.stExpander summary p{color:#E6EDF3!important;font-weight:600!important}
.stExpander details{background:#161B22!important}
.stCaption p,.stCaption span{color:#6B7280!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div,[data-testid="stAlert"] span{color:#C9D1D9!important}
[data-testid="stAlert"]{background:#1a2332!important;border-color:#30363D!important}
.stDataFrame,[data-testid="stDataFrame"]{background:#161B22!important}
</style>""", unsafe_allow_html=True)

    st.markdown(f"<div style='background:#161B22;border-radius:16px;padding:22px 28px;border:1px solid #21262D;border-left:4px solid #3FB950;margin-bottom:8px;'><div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;color:#3FB950;text-transform:uppercase;'>EL PASAJE 3D STUDIO · PRODUCCION</div><div style='font-size:1.7rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>🖨️ Centro de Fabricacion</div><div style='font-size:0.78rem;color:#8B949E;margin-top:6px;'>Fernando · {datetime.now().strftime('%A %d/%m/%Y')} · {datetime.now().strftime('%H:%M')}</div></div>", unsafe_allow_html=True)

    _hoy_str = datetime.now().strftime("%Y-%m-%d")
    from utils.pricing import cargar_materiales
    mats = cargar_materiales()
    try:
        _pedidos_all = pd.read_sql("""
            SELECT o.id, o.client_id, o.status, o.date, o.notas, o.fecha_entrega_est,
                   oi.product_sku, oi.cantidad,
                   p.name AS product_name, p.weight_gr, p.material_id
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN products p ON p.sku = oi.product_sku
            ORDER BY o.date DESC
        """, engine)
    except Exception:
        _pedidos_all = pd.DataFrame()
    try:
        _tenant_map = dict(pd.read_sql("SELECT id, name FROM tenants", engine).values)
    except Exception:
        _tenant_map = {}
    _pedidos_activos = _pedidos_all[_pedidos_all["status"].isin(["Pendiente","En Proceso"])] if not _pedidos_all.empty else pd.DataFrame()
    tab_panel, tab_fab, tab_mats, tab_cola, tab_mike, tab_stats = st.tabs(["🛠️ Mi Panel", "📦 Cargar Fabricacion", "🧵 Materiales", "📋 Cola de Pedidos", "🤖 Mike", "💹 Finanzas CFO"])

    # ══ TAB 1 — MI PANEL ══
    with tab_panel:
        try:
            _fab_total = pd.read_sql("SELECT COUNT(*) AS n FROM production_log", engine).iloc[0]["n"]
        except Exception:
            _fab_total = 0
        _criticos   = len(mats[mats["stock_gr"] <= mats["stock_minimo_gr"]]) if not mats.empty else 0
        _nuevos_hoy = len(_pedidos_all[_pedidos_all["date"].astype(str).str.startswith(_hoy_str)]) if not _pedidos_all.empty else 0
        _n_pendientes = len(_pedidos_all[_pedidos_all["status"] == "Pendiente"]) if not _pedidos_all.empty else 0
        k1, k2, k3, k4 = st.columns(4)
        for _col, _title, _val, _sub, _color in [
            (k1, "⏳ Pendientes",  str(_n_pendientes), "en espera",       "#F59E0B"),
            (k2, "🆕 Hoy",        str(_nuevos_hoy),   "pedidos del dia", "#3B82F6"),
            (k3, "✅ Fabricadas",  str(_fab_total),    "en el log",       "#22C55E"),
            (k4, "⚠️ Criticos",   str(_criticos),     "bajo minimo",     "#EF4444"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;border:1px solid #21262D;border-top:3px solid {_color};text-align:center;margin-bottom:8px;'><div style='font-size:2.2rem;font-weight:800;color:{_color};line-height:1;'>{_val}</div><div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_title}</div><div style='font-size:0.64rem;color:#6B7280;margin-top:4px;letter-spacing:0.5px;'>{_sub}</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:24px;margin-bottom:12px;font-size:0.68rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>📋 COLA ACTIVA</div>", unsafe_allow_html=True)
        if _pedidos_activos.empty:
            try:
                _mat_mas_usado = pd.read_sql("""
                    SELECT m.name FROM production_log pl
                    JOIN materials m ON m.material_id = pl.material_id
                    GROUP BY pl.material_id ORDER BY SUM(pl.gramos_usados) DESC LIMIT 1
                """, engine)
                _ultima_fab_row = pd.read_sql("SELECT fecha_fin FROM production_log ORDER BY id DESC LIMIT 1", engine)
            except Exception:
                _mat_mas_usado = pd.DataFrame()
                _ultima_fab_row = pd.DataFrame()
            _mat_nom = _mat_mas_usado.iloc[0]["name"] if not _mat_mas_usado.empty else "—"
            _ult_f   = str(_ultima_fab_row.iloc[0]["fecha_fin"])[:10] if not _ultima_fab_row.empty else "—"
            st.markdown("<div style='background:#0D2818;border-radius:16px;padding:20px 24px;border:1px solid #238636;border-left:4px solid #3FB950;margin-bottom:16px;'><div style='font-size:1.05rem;font-weight:700;color:#3FB950;'>Sin pedidos activos — el taller está al día ✅</div><div style='font-size:0.82rem;color:#8B949E;margin-top:6px;'>Podés registrar fabricaciones libres desde la pestaña 📦 Cargar Fabricacion</div></div>", unsafe_allow_html=True)
            _es1, _es2, _es3 = st.columns(3)
            _es1.metric("Piezas fabricadas", _fab_total)
            _es2.metric("Material más usado", _mat_nom)
            _es3.metric("Última fabricación", _ult_f)
        else:
            for _, _p in _pedidos_activos.iterrows():
                _ecfg  = _EC.get(_p["status"], _EC["Pendiente"])
                _socio = _tenant_map.get(_p["client_id"], _p["client_id"])
                _fecha = str(_p["date"])[:10]
                _pid   = _p["id"]
                _prod  = _p.get("product_name") or "—"
                _gramos  = f"{_p['weight_gr']:.0f} g" if pd.notna(_p.get("weight_gr")) else "—"
                _entrega = _p.get("fecha_entrega_est") or "—"
                with st.expander(f"{_ecfg['emoji']} Pedido #{_pid} · {_prod} · {_socio}"):
                    _c1, _c2, _c3, _c4 = st.columns(4)
                    _c1.metric("Cliente", _socio)
                    _c2.metric("Gramos estimados", _gramos)
                    _c3.metric("Entrega est.", _entrega)
                    _c4.metric("Cargado", _fecha)
                    if _p.get("notas"):
                        st.caption(f"Notas: {_p['notas']}")
                    _nuevo_est = st.selectbox("Cambiar estado", ["Pendiente","En Proceso","Listo","Cancelado"],
                                              index=["Pendiente","En Proceso","Listo","Cancelado"].index(_p["status"]),
                                              key=f"panel_est_{_pid}")
                    if _nuevo_est != _p["status"]:
                        if st.button("Confirmar cambio", key=f"panel_btn_{_pid}", type="primary"):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE orders SET status=:s WHERE id=:id"), {"s": _nuevo_est, "id": _pid})
                                _conn.commit()
                            st.success(f"Pedido #{_pid} → {_nuevo_est}")
                            st.rerun()

    # ══ TAB 2 — CARGAR FABRICACION ══
    with tab_fab:
        st.markdown("<div class='section-title'>Registrar produccion de una pieza</div>", unsafe_allow_html=True)
        from slicer_parser import parsear_archivo_slicer, match_material_idx
        _slicer_up = st.file_uploader(
            "📎 Importar desde slicer (.gcode / .3mf)",
            type=["gcode", "3mf"],
            help="Bambu Studio, PrusaSlicer o Cura — pre-llena gramos, tiempo y material automáticamente",
            key="slicer_upload"
        )
        if _slicer_up is not None:
            _sp = parsear_archivo_slicer(_slicer_up)
            if _sp:
                _mat_nombres_all = mats["name"].tolist() if not mats.empty else []
                if _sp.get("gramos"):     st.session_state["fab_grams"] = float(_sp["gramos"])
                if _sp.get("tiempo_min"): st.session_state["fab_tiempo"] = int(_sp["tiempo_min"])
                if _sp.get("material_tipo") and _mat_nombres_all:
                    _mi = match_material_idx(_sp["material_tipo"], _mat_nombres_all)
                    st.session_state["fab_mat"] = _mat_nombres_all[_mi]
                _info_parts = []
                if _sp.get("gramos"):        _info_parts.append(f"**{_sp['gramos']} g**")
                if _sp.get("tiempo_min"):    _info_parts.append(f"**{_sp['tiempo_min']} min**")
                if _sp.get("material_tipo"): _info_parts.append(f"**{_sp['material_tipo']}**")
                if _sp.get("color"):         _info_parts.append(f"color {_sp['color']}")
                st.success(f"✅ Slicer cargado — {' · '.join(_info_parts)}")
            else:
                st.warning("No se pudieron leer los datos del archivo. Completá el formulario manualmente.")
        st.markdown("---")
        _ops_pedido = {"Sin pedido": None}
        if not _pedidos_activos.empty:
            for _, _r in _pedidos_activos.drop_duplicates("id").iterrows():
                _lbl = f"#{_r['id']} · {_r.get('product_name','—')} · {_tenant_map.get(_r['client_id'], _r['client_id'])}"
                _ops_pedido[_lbl] = _r["id"]
        _sel_label = st.selectbox("Pedido asociado (opcional)", list(_ops_pedido.keys()), key="fab_pedido")
        _sel_oid   = _ops_pedido[_sel_label]
        if _sel_oid is not None:
            _pedido_row = _pedidos_activos[_pedidos_activos["id"] == _sel_oid].iloc[0]
            _sku_auto   = _pedido_row.get("product_sku") or ""
            _mid_auto   = _pedido_row.get("material_id") or ""
            _weight_def = max(float(_pedido_row.get("weight_gr") or 50), 1.0)
        else:
            _sku_auto, _mid_auto, _weight_def = "", "", 50.0
        _fc1, _fc2 = st.columns(2)
        with _fc1:
            _fab_sku   = st.text_input("SKU del producto", value=_sku_auto, key="fab_sku")
            _fab_grams = st.number_input("Gramos consumidos", min_value=1.0, max_value=2000.0, value=_weight_def, step=5.0, key="fab_grams")
            _fab_res   = st.selectbox("Resultado", ["ok","fallo","reimpresion"], key="fab_res")
        with _fc2:
            _mat_nombres = mats["name"].tolist() if not mats.empty else []
            _mat_ids     = mats["material_id"].tolist() if not mats.empty else []
            _mid_idx     = _mat_ids.index(_mid_auto) if _mid_auto in _mat_ids else 0
            _fab_mat_nom = st.selectbox("Material usado", _mat_nombres, index=_mid_idx, key="fab_mat")
            _fab_tiempo  = st.number_input("Tiempo real (minutos)", min_value=1, max_value=600, value=30, key="fab_tiempo")
        _fab_desc = ""
        if _fab_res != "ok":
            _fab_desc = st.text_area("Descripcion del fallo/problema", height=60, key="fab_desc")
        if st.button("Registrar Fabricacion", type="primary", key="fab_submit"):
            _fab_mid = mats.loc[mats["name"] == _fab_mat_nom, "material_id"].iloc[0] if not mats.empty else ""
            with engine.connect() as _conn:
                _conn.execute(text("""
                    INSERT INTO production_log
                    (order_id, product_sku, material_id, gramos_usados, tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                    VALUES (:oid, :sku, :mid, :grams, :tiempo, :fi, :ff, :res)
                """), {"oid": _sel_oid, "sku": _fab_sku or "LIBRE", "mid": _fab_mid,
                       "grams": _fab_grams, "tiempo": _fab_tiempo,
                       "fi": _hoy_str, "ff": _hoy_str,
                       "res": _fab_res + (f" — {_fab_desc}" if _fab_desc else "")})
                _conn.execute(text("UPDATE materials SET stock_gr = stock_gr - :g WHERE material_id = :mid"),
                              {"g": _fab_grams, "mid": _fab_mid})
                if _fab_res == "ok" and _sel_oid is not None:
                    _conn.execute(text("UPDATE orders SET status='Listo' WHERE id=:id"), {"id": int(_sel_oid)})
                _conn.commit()
            st.success(f"Fabricacion registrada · {_fab_grams}g de {_fab_mat_nom} descontados del stock")
            st.rerun()
        st.markdown("<div class='section-title' style='margin-top:24px;'>Ultimas 20 fabricaciones</div>", unsafe_allow_html=True)
        try:
            _hist = pd.read_sql("""
                SELECT pl.id, pl.order_id, pl.product_sku, m.name AS material,
                       pl.gramos_usados, pl.tiempo_real_min, pl.fecha_fin, pl.resultado
                FROM production_log pl
                LEFT JOIN materials m ON m.material_id = pl.material_id
                ORDER BY pl.id DESC LIMIT 20
            """, engine)
            if _hist.empty:
                st.caption("Sin fabricaciones registradas todavia.")
            else:
                st.dataframe(_hist.rename(columns={"id":"#","order_id":"Pedido","product_sku":"SKU","material":"Material","gramos_usados":"Gramos","tiempo_real_min":"Min","fecha_fin":"Fecha","resultado":"Resultado"}), use_container_width=True, hide_index=True)
        except Exception as _e:
            st.caption(f"Sin datos: {_e}")

    # ══ TAB 3 — MATERIALES ══
    with tab_mats:
        if mats.empty:
            st.info("No hay materiales cargados.")
        else:
            _mes_inicio = datetime.now().strftime("%Y-%m-01")
            try:
                _consumo_mes = pd.read_sql("""
                    SELECT material_id, SUM(gramos_usados) AS consumido
                    FROM production_log WHERE fecha_fin >= :mes GROUP BY material_id
                """, engine, params={"mes": _mes_inicio})
                _consumo_map = dict(zip(_consumo_mes["material_id"], _consumo_mes["consumido"]))
            except Exception:
                _consumo_map = {}
            try:
                _lineas_mat = pd.read_sql("""
                    SELECT material_id, GROUP_CONCAT(DISTINCT client_id) AS lineas
                    FROM products WHERE activo=1 GROUP BY material_id
                """, engine)
                _lineas_map = dict(zip(_lineas_mat["material_id"], _lineas_mat["lineas"]))
            except Exception:
                _lineas_map = {}
            for _, _mat in mats.iterrows():
                _mid      = _mat["material_id"]
                _stock    = _mat["stock_gr"]
                _min_g    = _mat.get("stock_minimo_gr") or 200
                _ckg      = _mat["cost_kg"]
                _valor    = _stock * _ckg / 1000
                _consumido = _consumo_map.get(_mid, 0) or 0
                _dias_est  = f"{int(_stock / (_consumido / 30))}" if _consumido > 0 else "—"
                _lineas_r  = _lineas_map.get(_mid, "")
                _lineas_nombres = " · ".join([LINEAS.get(l, {}).get("nombre", l) for l in (_lineas_r.split(",") if _lineas_r else [])])
                _pct = min(_stock / max(_min_g * 5, 1) * 100, 100)
                _mc  = "#22C55E" if _stock > _min_g * 2 else ("#F59E0B" if _stock > _min_g else "#EF4444")
                _alerta = " ⚠️" if _stock <= _min_g else ""
                with st.expander(f"🧵 {_mat['name']}{_alerta} · {_stock:.0f} g restantes"):
                    _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                    _mc1.metric("Precio/kg", f"${_ckg:,.0f}")
                    _mc2.metric("Valor en stock", f"${_valor:,.0f}")
                    _mc3.metric("Consumido este mes", f"{_consumido:.0f} g")
                    _mc4.metric("Dias de stock est.", _dias_est)
                    _bar_html = (f"<div style='background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;margin:10px 0 6px;'>"
                                 f"<div style='width:{_pct:.0f}%;background:{_mc};height:100%;border-radius:999px;'></div></div>"
                                 f"<div style='font-size:0.72rem;color:#6B7280;'>{_stock:.0f} g de ~{int(_min_g*5)} g referencia · Stock mínimo: {_min_g:.0f} g</div>")
                    if _lineas_nombres:
                        _bar_html += f"<div style='font-size:0.72rem;color:#6B7280;margin-top:4px;'>Usado en: {_lineas_nombres}</div>"
                    if _mat.get("fecha_compra"):
                        _bar_html += f"<div style='font-size:0.72rem;color:#6B7280;margin-top:2px;'>Ultima compra: {_mat['fecha_compra']}</div>"
                    st.markdown(_bar_html, unsafe_allow_html=True)
                    st.markdown("**Registrar compra**")
                    _rep_col1, _rep_col2 = st.columns(2)
                    with _rep_col1:
                        _gramos_rep = st.number_input("Gramos comprados", min_value=100, max_value=10000, step=100, value=1000, key=f"rep_{_mid}")
                    with _rep_col2:
                        _precio_rep = st.number_input("Precio pagado ($)", min_value=0.0, step=100.0, value=0.0, key=f"precio_{_mid}")
                    if st.button("Registrar compra", key=f"repbtn_{_mid}", type="primary"):
                        _total_gr = _stock + _gramos_rep
                        if _precio_rep > 0 and _total_gr > 0:
                            _nuevo_ck = round((_stock * (_ckg or 0) + _precio_rep * 1000) / _total_gr, 2)
                        else:
                            _nuevo_ck = _ckg or 0
                        with engine.connect() as _conn:
                            _conn.execute(text("UPDATE materials SET stock_gr = stock_gr + :g, fecha_compra = :f, cost_kg = :ck WHERE material_id = :mid"),
                                          {"g": _gramos_rep, "f": _hoy_str, "ck": _nuevo_ck, "mid": _mid})
                            _conn.commit()
                        _ck_msg = f" · Costo/kg → ${_nuevo_ck:,.0f}" if _precio_rep > 0 else ""
                        st.success(f"+{_gramos_rep}g registrados en {_mat['name']}{_ck_msg}")
                        st.rerun()

    # ══ TAB 4 — COLA DE PEDIDOS ══
    with tab_cola:
        _filtro_est = st.radio("Filtrar por estado", ["Todos","Pendiente","En Proceso","Listo","Cancelado"],
                               horizontal=True, key="cola_filtro")
        if _pedidos_all.empty:
            st.info("No hay pedidos registrados aun.")
        else:
            _df_cola = _pedidos_all if _filtro_est == "Todos" else _pedidos_all[_pedidos_all["status"] == _filtro_est]
            _df_cola = _df_cola.drop_duplicates("id")
            if _df_cola.empty:
                st.info(f"No hay pedidos con estado '{_filtro_est}'.")
            else:
                for _, _p in _df_cola.iterrows():
                    _ecfg  = _EC.get(_p["status"], _EC["Pendiente"])
                    _socio = _tenant_map.get(_p["client_id"], _p["client_id"])
                    _fecha = str(_p["date"])[:10]
                    _prod  = _p.get("product_name") or "—"
                    _pid   = _p["id"]
                    _notas_html = f"<div style='font-size:0.75rem;color:#9CA3AF;margin-top:3px;'>{_p['notas']}</div>" if _p.get("notas") else ""
                    _col_card, _col_sel = st.columns([3, 1])
                    with _col_card:
                        st.markdown(
                            f"<div style='background:white;border-radius:12px;padding:12px 18px;"
                            f"border-left:5px solid {_ecfg['color']};box-shadow:0 1px 6px rgba(0,0,0,0.06);'>"
                            f"<div style='font-weight:700;color:#1a1a2e;'>{_ecfg['emoji']} {_prod}</div>"
                            f"<div style='font-size:0.78rem;color:#6B7280;margin-top:3px;'>👤 {_socio} · 📅 {_fecha} · "
                            f"<span style='background:{_ecfg['color']}22;color:{_ecfg['color']};padding:1px 8px;"
                            f"border-radius:99px;font-weight:600;'>{_p['status']}</span></div>"
                            f"{_notas_html}</div>",
                            unsafe_allow_html=True
                        )
                    with _col_sel:
                        _nuevo_est = st.selectbox("", ["Pendiente","En Proceso","Listo","Cancelado"],
                                                  index=["Pendiente","En Proceso","Listo","Cancelado"].index(_p["status"]),
                                                  key=f"cola_est_{_pid}", label_visibility="collapsed")
                        if _nuevo_est != _p["status"]:
                            if st.button("✓", key=f"cola_btn_{_pid}", type="primary"):
                                with engine.connect() as _conn:
                                    _conn.execute(text("UPDATE orders SET status=:s WHERE id=:id"), {"s": _nuevo_est, "id": _pid})
                                    _conn.commit()
                                st.success(f"#{_pid} → {_nuevo_est}")
                                st.rerun()

    # ══ TAB 5 — MIKE ══
    with tab_mike:
        _alertas_mike = get_alertas_dashboard()
        _n_crit = sum(1 for a in _alertas_mike if a["nivel"] == "critico")
        _n_atc  = sum(1 for a in _alertas_mike if a["nivel"] == "atencion")
        _est_color = "#EF4444" if _n_crit > 0 else ("#F59E0B" if _n_atc > 0 else "#3FB950")
        _est_txt   = f"{_n_crit} crítica{'s' if _n_crit!=1 else ''}" if _n_crit > 0 else ("Todo en orden" if not _n_atc else f"{_n_atc} atención")
        st.markdown(f"""
<div style='background:#161B22;border-radius:16px;padding:20px 24px;border:1px solid #21262D;margin-bottom:4px;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ASISTENTE DE PRODUCCION</div>
  <div style='font-size:1.5rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>🤖 Mike</div>
  <div style='margin-top:10px;'>
    <span style='background:{_est_color}22;color:{_est_color};padding:4px 12px;border-radius:99px;font-weight:700;font-size:0.78rem;border:1px solid {_est_color}44;'>● {_est_txt}</span>
    <span style='color:#6B7280;margin-left:12px;font-size:0.72rem;'>{len(_alertas_mike)} alertas · actualizado ahora</span>
  </div>
</div>""", unsafe_allow_html=True)
        try:
            _fab_wk = pd.read_sql("SELECT COUNT(*) AS t, SUM(CASE WHEN resultado NOT LIKE 'ok%' THEN 1 ELSE 0 END) AS f FROM production_log WHERE fecha_fin >= date('now','-7 days')", engine).iloc[0]
            _fab_semana, _fallos_semana = int(_fab_wk["t"] or 0), int(_fab_wk["f"] or 0)
        except Exception:
            _fab_semana = _fallos_semana = 0
        _tasa_txt   = f"{_fallos_semana/_fab_semana*100:.0f}%" if _fab_semana > 0 else "—"
        _mat_crit_n = len(mats[mats["stock_gr"] <= mats["stock_minimo_gr"]]) if not mats.empty else 0
        _mk1, _mk2, _mk3, _mk4 = st.columns(4)
        for _col, _v, _l, _c in [
            (_mk1, str(len(_pedidos_activos)), "Pedidos activos",  "#3B82F6"),
            (_mk2, str(_fab_semana),           "Fab. esta semana", "#22C55E"),
            (_mk3, _tasa_txt,                  "Tasa de fallos",   "#EF4444" if _fab_semana > 0 and _fallos_semana/_fab_semana >= 0.25 else "#4B5563"),
            (_mk4, str(_mat_crit_n),           "Mat. críticos",   "#F59E0B" if _mat_crit_n > 0 else "#4B5563"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:16px;border:1px solid #21262D;border-top:3px solid {_c};text-align:center;margin-bottom:4px;'><div style='font-size:1.8rem;font-weight:800;color:{_c};line-height:1;'>{_v}</div><div style='font-size:0.64rem;color:#8B949E;margin-top:6px;text-transform:uppercase;letter-spacing:1px;'>{_l}</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ALERTAS ACTIVAS</div>", unsafe_allow_html=True)
        if not _alertas_mike:
            st.markdown("<div style='background:#0D2818;border-radius:12px;padding:14px 20px;border:1px solid #238636;'><span style='color:#3FB950;font-weight:700;font-size:0.88rem;'>✅ Sin alertas</span><span style='color:#8B949E;margin-left:12px;font-size:0.8rem;'>El taller está en orden — buen trabajo.</span></div>", unsafe_allow_html=True)
        else:
            _cm = {"critico":"#EF4444","atencion":"#F59E0B","info":"#58A6FF"}
            _bm = {"critico":"#2D1117","atencion":"#2D2007","info":"#0D1B2E"}
            _dm = {"critico":"#451B1B","atencion":"#3D2B0A","info":"#1B2D4A"}
            for _i, _a in enumerate(_alertas_mike):
                _c  = _cm.get(_a["nivel"], "#8B949E")
                _bg = _bm.get(_a["nivel"], "#161B22")
                _bd = _dm.get(_a["nivel"], "#21262D")
                st.markdown(f"<div style='background:{_bg};border-radius:12px;padding:14px 18px;border:1px solid {_bd};border-left:4px solid {_c};margin-bottom:8px;'><div style='font-size:0.88rem;font-weight:700;color:{_c};'>{_a['titulo']}</div><div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>{_a['detalle']}</div><div style='font-size:0.7rem;color:#6B7280;margin-top:3px;'>→ {_a['accion']}</div></div>", unsafe_allow_html=True)
                if st.button(f"Preguntarle a Mike →", key=f"ask_a_{_i}", help=_a["titulo"]):
                    st.session_state["mike_auto_q"] = f"Tengo esta alerta activa: {_a['titulo']} — {_a['detalle']}. Acción sugerida: {_a['accion']}. ¿Qué me recomendás hacer exactamente y cómo lo soluciono?"
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>PREGUNTAS RÁPIDAS</div>", unsafe_allow_html=True)
        _qs = [
            ("📋 Prioridades de hoy",   "¿Qué pedidos tengo que priorizar hoy y en qué orden los fabrico?"),
            ("🧵 Días de stock",         "¿Cuántos días de stock me queda en cada material al ritmo de consumo actual?"),
            ("🔴 Analizar fallos",       "Tuve fallos de fabricación esta semana. ¿Cuáles son las causas más probables y cómo los prevengo?"),
            ("💰 Mejor margen",          "¿Qué piezas debería fabricar primero para maximizar el margen del taller hoy?"),
            ("🛒 Qué comprar",           "¿Qué materiales necesito comprar esta semana y en qué cantidad para no quedarme sin stock?"),
            ("📊 Estado del taller",     "Haceme un diagnóstico rápido del estado general del taller ahora mismo."),
        ]
        _qc1, _qc2, _qc3 = st.columns(3)
        for _qi, (_ql, _qt) in enumerate(_qs):
            with [_qc1, _qc2, _qc3][_qi % 3]:
                if st.button(_ql, key=f"qs_{_qi}", use_container_width=True):
                    st.session_state["mike_auto_q"] = _qt
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>CHAT CON MIKE</div>", unsafe_allow_html=True)
        if "mike_history" not in st.session_state:
            st.session_state["mike_history"] = []
        for _msg in st.session_state["mike_history"]:
            with st.chat_message("user" if _msg["role"] == "user" else "assistant", avatar="👤" if _msg["role"] == "user" else "🤖"):
                st.markdown(_msg["content"])
        _mike_q    = st.chat_input("Escribile a Mike...", key="mike_chat_input")
        _mike_auto = st.session_state.pop("mike_auto_q", None)
        _pregunta  = _mike_q or _mike_auto
        if _pregunta:
            _mat_stock_str = ", ".join(f"{r['name']} {r['stock_gr']:.0f}g" for _, r in mats.iterrows()) if not mats.empty else "sin datos"
            _ctx = (
                f"Pedidos activos: {len(_pedidos_activos)}\n"
                f"Alertas: {len(_alertas_mike)} ({_n_crit} críticas, {_n_atc} atención)\n"
                f"Fabricaciones esta semana: {_fab_semana} ({_fallos_semana} fallos)\n"
                f"Materiales críticos: {_mat_crit_n}\n"
                f"Stock materiales: {_mat_stock_str}"
            )
            with st.chat_message("user", avatar="👤"):
                st.markdown(_pregunta)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Mike está pensando..."):
                    _resp = _preguntar_mike(_pregunta, contexto_extra=_ctx)
                st.markdown(_resp)
        if st.session_state["mike_history"]:
            if st.button("Limpiar chat", key="mike_clear"):
                st.session_state["mike_history"] = []
                st.rerun()

    # ══ TAB 6 — FINANZAS CFO ══
    with tab_stats:
        st.markdown("<div style='margin-bottom:8px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>RESUMEN FINANCIERO · TALLER</div>", unsafe_allow_html=True)
        try:
            _df_ingresos = pd.read_sql("""
                SELECT strftime('%Y-%m', o.date) AS mes,
                       SUM(oi.precio_unitario * oi.cantidad) AS facturado,
                       COUNT(DISTINCT o.id) AS pedidos
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                WHERE o.status = 'Listo'
                GROUP BY mes ORDER BY mes DESC LIMIT 12
            """, engine)
        except Exception:
            _df_ingresos = pd.DataFrame(columns=["mes","facturado","pedidos"])
        try:
            _df_costo_mat = pd.read_sql("""
                SELECT strftime('%Y-%m', pl.fecha_fin) AS mes,
                       SUM(pl.gramos_usados * m.cost_kg / 1000.0) AS costo_mat,
                       SUM(pl.gramos_usados) AS gramos_total
                FROM production_log pl
                JOIN materials m ON m.material_id = pl.material_id
                WHERE pl.fecha_fin IS NOT NULL
                GROUP BY mes ORDER BY mes DESC LIMIT 12
            """, engine)
        except Exception:
            _df_costo_mat = pd.DataFrame(columns=["mes","costo_mat","gramos_total"])
        try:
            _overhead_total = pd.read_sql("SELECT SUM(monto_mensual) AS total FROM overhead WHERE activo=1", engine).iloc[0]["total"] or 0
            _df_overhead    = pd.read_sql("SELECT concepto, monto_mensual, categoria FROM overhead WHERE activo=1 ORDER BY monto_mensual DESC", engine)
        except Exception:
            _overhead_total = 0
            _df_overhead = pd.DataFrame()
        try:
            _df_margen_prod = pd.read_sql("""
                SELECT p.sku, p.name, t.name AS socio, p.price,
                       p.weight_gr, m.cost_kg,
                       p.price - (p.weight_gr * m.cost_kg / 1000.0) AS margen_bruto,
                       CASE WHEN p.price > 0 THEN
                            ((p.price - (p.weight_gr * m.cost_kg / 1000.0)) / p.price * 100)
                       ELSE 0 END AS pct_margen
                FROM products p
                JOIN tenants t ON t.id = p.client_id
                LEFT JOIN materials m ON m.material_id = p.material_id
                WHERE p.activo = 1 AND p.price > 0
                ORDER BY margen_bruto DESC
            """, engine)
        except Exception:
            _df_margen_prod = pd.DataFrame()
        try:
            _df_por_socio = pd.read_sql("""
                SELECT t.name AS socio, o.client_id,
                       COUNT(DISTINCT o.id) AS n_pedidos,
                       SUM(oi.precio_unitario * oi.cantidad) AS facturado
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                JOIN tenants t ON t.id = o.client_id
                WHERE o.status = 'Listo'
                GROUP BY o.client_id ORDER BY facturado DESC
            """, engine)
        except Exception:
            _df_por_socio = pd.DataFrame()
        try:
            _df_stock_inv = pd.read_sql("""
                SELECT name, tipo, stock_gr, cost_kg,
                       ROUND(stock_gr * cost_kg / 1000.0, 0) AS valor_stock
                FROM materials WHERE activo=1 ORDER BY valor_stock DESC
            """, engine)
        except Exception:
            _df_stock_inv = pd.DataFrame()

        _fac_total      = float(_df_ingresos["facturado"].sum()) if not _df_ingresos.empty else 0
        _cost_mat_total = float(_df_costo_mat["costo_mat"].sum()) if not _df_costo_mat.empty else 0
        _margen_bruto   = _fac_total - _cost_mat_total - _overhead_total
        _n_ped_listo    = int(_df_ingresos["pedidos"].sum()) if not _df_ingresos.empty else 0

        _fk1, _fk2, _fk3, _fk4 = st.columns(4)
        for _fc, _fv, _fl, _fs, _fcolor in [
            (_fk1, f"${_fac_total:,.0f}",     "💰 Facturación Total",  f"{_n_ped_listo} pedidos completados", "#3FB950"),
            (_fk2, f"${_cost_mat_total:,.0f}", "🧵 Costo Materiales",   "consumo registrado en log",          "#F59E0B"),
            (_fk3, f"${_overhead_total:,.0f}", "⚙️ Overhead Mensual",   "costos fijos del taller",            "#58A6FF"),
            (_fk4, f"${_margen_bruto:,.0f}",   "📈 Margen Bruto Est.",  "facturado − mat − overhead",         "#EF4444" if _margen_bruto < 0 else "#22C55E"),
        ]:
            with _fc:
                st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;border:1px solid #21262D;border-top:3px solid {_fcolor};text-align:center;margin-bottom:8px;'><div style='font-size:1.65rem;font-weight:800;color:{_fcolor};line-height:1;'>{_fv}</div><div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_fl}</div><div style='font-size:0.64rem;color:#6B7280;margin-top:4px;'>{_fs}</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:28px;margin-bottom:12px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>📅 DETALLE MENSUAL</div>", unsafe_allow_html=True)
        if not _df_ingresos.empty or not _df_costo_mat.empty:
            _meses_all = sorted(set(
                list(_df_ingresos["mes"].tolist() if not _df_ingresos.empty else []) +
                list(_df_costo_mat["mes"].tolist() if not _df_costo_mat.empty else [])
            ), reverse=True)[:6]
            _rows_mes = []
            for _m in _meses_all:
                _fac = float(_df_ingresos[_df_ingresos["mes"]==_m]["facturado"].sum()) if not _df_ingresos.empty else 0
                _ped = int(_df_ingresos[_df_ingresos["mes"]==_m]["pedidos"].sum()) if not _df_ingresos.empty else 0
                _cm  = float(_df_costo_mat[_df_costo_mat["mes"]==_m]["costo_mat"].sum()) if not _df_costo_mat.empty else 0
                _gr  = float(_df_costo_mat[_df_costo_mat["mes"]==_m]["gramos_total"].sum()) if not _df_costo_mat.empty else 0
                _mg  = _fac - _cm - _overhead_total
                _rows_mes.append({"Mes":_m,"Pedidos":_ped,"Facturado $":f"${_fac:,.0f}","Costo Mat $":f"${_cm:,.0f}","Overhead $":f"${_overhead_total:,.0f}","Margen $":f"${_mg:,.0f}","Gramos usados":f"{_gr:,.0f} g"})
            st.dataframe(pd.DataFrame(_rows_mes), use_container_width=True, hide_index=True)
        else:
            st.info("Sin registros de ventas completadas todavía.")

        _col_soc, _col_prod = st.columns(2)
        with _col_soc:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🤝 FACTURACIÓN POR SOCIO</div>", unsafe_allow_html=True)
            if not _df_por_socio.empty:
                _fac_max = float(_df_por_socio["facturado"].max()) if _df_por_socio["facturado"].max() > 0 else 1
                for _, _sr in _df_por_socio.iterrows():
                    _pct = min(100, float(_sr["facturado"]) / _fac_max * 100)
                    st.markdown(f"""<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:6px;border:1px solid #21262D;'>
<div style='font-size:0.82rem;font-weight:700;color:#E6EDF3;margin-bottom:6px;'>{_sr['socio']} <span style='color:#6B7280;font-weight:400;font-size:0.72rem;'>· {int(_sr['n_pedidos'])} pedidos</span></div>
<div style='background:#21262D;border-radius:4px;height:6px;margin-bottom:4px;'><div style='background:#3FB950;height:6px;border-radius:4px;width:{_pct:.0f}%;'></div></div>
<div style='font-size:0.88rem;font-weight:700;color:#3FB950;'>${float(_sr['facturado']):,.0f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin ventas completadas registradas.")
        with _col_prod:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🏆 TOP PRODUCTOS POR MARGEN</div>", unsafe_allow_html=True)
            if not _df_margen_prod.empty:
                _top10  = _df_margen_prod.head(10)
                _mg_max = float(_top10["margen_bruto"].max()) if _top10["margen_bruto"].max() > 0 else 1
                for _, _pr in _top10.iterrows():
                    _pct = max(0, min(100, float(_pr["margen_bruto"]) / _mg_max * 100))
                    _mc  = "#22C55E" if float(_pr["pct_margen"]) >= 50 else ("#F59E0B" if float(_pr["pct_margen"]) >= 25 else "#EF4444")
                    st.markdown(f"""<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:6px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:700;color:#E6EDF3;'>{_pr['name']} <span style='color:#6B7280;font-size:0.68rem;'>{_pr['sku']}</span></div>
<div style='font-size:0.68rem;color:#8B949E;margin-bottom:5px;'>{_pr['socio']} · ${float(_pr['price']):,.0f} PVP</div>
<div style='background:#21262D;border-radius:4px;height:5px;margin-bottom:4px;'><div style='background:{_mc};height:5px;border-radius:4px;width:{_pct:.0f}%;'></div></div>
<div style='font-size:0.8rem;font-weight:700;color:{_mc};'>Margen ${float(_pr['margen_bruto']):,.0f} <span style='font-size:0.7rem;font-weight:400;'>({float(_pr['pct_margen']):.0f}%)</span></div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin datos de productos con material asignado.")

        _col_mat2, _col_oh = st.columns(2)
        with _col_mat2:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🧵 CAPITAL EN STOCK DE MATERIALES</div>", unsafe_allow_html=True)
            if not _df_stock_inv.empty:
                _inv_total = float(_df_stock_inv["valor_stock"].sum())
                st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:10px;border:1px solid #21262D;border-left:3px solid #F59E0B;'><span style='color:#F59E0B;font-weight:700;font-size:0.9rem;'>Total invertido en stock: ${_inv_total:,.0f}</span></div>", unsafe_allow_html=True)
                for _, _mr in _df_stock_inv.iterrows():
                    _pct_s = min(100, float(_mr["valor_stock"]) / max(1, _inv_total) * 100)
                    st.markdown(f"""<div style='background:#161B22;border-radius:8px;padding:10px 14px;margin-bottom:5px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:600;color:#C9D1D9;'>{_mr['name']}</div>
<div style='font-size:0.65rem;color:#6B7280;margin-bottom:4px;'>{_mr['stock_gr']:,.0f} g · ${float(_mr['cost_kg']):,.0f}/kg</div>
<div style='background:#21262D;border-radius:3px;height:4px;margin-bottom:3px;'><div style='background:#F59E0B;height:4px;border-radius:3px;width:{_pct_s:.0f}%;'></div></div>
<div style='font-size:0.75rem;color:#F59E0B;font-weight:700;'>${float(_mr['valor_stock']):,.0f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin materiales activos.")
        with _col_oh:
            st.markdown("<div style='margin-top:20px;margin-bottom:10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>⚙️ OVERHEAD MENSUAL FIJO</div>", unsafe_allow_html=True)
            if not _df_overhead.empty:
                st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;margin-bottom:10px;border:1px solid #21262D;border-left:3px solid #58A6FF;'><span style='color:#58A6FF;font-weight:700;font-size:0.9rem;'>Total mensual: ${_overhead_total:,.0f}</span></div>", unsafe_allow_html=True)
                for _, _ohr in _df_overhead.iterrows():
                    _pct_oh   = min(100, float(_ohr["monto_mensual"]) / max(1, _overhead_total) * 100)
                    _cat_color = {"Servicios":"#F59E0B","Maquinaria":"#EF4444","Infraestructura":"#58A6FF","Produccion":"#22C55E"}.get(_ohr.get("categoria",""), "#8B949E")
                    st.markdown(f"""<div style='background:#161B22;border-radius:8px;padding:10px 14px;margin-bottom:5px;border:1px solid #21262D;'>
<div style='font-size:0.78rem;font-weight:600;color:#C9D1D9;'>{_ohr['concepto']}</div>
<div style='font-size:0.65rem;color:{_cat_color};margin-bottom:4px;'>{_ohr.get('categoria','')}</div>
<div style='background:#21262D;border-radius:3px;height:4px;margin-bottom:3px;'><div style='background:{_cat_color};height:4px;border-radius:3px;width:{_pct_oh:.0f}%;'></div></div>
<div style='font-size:0.75rem;color:#58A6FF;font-weight:700;'>${float(_ohr['monto_mensual']):,.0f}/mes</div>
</div>""", unsafe_allow_html=True)
            else:
                st.caption("Sin overhead configurado.")

        # ── Links a páginas de socios ──────────────────────────
        st.markdown("<div style='margin-top:32px;margin-bottom:12px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>🌐 PÁGINAS WEB DE SOCIOS</div>", unsafe_allow_html=True)
        _BASE_URL = "https://silac1981.github.io/elpasaje-app"
        _paginas = [
            ("Oasis Animal",     "oasis-animal",  "#22C55E", "🐾"),
            ("Oasis del Estero", "oasis-estero",  "#10B981", "🌿"),
            ("Core Tech",        "core-tech",     "#3B82F6", "⚙️"),
            ("Coquette",         "coquette",      "#EC4899", "🎀"),
            ("Sport",            "sport",         "#F59E0B", "🏃"),
            ("Pharma DeLux",     "pharma-delux",  "#8B5CF6", "💊"),
            ("Aero Tech",        "aero-tech",     "#06B6D4", "✈️"),
            ("Melómano",         "melomano",      "#EF4444", "🎵"),
            ("Luminis",          "luminis",       "#FBBF24", "💡"),
            ("Vuelo Certero",    "vuelo-certero", "#14B8A6", "🎯"),
            ("Magnitud 19",      "magnitud19",    "#6366F1", "🏭"),
            ("El Pasaje",        "index",         "#F0F6FC", "🏠"),
        ]
        _pcols = st.columns(4)
        for _pi, (_pname, _pslug, _pcolor, _picon) in enumerate(_paginas):
            _purl = f"{_BASE_URL}/{_pslug}.html"
            with _pcols[_pi % 4]:
                st.markdown(f"""<a href="{_purl}" target="_blank" style='text-decoration:none;'>
<div style='background:#161B22;border-radius:12px;padding:16px 14px;border:1px solid #21262D;border-left:3px solid {_pcolor};margin-bottom:8px;transition:all 0.2s;cursor:pointer;'>
  <div style='font-size:1.3rem;line-height:1;'>{_picon}</div>
  <div style='font-size:0.8rem;font-weight:700;color:#E6EDF3;margin-top:6px;'>{_pname}</div>
  <div style='font-size:0.62rem;color:#6B7280;margin-top:2px;'>/{_pslug}.html</div>
</div></a>""", unsafe_allow_html=True)

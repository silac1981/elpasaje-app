"""modules/panel_fer.py â€” Panel de producciÃ³n para Fernando."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, _EC, get_linea, IP_RESTRINGIDA
from utils.mike import get_alertas_dashboard, preguntar_mike as _preguntar_mike
from utils.orders import avanzar_estado as _avanzar_estado, verificar_material_disponible as _verificar_mat


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
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stSelectbox"] div[data-baseweb="select"] div{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stDateInput"] input{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#6B7280!important}
</style>""", unsafe_allow_html=True)

    st.markdown(f"<div style='background:#161B22;border-radius:16px;padding:22px 28px;border:1px solid #21262D;border-left:4px solid #3FB950;margin-bottom:8px;'><div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;color:#3FB950;text-transform:uppercase;'>EL PASAJE 3D STUDIO Â· PRODUCCION</div><div style='font-size:1.7rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>ðŸ–¨ï¸ Centro de Fabricacion</div><div style='font-size:0.78rem;color:#8B949E;margin-top:6px;'>Fernando Â· {datetime.now().strftime('%A %d/%m/%Y')} Â· {datetime.now().strftime('%H:%M')}</div></div>", unsafe_allow_html=True)

    _hoy_str = datetime.now().strftime("%Y-%m-%d")
    from utils.pricing import cargar_materiales
    mats = cargar_materiales()
    try:
        _pedidos_all = pd.read_sql("""
            SELECT o.id, o.client_id, o.status, o.date, o.notas, o.fecha_entrega_est,
                   oi.product_sku, oi.cantidad,
                   p.name AS product_name, p.weight_gr, p.material_id,
                   p.imagen_url
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
    tab_panel, tab_fab, tab_mats, tab_cola, tab_archivos, tab_mike = st.tabs(["ðŸ› ï¸ Mi Panel", "ðŸ“¦ Cargar Fabricacion", "ðŸ§µ Materiales", "ðŸ“‹ Cola de Pedidos", "ðŸ“ Archivos", "ðŸ¤– Mike"])

    # â•â• TAB 1 â€” MI PANEL â•â•
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
            (k1, "â³ Pendientes",  str(_n_pendientes), "en espera",       "#F59E0B"),
            (k2, "ðŸ†• Hoy",        str(_nuevos_hoy),   "pedidos del dia", "#3B82F6"),
            (k3, "âœ… Fabricadas",  str(_fab_total),    "en el log",       "#22C55E"),
            (k4, "âš ï¸ Criticos",   str(_criticos),     "bajo minimo",     "#EF4444"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;border:1px solid #21262D;border-top:3px solid {_color};text-align:center;margin-bottom:8px;'><div style='font-size:2.2rem;font-weight:800;color:{_color};line-height:1;'>{_val}</div><div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_title}</div><div style='font-size:0.64rem;color:#6B7280;margin-top:4px;letter-spacing:0.5px;'>{_sub}</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:24px;margin-bottom:12px;font-size:0.68rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ðŸ“‹ COLA ACTIVA</div>", unsafe_allow_html=True)
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
            _mat_nom = _mat_mas_usado.iloc[0]["name"] if not _mat_mas_usado.empty else "â€”"
            _ult_f   = str(_ultima_fab_row.iloc[0]["fecha_fin"])[:10] if not _ultima_fab_row.empty else "â€”"
            st.markdown("<div style='background:#0D2818;border-radius:16px;padding:20px 24px;border:1px solid #238636;border-left:4px solid #3FB950;margin-bottom:16px;'><div style='font-size:1.05rem;font-weight:700;color:#3FB950;'>Sin pedidos activos â€” el taller estÃ¡ al dÃ­a âœ…</div><div style='font-size:0.82rem;color:#8B949E;margin-top:6px;'>PodÃ©s registrar fabricaciones libres desde la pestaÃ±a ðŸ“¦ Cargar Fabricacion</div></div>", unsafe_allow_html=True)
            _es1, _es2, _es3 = st.columns(3)
            _es1.metric("Piezas fabricadas", _fab_total)
            _es2.metric("Material mÃ¡s usado", _mat_nom)
            _es3.metric("Ãšltima fabricaciÃ³n", _ult_f)
        else:
            _fab_modal_pid = st.session_state.get("_fab_modal_pid")
            for _, _p in _pedidos_activos.iterrows():
                _ecfg  = _EC.get(_p["status"], _EC["Pendiente"])
                _socio = get_linea(_p["client_id"])["nombre"]
                _fecha = str(_p["date"])[:10]
                _pid   = int(_p["id"])
                _prod  = _p.get("product_name") or "-"
                _gramos  = f"{_p['weight_gr']:.0f} g" if pd.notna(_p.get("weight_gr")) else "-"
                _entrega = _p.get("fecha_entrega_est") or "-"
                with st.expander(f"{_ecfg['emoji']} Pedido #{_pid} Â· {_prod} Â· {_socio}"):
                    _c1, _c2, _c3, _c4 = st.columns(4)
                    _c1.metric("LÃ­nea", _socio)
                    _c2.metric("Gramos estimados", _gramos)
                    _c3.metric("Entrega est.", _entrega)
                    _c4.metric("Cargado", _fecha)
                    if _p.get("notas"):
                        st.caption(f"Notas: {_p['notas']}")
                    # Verificar material disponible
                    _mat_ok = _verificar_mat(_pid)
                    if not _mat_ok["ok"]:
                        st.warning(f"Material insuficiente: falta {_mat_ok.get('faltante_gr',0):.0f} g de {_mat_ok.get('material','?')}")

                    # Botones de accion directa (<=1 click)
                    _btn1, _btn2, _btn3 = st.columns(3)
                    if _p["status"] == "Pendiente":
                        if _btn1.button("Iniciar", key=f"ini_{_pid}", type="primary", use_container_width=True):
                            _r = _avanzar_estado(_pid, "En Proceso")
                            if _r["ok"]:
                                st.success(f"#{_pid} -> En Proceso")
                                st.rerun()
                            else:
                                st.error(_r["error"])
                    elif _p["status"] == "En Proceso":
                        if _btn1.button("Registrar Fab", key=f"fab_{_pid}", type="primary", use_container_width=True):
                            st.session_state["_fab_modal_pid"] = _pid
                            st.rerun()
                    elif _p["status"] == "Listo":
                        if _btn1.button("Entregar", key=f"ent_{_pid}", type="primary", use_container_width=True):
                            _r = _avanzar_estado(_pid, "Entregado")
                            if _r["ok"]:
                                st.success(f"#{_pid} -> Entregado - Venta registrada")
                                st.rerun()
                            else:
                                st.error(_r["error"])
                    if _p["status"] not in ("Entregado", "Cancelado"):
                        if _btn3.button("Cancelar", key=f"canc_{_pid}", use_container_width=True):
                            _r = _avanzar_estado(_pid, "Cancelado", motivo="Cancelado desde panel")
                            if _r["ok"]:
                                st.rerun()
                            else:
                                st.error(_r["error"])
                            st.success(f"Pedido #{_pid} â†’ {_nuevo_est}")
                            st.rerun()

        # Materiales para esta semana â€” colapsado al final del panel
        with st.expander("ðŸ“¦ Materiales para esta semana"):
            if _pedidos_activos.empty or mats.empty:
                st.caption("Sin pedidos activos o materiales registrados.")
            else:
                _sem_demanda: dict = {}
                for _, _mr in _pedidos_activos.iterrows():
                    _mmid = _mr.get("material_id")
                    _mgr  = float(_mr.get("weight_gr") or 0)
                    if _mmid and _mgr > 0:
                        _sem_demanda[_mmid] = _sem_demanda.get(_mmid, 0) + _mgr
                if not _sem_demanda:
                    st.caption("Los pedidos activos no tienen materiales asignados.")
                else:
                    for _mmid, _mneed in sorted(_sem_demanda.items(), key=lambda x: -x[1]):
                        _mrow = mats[mats["material_id"] == _mmid]
                        _mnom  = _mrow.iloc[0]["name"] if not _mrow.empty else _mmid
                        _mstk  = float(_mrow.iloc[0]["stock_gr"]) if not _mrow.empty else 0
                        _mmin  = float(_mrow.iloc[0].get("stock_minimo_gr") or 200) if not _mrow.empty else 200
                        _mok   = _mstk >= _mneed
                        _mc    = "#3FB950" if _mok else "#EF4444"
                        _mind  = "ðŸŸ¢" if _mok else "ðŸ”´"
                        st.markdown(
                            f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;"
                            f"margin-bottom:6px;border:1px solid #21262D;border-left:3px solid {_mc};'>"
                            f"<div style='display:flex;justify-content:space-between;'>"
                            f"<span style='font-size:0.82rem;font-weight:700;color:#E6EDF3;'>{_mind} {_mnom}</span>"
                            f"<span style='font-size:0.78rem;color:{_mc};font-weight:700;'>"
                            f"{'OK' if _mok else 'FALTA'}</span></div>"
                            f"<div style='font-size:0.7rem;color:#8B949E;margin-top:3px;'>"
                            f"Necesario: {_mneed:.0f} g Â· Disponible: {_mstk:.0f} g Â· MÃ­nimo: {_mmin:.0f} g</div></div>",
                            unsafe_allow_html=True,
                        )

    # â•â• TAB 2 â€” CARGAR FABRICACION (simplificado) â•â•

            # Form inline: aparece cuando se presiona "Registrar Fab"
            if _fab_modal_pid:
                _p_fab = _pedidos_all[_pedidos_all["id"] == _fab_modal_pid]
                if not _p_fab.empty:
                    _p_fab = _p_fab.iloc[0]
                    st.markdown("---")
                    st.markdown(f"**Fabricacion Pedido #{_fab_modal_pid} - {_p_fab.get('product_name','?')}**")
                    _mat_nombres = mats["name"].tolist() if not mats.empty else []
                    _mat_ids = mats["material_id"].tolist() if not mats.empty else []
                    _mid_auto = str(_p_fab.get("material_id") or "")
                    _wdef = max(float(_p_fab.get("weight_gr") or 50), 1.0)
                    _mid_idx = _mat_ids.index(_mid_auto) if _mid_auto in _mat_ids else 0
                    _mf1, _mf2 = st.columns(2)
                    with _mf1:
                        _fab_grams = st.number_input("Gramos consumidos", min_value=1.0, max_value=2000.0, value=_wdef, step=5.0, key="mfab_grams")
                        _fab_horas = st.number_input("Tiempo (horas)", min_value=0.5, max_value=24.0, value=1.0, step=0.5, key="mfab_horas")
                    with _mf2:
                        _fab_mat_nom = st.selectbox("Material", _mat_nombres, index=_mid_idx, key="mfab_mat")
                        _fab_res = st.radio("Resultado", ["Exito", "Fallo parcial", "Fallo total"], horizontal=True, key="mfab_res")
                    _mfbc1, _mfbc2 = st.columns(2)
                    if _mfbc1.button("Confirmar fabricacion", type="primary", key="mfab_confirm", use_container_width=True):
                        _fab_mid = mats.loc[mats["name"] == _fab_mat_nom, "material_id"].iloc[0] if not mats.empty else ""
                        _r = _avanzar_estado(
                            _fab_modal_pid, "Listo",
                            gramos_reales=_fab_grams,
                            tiempo_min=int(_fab_horas * 60),
                            material_id=_fab_mid,
                            resultado=_fab_res,
                        )
                        if _r["ok"]:
                            st.session_state.pop("_fab_modal_pid", None)
                            estado_final = _r["estado_final"]
                            fallo = _r.get("fallo", False)
                            msg = f"Fabricacion #{_fab_modal_pid} -> {estado_final}"
                            if fallo:
                                msg += " (fallo - regresa a Pendiente)"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(_r["error"])
                    if _mfbc2.button("Cancelar", key="mfab_cancel", use_container_width=True):
                        st.session_state.pop("_fab_modal_pid", None)
                        st.rerun()
    with tab_fab:
        st.markdown(
            "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
            "color:#58A6FF;margin-bottom:14px;'>REGISTRAR FABRICACIÃ“N</div>",
            unsafe_allow_html=True,
        )

        # Campo 1 â€” Pedido (solo En Proceso)
        _ops_ep = {"Sin pedido": None}
        if not _pedidos_activos.empty:
            _ep_df = _pedidos_activos[_pedidos_activos["status"] == "En Proceso"].drop_duplicates("id")
            for _, _r in _ep_df.iterrows():
                _linea_n = get_linea(_r["client_id"])["nombre"]
                _ops_ep[f"#{_r['id']} Â· {_r.get('product_name','â€”')} Â· {_linea_n}"] = _r["id"]
        _sel_label_f = st.selectbox("Pedido en proceso", list(_ops_ep.keys()), key="fab2_pedido")
        _sel_oid_f   = _ops_ep[_sel_label_f]

        if _sel_oid_f is not None:
            _row_f    = _pedidos_activos[_pedidos_activos["id"] == _sel_oid_f].iloc[0]
            _mid_auto = _row_f.get("material_id") or ""
            _wdef     = max(float(_row_f.get("weight_gr") or 50), 1.0)
            _sku_f    = _row_f.get("product_sku") or "LIBRE"
            _img_f    = _row_f.get("imagen_url") or ""
            _img_f    = str(_img_f) if _img_f and str(_img_f).startswith("http") else ""
        else:
            _mid_auto, _wdef, _sku_f, _img_f = "", 50.0, "LIBRE", ""

        # Miniatura del producto seleccionado
        if _img_f:
            _fi_c1, _fi_c2 = st.columns([1, 5])
            with _fi_c1:
                st.image(_img_f, width=80)
            with _fi_c2:
                st.markdown(
                    f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;"
                    f"border:1px solid #21262D;font-size:0.82rem;color:#C9D1D9;'>"
                    f"SKU: <b style='color:#58A6FF;'>{_sku_f}</b></div>",
                    unsafe_allow_html=True,
                )

        # Campo 2 â€” Resultado
        _fab2_res = st.radio(
            "Resultado",
            ["âœ… Ã‰xito", "âš ï¸ Fallo parcial", "âŒ Fallo total"],
            horizontal=True, key="fab2_res",
        )

        # Campos 3 & 4 â€” Gramos y Tiempo en 2 columnas
        _mat_nombres = mats["name"].tolist() if not mats.empty else []
        _mat_ids     = mats["material_id"].tolist() if not mats.empty else []
        _mid_idx     = _mat_ids.index(_mid_auto) if _mid_auto in _mat_ids else 0
        _fv1, _fv2 = st.columns(2)
        with _fv1:
            _fab2_grams = st.number_input(
                "Gramos consumidos", min_value=1.0, max_value=2000.0,
                value=_wdef, step=5.0, key="fab2_grams",
            )
        with _fv2:
            _fab2_horas = st.number_input(
                "Tiempo (horas)", min_value=0.5, max_value=24.0,
                value=1.0, step=0.5, key="fab2_horas",
            )

        # Slicer â€” opcional, colapsado
        with st.expander("ðŸ“Ž Importar desde slicer (opcional)"):
            try:
                from slicer_parser import parsear_archivo_slicer, match_material_idx
                _slicer_up = st.file_uploader(
                    "Archivo .gcode / .3mf", type=["gcode", "3mf"], key="fab2_slicer"
                )
                if _slicer_up is not None:
                    _sp = parsear_archivo_slicer(_slicer_up)
                    if _sp:
                        if _sp.get("gramos"):     st.session_state["fab2_grams"]  = float(_sp["gramos"])
                        if _sp.get("tiempo_min"): st.session_state["fab2_horas"]  = round(int(_sp["tiempo_min"]) / 60, 1)
                        if _sp.get("material_tipo") and _mat_nombres:
                            _mi = match_material_idx(_sp["material_tipo"], _mat_nombres)
                            st.session_state["fab2_mat_nom"] = _mat_nombres[_mi]
                        st.success("Slicer cargado â€” actualizÃ¡ los campos si es necesario.")
                    else:
                        st.warning("No se pudieron leer los datos del archivo.")
            except ImportError:
                st.caption("MÃ³dulo slicer_parser no disponible.")

        # Material
        _fab2_mat_nom = st.selectbox(
            "Material", _mat_nombres, index=_mid_idx, key="fab2_mat_nom",
        )

        # Notas â€” opcional, colapsado
        _fab2_notas = ""
        with st.expander("ðŸ“ Notas (opcional)"):
            _fab2_notas = st.text_area("", height=60, key="fab2_notas", label_visibility="collapsed")

        # Checkbox "marcar como Listo"
        _marcar_listo = False
        if "Ã‰xito" in _fab2_res and _sel_oid_f is not None:
            _marcar_listo = st.checkbox("Marcar pedido como Listo al guardar", value=True, key="fab2_marcar_listo")

        if st.button("Registrar fabricacion", type="primary", key="fab2_submit", use_container_width=True):
            _fab2_mid = mats.loc[mats["name"] == _fab2_mat_nom, "material_id"].iloc[0] if not mats.empty else ""
            _fab2_min = int(_fab2_horas * 60)
            _res_clean = _fab2_res.split(" ", 1)[1] if " " in _fab2_res else _fab2_res
            _res_str = _res_clean + (f" - {_fab2_notas}" if _fab2_notas else "")
            if _sel_oid_f is not None and _marcar_listo:
                _r2 = _avanzar_estado(
                    int(_sel_oid_f), "Listo",
                    gramos_reales=_fab2_grams,
                    tiempo_min=_fab2_min,
                    material_id=_fab2_mid,
                    resultado=_res_str,
                )
                if _r2["ok"]:
                    msg2 = f"Fabricacion: {_fab2_grams:.0f} g de {_fab2_mat_nom}"
                    if _r2.get("fallo"):
                        msg2 += " - Fallo total, pedido a Pendiente"
                    else:
                        msg2 += f" - Pedido #{_sel_oid_f} -> {_r2['estado_final']}"
                    st.success(msg2)
                else:
                    st.error(_r2["error"])
            else:
                with engine.connect() as _conn2:
                    _conn2.execute(
                        text("""INSERT INTO production_log
                               (order_id, product_sku, material_id, gramos_usados,
                                tiempo_real_min, fecha_inicio, fecha_fin, resultado)
                               VALUES (:oid, :sku, :mid, :grams, :tiempo, :fi, :ff, :res)"""),
                        {"oid": _sel_oid_f, "sku": _sku_f, "mid": _fab2_mid,
                         "grams": _fab2_grams, "tiempo": _fab2_min,
                         "fi": _hoy_str, "ff": _hoy_str, "res": _res_str},
                    )
                    _conn2.execute(
                        text("UPDATE materials SET stock_gr = stock_gr - :g WHERE material_id = :mid"),
                        {"g": _fab2_grams, "mid": _fab2_mid},
                    )
                    _conn2.commit()
                st.success(f"Registrado: {_fab2_grams:.0f} g de {_fab2_mat_nom} descontados")
            st.rerun()

        st.markdown("<div style='margin-top:24px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ÃšLTIMAS 20 FABRICACIONES</div>", unsafe_allow_html=True)
        try:
            _hist = pd.read_sql(text("""
                SELECT pl.id, pl.order_id, pl.product_sku, m.name AS material,
                       pl.gramos_usados, pl.tiempo_real_min, pl.fecha_fin, pl.resultado
                FROM production_log pl
                LEFT JOIN materials m ON m.material_id = pl.material_id
                ORDER BY pl.id DESC LIMIT 20
            """), engine)
            if _hist.empty:
                st.caption("Sin fabricaciones registradas todavia.")
            else:
                st.dataframe(
                    _hist.rename(columns={
                        "id": "#", "order_id": "Pedido", "product_sku": "SKU",
                        "material": "Material", "gramos_usados": "Gramos",
                        "tiempo_real_min": "Min", "fecha_fin": "Fecha", "resultado": "Resultado",
                    }),
                    use_container_width=True, hide_index=True,
                )
        except Exception as _e:
            st.caption(f"Sin datos: {_e}")

    # â•â• TAB 3 â€” MATERIALES â•â•
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
                _dias_est  = f"{int(_stock / (_consumido / 30))}" if _consumido > 0 else "â€”"
                _lineas_r  = _lineas_map.get(_mid, "")
                _lineas_nombres = " Â· ".join([LINEAS.get(l, {}).get("nombre", l) for l in (_lineas_r.split(",") if _lineas_r else [])])
                _kg_stock = _stock / 1000
                # barra: escala al mayor entre stock actual y 5Ã— el mÃ­nimo â€” nunca "100% = menos que el stock"
                _ref_g = max(_stock, _min_g * 5)
                _pct   = min(_stock / max(_ref_g, 1) * 100, 100)
                _mc  = "#22C55E" if _stock > _min_g * 2 else ("#F59E0B" if _stock > _min_g else "#EF4444")
                _alerta = " âš ï¸" if _stock <= _min_g else ""
                with st.expander(f"ðŸ§µ {_mat['name']}{_alerta} Â· {_kg_stock:.2f} kg ({_stock:.0f} g)"):
                    _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                    _mc1.metric("Precio/kg", f"${_ckg:,.0f}")
                    _mc2.metric("Valor en stock", f"${_valor:,.0f}")
                    _mc3.metric("Consumido este mes", f"{_consumido:.0f} g")
                    _mc4.metric("Dias de stock est.", _dias_est)
                    _bar_html = (f"<div style='background:#21262D;border-radius:999px;height:8px;overflow:hidden;margin:10px 0 6px;'>"
                                 f"<div style='width:{_pct:.0f}%;background:{_mc};height:100%;border-radius:999px;'></div></div>"
                                 f"<div style='font-size:0.72rem;color:#6B7280;'>{_stock:.0f} g disponibles Â· MÃ­nimo: {_min_g:.0f} g Â· {_kg_stock:.2f} kg</div>")
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
                        _ck_msg = f" Â· Costo/kg â†’ ${_nuevo_ck:,.0f}" if _precio_rep > 0 else ""
                        st.success(f"+{_gramos_rep}g registrados en {_mat['name']}{_ck_msg}")
                        st.rerun()

        # â”€â”€ Agregar nuevo material â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown(
            "<div style='margin:28px 0 12px;font-size:0.65rem;font-weight:700;letter-spacing:3px;"
            "text-transform:uppercase;color:#58A6FF;'>âž• AGREGAR NUEVO FILAMENTO</div>",
            unsafe_allow_html=True,
        )

        _TIPOS_MAT   = ["PLA", "PLA+", "PETG", "PETG-CF", "ABS", "ASA", "TPU", "TPE",
                        "Nylon", "Nylon-CF", "PC (Policarbonato)", "HIPS", "Compuesto/Madera",
                        "Compuesto/Metal", "Otro"]
        _COLORES_MAT = ["Negro Mate", "Negro Brillante", "Blanco", "Gris Claro", "Gris Oscuro",
                        "Gris MecÃ¡nico", "Rojo", "Azul", "Azul OcÃ©ano", "Azul Marino",
                        "Verde", "Verde Lima", "Amarillo", "Naranja", "Rosa", "Rosa BebÃ©",
                        "Lila / Violeta", "Transparente / Natural", "Bronce", "Dorado",
                        "Plateado", "Seda (iridiscente)", "Madera", "MÃ¡rmol", "Multicolor",
                        "Otro"]
        _MARCAS_MAT  = ["Bambu Lab", "eSUN", "Polymaker", "Creality", "Sunlu", "Elegoo",
                        "Hatchbox", "Prusament", "Fiberlogy", "FormFutura", "Ziro",
                        "Anycubic", "Raise3D", "3D-Fuel", "Otra"]

        with st.expander("CompletÃ¡ los datos del filamento nuevo", expanded=False):
            _nm1, _nm2 = st.columns(2)
            with _nm1:
                _nuevo_tipo_sel = st.selectbox("Tipo de material", _TIPOS_MAT, key="nm_tipo")
                _nuevo_tipo_cust = ""
                if _nuevo_tipo_sel == "Otro":
                    _nuevo_tipo_cust = st.text_input("EspecificÃ¡ el tipo", placeholder="ej: PLA Silk, PAHT, CF15...", key="nm_tipo_cust")
                _nuevo_tipo_final = _nuevo_tipo_cust.strip() if _nuevo_tipo_sel == "Otro" and _nuevo_tipo_cust.strip() else _nuevo_tipo_sel

                _nuevo_color_sel = st.selectbox("Color", _COLORES_MAT, key="nm_color_sel")
                _nuevo_color_cust = ""
                if _nuevo_color_sel == "Otro":
                    _nuevo_color_cust = st.text_input("EspecificÃ¡ el color", placeholder="ej: Terracota, Mint, Celeste...", key="nm_color_cust")
                _nuevo_color_final = _nuevo_color_cust.strip() if _nuevo_color_sel == "Otro" and _nuevo_color_cust.strip() else _nuevo_color_sel

                _nuevo_marca_sel = st.selectbox("Marca", _MARCAS_MAT, key="nm_marca_sel")
                _nuevo_marca_cust = ""
                if _nuevo_marca_sel == "Otra":
                    _nuevo_marca_cust = st.text_input("EspecificÃ¡ la marca", placeholder="ej: Giantarm, Extrudr...", key="nm_marca_cust")
                _nuevo_marca_final = _nuevo_marca_cust.strip() if _nuevo_marca_sel == "Otra" and _nuevo_marca_cust.strip() else _nuevo_marca_sel

            with _nm2:
                _nuevo_stock = st.number_input("Stock inicial (gramos)", min_value=0.0, max_value=20000.0,
                                                value=1000.0, step=100.0, key="nm_stock",
                                                help="1 bobina estÃ¡ndar = 1000 g")
                _nuevo_ckg   = st.number_input("Costo por kg ($)", min_value=0.0, max_value=200000.0,
                                                value=2500.0, step=100.0, key="nm_ckg")
                _nuevo_min   = st.number_input("Stock mÃ­nimo (g)", min_value=50.0, max_value=5000.0,
                                                value=200.0, step=50.0, key="nm_min",
                                                help="Alerta cuando el stock baje de este valor")
                _nuevo_peso_bobina = st.selectbox("Peso de bobina estÃ¡ndar", ["1000 g (1 kg)", "500 g", "250 g", "2000 g (2 kg)", "Otro"], key="nm_bobina")

            # Preview del nombre que se va a guardar
            _nombre_preview = f"{_nuevo_tipo_final} {_nuevo_color_final}"
            if _nuevo_marca_final and _nuevo_marca_final not in ("Otra", ""):
                _nombre_preview += f" Â· {_nuevo_marca_final}"
            st.markdown(
                f"<div style='background:#0D1B2E;border-radius:8px;padding:10px 14px;border:1px solid #1B2D4A;margin:8px 0;'>"
                f"<span style='font-size:0.7rem;color:#8B949E;'>Nombre que se guardarÃ¡: </span>"
                f"<span style='font-size:0.85rem;font-weight:700;color:#58A6FF;'>{_nombre_preview}</span></div>",
                unsafe_allow_html=True,
            )

            if st.button("ðŸ’¾ Guardar filamento", type="primary", use_container_width=True, key="nm_submit"):
                if not _nuevo_tipo_final or not _nuevo_color_final:
                    st.error("Tipo y color son obligatorios.")
                else:
                    _raw     = f"{_nuevo_tipo_final.lower().replace(' ', '_')}_{_nuevo_color_final.lower().replace(' ', '_')}"
                    _mid_new = "".join(c if c.isalnum() or c == "_" else "" for c in _raw)[:40]
                    try:
                        with engine.connect() as _conn:
                            _conn.execute(
                                text("""
                                    INSERT INTO materials
                                    (material_id, name, tipo, color, stock_gr, cost_kg, stock_minimo_gr, activo)
                                    VALUES (:mid, :name, :tipo, :color, :stock, :ckg, :min, 1)
                                """),
                                {"mid": _mid_new, "name": _nombre_preview,
                                 "tipo": _nuevo_tipo_final, "color": _nuevo_color_final,
                                 "stock": _nuevo_stock, "ckg": _nuevo_ckg, "min": _nuevo_min},
                            )
                            _conn.commit()
                        st.success(f"âœ… {_nombre_preview} agregado â€” {_nuevo_stock:.0f} g ({_nuevo_stock/1000:.2f} kg) en stock")
                        st.rerun()
                    except Exception as _e:
                        if "UNIQUE constraint" in str(_e):
                            st.error("Ya existe ese material. CambiÃ¡ el tipo o el color para diferenciarlo.")
                        else:
                            st.error(f"Error al guardar: {_e}")

    # â•â• TAB 4 â€” COLA INTELIGENTE â•â•
    with tab_cola:
        _cola_df = _pedidos_activos.copy() if not _pedidos_activos.empty else pd.DataFrame()

        # Banner global: demanda agregada vs stock
        if not _cola_df.empty and not mats.empty:
            _demanda_mat: dict = {}
            for _, _cr in _cola_df.iterrows():
                _cmid = _cr.get("material_id")
                _cgr  = float(_cr.get("weight_gr") or 0)
                if _cmid and _cgr > 0:
                    _demanda_mat[_cmid] = _demanda_mat.get(_cmid, 0) + _cgr
            _faltantes = []
            for _cmid, _cneed in _demanda_mat.items():
                _cmat = mats[mats["material_id"] == _cmid]
                if not _cmat.empty and float(_cmat.iloc[0]["stock_gr"]) < _cneed:
                    _faltantes.append(_cmat.iloc[0]["name"])
            if _faltantes:
                st.markdown(
                    f"<div style='background:#2D2007;border-radius:12px;padding:12px 18px;"
                    f"border:1px solid #3D2B0A;border-left:4px solid #F59E0B;margin-bottom:12px;'>"
                    f"<span style='color:#F59E0B;font-weight:700;'>âš ï¸ Stock insuficiente para la cola actual: "
                    f"{', '.join(_faltantes)}</span></div>",
                    unsafe_allow_html=True,
                )

        if _cola_df.empty:
            st.markdown(
                "<div style='background:#0D2818;border-radius:16px;padding:20px 24px;"
                "border:1px solid #238636;border-left:4px solid #3FB950;'>"
                "<div style='font-size:1.05rem;font-weight:700;color:#3FB950;'>Cola vacÃ­a â€” al dÃ­a âœ…</div>"
                "<div style='font-size:0.82rem;color:#8B949E;margin-top:6px;'>No hay pedidos pendientes ni en proceso.</div></div>",
                unsafe_allow_html=True,
            )
        else:
            # pre-cargar archivos disponibles para mostrar indicador por SKU
            try:
                _arch_skus = pd.read_sql(
                    text("SELECT DISTINCT sku FROM archivos_produccion WHERE sku IS NOT NULL"),
                    engine
                )["sku"].tolist()
            except Exception:
                _arch_skus = []

            _cola_orders = _cola_df.drop_duplicates("id")
            for _, _p in _cola_orders.iterrows():
                _pid   = _p["id"]
                _prod  = _p.get("product_name") or "â€”"
                _est   = _p["status"]
                _ecfg  = _EC.get(_est, _EC["Pendiente"])
                _linea_nom = get_linea(_p["client_id"])["nombre"]
                _gramos    = f"{_p['weight_gr']:.0f} g" if pd.notna(_p.get("weight_gr")) else "â€”"
                _fecha     = str(_p["date"])[:10]
                _img_url   = str(_p.get("imagen_url") or "")
                _img_url   = _img_url if _img_url.startswith("http") else ""

                # material indicator
                _cmid   = _p.get("material_id")
                _cgr    = float(_p.get("weight_gr") or 0)
                _mat_ok = True
                if _cmid and not mats.empty:
                    _cmat = mats[mats["material_id"] == _cmid]
                    _mat_ok = (not _cmat.empty) and float(_cmat.iloc[0]["stock_gr"]) >= _cgr
                _mat_ind = "ðŸŸ¢" if _mat_ok else "ðŸ”´"

                # IP badge y archivo badge
                _prod_lower = _prod.lower()
                _is_ip = any(ip in _prod_lower for ip in IP_RESTRINGIDA)
                _ip_badge   = " ðŸ”’" if _is_ip else ""
                _sku_p      = _p.get("product_sku") or ""
                _has_arch   = _sku_p in _arch_skus
                _arch_badge = " ðŸ“" if _has_arch else ""

                _notas_html = (f"<div style='font-size:0.72rem;color:#9CA3AF;margin-top:3px;'>{_p['notas']}</div>"
                               if _p.get("notas") else "")

                # Card con miniatura
                _card_col, _img_col = st.columns([5, 1]) if _img_url else (None, None)
                _card_container = _card_col if _img_url else st
                _card_container.markdown(
                    f"<div style='background:#161B22;border-radius:14px;padding:16px 18px;"
                    f"border:1px solid #21262D;border-left:4px solid {_ecfg['color']};margin-bottom:4px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                    f"<div><span style='font-size:0.95rem;font-weight:700;color:#F0F6FC;'>#{_pid} Â· {_prod}{_ip_badge}{_arch_badge}</span>"
                    f"<span style='margin-left:8px;font-size:0.7rem;background:{_ecfg['color']}22;color:{_ecfg['color']};"
                    f"padding:2px 8px;border-radius:99px;font-weight:600;'>{_est}</span></div>"
                    f"<span style='font-size:1.1rem;'>{_mat_ind}</span></div>"
                    f"<div style='font-size:0.75rem;color:#8B949E;margin-top:6px;'>"
                    f"ðŸ·ï¸ {_linea_nom} Â· âš–ï¸ {_gramos} Â· ðŸ“… {_fecha}</div>"
                    f"{_notas_html}</div>",
                    unsafe_allow_html=True,
                )
                if _img_url:
                    with _img_col:
                        st.image(_img_url, width=72)
                _btn_c1, _btn_c2, _btn_c3 = st.columns([2, 2, 3])
                with _btn_c1:
                    if _est == "Pendiente":
                        if st.button("â–¶ Iniciar fabricaciÃ³n", key=f"cola_ini_{_pid}", type="primary", use_container_width=True):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE orders SET status='En Proceso' WHERE id=:id"), {"id": _pid})
                                _conn.commit()
                            st.success(f"#{_pid} â†’ En Proceso")
                            st.rerun()
                with _btn_c2:
                    if _est == "En Proceso":
                        if st.button("âœ… Marcar listo", key=f"cola_listo_{_pid}", type="primary", use_container_width=True):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE orders SET status='Listo' WHERE id=:id"), {"id": _pid})
                                _conn.commit()
                            st.success(f"#{_pid} â†’ Listo")
                            st.rerun()
                with _btn_c3:
                    _nuevo_est = st.selectbox(
                        "", ["Pendiente", "En Proceso", "Listo", "Cancelado"],
                        index=["Pendiente", "En Proceso", "Listo", "Cancelado"].index(_est),
                        key=f"cola_sel_{_pid}", label_visibility="collapsed",
                    )
                    if _nuevo_est != _est:
                        if st.button("âœ“ Confirmar", key=f"cola_conf_{_pid}"):
                            with engine.connect() as _conn:
                                _conn.execute(text("UPDATE orders SET status=:s WHERE id=:id"), {"s": _nuevo_est, "id": _pid})
                                _conn.commit()
                            st.rerun()

    # â•â• TAB 5 â€” ARCHIVOS â•â•
    with tab_archivos:
        st.markdown(
            "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
            "color:#58A6FF;margin-bottom:14px;'>REPOSITORIO DE ARCHIVOS DE IMPRESIÃ“N</div>",
            unsafe_allow_html=True,
        )

        # â”€â”€ Subir archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        with st.expander("âž• Subir nuevo archivo", expanded=True):
            _arch_sku_opts = ["(sin SKU / libre)"]
            try:
                _prods_all = pd.read_sql("SELECT sku, name FROM products WHERE activo=1 ORDER BY name", engine)
                _arch_sku_opts += [f"{r['sku']} Â· {r['name']}" for _, r in _prods_all.iterrows()]
            except Exception:
                _prods_all = pd.DataFrame()

            _ua1, _ua2 = st.columns(2)
            with _ua1:
                _arch_sku_sel  = st.selectbox("SKU del producto", _arch_sku_opts, key="arch_sku_sel")
                _arch_sku_val  = _arch_sku_sel.split(" Â· ")[0] if " Â· " in _arch_sku_sel else None
            with _ua2:
                _arch_orden_sel = st.number_input("Pedido asociado (opcional)", min_value=0, value=0,
                                                   step=1, key="arch_order_n",
                                                   help="0 = sin pedido")
                _arch_orden_val = int(_arch_orden_sel) if _arch_orden_sel > 0 else None

            _arch_file = st.file_uploader(
                "Archivo .gcode / .3mf / .stl",
                type=["gcode", "3mf", "stl", "bgcode"],
                key="arch_upload",
            )
            _arch_notas = st.text_input("Notas (opcional)", key="arch_notas",
                                         placeholder="v2 optimizado, 15% infill, PETG blanco...")

            if _arch_file is not None:
                _arch_size_kb = round(_arch_file.size / 1024, 1)
                st.caption(f"TamaÃ±o: {_arch_size_kb:.1f} KB")
                if _arch_size_kb > 30_000:
                    st.warning("El archivo supera 30 MB â€” puede ser lento. ConsiderÃ¡ exportar como .3mf comprimido.")
                if st.button("ðŸ’¾ Guardar archivo", type="primary", key="arch_guardar", use_container_width=True):
                    _arch_bytes = _arch_file.read()
                    _ext = _arch_file.name.rsplit(".", 1)[-1].lower()
                    _tipo_map = {"gcode": "gcode", "bgcode": "gcode", "3mf": "3mf", "stl": "stl"}
                    _arch_tipo = _tipo_map.get(_ext, "otro")
                    with engine.connect() as _conn:
                        _conn.execute(
                            text("""INSERT INTO archivos_produccion
                                     (sku, order_id, filename, tipo, contenido, size_kb, notas, fecha)
                                     VALUES (:sku, :oid, :fn, :tipo, :cont, :size, :notas, :fecha)"""),
                            {"sku": _arch_sku_val, "oid": _arch_orden_val,
                             "fn": _arch_file.name, "tipo": _arch_tipo,
                             "cont": _arch_bytes, "size": _arch_size_kb,
                             "notas": _arch_notas or None, "fecha": _hoy_str},
                        )
                        _conn.commit()
                    st.success(f"âœ… {_arch_file.name} guardado ({_arch_size_kb:.1f} KB)")
                    st.rerun()

        # â”€â”€ Filtro â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown("<div style='margin:16px 0 10px;font-size:0.68rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;'>ARCHIVOS GUARDADOS</div>", unsafe_allow_html=True)
        try:
            _arch_lista = pd.read_sql(
                text("SELECT id, sku, order_id, filename, tipo, size_kb, notas, fecha FROM archivos_produccion ORDER BY id DESC"),
                engine,
            )
        except Exception:
            _arch_lista = pd.DataFrame()

        if _arch_lista.empty:
            st.markdown(
                "<div style='background:#161B22;border-radius:12px;padding:16px 20px;border:1px solid #21262D;'>"
                "<span style='color:#8B949E;font-size:0.82rem;'>Sin archivos guardados todavÃ­a â€” subÃ­ el primero arriba.</span></div>",
                unsafe_allow_html=True,
            )
        else:
            _filt_sku = st.selectbox("Filtrar por SKU", ["Todos"] + sorted(_arch_lista["sku"].dropna().unique().tolist()), key="arch_filt_sku")
            _filt_tipo = st.selectbox("Tipo", ["Todos"] + sorted(_arch_lista["tipo"].dropna().unique().tolist()), key="arch_filt_tipo", label_visibility="visible")
            _arch_show = _arch_lista.copy()
            if _filt_sku != "Todos":
                _arch_show = _arch_show[_arch_show["sku"] == _filt_sku]
            if _filt_tipo != "Todos":
                _arch_show = _arch_show[_arch_show["tipo"] == _filt_tipo]

            _tipo_color = {"gcode": "#3FB950", "3mf": "#58A6FF", "stl": "#F59E0B", "otro": "#8B949E"}
            for _, _af in _arch_show.iterrows():
                _tc = _tipo_color.get(_af["tipo"], "#8B949E")
                _sku_d = _af["sku"] or "â€”"
                _oid_d = f"Pedido #{int(_af['order_id'])}" if pd.notna(_af.get("order_id")) and _af["order_id"] else "Sin pedido"
                _sz_d  = f"{_af['size_kb']:.1f} KB"
                _nota_d = _af.get("notas") or ""
                _fa_c1, _fa_c2 = st.columns([5, 2])
                with _fa_c1:
                    st.markdown(
                        f"<div style='background:#161B22;border-radius:12px;padding:14px 16px;"
                        f"border:1px solid #21262D;border-left:3px solid {_tc};'>"
                        f"<div style='font-size:0.88rem;font-weight:700;color:#E6EDF3;'>{_af['filename']}</div>"
                        f"<div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>"
                        f"<span style='color:{_tc};font-weight:700;text-transform:uppercase;'>{_af['tipo']}</span>"
                        f" Â· SKU: {_sku_d} Â· {_oid_d} Â· {_sz_d} Â· {str(_af['fecha'])[:10]}</div>"
                        f"{'<div style=\"font-size:0.68rem;color:#6B7280;margin-top:3px;\">' + _nota_d + '</div>' if _nota_d else ''}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with _fa_c2:
                    # Obtener contenido para download
                    try:
                        _contenido = pd.read_sql(
                            text("SELECT contenido FROM archivos_produccion WHERE id=:id"),
                            engine, params={"id": int(_af["id"])},
                        ).iloc[0]["contenido"]
                        _mime = "application/octet-stream"
                        st.download_button(
                            "â¬‡ Descargar",
                            data=bytes(_contenido) if _contenido else b"",
                            file_name=_af["filename"],
                            mime=_mime,
                            key=f"arch_dl_{_af['id']}",
                            use_container_width=True,
                        )
                    except Exception:
                        st.caption("Error al leer")
                    # Borrar archivo
                    if st.button("ðŸ—‘", key=f"arch_del_{_af['id']}", help="Eliminar archivo"):
                        with engine.connect() as _conn:
                            _conn.execute(text("DELETE FROM archivos_produccion WHERE id=:id"), {"id": int(_af["id"])})
                            _conn.commit()
                        st.rerun()

    # â•â• TAB 6 â€” MIKE â•â•
    with tab_mike:
        _alertas_mike = get_alertas_dashboard()
        _n_crit = sum(1 for a in _alertas_mike if a["nivel"] == "critico")
        _n_atc  = sum(1 for a in _alertas_mike if a["nivel"] == "atencion")
        _est_color = "#EF4444" if _n_crit > 0 else ("#F59E0B" if _n_atc > 0 else "#3FB950")
        _est_txt   = f"{_n_crit} crÃ­tica{'s' if _n_crit!=1 else ''}" if _n_crit > 0 else ("Todo en orden" if not _n_atc else f"{_n_atc} atenciÃ³n")
        st.markdown(f"""
<div style='background:#161B22;border-radius:16px;padding:20px 24px;border:1px solid #21262D;margin-bottom:4px;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ASISTENTE DE PRODUCCION</div>
  <div style='font-size:1.5rem;font-weight:800;color:#F0F6FC;margin-top:6px;'>ðŸ¤– Mike</div>
  <div style='margin-top:10px;'>
    <span style='background:{_est_color}22;color:{_est_color};padding:4px 12px;border-radius:99px;font-weight:700;font-size:0.78rem;border:1px solid {_est_color}44;'>â— {_est_txt}</span>
    <span style='color:#6B7280;margin-left:12px;font-size:0.72rem;'>{len(_alertas_mike)} alertas Â· actualizado ahora</span>
  </div>
</div>""", unsafe_allow_html=True)
        try:
            _fab_wk = pd.read_sql("SELECT COUNT(*) AS t, SUM(CASE WHEN resultado NOT LIKE 'ok%' THEN 1 ELSE 0 END) AS f FROM production_log WHERE fecha_fin >= date('now','-7 days')", engine).iloc[0]
            _fab_semana, _fallos_semana = int(_fab_wk["t"] or 0), int(_fab_wk["f"] or 0)
        except Exception:
            _fab_semana = _fallos_semana = 0
        _tasa_txt   = f"{_fallos_semana/_fab_semana*100:.0f}%" if _fab_semana > 0 else "â€”"
        _mat_crit_n = len(mats[mats["stock_gr"] <= mats["stock_minimo_gr"]]) if not mats.empty else 0
        _mk1, _mk2, _mk3, _mk4 = st.columns(4)
        for _col, _v, _l, _c in [
            (_mk1, str(len(_pedidos_activos)), "Pedidos activos",  "#3B82F6"),
            (_mk2, str(_fab_semana),           "Fab. esta semana", "#22C55E"),
            (_mk3, _tasa_txt,                  "Tasa de fallos",   "#EF4444" if _fab_semana > 0 and _fallos_semana/_fab_semana >= 0.25 else "#4B5563"),
            (_mk4, str(_mat_crit_n),           "Mat. crÃ­ticos",   "#F59E0B" if _mat_crit_n > 0 else "#4B5563"),
        ]:
            with _col:
                st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:16px;border:1px solid #21262D;border-top:3px solid {_c};text-align:center;margin-bottom:4px;'><div style='font-size:1.8rem;font-weight:800;color:{_c};line-height:1;'>{_v}</div><div style='font-size:0.64rem;color:#8B949E;margin-top:6px;text-transform:uppercase;letter-spacing:1px;'>{_l}</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>ALERTAS ACTIVAS</div>", unsafe_allow_html=True)
        if not _alertas_mike:
            st.markdown("<div style='background:#0D2818;border-radius:12px;padding:14px 20px;border:1px solid #238636;'><span style='color:#3FB950;font-weight:700;font-size:0.88rem;'>âœ… Sin alertas</span><span style='color:#8B949E;margin-left:12px;font-size:0.8rem;'>El taller estÃ¡ en orden â€” buen trabajo.</span></div>", unsafe_allow_html=True)
        else:
            _cm = {"critico":"#EF4444","atencion":"#F59E0B","info":"#58A6FF"}
            _bm = {"critico":"#2D1117","atencion":"#2D2007","info":"#0D1B2E"}
            _dm = {"critico":"#451B1B","atencion":"#3D2B0A","info":"#1B2D4A"}
            for _i, _a in enumerate(_alertas_mike):
                _c  = _cm.get(_a["nivel"], "#8B949E")
                _bg = _bm.get(_a["nivel"], "#161B22")
                _bd = _dm.get(_a["nivel"], "#21262D")
                st.markdown(f"<div style='background:{_bg};border-radius:12px;padding:14px 18px;border:1px solid {_bd};border-left:4px solid {_c};margin-bottom:8px;'><div style='font-size:0.88rem;font-weight:700;color:{_c};'>{_a['titulo']}</div><div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>{_a['detalle']}</div><div style='font-size:0.7rem;color:#6B7280;margin-top:3px;'>â†’ {_a['accion']}</div></div>", unsafe_allow_html=True)
                if st.button(f"Preguntarle a Mike â†’", key=f"ask_a_{_i}", help=_a["titulo"]):
                    st.session_state["mike_auto_q"] = f"Tengo esta alerta activa: {_a['titulo']} â€” {_a['detalle']}. AcciÃ³n sugerida: {_a['accion']}. Â¿QuÃ© me recomendÃ¡s hacer exactamente y cÃ³mo lo soluciono?"
        st.markdown("<div style='margin:20px 0 10px;font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#58A6FF;'>PREGUNTAS RÃPIDAS</div>", unsafe_allow_html=True)
        _qs = [
            ("ðŸ“‹ Prioridades de hoy",   "Â¿QuÃ© pedidos tengo que priorizar hoy y en quÃ© orden los fabrico?"),
            ("ðŸ§µ DÃ­as de stock",         "Â¿CuÃ¡ntos dÃ­as de stock me queda en cada material al ritmo de consumo actual?"),
            ("ðŸ”´ Analizar fallos",       "Tuve fallos de fabricaciÃ³n esta semana. Â¿CuÃ¡les son las causas mÃ¡s probables y cÃ³mo los prevengo?"),
            ("ðŸ’° Mejor margen",          "Â¿QuÃ© piezas deberÃ­a fabricar primero para maximizar el margen del taller hoy?"),
            ("ðŸ›’ QuÃ© comprar",           "Â¿QuÃ© materiales necesito comprar esta semana y en quÃ© cantidad para no quedarme sin stock?"),
            ("ðŸ“Š Estado del taller",     "Haceme un diagnÃ³stico rÃ¡pido del estado general del taller ahora mismo."),
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
            with st.chat_message("user" if _msg["role"] == "user" else "assistant", avatar="ðŸ‘¤" if _msg["role"] == "user" else "ðŸ¤–"):
                st.markdown(_msg["content"])
        _mike_q    = st.chat_input("Escribile a Mike...", key="mike_chat_input")
        _mike_auto = st.session_state.pop("mike_auto_q", None)
        _pregunta  = _mike_q or _mike_auto
        if _pregunta:
            _mat_stock_str = ", ".join(f"{r['name']} {r['stock_gr']:.0f}g" for _, r in mats.iterrows()) if not mats.empty else "sin datos"
            _ctx = (
                f"Pedidos activos: {len(_pedidos_activos)}\n"
                f"Alertas: {len(_alertas_mike)} ({_n_crit} crÃ­ticas, {_n_atc} atenciÃ³n)\n"
                f"Fabricaciones esta semana: {_fab_semana} ({_fallos_semana} fallos)\n"
                f"Materiales crÃ­ticos: {_mat_crit_n}\n"
                f"Stock materiales: {_mat_stock_str}"
            )
            with st.chat_message("user", avatar="ðŸ‘¤"):
                st.markdown(_pregunta)
            with st.chat_message("assistant", avatar="ðŸ¤–"):
                with st.spinner("Mike estÃ¡ pensando..."):
                    _resp = _preguntar_mike(_pregunta, contexto_extra=_ctx)
                st.markdown(_resp)
        if st.session_state["mike_history"]:
            if st.button("Limpiar chat", key="mike_clear"):
                st.session_state["mike_history"] = []
                st.rerun()

    # TAB Finanzas CFO eliminado: costos y margenes son exclusivos del rol admin.

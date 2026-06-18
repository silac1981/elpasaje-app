"""modules/panel_socio.py — Panel de socio individual y multi-línea."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, PAGINAS_SOCIOS, _BASE_PAGES, get_linea, get_lineas_usuario, _SC, get_productos_capa2, IP_RESTRINGIDA
from utils.whatsapp import (
    get_numero_linea as _get_wa_numero,
    link_producto as _wa_link_producto,
    link_presupuesto as _wa_link_presup,
    texto_presupuesto as _wa_texto_presup,
)


def render():
    uid  = st.session_state["uid"]
    role = st.session_state["role"]

    st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background-color:#0D1117!important}
.stTabs [data-baseweb="tab-list"]{background:#161B22!important;border-radius:12px!important;padding:4px!important;gap:2px!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}
.stTabs [aria-selected="true"]{background:#21262D!important;color:#F0F6FC!important}
[data-testid="stMetricValue"]{color:#E6EDF3!important}
[data-testid="stMetricLabel"]{color:#8B949E!important}
[data-testid="stMetricDelta"]{font-size:0.8rem!important}
.stDataFrame,[data-testid="stDataFrame"]{background:#161B22!important}
.stSelectbox [data-baseweb="select"]{background:#161B22!important;border-color:#30363D!important}
[data-testid="stChatMessage"]{background:#161B22!important;border-radius:12px!important}
[data-testid="stChatMessageContent"] p{color:#E6EDF3!important}
[data-testid="stFileUploaderDropzone"]{background:#161B22!important;border-color:#30363D!important}
.stMarkdown p,.stMarkdown span{color:#C9D1D9!important}
.stMarkdown strong,.stMarkdown b{color:#F0F6FC!important}
.stSelectbox label,.stTextInput label,.stTextArea label{color:#8B949E!important;font-weight:500!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:#C9D1D9!important}
[data-testid="stAlert"]{background:#1a2332!important;border-color:#30363D!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stSelectbox"] div[data-baseweb="select"] div{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stDateInput"] input{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#6B7280!important}
</style>""", unsafe_allow_html=True)

    if role == "socio_multi":
        lineas_activas = st.session_state.get("linea_filtro", get_lineas_usuario(uid))
        sel_nombre     = st.session_state.get("linea_sel", "Todas")
        if sel_nombre == "Todas":
            hdr_nombre = "Mis Líneas"
            hdr_emoji  = LINEAS.get(uid, {}).get("emoji", "✨")
            hdr_color  = LINEAS.get(uid, {}).get("color", "#6366F1")
        else:
            lid        = lineas_activas[0] if lineas_activas else uid
            _lc        = LINEAS.get(lid, {"nombre": sel_nombre, "emoji": "●", "color": "#6366F1"})
            hdr_nombre = _lc["nombre"]
            hdr_emoji  = _lc["emoji"]
            hdr_color  = _lc["color"]
    else:
        lineas_activas = [uid]
        cfg            = get_linea(uid)
        hdr_nombre, hdr_emoji, hdr_color = cfg["nombre"], cfg["emoji"], cfg["color"]

    _hoy_s = datetime.now().strftime("%Y-%m-%d")
    _mes_s = datetime.now().strftime("%Y-%m")

    _FEMENINO_UIDS = {"oasis_animal", "agustina", "olivia_coquette"}
    _saludo = "Bienvenida" if uid in _FEMENINO_UIDS else "Bienvenido"
    st.markdown(f"""
<div style='background:linear-gradient(135deg,{hdr_color}dd,{hdr_color}88);
     border-radius:20px;padding:24px 32px;margin-bottom:4px;
     border:1px solid {hdr_color}44;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;
       text-transform:uppercase;color:rgba(255,255,255,0.7);'>EL PASAJE 3D STUDIO · SOCIO</div>
  <div style='font-size:2rem;font-weight:800;color:white;margin-top:8px;'>{hdr_emoji} {hdr_nombre}</div>
  <div style='font-size:0.8rem;color:rgba(255,255,255,0.75);margin-top:4px;'>
    {_saludo}, {st.session_state['user']}! &nbsp;·&nbsp; {datetime.now().strftime('%A %d/%m/%Y')}
  </div>
</div>""", unsafe_allow_html=True)

    from utils.pricing import cargar_productos
    df_all = cargar_productos()
    prod   = df_all[df_all["client_id"].isin(lineas_activas)].copy()

    _lid_str = "','".join(lineas_activas)
    try:
        _pedidos_s = pd.read_sql(f"""
            SELECT o.id, o.client_id, o.status, o.date, o.fecha_entrega_est, o.notas,
                   o.canal_origen,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total,
                   pag.estado AS pago_estado, pag.metodo AS pago_metodo
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            LEFT JOIN pagos pag ON pag.order_id = o.id
            WHERE o.client_id IN ('{_lid_str}')
            GROUP BY o.id ORDER BY o.date DESC
        """, engine)
    except Exception:
        try:
            _pedidos_s = pd.read_sql(f"""
                SELECT o.id, o.client_id, o.status, o.date, o.fecha_entrega_est, o.notas,
                       o.canal_origen,
                       COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.client_id IN ('{_lid_str}')
                GROUP BY o.id ORDER BY o.date DESC
            """, engine)
        except Exception:
            _pedidos_s = pd.DataFrame()

    try:
        _items_socio = pd.read_sql(f"""
            SELECT oi.order_id, oi.product_sku, oi.cantidad, oi.precio_unitario,
                   COALESCE(p.name, oi.product_sku) AS producto,
                   p.imagen_url
            FROM order_items oi
            LEFT JOIN products p ON p.sku = oi.product_sku
            JOIN orders o ON o.id = oi.order_id
            WHERE o.client_id IN ('{_lid_str}')
            ORDER BY oi.order_id, oi.id
        """, engine)
    except Exception:
        _items_socio = pd.DataFrame()

    try:
        _hist_mes = pd.read_sql(f"""
            SELECT strftime('%Y-%m', o.date) AS mes,
                   COUNT(DISTINCT o.id) AS pedidos,
                   SUM(oi.cantidad * oi.precio_unitario) AS facturado
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.client_id IN ('{_lid_str}') AND o.status='Listo'
            GROUP BY mes ORDER BY mes
        """, engine)
    except Exception:
        _hist_mes = pd.DataFrame()

    try:
        _fab_socio = pd.read_sql(f"""
            SELECT pl.product_sku, pl.gramos_usados, pl.resultado, pl.fecha_fin,
                   p.name AS producto
            FROM production_log pl
            JOIN orders o ON o.id = pl.order_id
            JOIN products p ON p.sku = pl.product_sku
            WHERE o.client_id IN ('{_lid_str}')
            ORDER BY pl.fecha_fin DESC
        """, engine)
    except Exception:
        _fab_socio = pd.DataFrame()

    try:
        _prec_hist = pd.read_sql(f"""
            SELECT ph.product_sku, p.name AS producto,
                   ph.precio_anterior, ph.precio_nuevo, ph.fecha, ph.motivo
            FROM price_history ph
            JOIN products p ON p.sku = ph.product_sku
            WHERE p.client_id IN ('{_lid_str}')
            ORDER BY ph.fecha DESC LIMIT 20
        """, engine)
    except Exception:
        _prec_hist = pd.DataFrame()

    try:
        _senales_sm = pd.read_sql(
            "SELECT fecha, linea, producto, reaccion, segmento_detectado, oportunidad, canal "
            "FROM senales_mercado ORDER BY fecha DESC LIMIT 20",
            engine,
        )
        if not _senales_sm.empty:
            _lineas_nombres = {LINEAS.get(l, {}).get("nombre", l) for l in lineas_activas}
            _senales_sm = _senales_sm[
                _senales_sm["linea"].isin(_lineas_nombres) |
                _senales_sm["linea"].isin(lineas_activas)
            ].reset_index(drop=True)
    except Exception:
        _senales_sm = pd.DataFrame()

    _cap_stock  = float(prod["valor_stock"].sum()) if not prod.empty else 0
    _gan_stock  = float(prod["ganancia_stock"].sum()) if not prod.empty and "ganancia_stock" in prod.columns else 0
    _margen_avg = float(prod["margen_pct"].mean()) if not prod.empty and "margen_pct" in prod.columns else 0
    _n_skus     = len(prod[prod["activo"]==1]) if "activo" in prod.columns else len(prod)
    _n_activos  = len(_pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])]) if not _pedidos_s.empty else 0
    _n_listo    = len(_pedidos_s[_pedidos_s["status"]=="Listo"]) if not _pedidos_s.empty else 0
    _fac_total  = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum()) if not _pedidos_s.empty else 0

    _page_slug_s = PAGINAS_SOCIOS.get(uid if role != "socio_multi" else lineas_activas[0] if len(lineas_activas)==1 else uid)
    if _page_slug_s:
        _page_url_s = f"{_BASE_PAGES}/{_page_slug_s}.html"
        st.markdown(f"""<a href="{_page_url_s}" target="_blank" style="text-decoration:none;">
<div style="background:linear-gradient(90deg,#161B22,{hdr_color}22);border-radius:12px;
     padding:12px 20px;border:1px solid {hdr_color}44;margin-bottom:12px;
     display:flex;align-items:center;gap:12px;">
  <span style="font-size:1.2rem;">🌐</span>
  <div>
    <div style="font-size:0.72rem;font-weight:700;color:{hdr_color};letter-spacing:1px;">TU PÁGINA WEB</div>
    <div style="font-size:0.78rem;color:#8B949E;margin-top:1px;">{_page_url_s}</div>
  </div>
  <div style="margin-left:auto;background:{hdr_color}22;color:{hdr_color};padding:6px 16px;
       border-radius:99px;font-size:0.7rem;font-weight:700;border:1px solid {hdr_color}44;">
    Abrir →
  </div>
</div></a>""", unsafe_allow_html=True)

    _sk1, _sk2, _sk3, _sk4 = st.columns(4)
    for _sc_col, _sv, _sl, _ss, _scolor in [
        (_sk1, f"${_cap_stock:,.0f}",  "💰 Valor Stock",     "precio venta × unidades",   hdr_color),
        (_sk2, str(_n_skus),           "📦 Productos",       "activos en tu catálogo",    hdr_color),
        (_sk3, f"${_fac_total:,.0f}",  "✅ Facturado Total", f"{_n_listo} pedidos listos","#3B82F6"),
        (_sk4, str(_n_activos),        "🏭 En Producción",   "pedidos activos hoy",       "#F59E0B"),
    ]:
        with _sc_col:
            st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:18px 14px;border:1px solid #21262D;border-top:3px solid {_scolor};text-align:center;margin-bottom:8px;'><div style='font-size:1.5rem;font-weight:800;color:{_scolor};line-height:1;'>{_sv}</div><div style='font-size:0.72rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_sl}</div><div style='font-size:0.62rem;color:#8B949E;margin-top:3px;'>{_ss}</div></div>", unsafe_allow_html=True)

    _t_res, _t_stats, _t_prod, _t_ped, _t_tienda, _t_presup, _t_mike, _t_linea = st.tabs([
        "🏠 Resumen", "📊 Estadísticas", "📦 Productos", "🛒 Pedidos",
        "🏪 Mi Tienda", "🧮 Presupuesto", "🤖 Mike", "⚙️ Mi Línea",
    ])

    # ══ TAB RESUMEN ══
    with _t_res:
        # ── Pantalla partida para socio_multi con múltiples líneas ──
        if role == "socio_multi" and len(lineas_activas) > 1:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;"
                "text-transform:uppercase;color:#8B949E;margin-bottom:10px;'>"
                "TUS LÍNEAS — elegí cuál querés ver o navegá el panel completo</div>",
                unsafe_allow_html=True,
            )
            _lcard_cols = st.columns(len(lineas_activas))
            for _lci, _lid_c in enumerate(lineas_activas):
                _lcc  = LINEAS.get(_lid_c, {"nombre": _lid_c, "emoji": "●", "color": "#6366F1"})
                _lcp  = prod[prod["client_id"] == _lid_c]
                _lcp_stk   = float(_lcp["valor_stock"].sum()) if not _lcp.empty else 0
                _lcp_n     = len(_lcp[_lcp["activo"] == 1]) if not _lcp.empty and "activo" in _lcp.columns else len(_lcp)
                _lcp_ped   = len(_pedidos_s[(_pedidos_s["client_id"] == _lid_c) & (_pedidos_s["status"].isin(["Pendiente","En Proceso"]))]) if not _pedidos_s.empty else 0
                _lcp_fac   = float(_pedidos_s[(_pedidos_s["client_id"] == _lid_c) & (_pedidos_s["status"].isin(["Listo","Entregado"]))]["total"].sum()) if not _pedidos_s.empty else 0
                _lc_glow   = f"0 0 16px {_lcc['color']}44"
                with _lcard_cols[_lci]:
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,{_lcc['color']}22,{_lcc['color']}08);"
                        f"border-radius:16px;padding:18px 16px;border:1px solid {_lcc['color']}44;"
                        f"box-shadow:{_lc_glow};margin-bottom:8px;'>"
                        f"<div style='font-size:1.6rem;line-height:1;'>{_lcc['emoji']}</div>"
                        f"<div style='font-size:1rem;font-weight:800;color:#E6EDF3;margin-top:6px;'>"
                        f"{_lcc['nombre']}</div>"
                        f"<div style='margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:6px;'>"
                        f"<div style='background:#0D1117;border-radius:8px;padding:8px;text-align:center;'>"
                        f"<div style='font-size:1.1rem;font-weight:800;color:{_lcc['color']};'>{_lcp_n}</div>"
                        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-top:1px;'>productos</div></div>"
                        f"<div style='background:#0D1117;border-radius:8px;padding:8px;text-align:center;'>"
                        f"<div style='font-size:1.1rem;font-weight:800;color:#F59E0B;'>{_lcp_ped}</div>"
                        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-top:1px;'>en producc.</div></div>"
                        f"<div style='background:#0D1117;border-radius:8px;padding:8px;text-align:center;'>"
                        f"<div style='font-size:0.85rem;font-weight:800;color:#10B981;'>${_lcp_stk:,.0f}</div>"
                        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-top:1px;'>valor stock</div></div>"
                        f"<div style='background:#0D1117;border-radius:8px;padding:8px;text-align:center;'>"
                        f"<div style='font-size:0.85rem;font-weight:800;color:#3B82F6;'>${_lcp_fac:,.0f}</div>"
                        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-top:1px;'>facturado</div></div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"Ver {_lcc['nombre']} →",
                        key=f"res_ver_{_lid_c}",
                        use_container_width=True,
                    ):
                        st.session_state["linea_filtro"] = [_lid_c]
                        st.session_state["linea_sel"]    = _lcc["nombre"]
                        st.rerun()
            st.markdown("<div style='height:8px;border-top:1px solid #21262D;margin-bottom:12px;'></div>", unsafe_allow_html=True)

        _ra, _rb = st.columns([1.4, 1])
        with _ra:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>PEDIDOS ACTIVOS</div>", unsafe_allow_html=True)
            _pact = _pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])] if not _pedidos_s.empty else pd.DataFrame()
            if _pact.empty:
                st.markdown("<div style='background:#0D2818;border-radius:12px;padding:16px 20px;border:1px solid #238636;border-left:4px solid #3FB950;'><span style='color:#3FB950;font-weight:700;'>✅ Sin pedidos en curso</span><br><span style='color:#8B949E;font-size:0.8rem;'>Podés cargar un nuevo pedido desde el menú 🛒</span></div>", unsafe_allow_html=True)
            else:
                for _, _pr in _pact.iterrows():
                    _sc2      = _SC.get(_pr["status"], "#9CA3AF")
                    _fecha2   = str(_pr["date"])[:10] if _pr["date"] else "—"
                    _entrega2 = str(_pr.get("fecha_entrega_est", "—") or "—")
                    _oid_r    = int(_pr["id"])
                    _res_items = (
                        _items_socio[_items_socio["order_id"] == _oid_r]
                        if not _items_socio.empty else pd.DataFrame()
                    )
                    _res_items_html = ""
                    if not _res_items.empty:
                        _rparts = [
                            f"<span style='color:#F59E0B;font-weight:700;'>{int(_ri['cantidad'])}×</span>"
                            f" <span style='color:#E6EDF3;'>{_ri['producto']}</span>"
                            f"<span style='color:#6B7280;font-size:0.68rem;'> · ${float(_ri['precio_unitario']):,.0f}</span>"
                            for _, _ri in _res_items.iterrows()
                        ]
                        _res_items_html = (
                            "<div style='margin-top:7px;padding:7px 10px;background:#0D1117;"
                            "border-radius:7px;border:1px solid #21262D;font-size:0.78rem;"
                            "display:flex;flex-direction:column;gap:3px;'>"
                            + "".join(f"<div>{p}</div>" for p in _rparts)
                            + "</div>"
                        )
                    _not_r = (
                        f"<div style='font-size:0.7rem;color:#8B949E;margin-top:5px;"
                        f"padding:5px 8px;background:#161B22;border-radius:5px;"
                        f"border:1px dashed #30363D;'><em>{_pr['notas']}</em></div>"
                    ) if _pr.get("notas") else ""
                    st.markdown(
                        f"<div style='background:#161B22;border-radius:12px;padding:14px 18px;"
                        f"margin-bottom:8px;border-left:4px solid {_sc2};border:1px solid #21262D;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div style='flex:1;min-width:0;'>"
                        f"<div style='font-weight:700;font-size:0.95rem;color:#E6EDF3;'>"
                        f"Pedido #{_oid_r} "
                        f"<span style='background:{_sc2}22;color:{_sc2};border:1px solid {_sc2}44;"
                        f"border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:600;"
                        f"margin-left:6px;'>{_pr['status']}</span></div>"
                        f"<div style='font-size:0.73rem;color:#8B949E;margin-top:3px;'>"
                        f"📅 {_fecha2} &nbsp;·&nbsp; 🎯 entrega {_entrega2}</div>"
                        f"{_res_items_html}"
                        f"{_not_r}"
                        f"</div>"
                        f"<div style='font-size:1.3rem;font-weight:800;color:{_sc2};"
                        f"margin-left:14px;white-space:nowrap;padding-top:2px;'>"
                        f"${float(_pr['total']):,.0f}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
        with _rb:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>ESTADO DE TU CATÁLOGO</div>", unsafe_allow_html=True)
            if not prod.empty:
                _top3 = prod.sort_values("price", ascending=False).head(3)
                for _, _p3 in _top3.iterrows():
                    _pstk3 = int(_p3.get("stock", 0) or 0)
                    _stk_c3 = "#10B981" if _pstk3 > 5 else ("#F59E0B" if _pstk3 > 0 else "#EF4444")
                    st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;margin-bottom:6px;border:1px solid #21262D;'><div style='font-size:0.8rem;font-weight:600;color:#E6EDF3;'>{_p3['name']}</div><div style='font-size:0.72rem;color:#8B949E;margin-top:3px;'>${_p3['price']:,.0f} · <span style='color:{_stk_c3};font-weight:700;'>{_pstk3} u stock</span></div></div>", unsafe_allow_html=True)
                _stock_bajo = prod[prod["stock"] <= 2] if "stock" in prod.columns else pd.DataFrame()
                if not _stock_bajo.empty:
                    st.markdown(f"<div style='background:#2D2007;border-radius:10px;padding:10px 14px;border-left:3px solid #F59E0B;margin-top:6px;border:1px solid #3D2B0A;'><span style='color:#F59E0B;font-weight:700;font-size:0.8rem;'>⚠️ Stock bajo: {', '.join(_stock_bajo['name'].tolist()[:3])}</span></div>", unsafe_allow_html=True)
        if not _fab_socio.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:10px;'>ÚLTIMAS FABRICACIONES</div>", unsafe_allow_html=True)
            _fab_show = _fab_socio.head(5).copy()
            _fab_show["resultado"]    = _fab_show["resultado"].fillna("ok")
            _fab_show["fecha_fin"]    = _fab_show["fecha_fin"].astype(str).str[:10]
            _fab_show["gramos_usados"]= _fab_show["gramos_usados"].apply(lambda x: f"{x:.0f} g" if pd.notna(x) else "—")
            st.dataframe(
                _fab_show[["fecha_fin","producto","gramos_usados","resultado"]].rename(
                    columns={"fecha_fin":"Fecha","producto":"Producto","gramos_usados":"Gramos","resultado":"Resultado"}
                ), use_container_width=True, hide_index=True
            )

    # ══ TAB ESTADÍSTICAS ══
    with _t_stats:
        # ── Cálculos pre-tab ────────────────────────────────────────
        _all_listo_s   = _pedidos_s[_pedidos_s["status"].isin(["Listo","Entregado"])] if not _pedidos_s.empty else pd.DataFrame()
        _fac_total_all = float(_all_listo_s["total"].sum()) if not _all_listo_s.empty else 0
        _n_completados = len(_all_listo_s)
        _ticket_prom   = _fac_total_all / _n_completados if _n_completados > 0 else 0

        _best_mes_val, _best_mes_nom = 0, "—"
        if not _hist_mes.empty:
            _bm_idx      = _hist_mes["facturado"].idxmax()
            _best_mes_val = float(_hist_mes.loc[_bm_idx, "facturado"])
            _best_mes_nom = str(_hist_mes.loc[_bm_idx, "mes"])

        _mes_actual_fac, _mes_ant_fac, _growth_pct = 0.0, 0.0, 0.0
        if not _hist_mes.empty:
            _ms = _hist_mes.sort_values("mes")
            _mes_actual_fac = float(_ms.iloc[-1]["facturado"])
            if len(_ms) >= 2:
                _mes_ant_fac = float(_ms.iloc[-2]["facturado"])
                _growth_pct = (_mes_actual_fac - _mes_ant_fac) / _mes_ant_fac * 100 if _mes_ant_fac > 0 else 0

        _top_prods = pd.DataFrame()
        if not _items_socio.empty:
            _top_prods = (
                _items_socio
                .assign(_ing=_items_socio["cantidad"] * _items_socio["precio_unitario"])
                .groupby("producto")
                .agg(unidades=("cantidad", "sum"), ingresos=("_ing", "sum"))
                .sort_values("unidades", ascending=False)
                .head(5).reset_index()
            )

        _canales_df = pd.DataFrame()
        if not _pedidos_s.empty and "canal_origen" in _pedidos_s.columns:
            _cx = _pedidos_s[_pedidos_s["canal_origen"].notna() & (_pedidos_s["canal_origen"] != "")]
            if not _cx.empty:
                _canales_df = _cx.groupby("canal_origen").size().reset_index(name="n").sort_values("n", ascending=False)

        _total_gramos_fab = float(_fab_socio["gramos_usados"].fillna(0).sum()) if not _fab_socio.empty else 0

        # ── Helper: KPI neon card ────────────────────────────────────
        def _neon_kpi(col, value, label, color, icon, sub=""):
            _glow = f"0 0 14px {color}66, 0 0 28px {color}22"
            _sub_h = f"<div style='font-size:0.68rem;color:#555;margin-top:3px;'>{sub}</div>" if sub else ""
            with col:
                st.markdown(
                    f"<div style='background:#050508;border-radius:16px;padding:22px 14px;"
                    f"border:1px solid {color}44;box-shadow:{_glow};text-align:center;margin-bottom:4px;'>"
                    f"<div style='font-size:1.6rem;line-height:1;'>{icon}</div>"
                    f"<div style='font-size:1.55rem;font-weight:900;color:{color};line-height:1.1;"
                    f"margin-top:6px;text-shadow:0 0 10px {color}88;'>{value}</div>"
                    f"<div style='font-size:0.6rem;font-weight:700;color:#444;text-transform:uppercase;"
                    f"letter-spacing:1.5px;margin-top:7px;'>{label}</div>"
                    f"{_sub_h}</div>",
                    unsafe_allow_html=True,
                )

        # ── Fila 1: KPIs neon ────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.6rem;font-weight:700;letter-spacing:3px;color:#39FF14;"
            "text-transform:uppercase;margin-bottom:12px;'>⚡ TUS NÚMEROS</div>",
            unsafe_allow_html=True,
        )
        _ka, _kb, _kc, _kd = st.columns(4)
        _neon_kpi(_ka, f"${_fac_total_all:,.0f}", "Total facturado", "#39FF14", "💰",
                  f"{_n_completados} pedidos completados")
        _neon_kpi(_kb, f"${_ticket_prom:,.0f}", "Ticket promedio", "#00FFFF", "🎯",
                  "por pedido completado")
        _neon_kpi(_kc, f"${_best_mes_val:,.0f}", "Mejor mes", "#FF10F0", "🏆", _best_mes_nom)
        _gw_icon  = "📈" if _growth_pct >= 0 else "📉"
        _gw_color = "#39FF14" if _growth_pct >= 0 else "#FF4444"
        _gw_str   = f"+{_growth_pct:.0f}%" if _growth_pct >= 0 else f"{_growth_pct:.0f}%"
        _neon_kpi(_kd, _gw_str, "vs mes anterior", _gw_color, _gw_icon, "tendencia mensual")

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # ── Fila 2: Gráfico mensual + Canales ───────────────────────
        _sc1, _sc2 = st.columns([3, 2])
        with _sc1:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#00FFFF;"
                "text-transform:uppercase;margin-bottom:8px;'>📊 FACTURACIÓN MENSUAL</div>",
                unsafe_allow_html=True,
            )
            if not _hist_mes.empty:
                _chart_df = _hist_mes.sort_values("mes").set_index("mes")[["facturado"]].rename(
                    columns={"facturado": "$ Facturado"}
                )
                st.bar_chart(_chart_df, color="#00FFFF", height=200)
            else:
                st.markdown(
                    "<div style='background:#050508;border-radius:12px;padding:40px;text-align:center;"
                    "border:1px dashed #222;color:#444;font-size:0.8rem;'>Sin pedidos completados aún</div>",
                    unsafe_allow_html=True,
                )
        with _sc2:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#FF10F0;"
                "text-transform:uppercase;margin-bottom:8px;'>📡 DE DÓNDE VIENEN TUS CLIENTES</div>",
                unsafe_allow_html=True,
            )
            _canal_colors_map = {
                "Instagram":                "#E1306C",
                "TikTok":                   "#00F2EA",
                "Recomendación personal":   "#39FF14",
                "WhatsApp directo":         "#25D366",
                "WhatsApp":                 "#25D366",
                "Ya era cliente / familia": "#FF10F0",
                "Presencial / evento":      "#FFE600",
                "Presencial":               "#FFE600",
                "Otro":                     "#888",
            }
            if _canales_df.empty:
                st.markdown(
                    "<div style='color:#444;font-size:0.8rem;padding:12px;'>Sin datos de canal todavía.<br>"
                    "<span style='font-size:0.7rem;'>Se registran al cargar pedidos.</span></div>",
                    unsafe_allow_html=True,
                )
            else:
                _canal_total_n = _canales_df["n"].sum()
                for _, _cr in _canales_df.iterrows():
                    _cc = _canal_colors_map.get(_cr["canal_origen"], "#888")
                    _pct_c = int(_cr["n"] / _canal_total_n * 100) if _canal_total_n else 0
                    st.markdown(
                        f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
                        f"<span style='font-size:0.78rem;color:#C9D1D9;'>{_cr['canal_origen']}</span>"
                        f"<span style='font-size:0.75rem;font-weight:800;color:{_cc};'>"
                        f"{int(_cr['n'])} · {_pct_c}%</span></div>"
                        f"<div style='background:#0D0D12;border-radius:99px;height:5px;'>"
                        f"<div style='background:{_cc};width:{_pct_c}%;height:5px;border-radius:99px;"
                        f"box-shadow:0 0 6px {_cc}99;'></div></div></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # ── Fila 3: Top productos + Pipeline ────────────────────────
        _st1, _st2 = st.columns([3, 2])
        with _st1:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#FFE600;"
                "text-transform:uppercase;margin-bottom:8px;'>🏅 TUS PRODUCTOS MÁS PEDIDOS</div>",
                unsafe_allow_html=True,
            )
            if _top_prods.empty:
                st.markdown(
                    "<div style='color:#444;font-size:0.8rem;padding:12px;'>Aún sin items de pedidos.</div>",
                    unsafe_allow_html=True,
                )
            else:
                _max_u = float(_top_prods["unidades"].max())
                _rank_c = ["#FFE600", "#C0C0C0", "#CD7F32", "#6B7280", "#444"]
                for _ri, (_, _tp) in enumerate(_top_prods.iterrows()):
                    _rc    = _rank_c[min(_ri, 4)]
                    _bw    = int(_tp["unidades"] / _max_u * 100) if _max_u > 0 else 0
                    _nom_t = str(_tp["producto"])[:32]
                    st.markdown(
                        f"<div style='margin-bottom:7px;padding:10px 14px;background:#050508;"
                        f"border-radius:10px;border:1px solid {_rc}33;"
                        f"box-shadow:0 0 8px {_rc}22;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<div style='display:flex;align-items:center;gap:10px;'>"
                        f"<span style='font-size:1rem;font-weight:900;color:{_rc};min-width:22px;'>#{_ri+1}</span>"
                        f"<div><div style='font-size:0.82rem;color:#E6EDF3;font-weight:600;'>{_nom_t}</div>"
                        f"<div style='font-size:0.65rem;color:#555;'>${float(_tp['ingresos']):,.0f} facturado</div></div>"
                        f"</div>"
                        f"<span style='font-size:1.1rem;font-weight:900;color:{_rc};"
                        f"text-shadow:0 0 8px {_rc}88;'>{int(_tp['unidades'])} u</span></div>"
                        f"<div style='margin-top:6px;background:#0D0D12;border-radius:99px;height:4px;'>"
                        f"<div style='background:{_rc};width:{_bw}%;height:4px;border-radius:99px;"
                        f"box-shadow:0 0 5px {_rc}99;'></div></div></div>",
                        unsafe_allow_html=True,
                    )
        with _st2:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#FF6B35;"
                "text-transform:uppercase;margin-bottom:8px;'>🔄 ESTADO DEL PIPELINE</div>",
                unsafe_allow_html=True,
            )
            _pipe_cfg = [
                ("Pendiente",  "#FFE600", "⏳"),
                ("En Proceso", "#00FFFF", "🖨️"),
                ("Listo",      "#39FF14", "✅"),
                ("Entregado",  "#FF10F0", "📦"),
                ("Cancelado",  "#FF4444", "❌"),
            ]
            if not _pedidos_s.empty:
                for _dst, _dc_n, _dc_e in _pipe_cfg:
                    _dn2 = len(_pedidos_s[_pedidos_s["status"] == _dst])
                    if _dn2 == 0 and _dst == "Cancelado":
                        continue
                    st.markdown(
                        f"<div style='display:flex;align-items:center;justify-content:space-between;"
                        f"background:#050508;border-radius:10px;padding:10px 14px;"
                        f"border:1px solid {_dc_n}33;box-shadow:0 0 8px {_dc_n}22;margin-bottom:6px;'>"
                        f"<span style='font-size:0.82rem;color:#C9D1D9;'>{_dc_e} {_dst}</span>"
                        f"<span style='font-size:1.35rem;font-weight:900;color:{_dc_n};"
                        f"text-shadow:0 0 8px {_dc_n}88;'>{_dn2}</span></div>",
                        unsafe_allow_html=True,
                    )

            if _total_gramos_fab > 0:
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                _kg = _total_gramos_fab / 1000
                st.markdown(
                    f"<div style='background:#050508;border-radius:12px;padding:14px;"
                    f"border:1px solid #FF6B3544;box-shadow:0 0 10px #FF6B3522;text-align:center;'>"
                    f"<div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:1.5px;'>"
                    f"imprimimos para vos</div>"
                    f"<div style='font-size:1.4rem;font-weight:900;color:#FF6B35;"
                    f"text-shadow:0 0 8px #FF6B3588;margin-top:4px;'>{_kg:.2f} kg</div>"
                    f"<div style='font-size:0.62rem;color:#444;margin-top:2px;'>de filamento 3D</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        # ── Fila 4: Historial de precios (cards) + Producción ───────
        _exp1, _exp2 = st.columns(2)
        with _exp1:
            if not _prec_hist.empty:
                st.markdown(
                    "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#FBBF24;"
                    "text-transform:uppercase;margin-bottom:8px;'>💲 EVOLUCIÓN DE PRECIOS</div>",
                    unsafe_allow_html=True,
                )
                for _, _ph in _prec_hist.iterrows():
                    _pa  = float(_ph["precio_anterior"])
                    _pn  = float(_ph["precio_nuevo"])
                    _dlt = _pn - _pa
                    _pct = (_dlt / _pa * 100) if _pa > 0 else 0
                    _up  = _dlt >= 0
                    _dc  = "#10B981" if _up else "#F59E0B"
                    _arr = "▲" if _up else "▼"
                    _sig = "+" if _up else ""
                    _mot = str(_ph.get("motivo") or "")[:48]
                    _fec = str(_ph["fecha"])[:10]
                    st.markdown(
                        f"<div style='background:#050508;border-radius:10px;padding:10px 14px;"
                        f"border:1px solid {_dc}33;box-shadow:0 0 8px {_dc}11;margin-bottom:6px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div style='flex:1;min-width:0;'>"
                        f"<div style='font-size:0.8rem;font-weight:700;color:#E6EDF3;'>{_ph['producto']}</div>"
                        f"<div style='font-size:0.62rem;color:#555;margin-top:2px;'>{_fec} · {_mot}</div>"
                        f"<div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>"
                        f"<span style='text-decoration:line-through;'>${_pa:,.0f}</span>"
                        f" <span style='color:#C9D1D9;font-weight:700;margin-left:4px;'>${_pn:,.0f}</span>"
                        f"</div>"
                        f"</div>"
                        f"<div style='font-size:1.2rem;font-weight:900;color:{_dc};"
                        f"text-shadow:0 0 8px {_dc}88;white-space:nowrap;margin-left:10px;padding-top:2px;'>"
                        f"{_arr} {_sig}{_pct:.0f}%</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
        with _exp2:
            if not _fab_socio.empty:
                st.markdown(
                    "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;color:#FF6B35;"
                    "text-transform:uppercase;margin-bottom:8px;'>🏭 PRODUCCIÓN POR PRODUCTO</div>",
                    unsafe_allow_html=True,
                )
                _vol_prod = _fab_socio.groupby("producto").agg(
                    fabricaciones=("resultado","count"),
                    gramos_total=("gramos_usados","sum")
                ).sort_values("fabricaciones", ascending=False).head(8).reset_index()
                for _, _vp in _vol_prod.iterrows():
                    _kg_vp = float(_vp["gramos_total"]) / 1000
                    st.markdown(
                        f"<div style='background:#050508;border-radius:8px;padding:8px 12px;"
                        f"border:1px solid #FF6B3522;margin-bottom:5px;display:flex;"
                        f"justify-content:space-between;align-items:center;'>"
                        f"<div style='font-size:0.78rem;color:#C9D1D9;'>{_vp['producto']}</div>"
                        f"<div style='text-align:right;'>"
                        f"<div style='font-size:0.82rem;font-weight:800;color:#FF6B35;'>{int(_vp['fabricaciones'])}x</div>"
                        f"<div style='font-size:0.62rem;color:#555;'>{_kg_vp:.2f} kg</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

        # ── Fila 5: Señales de mercado ───────────────────────────────
        if not _senales_sm.empty:
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:3px;color:#A855F7;"
                "text-transform:uppercase;margin-bottom:10px;'>🔮 SEÑALES DE MERCADO</div>",
                unsafe_allow_html=True,
            )
            for _, _sm in _senales_sm.iterrows():
                _sm_fec  = str(_sm.get("fecha", ""))[:10]
                _sm_prod = str(_sm.get("producto") or "")
                _sm_reac = str(_sm.get("reaccion") or "")
                _sm_seg  = str(_sm.get("segmento_detectado") or "")
                _sm_op   = str(_sm.get("oportunidad") or "")
                _sm_can  = str(_sm.get("canal") or "")
                _seg_color = "#A855F7" if "B2B" in _sm_seg else ("#39FF14" if "Retail" in _sm_seg else "#00FFFF")
                st.markdown(
                    f"<div style='background:linear-gradient(135deg,#0D0D18,#150D20);"
                    f"border-radius:12px;padding:14px 18px;border:1px solid #A855F744;"
                    f"box-shadow:0 0 12px #A855F722;margin-bottom:8px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                    f"<div style='flex:1;'>"
                    f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                    f"<span style='font-size:0.85rem;font-weight:800;color:#E6EDF3;'>{_sm_prod}</span>"
                    f"<span style='background:{_seg_color}22;color:{_seg_color};border:1px solid {_seg_color}44;"
                    f"border-radius:99px;padding:1px 8px;font-size:0.6rem;font-weight:700;'>{_sm_seg}</span>"
                    f"</div>"
                    f"<div style='font-size:0.73rem;color:#A855F7;font-style:italic;'>✨ {_sm_reac}</div>"
                    f"<div style='font-size:0.72rem;color:#C9D1D9;margin-top:5px;line-height:1.4;'>{_sm_op}</div>"
                    f"</div>"
                    f"<div style='text-align:right;margin-left:10px;'>"
                    f"<div style='font-size:0.62rem;color:#555;'>{_sm_fec}</div>"
                    f"<div style='font-size:0.65rem;color:#6B7280;margin-top:2px;'>{_sm_can}</div>"
                    f"</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

    # ══ TAB PRODUCTOS ══
    with _t_prod:
        def _render_cards_linea(df_p, _col_default):
            _df_act = df_p[df_p["activo"]==1] if "activo" in df_p.columns else df_p
            if _df_act.empty:
                st.info("Sin productos activos en esta línea.")
                return
            _pcols2 = st.columns(3)
            for _pii, (_, _prow) in enumerate(_df_act.sort_values("price", ascending=False).iterrows()):
                _plincolor = LINEAS.get(_prow["client_id"],{}).get("color", _col_default)
                _pstock_c  = "#10B981" if (_prow.get("stock",0) or 0) > 5 else ("#F59E0B" if (_prow.get("stock",0) or 0) > 0 else "#EF4444")
                _peso_g    = int(_prow.get("weight_gr", 0) or 0)
                with _pcols2[_pii % 3]:
                    _pdesc      = str(_prow.get("description", "") or "").strip()
                    _pdesc_html = (
                        f"<div style='font-size:0.72rem;color:#C9D1D9;margin-top:6px;"
                        f"line-height:1.45;font-style:italic;border-top:1px solid #21262D;"
                        f"padding-top:6px;'>{_pdesc}</div>"
                    ) if _pdesc else ""
                    _tipo_tp    = str(_prow.get("tipo_producto") or "")
                    _tipo_label = {"propio_3d": "EP 3D", "linea_propio": "Propio",
                                   "compartido": "Compartido", "kit_mixto": "Kit"}.get(_tipo_tp, "")
                    _tipo_html  = (
                        f"<span style='background:{_plincolor}22;color:{_plincolor};"
                        f"border-radius:99px;padding:1px 7px;font-size:0.58rem;"
                        f"font-weight:700;border:1px solid {_plincolor}44;'>{_tipo_label}</span>"
                    ) if _tipo_label else ""
                    _precio_p   = float(_prow.get("price", 0) or 0)
                    _stk_p      = int(_prow.get("stock", 0) or 0)
                    _costo_p    = float(_prow.get("costo_unit", 0) or 0)
                    _gan_p      = float(_prow.get("ganancia_unit", 0) or 0)
                    _margen_p   = float(_prow.get("margen_pct", 0) or 0)
                    _gan_color  = "#10B981" if _gan_p > 0 else "#EF4444"
                    _lbl_precio = "PRECIO VENTA" if _tipo_tp == "propio_3d" else "PRECIO"
                    _nums_html = (
                        f"<div style='margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:4px;'>"
                        f"<div style='background:#0D1117;border-radius:6px;padding:8px 4px;text-align:center;'>"
                        f"<div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>{_lbl_precio}</div>"
                        f"<div style='font-size:0.84rem;font-weight:700;color:{_plincolor};'>${_precio_p:,.0f}</div></div>"
                        f"<div style='background:#0D1117;border-radius:6px;padding:8px 4px;text-align:center;'>"
                        f"<div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>STOCK</div>"
                        f"<div style='font-size:0.84rem;font-weight:700;color:{_pstock_c};'>{_stk_p} u</div></div>"
                        + (
                        f"<div style='background:#0D1117;border-radius:6px;padding:8px 4px;text-align:center;'>"
                        f"<div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>COSTO</div>"
                        f"<div style='font-size:0.84rem;font-weight:700;color:#F59E0B;'>${_costo_p:,.0f}</div></div>"
                        f"<div style='background:#0D1117;border-radius:6px;padding:8px 4px;text-align:center;'>"
                        f"<div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>GANANCIA · {_margen_p:.0f}%</div>"
                        f"<div style='font-size:0.84rem;font-weight:700;color:{_gan_color};'>${_gan_p:,.0f}</div></div>"
                        if _costo_p > 0 else ""
                        )
                        + f"</div>"
                    )
                    st.markdown(
                        f"<div style='background:#161B22;border-radius:14px;padding:16px;"
                        f"border:1px solid #21262D;margin-bottom:10px;border-top:3px solid {_plincolor};'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div style='font-size:0.62rem;color:{_plincolor};font-weight:700;"
                        f"letter-spacing:1px;text-transform:uppercase;'>{_prow.get('sku','')} · {_peso_g}g</div>"
                        f"{_tipo_html}</div>"
                        f"<div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;margin-top:4px;"
                        f"line-height:1.2;'>{_prow['name']}</div>"
                        f"<div style='font-size:0.68rem;color:#8B949E;margin-top:2px;'>"
                        f"{_prow.get('categoria','') or ''}</div>"
                        f"{_pdesc_html}"
                        f"{_nums_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        if role == "socio_multi" and len(lineas_activas) > 1:
            _ltab_names = [
                f"{LINEAS.get(l,{}).get('emoji','●')} {LINEAS.get(l,{}).get('nombre',l)}"
                for l in lineas_activas
            ]
            _ltabs = st.tabs(_ltab_names)
            for _ltab, _lid3 in zip(_ltabs, lineas_activas):
                _lp3 = prod[prod["client_id"]==_lid3]
                _lc3 = LINEAS.get(_lid3, {"nombre":_lid3,"emoji":"●","color":"#6366F1"})
                with _ltab:
                    _ls1, _ls2 = st.columns(2)
                    _n_act3 = len(_lp3[_lp3["activo"]==1]) if "activo" in _lp3.columns else len(_lp3)
                    with _ls1:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>PRODUCTOS</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>{_n_act3}</div></div>", unsafe_allow_html=True)
                    with _ls2:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>VALOR STOCK</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>${_lp3['valor_stock'].sum():,.0f}</div></div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    _render_cards_linea(_lp3, _lc3["color"])
        else:
            if prod.empty:
                st.info("Aún no tenés productos cargados en tu línea.")
            else:
                _render_cards_linea(prod, hdr_color)

    # ══ TAB PEDIDOS ══
    with _t_ped:
        _show_badge = role == "socio_multi" and len(lineas_activas) > 1
        _canal_icons_ped = {
            "Ya era cliente / familia": "👨‍👩‍👧",
            "Instagram":                "📸",
            "TikTok":                   "🎵",
            "Recomendación personal":   "🤝",
            "Presencial / evento":      "🏪",
            "Presencial":               "🏪",
            "WhatsApp directo":         "💬",
            "WhatsApp":                 "💬",
            "Otro":                     "💡",
        }
        _pago_badge_map = {
            "pendiente":  ("💳 Pago pendiente", "#9CA3AF"),
            "acreditado": ("✅ Pago acreditado", "#10B981"),
            "devuelto":   ("↩️ Devuelto",        "#EF4444"),
        }
        if _pedidos_s.empty:
            st.info("Todavía no tenés pedidos registrados.")
        else:
            _pf_est = st.selectbox(
                "Filtrar por estado",
                ["Todos", "Pendiente", "En Proceso", "Listo", "Entregado", "Cancelado"],
                key="ped_filtro_socio",
            )
            _pf_df = _pedidos_s if _pf_est == "Todos" else _pedidos_s[_pedidos_s["status"] == _pf_est]
            if _pf_df.empty:
                st.info(f"Sin pedidos en estado {_pf_est}.")
            else:
                for _, _pr2 in _pf_df.iterrows():
                    _oid2  = int(_pr2["id"])
                    _sc3   = _SC.get(_pr2["status"], "#9CA3AF")
                    _lnom2 = LINEAS.get(_pr2["client_id"], {}).get("nombre", "")
                    _lcol2 = LINEAS.get(_pr2["client_id"], {}).get("color", hdr_color)
                    _fec2  = str(_pr2["date"])[:10] if _pr2["date"] else "—"
                    _ent2  = str(_pr2.get("fecha_entrega_est", "—") or "—")

                    _badge2 = (
                        f"<span style='background:{_lcol2}22;color:{_lcol2};border:1px solid {_lcol2}44;"
                        f"border-radius:99px;padding:2px 9px;font-size:0.68rem;font-weight:600;'>{_lnom2}</span>"
                    ) if _show_badge else ""

                    _pest2 = None
                    if "pago_estado" in _pedidos_s.columns:
                        _raw = _pr2.get("pago_estado")
                        if _raw is not None and not pd.isna(_raw):
                            _pest2 = str(_raw)
                    if _pest2:
                        _pb_txt, _pb_col = _pago_badge_map.get(_pest2, (_pest2, "#9CA3AF"))
                        _pago_badge2 = (
                            f"<span style='background:{_pb_col}22;color:{_pb_col};"
                            f"border:1px solid {_pb_col}44;border-radius:99px;"
                            f"padding:2px 9px;font-size:0.68rem;font-weight:600;'>{_pb_txt}</span>"
                        )
                    else:
                        _pago_badge2 = ""

                    _canal2     = _pr2.get("canal_origen") or ""
                    _canal_ico2 = _canal_icons_ped.get(_canal2, "")
                    _canal_html = (
                        f"<span style='font-size:0.68rem;color:#6B7280;'>{_canal_ico2} {_canal2}</span>"
                    ) if _canal2 else ""

                    # Items del pedido con nombre del producto
                    _ord_items = (
                        _items_socio[_items_socio["order_id"] == _oid2]
                        if not _items_socio.empty else pd.DataFrame()
                    )
                    _items_html = ""
                    if not _ord_items.empty:
                        _parts = []
                        for _, _ir in _ord_items.iterrows():
                            _parts.append(
                                f"<span style='color:#F59E0B;font-weight:700;'>{int(_ir['cantidad'])}×</span>"
                                f" <span style='color:#E6EDF3;font-weight:600;'>{_ir['producto']}</span>"
                                f"<span style='color:#6B7280;font-size:0.7rem;'> · ${float(_ir['precio_unitario']):,.0f} c/u</span>"
                            )
                        _items_html = (
                            "<div style='margin-top:8px;padding:8px 12px;background:#0D1117;"
                            "border-radius:8px;border:1px solid #21262D;font-size:0.8rem;"
                            "display:flex;flex-direction:column;gap:3px;'>"
                            + "".join(f"<div>{p}</div>" for p in _parts)
                            + "</div>"
                        )

                    _not2 = (
                        f"<div style='font-size:0.72rem;color:#8B949E;margin-top:6px;"
                        f"padding:6px 10px;background:#161B22;border-radius:6px;"
                        f"border:1px dashed #30363D;'><em>{_pr2['notas']}</em></div>"
                    ) if _pr2.get("notas") else ""

                    st.markdown(
                        f"<div style='background:#161B22;border-radius:14px;padding:16px 20px;"
                        f"margin-bottom:6px;border-left:4px solid {_sc3};border:1px solid #21262D;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div style='flex:1;min-width:0;'>"
                        f"<div style='display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:4px;'>"
                        f"<span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>#{_oid2}</span>"
                        f"<span style='background:{_sc3}22;color:{_sc3};border:1px solid {_sc3}44;"
                        f"border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:700;'>{_pr2['status']}</span>"
                        f"{_badge2}{_pago_badge2}"
                        f"</div>"
                        f"<div style='font-size:0.72rem;color:#8B949E;display:flex;gap:12px;flex-wrap:wrap;'>"
                        f"<span>📅 {_fec2}</span>"
                        f"<span>🎯 entrega {_ent2}</span>"
                        f"{_canal_html}"
                        f"</div>"
                        f"{_items_html}"
                        f"{_not2}"
                        f"</div>"
                        f"<div style='font-family:\"Bricolage Grotesque\",sans-serif;font-size:1.5rem;"
                        f"font-weight:800;color:#16181F;margin-left:16px;white-space:nowrap;"
                        f"letter-spacing:-.03em;padding-top:2px;'>${float(_pr2['total']):,.0f}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

                    # Acciones según estado
                    if _pr2["status"] == "Pendiente":
                        if st.button("❌ Cancelar pedido", key=f"ped_cancel_{_oid2}",
                                     help="Cancela este pedido — Fer no lo fabricará"):
                            with engine.connect() as _pc:
                                _pc.execute(text("UPDATE orders SET status='Cancelado' WHERE id=:id"), {"id": _oid2})
                                _pc.commit()
                            st.warning(f"Pedido #{_oid2} cancelado.")
                            st.rerun()
                    elif _pr2["status"] == "Listo":
                        if st.button("📦 Confirmar recepción", key=f"ped_entrega_{_oid2}",
                                     type="primary", help="Marca el pedido como recibido"):
                            with engine.connect() as _pc:
                                _pc.execute(text("UPDATE orders SET status='Entregado' WHERE id=:id"), {"id": _oid2})
                                _pc.commit()
                            st.success(f"✅ Pedido #{_oid2} confirmado como Entregado.")
                            st.rerun()

            _tot_fac = float(_pedidos_s[_pedidos_s["status"].isin(["Listo", "Entregado"])]["total"].sum())
            st.markdown(
                f"<div style='background:#0D1B2E;border-radius:10px;padding:12px 18px;"
                f"margin-top:8px;border:1px solid #1B2D4A;text-align:right;'>"
                f"<span style='color:#58A6FF;font-weight:700;'>"
                f"Total facturado (Listo + Entregado): ${_tot_fac:,.0f}</span></div>",
                unsafe_allow_html=True,
            )

    # ══ TAB MI TIENDA ══
    with _t_tienda:
        from utils.pricing import cargar_productos as _cp_tienda

        _VIS_COLOR = {"publico": "#10B981", "borrador": "#F59E0B", "pausado": "#6B7280"}
        _VIS_LABEL = {"publico": "Publico",  "borrador": "Borrador",  "pausado": "Pausado"}

        def _tienda_linea(lid, lnom, lcolor):
            st.markdown(f"""
<div style='background:linear-gradient(135deg,{lcolor}22,{lcolor}0a);border-radius:16px;
     padding:18px 24px;border:1px solid {lcolor}33;margin-bottom:16px;'>
  <div style='font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
       color:{lcolor};'>CATÁLOGO COMPLETO · TU LÍNEA</div>
  <div style='font-size:1.1rem;font-weight:800;color:#E6EDF3;margin-top:6px;'>🏪 Mi Tienda — {lnom}</div>
  <div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>
    Productos EP 3D = lo que El Pasaje fabrica para vos · Productos propios = los que vos creás y gestionás.
    Seteá tu precio de venta en cada uno para calcular tu margen.
  </div>
</div>""", unsafe_allow_html=True)

            df_c2 = get_productos_capa2(lid)

            # ── Productos EP (propio_3d) de esta línea ──────────────────
            try:
                _df_ep = pd.read_sql(
                    text("""SELECT sku, name, description, price, precio_socio,
                                   precio_reventa, weight_gr, stock, categoria, imagen_url
                            FROM products
                            WHERE client_id=:cid AND tipo_producto='propio_3d' AND activo=1
                            ORDER BY categoria, name"""),
                    engine, params={"cid": lid},
                )
                if "precio_reventa" not in _df_ep.columns:
                    _df_ep["precio_reventa"] = _df_ep.get("precio_socio", 0)
            except Exception:
                _df_ep = pd.DataFrame()

            # Verificar si la línea tiene número de WhatsApp configurado
            _wa_configured = False
            try:
                with engine.connect() as _wa_chk:
                    _wa_chk_row = _wa_chk.execute(
                        text("SELECT whatsapp_numero FROM lineas_config WHERE client_id=:cid"),
                        {"cid": lid},
                    ).fetchone()
                _wa_configured = bool(_wa_chk_row and _wa_chk_row[0] and str(_wa_chk_row[0]).strip())
            except Exception:
                pass

            # Preload kit components para todos los kits de esta línea (evita N+1 queries)
            try:
                with engine.connect() as _kc_conn:
                    _df_kc_all = pd.read_sql(
                        text("""
                            SELECT kc.kit_sku, kc.component_sku, kc.cantidad,
                                   p.name AS comp_name, p.price AS comp_price
                            FROM kit_components kc
                            LEFT JOIN products p ON p.sku = kc.component_sku
                            WHERE kc.kit_sku IN (
                                SELECT sku FROM products
                                WHERE client_id=:cid AND tipo_producto='kit_mixto'
                            )
                            ORDER BY kc.kit_sku, kc.orden
                        """),
                        _kc_conn, params={"cid": lid}
                    )
            except Exception:
                _df_kc_all = pd.DataFrame()

            # ── KPIs de márgenes ──────────────────────────────────────
            if not _df_ep.empty:
                _ep_cost_stk  = float((_df_ep["price"] * _df_ep["stock"]).sum())
                _df_ep_ps     = _df_ep["precio_reventa"].fillna(0)
                _ep_venta_stk = float((_df_ep_ps * _df_ep["stock"]).sum())
                _ep_margen_stk = _ep_venta_stk - _ep_cost_stk
                _n_con_ps     = int((_df_ep_ps > 0).sum())

                # Ganancia real acumulada del socio (50% de (precio-costo) en ventas Listo+Entregado)
                try:
                    with engine.connect() as _gc:
                        _gan_row = _gc.execute(text("""
                            SELECT COALESCE(SUM(
                                (oi.precio_unitario - (p.weight_gr * 1.10 * 2350.0 / 1000)) * 0.5 * oi.cantidad
                            ), 0)
                            FROM order_items oi
                            JOIN orders o ON o.id = oi.order_id
                            JOIN products p ON p.sku = oi.product_sku
                            WHERE o.client_id = :lid
                              AND o.status IN ('Listo','Entregado')
                              AND p.tipo_producto = 'propio_3d'
                        """), {"lid": lid}).fetchone()
                    _gan_acum = float(_gan_row[0] or 0)
                except Exception:
                    _gan_acum = 0.0

                _km1, _km2, _km3, _km4, _km5 = st.columns(5)
                for _kc, _kv, _kl, _kcol in [
                    (_km1, f"${_ep_cost_stk:,.0f}",   "Capital en EP", lcolor),
                    (_km2, f"${_ep_venta_stk:,.0f}",  "Venta proyectada",  "#10B981"),
                    (_km3, f"${_ep_margen_stk:,.0f}", "Margen proyectado",  "#3B82F6" if _ep_margen_stk >= 0 else "#EF4444"),
                    (_km4, f"{_n_con_ps}/{len(_df_ep)}", "Con precio de venta", "#F59E0B"),
                    (_km5, f"${_gan_acum:,.0f}", "Tu ganancia acumulada · 50%", "#A855F7"),
                ]:
                    with _kc:
                        st.markdown(
                            f"<div style='background:#161B22;border-radius:12px;padding:12px;border:1px solid #21262D;"
                            f"border-top:3px solid {_kcol};text-align:center;margin-bottom:12px;'>"
                            f"<div style='font-size:1.1rem;font-weight:800;color:{_kcol};line-height:1;'>{_kv}</div>"
                            f"<div style='font-size:0.55rem;color:#8B949E;margin-top:5px;text-transform:uppercase;"
                            f"letter-spacing:0.5px;'>{_kl}</div></div>",
                            unsafe_allow_html=True,
                        )

            # ── Sección: Catálogo EP 3D (grilla 2 columnas) ──────────────
            if not _df_ep.empty:
                st.markdown(
                    "<div style='font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
                    "color:#F59E0B;margin-bottom:12px;'>📦 CATÁLOGO EP 3D — LO QUE FABRICAMOS PARA VOS</div>",
                    unsafe_allow_html=True,
                )
                _ep_grid = st.columns(2)
                for _ep_i, (_, _ep_r) in enumerate(_df_ep.iterrows()):
                    _ep_price  = float(_ep_r.get("price", 0) or 0)
                    _ep_pr     = float(_ep_r.get("precio_reventa", 0) or 0)
                    _ep_margen = _ep_pr - _ep_price if _ep_pr > 0 else 0
                    _ep_pct    = _ep_margen / _ep_pr * 100 if _ep_pr > 0 else 0
                    _ep_markup = _ep_pr / _ep_price if (_ep_price > 0 and _ep_pr > 0) else 0
                    _ep_desc   = str(_ep_r.get("description", "") or "").strip()
                    _ep_cat    = str(_ep_r.get("categoria", "") or "").strip()
                    _ep_stk    = int(_ep_r.get("stock", 0) or 0)
                    _ep_wt     = float(_ep_r.get("weight_gr", 0) or 0)
                    _ep_stk_c  = "#10B981" if _ep_stk > 5 else ("#F59E0B" if _ep_stk > 0 else "#EF4444")
                    _ep_costo     = round(_ep_wt * 1.10 * 2350 / 1000) if _ep_wt > 0 else 0
                    _ep_gan_ep    = _ep_price - _ep_costo if _ep_costo > 0 else 0
                    _ep_mrg_ep    = round(_ep_gan_ep / _ep_price * 100) if (_ep_price > 0 and _ep_costo > 0) else 0
                    _ep_gan_socio = round(_ep_gan_ep * 0.5) if _ep_gan_ep > 0 else 0
                    _ep_cat_html = (
                        f"<span style='background:#21262D;color:#8B949E;border-radius:99px;"
                        f"padding:1px 8px;font-size:0.62rem;'>{_ep_cat}</span>"
                    ) if _ep_cat else ""
                    _ep_margen_line = (
                        f"<span style='color:#10B981;font-weight:700;'>+${_ep_margen:,.0f}"
                        f"<span style='font-size:0.7rem;font-weight:500;'> ({_ep_pct:.0f}% margen)</span></span>"
                    ) if _ep_pr > 0 else (
                        "<span style='color:#F59E0B;font-size:0.7rem;'>⚠ Sin precio de reventa seteado</span>"
                    )
                    _ep_markup_badge = (
                        f"<span style='background:#10B98122;color:#10B981;border-radius:99px;"
                        f"padding:1px 7px;font-size:0.6rem;font-weight:700;'>×{_ep_markup:.1f}</span>"
                    ) if _ep_markup > 0 else ""
                    _ep_desc_html = (
                        f"<div style='font-size:0.72rem;color:#C9D1D9;margin-top:6px;line-height:1.4;"
                        f"font-style:italic;border-top:1px solid #21262D;padding-top:6px;'>{_ep_desc}</div>"
                    ) if _ep_desc else ""
                    with _ep_grid[_ep_i % 2]:
                        st.markdown(f"""
<div style='background:#161B22;border-radius:12px;padding:14px 16px;
     border:1px solid #21262D;border-top:3px solid #F59E0B;margin-bottom:4px;'>
  <div style='display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:2px;'>
    <span style='font-size:0.85rem;font-weight:700;color:#E6EDF3;'>{_ep_r['name']}</span>
    {_ep_cat_html}
  </div>
  <div style='font-size:0.68rem;color:#8B949E;'>
    {_ep_r['sku']} · {_ep_wt:.0f}g ·
    <span style='color:{_ep_stk_c};font-weight:600;'>{_ep_stk} u stock</span>
  </div>
  {_ep_desc_html}
  <div style='margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px;'>
    <div style='background:#0D1117;border-radius:7px;padding:8px 10px;'>
      <div style='font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.4px;'>
        Precio EP <span style='font-size:0.5rem;opacity:.6;'>(lo que pagas)</span></div>
      <div style='font-size:0.92rem;font-weight:800;color:#F59E0B;'>${_ep_price:,.0f}</div>
    </div>
    <div style='background:#0D1117;border-radius:7px;padding:8px 10px;'>
      <div style='font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.4px;
                  display:flex;align-items:center;gap:4px;'>
        Tu precio {_ep_markup_badge}</div>
      <div style='font-size:0.92rem;font-weight:800;color:#10B981;'>${_ep_pr:,.0f}</div>
    </div>
    {f"<div style='background:#0D1117;border-radius:7px;padding:8px 10px;'><div style='font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.4px;'>Costo fabricación</div><div style='font-size:0.92rem;font-weight:800;color:#94A3B8;'>${_ep_costo:,.0f}</div></div><div style='background:#0D1117;border-radius:7px;padding:8px 10px;'><div style='font-size:0.55rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.4px;'>Ganancia EP total</div><div style='font-size:0.92rem;font-weight:800;color:#6366F1;'>${_ep_gan_ep:,.0f}</div></div>" if _ep_costo > 0 else ""}
  </div>
  {f"<div style='margin-top:6px;background:#2D1B69;border-radius:7px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;'><div style='font-size:0.6rem;color:#C4B5FD;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;'>Tu ganancia por unidad · 50%</div><div style='font-size:1.05rem;font-weight:800;color:#A855F7;'>${_ep_gan_socio:,.0f}</div></div>" if _ep_gan_socio > 0 else ""}
  <div style='margin-top:6px;font-size:0.78rem;'>{_ep_margen_line}</div>
</div>""", unsafe_allow_html=True)
                        _ep_inp = st.number_input(
                            "✏️ Tu precio de reventa",
                            min_value=float(_ep_price), value=max(_ep_pr, _ep_price),
                            step=100.0, format="%.0f",
                            key=f"ep_pr_{_ep_r['sku']}_{lid}",
                            help=f"Mínimo: ${_ep_price:,.0f} (precio EP)",
                        )
                        if abs(_ep_inp - _ep_pr) > 0.5:
                            if st.button(
                                "💾 Guardar",
                                key=f"ep_prsave_{_ep_r['sku']}_{lid}",
                                type="primary", use_container_width=True,
                            ):
                                with engine.begin() as _ep_conn:
                                    _ep_conn.execute(
                                        text("UPDATE products SET precio_reventa=:pr, precio_socio=:pr WHERE sku=:s"),
                                        {"pr": _ep_inp, "s": _ep_r["sku"]},
                                    )
                                    if _ep_pr > 0:
                                        _ep_conn.execute(
                                            text("""INSERT INTO price_history
                                                    (product_sku, precio_anterior, precio_nuevo, motivo)
                                                    VALUES (:s,:a,:n,:m)"""),
                                            {"s": _ep_r["sku"], "a": _ep_pr,
                                             "n": _ep_inp, "m": f"Precio reventa {lnom}"},
                                        )
                                get_productos_capa2.clear()
                                _cp_tienda.clear()
                                st.success(f"${_ep_inp:,.0f} guardado")
                                st.rerun()
                        if _ep_pr > 0 and _wa_configured:
                            _ep_wa_lnk = _wa_link_producto(
                                _ep_r["name"], _ep_r["sku"], _ep_price, lid, engine,
                                precio_override=_ep_pr,
                            )
                            st.link_button("📲 Compartir", url=_ep_wa_lnk, use_container_width=True)
                        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # ── Sección: Productos propios (Capa 2) ───────────────────
            if df_c2.empty:
                st.markdown(
                    "<div style='background:#161B22;border-radius:12px;padding:16px 20px;"
                    "border:1px dashed #30363D;color:#8B949E;margin-bottom:16px;'>"
                    "Sin productos propios agregados todavía.<br>"
                    "Usá el formulario de abajo para agregar el primero.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
                    "color:#58A6FF;margin-bottom:10px;'>✨ TUS PRODUCTOS PROPIOS</div>",
                    unsafe_allow_html=True,
                )
                df_c2["_cat"] = df_c2["categoria"].fillna("Sin categoría").replace("", "Sin categoría")
                for _cat in sorted(df_c2["_cat"].unique()):
                    _df_cat = df_c2[df_c2["_cat"] == _cat]
                    _n_cat  = len(_df_cat)
                    with st.expander(f"📦 {_cat}  ·  {_n_cat} producto{'s' if _n_cat != 1 else ''}", expanded=True):
                        for _, _r2 in _df_cat.iterrows():
                            _vis2        = _r2.get("visibilidad", "borrador") or "borrador"
                            _vc2         = _VIS_COLOR.get(_vis2, "#6B7280")
                            _vl2         = _VIS_LABEL.get(_vis2, _vis2)
                            _tipo2       = (_r2.get("tipo_producto", "linea_propio") or "linea_propio").replace("_", " ").title()
                            _is_kit      = (_r2.get("tipo_producto") or "") == "kit_mixto"
                            _kc_this     = _df_kc_all[_df_kc_all["kit_sku"] == _r2["sku"]] if not _df_kc_all.empty else pd.DataFrame()
                            _kit_badge   = f" · {len(_kc_this)} componentes" if _is_kit else ""
                            _img_url     = str(_r2.get("imagen_url") or "").strip()
                            _desc2       = str(_r2.get("description", "") or "").strip()
                            _precio_actual = float(_r2.get("price", 0) or 0)
                            _has_img     = _img_url.startswith("http") or _img_url.startswith("data:")

                            _desc2_html = (
                                f"<div style='font-size:0.73rem;color:#C9D1D9;margin-top:7px;"
                                f"line-height:1.4;font-style:italic;border-top:1px solid #21262D;"
                                f"padding-top:7px;'>{_desc2}</div>"
                            ) if _desc2 else ""

                            # Layout: imagen opcional + todo el contenido en una sola columna
                            if _has_img:
                                _c2img, _c2main = st.columns([1, 7])
                                with _c2img:
                                    st.image(_img_url, width=76)
                            else:
                                _c2main = st.container()

                            with _c2main:
                                # ── Tarjeta informativa ─────────────────────
                                st.markdown(f"""
<div style='background:#161B22;border-radius:12px;padding:12px 16px;
     border:1px solid #21262D;border-left:3px solid {_vc2};margin-bottom:6px;'>
  <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;'>
    <span style='font-size:0.84rem;font-weight:700;color:#E6EDF3;'>{_r2['name']}</span>
    <span style='background:{_vc2}22;color:{_vc2};border:1px solid {_vc2}44;border-radius:99px;
         padding:2px 9px;font-size:0.65rem;font-weight:700;'>{_vl2}</span>
    <span style='background:#21262D;color:#8B949E;border-radius:99px;
         padding:2px 9px;font-size:0.62rem;'>{_tipo2}</span>
  </div>
  <div style='font-size:0.72rem;color:#8B949E;margin-top:3px;'>
    {_r2.get('sku','')} &nbsp;·&nbsp;
    <b style='color:#F59E0B;'>${_precio_actual:,.0f}</b> &nbsp;·&nbsp;
    {int(_r2.get('stock',0) or 0)} u stock{_kit_badge}
  </div>
  {_desc2_html}
</div>""", unsafe_allow_html=True)

                                # ── Controles: visibilidad + precio (una sola fila) ─
                                _ctl1, _ctl2, _ctl3 = st.columns([2, 2, 1])
                                with _ctl1:
                                    _vis_opts = ["publico", "borrador", "pausado"]
                                    _vis_idx  = _vis_opts.index(_vis2) if _vis2 in _vis_opts else 1
                                    _new_vis  = st.selectbox(
                                        "Visibilidad", _vis_opts, index=_vis_idx,
                                        key=f"vis_{_r2['sku']}_{lid}",
                                        format_func=lambda x: {
                                            "publico": "🟢 Público",
                                            "borrador": "🟡 Borrador",
                                            "pausado": "⛔ Pausado",
                                        }.get(x, x),
                                        label_visibility="collapsed",
                                    )
                                    if _new_vis != _vis2:
                                        if st.button("Guardar visibilidad", key=f"vis_save_{_r2['sku']}_{lid}",
                                                     use_container_width=True):
                                            with engine.begin() as _cn2:
                                                _cn2.execute(
                                                    text("UPDATE products SET visibilidad=:v WHERE sku=:s"),
                                                    {"v": _new_vis, "s": _r2["sku"]},
                                                )
                                            get_productos_capa2.clear()
                                            _cp_tienda.clear()
                                            st.success("Visibilidad actualizada")
                                            st.rerun()
                                with _ctl2:
                                    _nuevo_precio = st.number_input(
                                        "💲 Precio de venta",
                                        min_value=0.0, value=_precio_actual, step=100.0, format="%.0f",
                                        key=f"precio_inp_{_r2['sku']}_{lid}",
                                        label_visibility="collapsed",
                                    )
                                with _ctl3:
                                    if abs(_nuevo_precio - _precio_actual) > 0.5:
                                        if st.button(
                                            "💾", key=f"precio_save_{_r2['sku']}_{lid}",
                                            type="primary", use_container_width=True,
                                            help="Guardar nuevo precio",
                                        ):
                                            with engine.begin() as _pe_conn:
                                                _pe_conn.execute(
                                                    text("UPDATE products SET price=:p WHERE sku=:s"),
                                                    {"p": _nuevo_precio, "s": _r2["sku"]},
                                                )
                                                _pe_conn.execute(
                                                    text("""INSERT INTO price_history
                                                            (product_sku, precio_anterior, precio_nuevo, motivo)
                                                            VALUES (:sku, :ant, :nvo, :mot)"""),
                                                    {"sku": _r2["sku"], "ant": _precio_actual,
                                                     "nvo": _nuevo_precio, "mot": f"Socio {lnom}"},
                                                )
                                            get_productos_capa2.clear()
                                            _cp_tienda.clear()
                                            st.success(f"${_nuevo_precio:,.0f} guardado")
                                            st.rerun()

                                # ── Componentes del kit ──────────────────────
                                if _is_kit:
                                    with st.expander(f"🧩 Componentes ({len(_kc_this)})"):
                                        if _kc_this.empty:
                                            st.caption("Sin componentes registrados.")
                                        else:
                                            for _, _kc_r in _kc_this.iterrows():
                                                _kcp = float(_kc_r.get("comp_price", 0) or 0) * int(_kc_r.get("cantidad", 1))
                                                st.markdown(
                                                    f"<div style='font-size:0.78rem;color:#C9D1D9;padding:5px 0;"
                                                    f"border-bottom:1px solid #21262D;'>"
                                                    f"<span style='font-family:monospace;color:#58A6FF;'>"
                                                    f"{_kc_r.get('component_sku','')}</span>"
                                                    f" — {_kc_r.get('comp_name','')} "
                                                    f"× {int(_kc_r.get('cantidad',1))}"
                                                    f" = <b style='color:#10B981;'>${_kcp:,.0f}</b></div>",
                                                    unsafe_allow_html=True,
                                                )
                                            _kit_total = float(
                                                (_kc_this["comp_price"].fillna(0) * _kc_this["cantidad"].fillna(1)).sum()
                                            )
                                            st.markdown(
                                                f"<div style='font-size:0.8rem;font-weight:700;color:#E6EDF3;"
                                                f"text-align:right;margin-top:6px;'>"
                                                f"Total componentes: ${_kit_total:,.0f}</div>",
                                                unsafe_allow_html=True,
                                            )

                                # ── WhatsApp ─────────────────────────────────
                                if _vis2 != "pausado":
                                    _is_ip_wa = any(kw in (_r2.get("name", "") or "").lower() for kw in IP_RESTRINGIDA)
                                    if _is_ip_wa:
                                        st.markdown(
                                            "<div style='font-size:0.72rem;color:#9CA3AF;padding:3px 0;'>"
                                            "🔒 Solo uso interno</div>",
                                            unsafe_allow_html=True,
                                        )
                                    elif _wa_configured:
                                        _c2_pr = float(_r2.get("precio_reventa", 0) or 0)
                                        _c2_p  = float(_r2.get("price", 0) or 0)
                                        _wa_lnk = _wa_link_producto(
                                            _r2.get("name", ""), _r2.get("sku", ""),
                                            _c2_p, lid, engine,
                                            precio_override=_c2_pr if _c2_pr > 0 else None,
                                        )
                                        st.link_button("📲 Compartir por WhatsApp", url=_wa_lnk,
                                                       use_container_width=True)

                            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

            # ── Formulario nuevo Tipo B ──────────────────────────────────
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            with st.expander("➕ Agregar nuevo producto (Tipo B — Propio de Línea)"):
                with st.form(f"form_tipob_{lid}"):
                    st.markdown("<div style='font-size:0.72rem;color:#8B949E;margin-bottom:10px;'>Tipo B: producto propio de tu línea. Quedará en borrador hasta que vos lo publiques.</div>", unsafe_allow_html=True)
                    _fc1, _fc2 = st.columns(2)
                    with _fc1:
                        _fn   = st.text_input("Nombre *", placeholder="Ej: Porta auriculares gaming")
                        _fsku = st.text_input("SKU *", placeholder=f"Ej: {lid[:3].upper()}-001")
                        _fcat = st.text_input("Categoría", placeholder="Ej: Accesorios")
                    with _fc2:
                        _fp   = st.number_input("Precio de venta *", min_value=0.0, step=100.0, format="%.0f")
                        _fstk = st.number_input("Stock inicial", min_value=0, step=1, value=1)
                        _fpeso= st.number_input("Peso aprox. (gr)", min_value=0.0, step=10.0, format="%.0f",
                                                help="Solo referencia; no afecta el precio en Tipo B.")
                    _fvis = st.radio(
                        "Publicar como",
                        ["borrador", "publico"],
                        format_func=lambda x: "Borrador (solo yo lo veo)" if x == "borrador" else "Publico (visible en mi pagina web)",
                        horizontal=True
                    )
                    _submitted_b = st.form_submit_button("Agregar producto", use_container_width=True)

                    if _submitted_b:
                        _errs = []
                        if not _fn.strip():
                            _errs.append("El nombre es obligatorio.")
                        if not _fsku.strip():
                            _errs.append("El SKU es obligatorio.")
                        if _fp <= 0:
                            _errs.append("El precio debe ser mayor a 0.")
                        _ip_hit = [kw for kw in IP_RESTRINGIDA if kw in _fn.lower()]
                        if _ip_hit:
                            _errs.append(f"Nombre no permitido: contiene '{_ip_hit[0]}' (IP restringida).")
                        if _errs:
                            for _e in _errs:
                                st.error(_e)
                        else:
                            try:
                                with engine.begin() as _cn3:
                                    _cn3.execute(text("""
                                        INSERT INTO products
                                            (sku, name, price, weight_gr, stock,
                                             client_id, activo, tipo_producto, visibilidad, categoria)
                                        VALUES
                                            (:sku, :name, :price, :wg, :stk,
                                             :cid, 1, 'linea_propio', :vis, :cat)
                                    """), {
                                        "sku":   _fsku.strip().upper(),
                                        "name":  _fn.strip(),
                                        "price": float(_fp),
                                        "wg":    float(_fpeso),
                                        "stk":   int(_fstk),
                                        "cid":   lid,
                                        "vis":   _fvis,
                                        "cat":   _fcat.strip() or None,
                                    })
                                get_productos_capa2.clear()
                                _cp_tienda.clear()
                                _vis_label = "Publico" if _fvis == "publico" else "Borrador"
                                st.success(f"'{_fn.strip()}' agregado como {_vis_label}.")
                                st.rerun()
                            except Exception as _ex3:
                                st.error(f"Error al guardar: {_ex3}")

            # ── Formulario nuevo Kit Tipo D ──────────────────────────────
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            with st.expander("🧩 Crear Kit Mixto (Tipo D — varios componentes)"):
                st.markdown("<div style='font-size:0.72rem;color:#8B949E;margin-bottom:10px;'>Tipo D: kit que agrupa productos existentes. El precio se calcula de la suma de componentes pero podés ajustarlo.</div>", unsafe_allow_html=True)

                # Carga de productos disponibles (fuera del form = live price update)
                try:
                    _kf_prods = pd.read_sql(
                        "SELECT sku, name, price, client_id FROM products WHERE activo=1 ORDER BY name",
                        engine
                    )
                except Exception:
                    _kf_prods = pd.DataFrame()

                _kf_opts = ["(ninguno)"] + (_kf_prods["sku"].tolist() if not _kf_prods.empty else [])

                def _kf_label(x):
                    if x == "(ninguno)" or _kf_prods.empty:
                        return "(ninguno)"
                    r = _kf_prods[_kf_prods["sku"] == x]
                    if r.empty:
                        return x
                    row = r.iloc[0]
                    return f"{row['sku']} — {row['name']}  ${float(row['price']):,.0f}"

                st.markdown("<div style='font-size:0.72rem;font-weight:700;color:#58A6FF;margin-bottom:6px;'>COMPONENTES (hasta 5)</div>", unsafe_allow_html=True)
                _kf_live = []
                for _ki in range(5):
                    _kfc1, _kfc2 = st.columns([5, 1])
                    with _kfc1:
                        _kf_sku_i = st.selectbox(
                            f"#{_ki+1}",
                            _kf_opts,
                            format_func=_kf_label,
                            key=f"kf_sku_{_ki}_{lid}",
                            label_visibility="collapsed"
                        )
                    with _kfc2:
                        _kf_qty_i = st.number_input(
                            "x",
                            min_value=1, value=1,
                            key=f"kf_qty_{_ki}_{lid}",
                            label_visibility="collapsed"
                        )
                    if _kf_sku_i != "(ninguno)":
                        _kf_live.append({"sku": _kf_sku_i, "cantidad": int(_kf_qty_i), "orden": _ki})

                # Precio automático en vivo
                _kf_auto = 0.0
                if _kf_live and not _kf_prods.empty:
                    for _kfc in _kf_live:
                        _pr = _kf_prods[_kf_prods["sku"] == _kfc["sku"]]
                        if not _pr.empty:
                            _kf_auto += float(_pr.iloc[0]["price"]) * _kfc["cantidad"]

                if _kf_live:
                    st.markdown(
                        f"<div style='background:#0D2E10;border-radius:8px;padding:8px 14px;"
                        f"border:1px solid #1a4a20;margin:8px 0;'>"
                        f"<span style='color:#3FB950;font-weight:700;'>Precio calculado: ${_kf_auto:,.0f}</span>"
                        f" &nbsp;·&nbsp; {len(_kf_live)} componente(s) seleccionado(s)</div>",
                        unsafe_allow_html=True
                    )

                with st.form(f"form_kit_{lid}"):
                    _kn1, _kn2 = st.columns(2)
                    with _kn1:
                        _kf_name    = st.text_input("Nombre del kit *", placeholder="Ej: Set Gaming Completo")
                        _kf_sku_inp = st.text_input("SKU *", placeholder=f"{lid[:3].upper()}-KIT-001")
                        _kf_cat     = st.text_input("Categoría", value="Kit")
                    with _kn2:
                        _kf_price = st.number_input(
                            "Precio final *", min_value=0.0, step=100.0, format="%.0f",
                            help=f"Calculado de componentes: ${_kf_auto:,.0f}. Podés ajustarlo."
                        )
                        _kf_stk = st.number_input("Stock inicial", min_value=0, value=1, step=1)
                    _kf_vis = st.radio(
                        "Publicar como",
                        ["borrador", "publico"],
                        format_func=lambda x: "Borrador (solo yo lo veo)" if x == "borrador" else "Publico",
                        horizontal=True
                    )
                    _kf_submit = st.form_submit_button("Crear Kit", use_container_width=True)

                    if _kf_submit:
                        # Leer componentes del session_state (están fuera del form)
                        _kf_comps_s = []
                        for _ki2 in range(5):
                            _ks2 = st.session_state.get(f"kf_sku_{_ki2}_{lid}", "(ninguno)")
                            _kq2 = int(st.session_state.get(f"kf_qty_{_ki2}_{lid}", 1))
                            if _ks2 != "(ninguno)":
                                _kf_comps_s.append({"sku": _ks2, "cantidad": _kq2, "orden": _ki2})

                        _kerrs = []
                        if not _kf_name.strip():
                            _kerrs.append("El nombre es obligatorio.")
                        if not _kf_sku_inp.strip():
                            _kerrs.append("El SKU es obligatorio.")
                        if _kf_price <= 0:
                            _kerrs.append("El precio debe ser mayor a 0.")
                        if len(_kf_comps_s) < 2:
                            _kerrs.append("Un kit necesita al menos 2 componentes.")
                        _ip_k = [kw for kw in IP_RESTRINGIDA if kw in _kf_name.lower()]
                        if _ip_k:
                            _kerrs.append(f"Nombre no permitido: '{_ip_k[0]}' (IP restringida).")

                        if _kerrs:
                            for _e in _kerrs:
                                st.error(_e)
                        else:
                            try:
                                _kit_sku_clean = _kf_sku_inp.strip().upper()
                                with engine.begin() as _kconn:
                                    _kconn.execute(text("""
                                        INSERT INTO products
                                            (sku, name, price, weight_gr, stock,
                                             client_id, activo, tipo_producto, visibilidad, categoria)
                                        VALUES
                                            (:sku, :name, :price, 0, :stk,
                                             :cid, 1, 'kit_mixto', :vis, :cat)
                                    """), {
                                        "sku":   _kit_sku_clean,
                                        "name":  _kf_name.strip(),
                                        "price": float(_kf_price),
                                        "stk":   int(_kf_stk),
                                        "cid":   lid,
                                        "vis":   _kf_vis,
                                        "cat":   _kf_cat.strip() or "Kit",
                                    })
                                    for _kci in _kf_comps_s:
                                        _kconn.execute(text("""
                                            INSERT INTO kit_components
                                                (kit_sku, component_sku, cantidad, orden)
                                            VALUES (:kit, :comp, :qty, :ord)
                                        """), {
                                            "kit":  _kit_sku_clean,
                                            "comp": _kci["sku"],
                                            "qty":  _kci["cantidad"],
                                            "ord":  _kci["orden"],
                                        })
                                get_productos_capa2.clear()
                                _cp_tienda.clear()
                                st.success(
                                    f"Kit '{_kf_name.strip()}' creado con "
                                    f"{len(_kf_comps_s)} componentes — ${float(_kf_price):,.0f}"
                                )
                                st.rerun()
                            except Exception as _ke:
                                st.error(f"Error al crear el kit: {_ke}")

        def _render_export_btn(lid, lnom):
            from utils.lineas import PAGINAS_SOCIOS
            if not PAGINAS_SOCIOS.get(lid):
                return
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:2px;"
                "text-transform:uppercase;color:#58A6FF;margin-bottom:8px;'>EXPORTAR A WEB</div>",
                unsafe_allow_html=True,
            )
            if st.button(f"📤 Exportar catálogo web — {lnom}", key=f"export_{lid}", use_container_width=True):
                try:
                    from utils.exports import exportar_catalogo_json
                    import json as _json
                    catalog, out_path = exportar_catalogo_json(lid)
                    n3d = len(catalog["productos_3d"])
                    nl  = len(catalog["productos_linea"])
                    nk  = len(catalog["kits"])
                    st.success(
                        f"Exportado: {n3d} prod. 3D · {nl} de línea · {nk} kits\n"
                        f"`{out_path}`"
                    )
                    st.download_button(
                        "⬇️ Descargar JSON",
                        data=_json.dumps(catalog, ensure_ascii=False, indent=2),
                        file_name=f"{catalog['slug']}-catalog.json",
                        mime="application/json",
                        key=f"dl_{lid}",
                    )
                    st.caption(
                        "Subí este archivo a la carpeta `exports/` del repo GitHub "
                        "para actualizar la página web."
                    )
                except Exception as _ex_exp:
                    st.error(f"Error al exportar: {_ex_exp}")

        if role == "socio_multi" and len(lineas_activas) > 1:
            _ltt_names = [
                f"{LINEAS.get(l,{}).get('emoji','●')} {LINEAS.get(l,{}).get('nombre',l)}"
                for l in lineas_activas
            ]
            _ltt_tabs = st.tabs(_ltt_names)
            for _ltt, _ltid in zip(_ltt_tabs, lineas_activas):
                _ltcfg = LINEAS.get(_ltid, {"nombre": _ltid, "emoji": "●", "color": "#6366F1"})
                with _ltt:
                    _tienda_linea(_ltid, _ltcfg["nombre"], _ltcfg["color"])
                    _render_export_btn(_ltid, _ltcfg["nombre"])
        else:
            _tienda_linea(uid, hdr_nombre, hdr_color)
            _render_export_btn(uid, hdr_nombre)

    # ══ TAB PRESUPUESTO ══
    with _t_presup:
        if role == "socio_multi" and len(lineas_activas) > 1:
            _pb_lid = st.selectbox(
                "Línea para el presupuesto",
                lineas_activas,
                format_func=lambda x: LINEAS.get(x, {}).get("nombre", x),
                key="presup_linea_sel",
            )
        else:
            _pb_lid = uid

        _pb_cfg    = get_linea(_pb_lid)
        _pb_color  = _pb_cfg["color"]
        _pb_nombre = _pb_cfg["nombre"]
        _pb_prods  = prod[(prod["client_id"] == _pb_lid) & (prod["activo"] == 1)].copy() if not prod.empty else pd.DataFrame()

        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;"
            f"text-transform:uppercase;color:{_pb_color};margin-bottom:14px;'>"
            f"🧮 PRESUPUESTADOR EXPRESS · {_pb_nombre}</div>",
            unsafe_allow_html=True,
        )

        if _pb_prods.empty:
            st.info("Aún no tenés productos activos. Agregá uno desde 🏪 Mi Tienda.")
        else:
            _paso_key  = f"presup_paso_{_pb_lid}"
            _items_key = f"presup_items_{_pb_lid}"
            _paso_act  = st.session_state.get(_paso_key, 1)

            # Helper: precio que se cobra al cliente
            def _precio_venta(row):
                pr = float(row.get("precio_reventa") or 0)
                return pr if pr > 0 else float(row.get("price") or 0)

            if _paso_act == 1:
                # ── Paso 1: armar presupuesto ──────────────────────────
                _pb_opts    = _pb_prods["sku"].tolist()
                _pb_lbl_map = {
                    r["sku"]: f"{r['sku']} — {r['name']} — ${_precio_venta(r):,.0f}"
                    for _, r in _pb_prods.iterrows()
                }
                _pb_sel = st.multiselect(
                    "Seleccioná los productos",
                    _pb_opts,
                    format_func=lambda x: _pb_lbl_map.get(x, x),
                    key=f"presup_sel_{_pb_lid}",
                )

                _pb_total_live = 0.0
                if _pb_sel:
                    for _pb_sku in _pb_sel:
                        _pb_row  = _pb_prods[_pb_prods["sku"] == _pb_sku].iloc[0]
                        _pb_pv   = _precio_venta(_pb_row)
                        _pb_qty  = st.number_input(
                            f"{_pb_row['name']}  (${_pb_pv:,.0f} c/u)",
                            min_value=1, value=1, step=1,
                            key=f"presup_qty_{_pb_sku}_{_pb_lid}",
                        )
                        _pb_sub = _pb_pv * int(_pb_qty)
                        _pb_total_live += _pb_sub
                        st.caption(f"Subtotal: ${_pb_sub:,.0f}")

                    st.markdown(
                        f"<div style='background:#0D2E10;border-radius:12px;padding:14px 20px;"
                        f"border:1px solid #1a4a20;margin:12px 0;text-align:center;'>"
                        f"<div style='font-size:0.62rem;color:#3FB950;font-weight:700;"
                        f"letter-spacing:2px;'>TOTAL ESTIMADO</div>"
                        f"<div style='font-size:2rem;font-weight:800;color:#3FB950;margin-top:4px;'>"
                        f"💰 ${_pb_total_live:,.0f}</div></div>",
                        unsafe_allow_html=True,
                    )

                    if st.button("Generar presupuesto →", type="primary",
                                 use_container_width=True, key=f"presup_gen_{_pb_lid}"):
                        _final_items = []
                        for _pb_sku2 in st.session_state.get(f"presup_sel_{_pb_lid}", []):
                            _r2 = _pb_prods[_pb_prods["sku"] == _pb_sku2]
                            if _r2.empty:
                                continue
                            _r2  = _r2.iloc[0]
                            _pv2 = _precio_venta(_r2)
                            _qty2 = int(st.session_state.get(f"presup_qty_{_pb_sku2}_{_pb_lid}", 1))
                            _final_items.append({
                                "nombre":         _r2["name"],
                                "sku":            _pb_sku2,
                                "cantidad":       _qty2,
                                "precio":         float(_r2.get("price", 0) or 0),
                                "precio_reventa": _pv2,
                            })
                        st.session_state[_items_key] = _final_items
                        st.session_state[_paso_key]  = 2
                        st.rerun()
                else:
                    st.caption("Seleccioná al menos un producto para armar el presupuesto.")

            else:
                # ── Paso 2: presupuesto generado ───────────────────────
                _pb_items_f = st.session_state.get(_items_key, [])
                _pb_total_f = sum(
                    float(it.get("precio_reventa") or it["precio"]) * int(it["cantidad"])
                    for it in _pb_items_f
                )
                _pb_numero  = _get_wa_numero(_pb_lid, engine)

                st.markdown(
                    f"<div style='background:#161B22;border-radius:14px;padding:20px 24px;"
                    f"border:1px solid #21262D;border-left:4px solid {_pb_color};margin-bottom:16px;'>"
                    f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;"
                    f"text-transform:uppercase;color:{_pb_color};margin-bottom:12px;'>"
                    f"📋 PRESUPUESTO · {_pb_nombre.upper()}</div>"
                    + "".join(
                        f"<div style='font-size:0.85rem;color:#E6EDF3;padding:5px 0;"
                        f"border-bottom:1px solid #21262D;'>"
                        f"• {it['cantidad']}x <b>{it['nombre']}</b>"
                        f"<span style='float:right;color:#3FB950;font-weight:700;'>"
                        f"${float(it.get('precio_reventa') or it['precio']) * int(it['cantidad']):,.0f}</span></div>"
                        for it in _pb_items_f
                    )
                    + f"<div style='font-size:1.1rem;font-weight:800;color:#3FB950;text-align:right;"
                    f"margin-top:12px;padding-top:8px;border-top:2px solid #21262D;'>"
                    f"TOTAL: ${_pb_total_f:,.0f}</div>"
                    f"<div style='font-size:0.68rem;color:#6B7280;margin-top:8px;'>"
                    f"Válido por 48 horas · Entrega bajo pedido 48-72hs · El Pasaje 3D Studio</div></div>",
                    unsafe_allow_html=True,
                )

                _txt_copy = _wa_texto_presup(
                    _pb_items_f, _pb_total_f,
                    linea_nombre=_pb_nombre,
                    numero=_pb_numero,
                )
                st.markdown("**📋 Texto para copiar:**")
                st.code(_txt_copy, language=None)

                _pb_btn1, _pb_btn2 = st.columns(2)
                with _pb_btn1:
                    _lnk_presup = _wa_link_presup(_pb_items_f, _pb_total_f, _pb_lid, engine)
                    st.link_button("📲 Enviar por WhatsApp", url=_lnk_presup, use_container_width=True)
                with _pb_btn2:
                    if st.button("🔄 Nuevo presupuesto", use_container_width=True,
                                 key=f"presup_reset_{_pb_lid}"):
                        st.session_state.pop(_items_key, None)
                        st.session_state[_paso_key] = 1
                        st.rerun()

    # ══ TAB MIKE ══
    with _t_mike:
        st.markdown(f"""
<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:16px;
     padding:20px 24px;border:1px solid #0F3460;margin-bottom:12px;'>
  <div style='font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
       color:#58A6FF;'>ASISTENTE IA</div>
  <div style='font-size:1.4rem;font-weight:800;color:white;margin-top:6px;'>🤖 Mike para {hdr_nombre}</div>
  <div style='font-size:0.78rem;color:#8B949E;margin-top:4px;'>
    Mike conoce tu línea, tus productos y tu historial — preguntale lo que quieras.
  </div>
</div>""", unsafe_allow_html=True)
        _mqs = [
            ("📋 Estado de mi línea",    f"Haceme un resumen del estado actual de la línea {hdr_nombre}: pedidos, stock, margen y oportunidades."),
            ("💰 Mis mejores productos", f"¿Cuáles son mis productos con mejor margen en {hdr_nombre} y por qué?"),
            ("📈 Tendencia de ventas",   f"¿Cómo evolucionaron mis ventas en {hdr_nombre} en los últimos meses? ¿Qué me recomendás?"),
            ("🛒 Cuándo pedir",         f"¿Cuándo conviene que haga el próximo pedido de producción en {hdr_nombre} según el stock y la demanda?"),
            ("⚠️ Riesgos",              f"¿Qué riesgos o alertas tengo en mi línea {hdr_nombre} ahora mismo?"),
            ("🚀 Oportunidades",        f"¿Qué oportunidades de crecimiento ves para la línea {hdr_nombre}?"),
        ]
        _mqc1, _mqc2, _mqc3 = st.columns(3)
        for _mqi, (_mql, _mqt) in enumerate(_mqs):
            with [_mqc1, _mqc2, _mqc3][_mqi % 3]:
                if st.button(_mql, key=f"smq_{_mqi}", use_container_width=True):
                    st.session_state["socio_mike_auto"] = _mqt
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _smk_key = f"socio_mike_hist_{uid}"
        if _smk_key not in st.session_state:
            st.session_state[_smk_key] = []
        for _smsg in st.session_state[_smk_key]:
            with st.chat_message("user" if _smsg["role"]=="user" else "assistant", avatar="👤" if _smsg["role"]=="user" else "🤖"):
                st.markdown(_smsg["content"])
        _smk_q    = st.chat_input(f"Preguntale a Mike sobre {hdr_nombre}...", key=f"smk_input_{uid}")
        _smk_auto = st.session_state.pop("socio_mike_auto", None)
        _smk_preg = _smk_q or _smk_auto
        if _smk_preg:
            _ctx_socio = (
                f"Línea del socio: {hdr_nombre}\n"
                f"SKUs activos: {_n_skus}\n"
                f"Capital en stock: ${_cap_stock:,.0f}\n"
                f"Ganancia proyectada stock: ${_gan_stock:,.0f}\n"
                f"Margen promedio catálogo: {_margen_avg:.1f}%\n"
                f"Pedidos activos: {_n_activos}\n"
                f"Total facturado histórico: ${_fac_total:,.0f}\n"
                f"Pedidos completados: {_n_listo}\n"
            )
            if not prod.empty:
                _ctx_socio += "Productos: " + ", ".join(f"{r['name']} (${r['price']:,.0f}, {r['margen_pct']:.0f}% margen)" for _,r in prod.iterrows()) + "\n"
            try:
                from anthropic import Anthropic as _Anthropic
                from context_elpasaje import SYSTEM_PROMPT, get_data_context
                _ac   = _Anthropic()
                _sys_s = SYSTEM_PROMPT + f"\n\nEres el asistente personal de {hdr_nombre} dentro del ecosistema El Pasaje 3D Studio.\n" + get_data_context()
                _sys_s += f"\n\nCONTEXTO DEL SOCIO:\n{_ctx_socio}"
                _hist_s = st.session_state[_smk_key]
                _hist_s.append({"role":"user","content":_smk_preg})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(_smk_preg)
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Mike está pensando..."):
                        _rr     = _ac.messages.create(model="claude-sonnet-4-6", max_tokens=800, system=_sys_s, messages=_hist_s)
                        _resp_s = _rr.content[0].text
                    st.markdown(_resp_s)
                _hist_s.append({"role":"assistant","content":_resp_s})
                st.session_state[_smk_key] = _hist_s[-20:]
            except Exception as _e:
                st.error(f"Mike no pudo conectarse: {_e}")
        if st.session_state.get(_smk_key):
            if st.button("Limpiar chat", key=f"smk_clear_{uid}"):
                st.session_state[_smk_key] = []
                st.rerun()

    # ══ TAB MI LÍNEA ══
    with _t_linea:
        if role == "socio_multi" and len(lineas_activas) > 1:
            _lc_lid = st.selectbox(
                "Seleccionar línea a configurar",
                lineas_activas,
                format_func=lambda x: LINEAS.get(x, {}).get("nombre", x),
                key="linea_cfg_sel",
            )
        else:
            _lc_lid = uid

        _lc_cfg   = get_linea(_lc_lid)
        _lc_color = _lc_cfg["color"]
        _lc_nom   = _lc_cfg["nombre"]

        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;"
            f"text-transform:uppercase;color:{_lc_color};margin-bottom:16px;'>"
            f"⚙️ CONFIGURACIÓN · {_lc_nom}</div>",
            unsafe_allow_html=True,
        )

        _lc_wa_current = ""
        try:
            with engine.connect() as _lc_conn:
                _lc_row = _lc_conn.execute(
                    text("SELECT whatsapp_numero FROM lineas_config WHERE client_id=:cid"),
                    {"cid": _lc_lid},
                ).fetchone()
            if _lc_row and _lc_row[0]:
                _lc_wa_current = str(_lc_row[0])
        except Exception:
            pass

        with st.form(f"form_linea_cfg_{_lc_lid}"):
            st.markdown(
                "<div style='font-size:0.75rem;color:#8B949E;margin-bottom:12px;'>"
                "Número de WhatsApp de tu línea — se usa para generar los links de contacto "
                "en 🏪 Mi Tienda y 🧮 Presupuesto.</div>",
                unsafe_allow_html=True,
            )
            _lc_wa_input = st.text_input(
                "Número de WhatsApp",
                value=_lc_wa_current,
                placeholder="Ej: 5491155443322 (sin + ni espacios)",
                key=f"lc_wa_{_lc_lid}",
            )
            _lc_submit = st.form_submit_button("Guardar", use_container_width=True, type="primary")

            if _lc_submit:
                _wa_clean = _lc_wa_input.strip().replace(" ", "").replace("+", "")
                if _wa_clean and not (_wa_clean.isdigit() and 10 <= len(_wa_clean) <= 15):
                    st.error("El número debe contener entre 10 y 15 dígitos numéricos (sin +, espacios ni guiones).")
                else:
                    try:
                        with engine.begin() as _lc_conn2:
                            _lc_res = _lc_conn2.execute(
                                text("UPDATE lineas_config SET whatsapp_numero=:wa WHERE client_id=:cid"),
                                {"wa": _wa_clean or None, "cid": _lc_lid},
                            )
                        if _lc_res.rowcount == 0:
                            st.warning("No se encontró la configuración de tu línea. Contactá a Alejandra para inicializarla.")
                        else:
                            st.success(f"Número guardado: {_wa_clean or '(vacío)'}")
                    except Exception as _lce:
                        st.error(f"Error al guardar: {_lce}")

        # ── Precios de reventa ──────────────────────────────────────
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;"
            f"text-transform:uppercase;color:{_lc_color};margin:28px 0 4px;'>"
            f"💲 PRECIOS DE REVENTA</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.75rem;color:#8B949E;margin-bottom:14px;'>"
            "Lo que vos cobrás a tus clientes. No afecta el precio de El Pasaje. "
            "Se usa en presupuestos y links de WhatsApp.</div>",
            unsafe_allow_html=True,
        )
        try:
            _pr_df = pd.read_sql(
                text("""SELECT sku, name, price, precio_reventa
                        FROM products
                        WHERE client_id=:cid AND activo=1
                        ORDER BY name"""),
                engine, params={"cid": _lc_lid},
            )
            if "precio_reventa" not in _pr_df.columns:
                _pr_df["precio_reventa"] = 0.0
        except Exception:
            _pr_df = pd.DataFrame()

        if not _pr_df.empty:
            _pr_inputs = {}
            for _, _prr in _pr_df.iterrows():
                _prr_ep  = float(_prr.get("price", 0) or 0)
                _prr_cur = float(_prr.get("precio_reventa", 0) or 0)
                _prr_mk  = _prr_cur / _prr_ep if (_prr_ep > 0 and _prr_cur > 0) else 0
                _prr_c1, _prr_c2 = st.columns([3, 1])
                with _prr_c1:
                    _mk_badge = (
                        f"<span style='background:#10B98122;color:#10B981;border-radius:99px;"
                        f"padding:1px 7px;font-size:0.6rem;font-weight:700;margin-left:6px;'>×{_prr_mk:.1f}</span>"
                    ) if _prr_mk > 0 else ""
                    st.markdown(
                        f"<div style='padding:6px 0;'>"
                        f"<span style='font-size:0.82rem;font-weight:600;color:#E6EDF3;'>{_prr['name']}</span>"
                        f"{_mk_badge}<br>"
                        f"<span style='font-size:0.65rem;color:#8B949E;'>Precio EP: "
                        f"<b style='color:#F59E0B;'>${_prr_ep:,.0f}</b></span></div>",
                        unsafe_allow_html=True,
                    )
                with _prr_c2:
                    _inp_val = st.number_input(
                        "Precio reventa",
                        min_value=float(_prr_ep),
                        value=max(_prr_cur, _prr_ep),
                        step=100.0, format="%.0f",
                        key=f"pr_inp_{_prr['sku']}_{_lc_lid}",
                        label_visibility="collapsed",
                        help=f"Mínimo ${_prr_ep:,.0f}",
                    )
                _pr_inputs[_prr["sku"]] = (_inp_val, _prr_cur, _prr_ep)
                st.markdown("<div style='border-bottom:1px solid #21262D;margin:2px 0 6px;'></div>",
                            unsafe_allow_html=True)

            if st.button("💾 Guardar todos los precios", type="primary",
                         use_container_width=True, key=f"pr_save_all_{_lc_lid}"):
                _saved = 0
                with engine.begin() as _pr_conn:
                    for _sku_k, (_new_p, _old_p, _ep_p) in _pr_inputs.items():
                        if _new_p < _ep_p:
                            continue
                        _pr_conn.execute(
                            text("UPDATE products SET precio_reventa=:pr, precio_socio=:pr WHERE sku=:s"),
                            {"pr": _new_p, "s": _sku_k},
                        )
                        if abs(_new_p - _old_p) > 0.5 and _old_p > 0:
                            _pr_conn.execute(
                                text("""INSERT INTO price_history
                                        (product_sku, precio_anterior, precio_nuevo, motivo)
                                        VALUES (:s,:a,:n,:m)"""),
                                {"s": _sku_k, "a": _old_p, "n": _new_p,
                                 "m": f"Reventa {_lc_nom} — batch"},
                            )
                        _saved += 1
                get_productos_capa2.clear()
                st.success(f"✅ {_saved} precios guardados")
                st.rerun()

        # ── Fotos de productos ──────────────────────────────────────
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;"
            f"text-transform:uppercase;color:{_lc_color};margin:28px 0 12px;'>"
            f"📷 FOTOS DE PRODUCTOS</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.78rem;color:#8B949E;margin-bottom:16px;'>"
            "Subí una foto por producto. Aparecerá en los cards de 🛒 Cargar Pedido y en el catálogo. "
            "Tamaño máximo: 5 MB. Formatos: JPG, PNG, WEBP.</div>",
            unsafe_allow_html=True,
        )
        try:
            _lc_prods = pd.read_sql(
                text("SELECT sku, name, imagen_url FROM products WHERE client_id=:cid AND activo=1 AND tipo_producto != 'propio_3d' ORDER BY name"),
                engine, params={"cid": _lc_lid},
            )
        except Exception:
            _lc_prods = pd.DataFrame()

        if _lc_prods.empty:
            st.caption("Sin productos cargados en esta línea.")
        else:
            import base64 as _b64
            for _, _lcp in _lc_prods.iterrows():
                _lcp_img = str(_lcp.get("imagen_url") or "")
                _has_lcp_img = bool(_lcp_img and (_lcp_img.startswith("http") or _lcp_img.startswith("data:")))
                _img_status = "✅ Con imagen" if _has_lcp_img else "⬜ Sin imagen"
                with st.expander(f"{_img_status} · {_lcp['name']} ({_lcp['sku']})"):
                    _lcp_c1, _lcp_c2 = st.columns([1, 2])
                    with _lcp_c1:
                        if _has_lcp_img:
                            try:
                                st.image(_lcp_img, width=120)
                            except Exception:
                                st.caption("Error al cargar imagen")
                        else:
                            st.markdown(
                                f"<div style='background:{_lc_color}22;border-radius:8px;width:120px;height:90px;"
                                f"display:flex;align-items:center;justify-content:center;border:1px dashed {_lc_color}44;'>"
                                f"<span style='font-size:1.8rem;'>📷</span></div>",
                                unsafe_allow_html=True,
                            )
                    with _lcp_c2:
                        _lcp_up = st.file_uploader(
                            "Subir foto",
                            type=["jpg", "jpeg", "png", "webp"],
                            key=f"lcp_img_{_lcp['sku']}",
                        )
                        if _lcp_up is not None:
                            if _lcp_up.size > 5 * 1024 * 1024:
                                st.error("La imagen supera 5 MB.")
                            else:
                                _lcp_b64 = _b64.b64encode(_lcp_up.read()).decode("utf-8")
                                _lcp_mime = "image/jpeg" if "jpeg" in (_lcp_up.type or "") else "image/png"
                                _lcp_uri  = f"data:{_lcp_mime};base64,{_lcp_b64}"
                                if st.button("Guardar foto", key=f"lcp_save_{_lcp['sku']}", type="primary", use_container_width=True):
                                    with engine.connect() as _lcp_conn:
                                        _lcp_conn.execute(
                                            text("UPDATE products SET imagen_url=:url WHERE sku=:sku"),
                                            {"url": _lcp_uri, "sku": _lcp["sku"]},
                                        )
                                        _lcp_conn.commit()
                                    st.success("Foto guardada ✅")
                                    st.rerun()
                        if _has_lcp_img:
                            if st.button("🗑 Quitar foto", key=f"lcp_del_{_lcp['sku']}"):
                                with engine.connect() as _lcp_conn:
                                    _lcp_conn.execute(
                                        text("UPDATE products SET imagen_url=NULL WHERE sku=:sku"),
                                        {"sku": _lcp["sku"]},
                                    )
                                    _lcp_conn.commit()
                                st.rerun()

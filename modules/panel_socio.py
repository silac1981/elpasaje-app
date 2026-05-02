"""modules/panel_socio.py — Panel de socio individual y multi-línea."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, PAGINAS_SOCIOS, _BASE_PAGES, get_linea, get_lineas_usuario, _SC


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

    st.markdown(f"""
<div style='background:linear-gradient(135deg,{hdr_color}dd,{hdr_color}88);
     border-radius:20px;padding:24px 32px;margin-bottom:4px;
     border:1px solid {hdr_color}44;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;
       text-transform:uppercase;color:rgba(255,255,255,0.7);'>EL PASAJE 3D STUDIO · SOCIO</div>
  <div style='font-size:2rem;font-weight:800;color:white;margin-top:8px;'>{hdr_emoji} {hdr_nombre}</div>
  <div style='font-size:0.8rem;color:rgba(255,255,255,0.75);margin-top:4px;'>
    Bienvenido/a, {st.session_state['user']} · {datetime.now().strftime('%A %d/%m/%Y')}
  </div>
</div>""", unsafe_allow_html=True)

    from utils.pricing import cargar_productos
    df_all = cargar_productos()
    prod   = df_all[df_all["client_id"].isin(lineas_activas)].copy()

    _lid_str = "','".join(lineas_activas)
    try:
        _pedidos_s = pd.read_sql(f"""
            SELECT o.id, o.client_id, o.status, o.date, o.fecha_entrega_est, o.notas,
                   COALESCE(SUM(oi.cantidad * oi.precio_unitario), 0) AS total
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.client_id IN ('{_lid_str}')
            GROUP BY o.id ORDER BY o.date DESC
        """, engine)
    except Exception:
        _pedidos_s = pd.DataFrame()

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

    _cap_stock  = prod["valor_stock"].sum()
    _gan_stock  = prod["ganancia_stock"].sum()
    _n_skus     = len(prod[prod["activo"]==1]) if "activo" in prod.columns else len(prod)
    _n_activos  = len(_pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])]) if not _pedidos_s.empty else 0
    _n_listo    = len(_pedidos_s[_pedidos_s["status"]=="Listo"]) if not _pedidos_s.empty else 0
    _fac_total  = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum()) if not _pedidos_s.empty else 0
    _margen_avg = prod["margen_pct"].mean() if not prod.empty else 0
    _mg_color   = "#10B981" if _margen_avg>=50 else ("#F59E0B" if _margen_avg>=25 else "#EF4444")

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

    _sk1, _sk2, _sk3, _sk4, _sk5 = st.columns(5)
    for _sc_col, _sv, _sl, _ss, _scolor in [
        (_sk1, f"${_cap_stock:,.0f}",  "💰 Stock",           "valor precio venta",        hdr_color),
        (_sk2, f"${_gan_stock:,.0f}",  "📈 Ganancia Stock",  "margen del inventario",     "#10B981"),
        (_sk3, f"${_fac_total:,.0f}",  "✅ Facturado Total", f"{_n_listo} pedidos listos","#3B82F6"),
        (_sk4, str(_n_activos),        "🏭 En Producción",   "pedidos activos hoy",       "#F59E0B"),
        (_sk5, f"{_margen_avg:.1f}%",  "📊 Margen Prom.",    "promedio de tu catálogo",   _mg_color),
    ]:
        with _sc_col:
            st.markdown(f"<div style='background:#161B22;border-radius:14px;padding:18px 14px;border:1px solid #21262D;border-top:3px solid {_scolor};text-align:center;margin-bottom:8px;'><div style='font-size:1.5rem;font-weight:800;color:{_scolor};line-height:1;'>{_sv}</div><div style='font-size:0.72rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_sl}</div><div style='font-size:0.62rem;color:#8B949E;margin-top:3px;'>{_ss}</div></div>", unsafe_allow_html=True)

    _t_res, _t_stats, _t_prod, _t_ped, _t_mike = st.tabs([
        "🏠 Resumen", "📊 Estadísticas", "📦 Productos", "🛒 Pedidos", "🤖 Mike"
    ])

    # ══ TAB RESUMEN ══
    with _t_res:
        _ra, _rb = st.columns([1.4, 1])
        with _ra:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>PEDIDOS ACTIVOS</div>", unsafe_allow_html=True)
            _pact = _pedidos_s[_pedidos_s["status"].isin(["Pendiente","En Proceso"])] if not _pedidos_s.empty else pd.DataFrame()
            if _pact.empty:
                st.markdown("<div style='background:#0D2818;border-radius:12px;padding:16px 20px;border:1px solid #238636;border-left:4px solid #3FB950;'><span style='color:#3FB950;font-weight:700;'>✅ Sin pedidos en curso</span><br><span style='color:#8B949E;font-size:0.8rem;'>Podés cargar un nuevo pedido desde el menú 🛒</span></div>", unsafe_allow_html=True)
            else:
                for _, _pr in _pact.iterrows():
                    _sc2    = _SC.get(_pr["status"], "#9CA3AF")
                    _fecha2 = str(_pr["date"])[:10] if _pr["date"] else "—"
                    _entrega2 = str(_pr.get("fecha_entrega_est","—") or "—")
                    st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:14px 18px;margin-bottom:8px;border-left:4px solid {_sc2};border:1px solid #21262D;'><div style='font-weight:700;font-size:0.95rem;color:#E6EDF3;'>Pedido #{int(_pr['id'])} <span style='background:{_sc2}22;color:{_sc2};border:1px solid {_sc2}44;border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:600;margin-left:6px;'>{_pr['status']}</span></div><div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>Cargado: {_fecha2} · Entrega: {_entrega2}</div><div style='font-size:0.88rem;font-weight:700;color:{_sc2};margin-top:6px;'>${float(_pr['total']):,.0f}</div></div>", unsafe_allow_html=True)
        with _rb:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>ESTADO DE TU CATÁLOGO</div>", unsafe_allow_html=True)
            if not prod.empty:
                _top3 = prod.sort_values("margen_pct", ascending=False).head(3)
                for _, _p3 in _top3.iterrows():
                    _mc3 = "#10B981" if _p3["margen_pct"]>=50 else ("#F59E0B" if _p3["margen_pct"]>=25 else "#EF4444")
                    st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;margin-bottom:6px;border:1px solid #21262D;'><div style='font-size:0.8rem;font-weight:600;color:#E6EDF3;'>{_p3['name']}</div><div style='background:#21262D;border-radius:3px;height:5px;margin:5px 0;'><div style='background:{_mc3};height:5px;border-radius:3px;width:{min(100,_p3['margen_pct']):.0f}%;'></div></div><div style='font-size:0.72rem;color:{_mc3};font-weight:700;'>{_p3['margen_pct']:.1f}% margen · ${_p3['price']:,.0f}</div></div>", unsafe_allow_html=True)
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
        _sa, _sb = st.columns(2)
        with _sa:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:8px;'>FACTURACIÓN MENSUAL (pedidos listos)</div>", unsafe_allow_html=True)
            if not _hist_mes.empty and len(_hist_mes) > 0:
                _chart_df = _hist_mes.set_index("mes")[["facturado"]].rename(columns={"facturado":"Facturado $"})
                st.bar_chart(_chart_df, color=hdr_color, height=220)
                _meses_ord = _hist_mes.sort_values("mes")
                if len(_meses_ord) >= 2:
                    _fac_act = float(_meses_ord.iloc[-1]["facturado"])
                    _fac_ant = float(_meses_ord.iloc[-2]["facturado"])
                    _delta   = _fac_act - _fac_ant
                    _delta_s = f"+${_delta:,.0f}" if _delta >= 0 else f"-${abs(_delta):,.0f}"
                    st.metric("Este mes vs mes anterior", f"${_fac_act:,.0f}", _delta_s)
            else:
                st.info("Aún no hay pedidos completados para graficar.")
        with _sb:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:8px;'>MARGEN POR PRODUCTO</div>", unsafe_allow_html=True)
            if not prod.empty:
                _mg_chart = prod.sort_values("margen_pct", ascending=False)[["name","margen_pct"]].head(12).copy()
                _mg_chart["name"] = _mg_chart["name"].str[:22]
                st.bar_chart(_mg_chart.set_index("name")[["margen_pct"]].rename(columns={"margen_pct":"Margen %"}), color="#3FB950", height=220)
            else:
                st.info("Sin productos para analizar.")
        st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:10px;'>DISTRIBUCIÓN DE PEDIDOS</div>", unsafe_allow_html=True)
        if not _pedidos_s.empty:
            _dist_cols = st.columns(4)
            for _dci, _dst in enumerate(["Pendiente","En Proceso","Listo","Cancelado"]):
                _dn = len(_pedidos_s[_pedidos_s["status"]==_dst])
                _dc = _SC[_dst]
                with _dist_cols[_dci]:
                    st.markdown(f"<div style='background:#161B22;border-radius:12px;padding:16px;border:1px solid #21262D;border-top:3px solid {_dc};text-align:center;'><div style='font-size:1.8rem;font-weight:800;color:{_dc};'>{_dn}</div><div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>{_dst}</div></div>", unsafe_allow_html=True)
        if not _prec_hist.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#6B7280;margin-top:24px;margin-bottom:8px;'>HISTORIAL DE PRECIOS</div>", unsafe_allow_html=True)
            _ph_show = _prec_hist.copy()
            _ph_show["fecha"]          = _ph_show["fecha"].astype(str).str[:10]
            _ph_show["precio_anterior"] = _ph_show["precio_anterior"].apply(lambda x: f"${x:,.0f}")
            _ph_show["precio_nuevo"]    = _ph_show["precio_nuevo"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(
                _ph_show[["fecha","producto","precio_anterior","precio_nuevo","motivo"]].rename(
                    columns={"fecha":"Fecha","producto":"Producto","precio_anterior":"Precio Anterior",
                             "precio_nuevo":"Precio Nuevo","motivo":"Motivo"}
                ), use_container_width=True, hide_index=True
            )
        if not _fab_socio.empty:
            st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:20px;margin-bottom:8px;'>PRODUCTOS MÁS FABRICADOS</div>", unsafe_allow_html=True)
            _vol_prod = _fab_socio.groupby("producto").agg(
                fabricaciones=("resultado","count"),
                gramos_total=("gramos_usados","sum")
            ).sort_values("fabricaciones", ascending=False).head(8).reset_index()
            st.dataframe(
                _vol_prod.rename(columns={"producto":"Producto","fabricaciones":"Fabricaciones","gramos_total":"Gramos totales"})
                .style.format({"Gramos totales":"{:.0f} g"}),
                use_container_width=True, hide_index=True
            )

    # ══ TAB PRODUCTOS ══
    with _t_prod:
        def _render_cards_linea(df_p, _col_default):
            _df_act = df_p[df_p["activo"]==1] if "activo" in df_p.columns else df_p
            if _df_act.empty:
                st.info("Sin productos activos en esta línea.")
                return
            _pcols2 = st.columns(3)
            for _pii, (_, _prow) in enumerate(_df_act.sort_values("margen_pct", ascending=False).iterrows()):
                _pmc       = "#10B981" if _prow["margen_pct"]>=50 else ("#F59E0B" if _prow["margen_pct"]>=25 else "#EF4444")
                _plincolor = LINEAS.get(_prow["client_id"],{}).get("color", _col_default)
                _pstock_c  = "#10B981" if (_prow.get("stock",0) or 0) > 5 else ("#F59E0B" if (_prow.get("stock",0) or 0) > 0 else "#EF4444")
                _costo_u   = _prow.get("costo_unit", 0) or 0
                _peso_g    = int(_prow.get("weight_gr", 0) or 0)
                with _pcols2[_pii % 3]:
                    st.markdown(f"""<div style='background:#161B22;border-radius:14px;padding:16px;border:1px solid #21262D;margin-bottom:10px;border-top:3px solid {_plincolor};'>
<div style='font-size:0.62rem;color:{_plincolor};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>{_prow.get('sku','')} · {_peso_g}g</div>
<div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;margin-top:4px;line-height:1.2;'>{_prow['name']}</div>
<div style='font-size:0.68rem;color:#8B949E;margin-top:2px;'>{_prow.get('categoria','') or ''}</div>
<div style='margin-top:10px;background:#21262D;border-radius:3px;height:5px;'><div style='background:{_pmc};height:5px;border-radius:3px;width:{min(100,max(0,_prow['margen_pct'])):.0f}%;'></div></div>
<div style='margin-top:8px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;'>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>COSTO EP</div><div style='font-size:0.76rem;font-weight:700;color:#F59E0B;'>${_costo_u:,.0f}</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>PRECIO</div><div style='font-size:0.76rem;font-weight:700;color:#E6EDF3;'>${_prow['price']:,.0f}</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>MARGEN</div><div style='font-size:0.76rem;font-weight:700;color:{_pmc};'>{_prow['margen_pct']:.1f}%</div></div>
  <div style='background:#0D1117;border-radius:6px;padding:5px 4px;text-align:center;'><div style='font-size:0.56rem;color:#8B949E;margin-bottom:2px;'>STOCK</div><div style='font-size:0.76rem;font-weight:700;color:{_pstock_c};'>{int(_prow.get("stock",0) or 0)} u</div></div>
</div>
</div>""", unsafe_allow_html=True)

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
                    _ls1, _ls2, _ls3 = st.columns(3)
                    _n_act3 = len(_lp3[_lp3["activo"]==1]) if "activo" in _lp3.columns else len(_lp3)
                    _mg3    = _lp3["margen_pct"].mean() if not _lp3.empty else 0
                    with _ls1:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>PRODUCTOS</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>{_n_act3}</div></div>", unsafe_allow_html=True)
                    with _ls2:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>VALOR STOCK</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>${_lp3['valor_stock'].sum():,.0f}</div></div>", unsafe_allow_html=True)
                    with _ls3:
                        st.markdown(f"<div style='background:#161B22;border-radius:10px;padding:10px;border:1px solid {_lc3['color']}33;text-align:center;'><div style='font-size:0.58rem;color:#8B949E;font-weight:600;letter-spacing:1px;'>MARGEN PROM.</div><div style='font-size:1.5rem;font-weight:800;color:{_lc3['color']};'>{_mg3:.1f}%</div></div>", unsafe_allow_html=True)
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
        if _pedidos_s.empty:
            st.info("Todavía no tenés pedidos registrados.")
        else:
            _pf_est = st.selectbox("Filtrar por estado", ["Todos","Pendiente","En Proceso","Listo","Cancelado"], key="ped_filtro_socio")
            _pf_df  = _pedidos_s if _pf_est=="Todos" else _pedidos_s[_pedidos_s["status"]==_pf_est]
            if _pf_df.empty:
                st.info(f"Sin pedidos en estado {_pf_est}.")
            for _, _pr2 in _pf_df.iterrows():
                _sc3   = _SC.get(_pr2["status"], "#9CA3AF")
                _lnom2 = LINEAS.get(_pr2["client_id"],{}).get("nombre","")
                _lcol2 = LINEAS.get(_pr2["client_id"],{}).get("color", hdr_color)
                _fec2  = str(_pr2["date"])[:10] if _pr2["date"] else "—"
                _ent2  = str(_pr2.get("fecha_entrega_est","—") or "—")
                _not2  = f"<div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'><em>{_pr2['notas']}</em></div>" if _pr2.get("notas") else ""
                _badge2 = f"<span style='background:{_lcol2}22;color:{_lcol2};border:1px solid {_lcol2}44;border-radius:99px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{_lnom2}</span>" if _show_badge else ""
                st.markdown(
                    f"<div style='background:#161B22;border-radius:14px;padding:16px 20px;margin-bottom:10px;"
                    f"border-left:4px solid {_sc3};border:1px solid #21262D;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div><span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>#{int(_pr2['id'])}</span>"
                    f"<span style='background:{_sc3}22;color:{_sc3};border:1px solid {_sc3}44;"
                    f"border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:700;margin-left:8px;'>{_pr2['status']}</span>"
                    f"{_badge2}"
                    f"<div style='font-size:0.72rem;color:#8B949E;margin-top:5px;'>📅 {_fec2} → entrega {_ent2}</div>"
                    f"{_not2}</div>"
                    f"<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;font-weight:700;color:#E6EDF3;'>${float(_pr2['total']):,.0f}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
            _tot_fac = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum())
            st.markdown(f"<div style='background:#0D1B2E;border-radius:10px;padding:12px 18px;margin-top:6px;border:1px solid #1B2D4A;text-align:right;'><span style='color:#58A6FF;font-weight:700;'>Total facturado (pedidos Listo): ${_tot_fac:,.0f}</span></div>", unsafe_allow_html=True)

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

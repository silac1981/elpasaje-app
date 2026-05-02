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

    _t_res, _t_stats, _t_prod, _t_ped, _t_tienda, _t_presup, _t_mike, _t_linea = st.tabs([
        "🏠 Resumen", "📊 Estadísticas", "📦 Productos", "🛒 Pedidos",
        "🏪 Mi Tienda", "🧮 Presupuesto", "🤖 Mike", "⚙️ Mi Línea",
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
            _pago_badge_map = {
                "pendiente":  ("💳 Pendiente", "#9CA3AF"),
                "acreditado": ("✅ Acreditado", "#10B981"),
                "devuelto":   ("↩️ Devuelto",   "#EF4444"),
            }
            for _, _pr2 in _pf_df.iterrows():
                _sc3   = _SC.get(_pr2["status"], "#9CA3AF")
                _lnom2 = LINEAS.get(_pr2["client_id"],{}).get("nombre","")
                _lcol2 = LINEAS.get(_pr2["client_id"],{}).get("color", hdr_color)
                _fec2  = str(_pr2["date"])[:10] if _pr2["date"] else "—"
                _ent2  = str(_pr2.get("fecha_entrega_est","—") or "—")
                _not2  = f"<div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'><em>{_pr2['notas']}</em></div>" if _pr2.get("notas") else ""
                _badge2 = f"<span style='background:{_lcol2}22;color:{_lcol2};border:1px solid {_lcol2}44;border-radius:99px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{_lnom2}</span>" if _show_badge else ""
                _pest2 = None
                if "pago_estado" in _pedidos_s.columns:
                    _raw_pest = _pr2.get("pago_estado")
                    if _raw_pest is not None and not pd.isna(_raw_pest):
                        _pest2 = str(_raw_pest)
                if _pest2:
                    _pb_txt, _pb_col = _pago_badge_map.get(_pest2, (_pest2, "#9CA3AF"))
                    _pago_badge2 = f"<span style='background:{_pb_col}22;color:{_pb_col};border:1px solid {_pb_col}44;border-radius:99px;padding:2px 9px;font-size:0.68rem;font-weight:600;margin-left:8px;'>{_pb_txt}</span>"
                else:
                    _pago_badge2 = ""
                st.markdown(
                    f"<div style='background:#161B22;border-radius:14px;padding:16px 20px;margin-bottom:10px;"
                    f"border-left:4px solid {_sc3};border:1px solid #21262D;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div><span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>#{int(_pr2['id'])}</span>"
                    f"<span style='background:{_sc3}22;color:{_sc3};border:1px solid {_sc3}44;"
                    f"border-radius:99px;padding:2px 10px;font-size:0.7rem;font-weight:700;margin-left:8px;'>{_pr2['status']}</span>"
                    f"{_badge2}{_pago_badge2}"
                    f"<div style='font-size:0.72rem;color:#8B949E;margin-top:5px;'>📅 {_fec2} → entrega {_ent2}</div>"
                    f"{_not2}</div>"
                    f"<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;font-weight:700;color:#E6EDF3;'>${float(_pr2['total']):,.0f}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
            _tot_fac = float(_pedidos_s[_pedidos_s["status"]=="Listo"]["total"].sum())
            st.markdown(f"<div style='background:#0D1B2E;border-radius:10px;padding:12px 18px;margin-top:6px;border:1px solid #1B2D4A;text-align:right;'><span style='color:#58A6FF;font-weight:700;'>Total facturado (pedidos Listo): ${_tot_fac:,.0f}</span></div>", unsafe_allow_html=True)

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
       color:{lcolor};'>CAPA 2 · UNIVERSO DE LA LINEA</div>
  <div style='font-size:1.1rem;font-weight:800;color:#E6EDF3;margin-top:6px;'>🏪 Mi Tienda — {lnom}</div>
  <div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>
    Publicá tus propios productos. Borrador = solo vos lo ves · Publico = visible en tu página web.
  </div>
</div>""", unsafe_allow_html=True)

            df_c2 = get_productos_capa2(lid)

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

            if df_c2.empty:
                st.markdown("<div style='background:#161B22;border-radius:12px;padding:20px;border:1px dashed #30363D;text-align:center;color:#8B949E;margin-bottom:16px;'>Todavía no tenés productos propios en Capa 2.<br>Usá el formulario de abajo para agregar el primero.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-bottom:10px;'>TUS PRODUCTOS</div>", unsafe_allow_html=True)
                for _, _r2 in df_c2.iterrows():
                    _vis2  = _r2.get("visibilidad", "borrador") or "borrador"
                    _vc2   = _VIS_COLOR.get(_vis2, "#6B7280")
                    _vl2   = _VIS_LABEL.get(_vis2, _vis2)
                    _tipo2 = (_r2.get("tipo_producto", "linea_propio") or "linea_propio").replace("_", " ").title()
                    _is_kit = (_r2.get("tipo_producto") or "") == "kit_mixto"
                    _kc_this = _df_kc_all[_df_kc_all["kit_sku"] == _r2["sku"]] if not _df_kc_all.empty else pd.DataFrame()
                    _kit_badge = f" · {len(_kc_this)} componentes" if _is_kit else ""
                    _ca2, _cb2 = st.columns([3, 1])
                    with _ca2:
                        st.markdown(f"""
<div style='background:#161B22;border-radius:12px;padding:14px 18px;
     border:1px solid #21262D;border-left:3px solid {_vc2};'>
  <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;'>
    <span style='font-size:0.82rem;font-weight:700;color:#E6EDF3;'>{_r2['name']}</span>
    <span style='background:{_vc2}22;color:{_vc2};border:1px solid {_vc2}44;border-radius:99px;
         padding:2px 9px;font-size:0.65rem;font-weight:700;'>{_vl2}</span>
    <span style='background:#21262D;color:#8B949E;border-radius:99px;
         padding:2px 9px;font-size:0.62rem;'>{_tipo2}</span>
  </div>
  <div style='font-size:0.72rem;color:#8B949E;margin-top:4px;'>
    SKU: {_r2.get('sku','')} &nbsp;·&nbsp; Precio: ${float(_r2.get('price',0) or 0):,.0f} &nbsp;·&nbsp; Stock: {int(_r2.get('stock',0) or 0)} u{_kit_badge}
  </div>
</div>""", unsafe_allow_html=True)
                    with _cb2:
                        _vis_opts = ["publico", "borrador", "pausado"]
                        _vis_idx  = _vis_opts.index(_vis2) if _vis2 in _vis_opts else 1
                        _new_vis  = st.selectbox("", _vis_opts, index=_vis_idx,
                                                 key=f"vis_{_r2['sku']}_{lid}",
                                                 format_func=lambda x: _VIS_LABEL[x])
                        if _new_vis != _vis2:
                            if st.button("Guardar", key=f"vis_save_{_r2['sku']}_{lid}",
                                         use_container_width=True):
                                with engine.begin() as _cn2:
                                    _cn2.execute(
                                        text("UPDATE products SET visibilidad=:v WHERE sku=:s"),
                                        {"v": _new_vis, "s": _r2["sku"]}
                                    )
                                get_productos_capa2.clear()
                                _cp_tienda.clear()
                                st.success("Visibilidad actualizada")
                                st.rerun()
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
                                        unsafe_allow_html=True
                                    )
                                _kit_total = float(
                                    (_kc_this["comp_price"].fillna(0) * _kc_this["cantidad"].fillna(1)).sum()
                                )
                                st.markdown(
                                    f"<div style='font-size:0.8rem;font-weight:700;color:#E6EDF3;"
                                    f"text-align:right;margin-top:6px;'>"
                                    f"Total componentes: ${_kit_total:,.0f}</div>",
                                    unsafe_allow_html=True
                                )

                    # ── Links de WhatsApp por producto ──────────────────
                    if _vis2 != "pausado":
                        _is_ip_wa = any(kw in (_r2.get("name", "") or "").lower() for kw in IP_RESTRINGIDA)
                        if _is_ip_wa:
                            st.markdown(
                                "<div style='font-size:0.72rem;color:#9CA3AF;padding:4px 2px;'>"
                                "🔒 Solo uso interno</div>",
                                unsafe_allow_html=True,
                            )
                        elif not _wa_configured:
                            st.caption("⚠️ Configurá el número de WhatsApp de tu línea en ⚙️ Mi Línea")
                        else:
                            _wa_lnk = _wa_link_producto(
                                _r2.get("name", ""), _r2.get("sku", ""),
                                float(_r2.get("price", 0) or 0), lid, engine,
                            )
                            _wa_txt_u = (
                                f"Hola! Me interesa el {_r2.get('name','')} "
                                f"(SKU: {_r2.get('sku','')}) — "
                                f"${float(_r2.get('price', 0) or 0):,.0f} ¿Está disponible?"
                            )
                            _wa_c1, _wa_c2 = st.columns(2)
                            with _wa_c1:
                                st.link_button("📲 WhatsApp", url=_wa_lnk, use_container_width=True)
                            with _wa_c2:
                                st.code(_wa_txt_u, language=None)

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

            if _paso_act == 1:
                # ── Paso 1: armar presupuesto ──────────────────────────
                _pb_opts    = _pb_prods["sku"].tolist()
                _pb_lbl_map = {
                    r["sku"]: f"{r['sku']} — {r['name']} — ${float(r['price']):,.0f}"
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
                        _pb_row = _pb_prods[_pb_prods["sku"] == _pb_sku].iloc[0]
                        _pb_qty = st.number_input(
                            f"{_pb_row['name']}  (${float(_pb_row['price']):,.0f} c/u)",
                            min_value=1, value=1, step=1,
                            key=f"presup_qty_{_pb_sku}_{_pb_lid}",
                        )
                        _pb_sub = float(_pb_row["price"]) * int(_pb_qty)
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
                            _r2 = _r2.iloc[0]
                            _qty2 = int(st.session_state.get(f"presup_qty_{_pb_sku2}_{_pb_lid}", 1))
                            _final_items.append({
                                "nombre":   _r2["name"],
                                "sku":      _pb_sku2,
                                "cantidad": _qty2,
                                "precio":   float(_r2["price"]),
                            })
                        st.session_state[_items_key] = _final_items
                        st.session_state[_paso_key]  = 2
                        st.rerun()
                else:
                    st.caption("Seleccioná al menos un producto para armar el presupuesto.")

            else:
                # ── Paso 2: presupuesto generado ───────────────────────
                _pb_items_f = st.session_state.get(_items_key, [])
                _pb_total_f = sum(float(it["precio"]) * int(it["cantidad"]) for it in _pb_items_f)
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
                        f"${float(it['precio']) * int(it['cantidad']):,.0f}</span></div>"
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
                text("SELECT sku, name, imagen_url FROM products WHERE client_id=:cid AND activo=1 ORDER BY name"),
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

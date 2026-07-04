"""modules/cargar_pedido.py — Formulario de carga de pedidos para socios."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, get_linea, get_lineas_usuario
from utils.orders import verificar_material_disponible as _verificar_mat_cp


def render():
    uid  = st.session_state["uid"]
    role = st.session_state["role"]
    if role == "socio_multi":
        lineas_activas = st.session_state.get("linea_filtro", get_lineas_usuario(uid))
        cfg = LINEAS.get(uid, {"nombre": "Mis Líneas", "emoji": "✨", "color": "#6366F1"})
    else:
        lineas_activas = [uid]
        cfg = get_linea(uid)

    _cp_color = cfg.get("color", "#6366F1")

    st.markdown(f"""<style>
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{background-color:#0D1117!important}}
.stTabs [data-baseweb="tab-list"]{{background:#161B22!important;border-radius:12px!important;padding:4px!important}}
.stTabs [data-baseweb="tab"]{{color:#8B949E!important;font-weight:600!important;border-radius:8px!important}}
.stTabs [aria-selected="true"]{{background:#21262D!important;color:#F0F6FC!important}}
[data-testid="stFileUploaderDropzone"]{{background:#161B22!important;border-color:{_cp_color}44!important}}
.stMarkdown p,.stMarkdown span{{color:#C9D1D9!important}}
.stMarkdown strong,.stMarkdown b{{color:#F0F6FC!important}}
.stSelectbox label,.stTextInput label,.stTextArea label,.stNumberInput label,.stDateInput label,.stFileUploader label{{color:#8B949E!important;font-weight:500!important}}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{{color:#C9D1D9!important}}
[data-testid="stAlert"]{{background:#1a2332!important;border-color:#30363D!important}}
details{{background:#161B22!important;border:1px solid #21262D!important;border-radius:12px!important}}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}}
[data-testid="stSelectbox"] div[data-baseweb="select"] div{{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}}
[data-testid="stDateInput"] input{{background:#161B22!important;color:#E6EDF3!important;border-color:#30363D!important}}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{{color:#6B7280!important}}
</style>""", unsafe_allow_html=True)

    st.markdown(f"""
<div style='background:linear-gradient(135deg,{_cp_color}dd,{_cp_color}88);
     border-radius:20px;padding:20px 28px;margin-bottom:16px;border:1px solid {_cp_color}44;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.7);'>EL PASAJE 3D STUDIO</div>
  <div style='font-size:1.6rem;font-weight:800;color:white;margin-top:4px;'>🛒 Nuevo Pedido · {cfg['nombre']}</div>
  <div style='font-size:0.78rem;color:rgba(255,255,255,0.65);margin-top:4px;'>Solicitá producción a Fer — quedará registrado en el sistema</div>
</div>""", unsafe_allow_html=True)

    with engine.connect() as _conn:
        _frames = [
            pd.read_sql(
                text("SELECT name, sku, price, weight_gr, description, categoria, color, client_id, imagen_url FROM products WHERE client_id=:uid AND activo=1 ORDER BY name"),
                _conn, params={"uid": lid}
            ) for lid in lineas_activas
        ]
    prods_socio = pd.concat(_frames, ignore_index=True) if _frames else pd.DataFrame()

    if prods_socio.empty:
        st.markdown("<div style='background:#161B22;border-radius:12px;padding:20px;border:1px solid #21262D;text-align:center;color:#8B949E;'>Sin productos cargados todavía. Contactá a Alejandra para agregarlos.</div>", unsafe_allow_html=True)
        st.stop()

    if "cp_sel_sku" not in st.session_state:
        st.session_state["cp_sel_sku"] = None

    _sel_sku  = st.session_state.get("cp_sel_sku")
    _sel_prod = prods_socio[prods_socio["sku"] == _sel_sku].iloc[0] if _sel_sku and not prods_socio[prods_socio["sku"]==_sel_sku].empty else None

    # ── Sin selección: grid agrupado por línea ────────────────────
    if _sel_prod is None:
        st.markdown(
            "<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
            "color:#58A6FF;margin-bottom:12px;'>SELECCIONÁ UN PRODUCTO</div>",
            unsafe_allow_html=True,
        )
        _multi = len(lineas_activas) > 1
        for _lid in lineas_activas:
            _ldf = prods_socio[prods_socio["client_id"] == _lid]
            if _ldf.empty:
                continue
            _lcfg   = get_linea(_lid)
            _lcolor = _lcfg["color"]
            _ln     = len(_ldf)
            _ctx = st.expander(
                f"{_lcfg['emoji']} {_lcfg['nombre']}  ·  {_ln} producto{'s' if _ln != 1 else ''}",
                expanded=True,
            ) if _multi else st.container()
            with _ctx:
                _cp_cols = st.columns(3)
                for _cpi, (_, _cpr) in enumerate(_ldf.iterrows()):
                    _img_url_cp = str(_cpr.get("imagen_url") or "")
                    _has_img_cp = _img_url_cp.startswith("http") or _img_url_cp.startswith("data:")
                    _img_tag = (f"<img src='{_img_url_cp}' style='width:100%;height:90px;object-fit:cover;"
                                f"border-radius:8px;margin-bottom:8px;' onerror=\"this.style.display='none'\">") if _has_img_cp else ""
                    with _cp_cols[_cpi % 3]:
                        st.markdown(f"""<div style='border:1px solid {_lcolor}44;background:#161B22;border-radius:14px;padding:14px;margin-bottom:8px;'>
{_img_tag}
<div style='font-size:0.6rem;color:{_lcolor};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>{_cpr['sku']}</div>
<div style='font-size:0.88rem;font-weight:700;color:#E6EDF3;margin-top:3px;'>{_cpr['name']}</div>
<div style='font-size:0.68rem;color:#8B949E;margin-top:2px;'>{_cpr.get('categoria','') or ''}</div>
<div style='margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:4px;'>
  <div><div style='font-size:0.52rem;color:#8B949E;text-transform:uppercase;'>Precio EP</div>
  <div style='font-size:0.92rem;font-weight:800;color:{_lcolor};'>${float(_cpr['price']):,.0f}</div></div>
  <div><div style='font-size:0.52rem;color:#8B949E;text-transform:uppercase;'>Costo fab.</div>
  <div style='font-size:0.92rem;font-weight:800;color:#94A3B8;'>${round(float(_cpr.get("weight_gr",0) or 0)*1.10*2350/1000):,.0f}</div></div>
</div>
<div style='font-size:0.65rem;color:#6B7280;'>{float(_cpr.get('weight_gr',0) or 0):.0f} g · {str(_cpr.get('description','') or '')[:50]}</div>
</div>""", unsafe_allow_html=True)
                        if st.button("Seleccionar", key=f"cpbtn_{_cpr['sku']}", use_container_width=True, type="secondary"):
                            st.session_state["cp_sel_sku"] = _cpr["sku"]
                            st.rerun()
        st.stop()

    # ── Con selección: banner compacto + formulario inmediatamente ──
    _cpc_s = LINEAS.get(_sel_prod["client_id"], {}).get("color", "#6366F1")
    _img_s = str(_sel_prod.get("imagen_url") or "")
    _img_s = _img_s if (_img_s.startswith("http") or _img_s.startswith("data:")) else ""

    _bn_img = _img_s
    _bn_img_html = ""
    if _bn_img:
        _bn_img_html = f"<img src='{_bn_img}' style='width:56px;height:56px;object-fit:cover;border-radius:8px;margin-right:14px;flex-shrink:0;'>"
    else:
        _bn_img_html = f"<div style='width:56px;height:56px;background:{_cpc_s}22;border-radius:8px;display:flex;align-items:center;justify-content:center;margin-right:14px;flex-shrink:0;font-size:1.5rem;'>{cfg.get('emoji','📦')}</div>"

    st.markdown(
        f"<div style='background:#161B22;border-radius:14px;padding:14px 18px;border:2px solid {_cpc_s};"
        f"margin-bottom:16px;display:flex;align-items:center;'>"
        f"{_bn_img_html}"
        f"<div style='flex:1;min-width:0;'>"
        f"<div style='font-size:0.6rem;color:{_cpc_s};font-weight:700;letter-spacing:1px;text-transform:uppercase;'>"
        f"✓ SELECCIONADO · {_sel_prod['sku']}</div>"
        f"<div style='font-size:1rem;font-weight:800;color:#E6EDF3;margin-top:2px;'>{_sel_prod['name']}</div>"
        f"<div style='font-size:0.72rem;color:#8B949E;margin-top:2px;'>"
        f"{str(_sel_prod.get('description','') or '')} · ${float(_sel_prod['price']):,.0f} · "
        f"{float(_sel_prod.get('weight_gr',0) or 0):.0f} g</div></div></div>",
        unsafe_allow_html=True,
    )
    if st.button("✏️ Cambiar producto", key="cp_cambiar"):
        st.session_state["cp_sel_sku"] = None
        st.rerun()

    st.markdown(
        f"<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
        f"color:#58A6FF;margin:16px 0 12px;'>DETALLE DEL PEDIDO · {_sel_prod['name'].upper()}</div>",
        unsafe_allow_html=True,
    )

    _fd1, _fd2 = st.columns(2)
    with _fd1:
        _cp_qty   = st.number_input("Cantidad de unidades", min_value=1, max_value=50, value=1, key="cp_qty")
        _cp_fecha = st.date_input("Fecha de entrega deseada (opcional)", value=None, key="cp_fecha")
    with _fd2:
        _cp_color_txt = st.text_input("Color o material preferido (ej: Rosa, Negro mate, PETG gris)", key="cp_color")
        _cp_urgente   = st.checkbox("🔴 Urgente", key="cp_urgente", help="Ferr lo prioriza en la cola")

    _cp_notas = st.text_area(
        "Notas adicionales para Fer (medidas especiales, acabado, packaging, etc.)",
        placeholder="Ej: Necesito el moño con cinta integrada, para regalo de 15 años este viernes...",
        height=90, key="cp_notas"
    )

    st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:16px;margin-bottom:8px;'>¿CÓMO NOS CONOCISTE?</div>", unsafe_allow_html=True)
    _canal_icons = {
        "Ya era cliente / familia": "👨‍👩‍👧",
        "Instagram":                "📸",
        "TikTok":                   "🎵",
        "Recomendación personal":   "🤝",
        "Presencial / evento":      "🏪",
        "WhatsApp directo":         "💬",
        "Otro":                     "💡",
    }
    _cp_canal = st.selectbox(
        "Canal de origen del pedido",
        list(_canal_icons.keys()),
        index=0, key="cp_canal", label_visibility="collapsed"
    )
    st.markdown(f"<div style='background:#161B22;border-radius:8px;padding:8px 14px;border:1px solid #21262D;font-size:0.8rem;color:#8B949E;'>{_canal_icons[_cp_canal]} <b style='color:#C9D1D9;'>{_cp_canal}</b> — esto ayuda a saber por dónde llegan los pedidos</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:16px;margin-bottom:8px;'>REFERENCIAS E IMÁGENES (opcional)</div>", unsafe_allow_html=True)
    _cp_files = st.file_uploader(
        "Subí fotos de referencia, bocetos, archivos STL, PDFs o cualquier cosa que le ayude a Fer",
        type=["png","jpg","jpeg","pdf","stl","3mf","dxf","svg","docx","txt"],
        accept_multiple_files=True, key="cp_files"
    )
    if _cp_files:
        _fnames = [f.name for f in _cp_files]
        st.markdown(f"<div style='background:#0D2818;border-radius:8px;padding:8px 14px;border:1px solid #238636;'><span style='color:#3FB950;font-size:0.8rem;'>📎 {len(_cp_files)} archivo{'s' if len(_cp_files)>1 else ''} adjunto{'s' if len(_cp_files)>1 else ''}: {', '.join(_fnames)}</span></div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#58A6FF;margin-top:16px;margin-bottom:8px;'>MÉTODO DE PAGO</div>", unsafe_allow_html=True)
    _cp_metodo_opts = ["Transferencia", "Efectivo", "MercadoPago (próximamente)"]
    _cp_metodo = st.radio("", _cp_metodo_opts, horizontal=True, key="cp_metodo", label_visibility="collapsed")
    if _cp_metodo == "MercadoPago (próximamente)":
        st.info("💳 MercadoPago estará disponible cuando se configure la cuenta vendedor. Tu pedido se registrará como pendiente de pago.")
        _cp_metodo_clean = "mp"
    elif _cp_metodo == "Efectivo":
        _cp_metodo_clean = "efectivo"
    else:
        _cp_metodo_clean = "transferencia"

    _total_est = float(_sel_prod["price"]) * _cp_qty
    st.markdown(f"""
<div style='background:#161B22;border-radius:14px;padding:16px 20px;border:1px solid {_cp_color}44;
     border-left:4px solid {_cp_color};margin-top:16px;margin-bottom:16px;'>
  <div style='font-size:0.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{_cp_color};margin-bottom:8px;'>RESUMEN DEL PEDIDO</div>
  <div style='font-size:0.9rem;font-weight:700;color:#E6EDF3;'>{_cp_qty}x {_sel_prod['name']}</div>
  <div style='font-size:0.75rem;color:#8B949E;margin-top:2px;'>{_cp_color_txt or "Color por defecto"} · {("🔴 URGENTE" if _cp_urgente else "Sin urgencia")} · {_canal_icons.get(_cp_canal,"")}{_cp_canal}</div>
  <div style='font-size:1.2rem;font-weight:800;color:{_cp_color};margin-top:8px;'>${_total_est:,.0f}</div>
</div>""", unsafe_allow_html=True)

    if st.button("✅ Confirmar Pedido", type="primary", use_container_width=True, key="cp_submit"):
        _notas_full = []
        if _cp_color_txt: _notas_full.append(f"Color/material: {_cp_color_txt}")
        if _cp_urgente:   _notas_full.append("🔴 URGENTE")
        if _cp_notas.strip(): _notas_full.append(_cp_notas.strip())
        if _cp_files:     _notas_full.append(f"Archivos adjuntos: {', '.join(f.name for f in _cp_files)}")
        _notas_full.append(f"Canal origen: {_cp_canal}")
        _notas_str    = " | ".join(_notas_full)
        _fecha_str    = _cp_fecha.isoformat() if _cp_fecha else None
        _archivos_str = ", ".join(f.name for f in _cp_files) if _cp_files else None
        linea_pedido  = _sel_prod["client_id"]
        with engine.connect() as _conn2:
            result = _conn2.execute(
                text("""INSERT INTO orders (client_id, status, date, notas, color_pedido,
                                           fecha_entrega_solicitada, referencia_archivo, canal_origen)
                        VALUES (:cid, 'Pendiente', :fecha, :notas, :color,
                                :entrega, :archivos, :canal)"""),
                {"cid": linea_pedido, "fecha": datetime.now().isoformat(),
                 "notas": _notas_str, "color": _cp_color_txt or "",
                 "entrega": _fecha_str, "archivos": _archivos_str, "canal": _cp_canal}
            )
            order_id = result.lastrowid
            prod_q = pd.read_sql(
                text("SELECT price FROM products WHERE sku=:sku"),
                _conn2, params={"sku": _sel_sku}
            )
            _conn2.execute(
                text("INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) VALUES (:oid, :sku, :qty, :precio)"),
                {"oid": order_id, "sku": _sel_sku, "qty": _cp_qty,
                 "precio": float(prod_q["price"].iloc[0]) if not prod_q.empty else float(_sel_prod["price"])}
            )
            try:
                _conn2.execute(
                    text("INSERT INTO pagos (order_id, monto, metodo, estado) VALUES (:oid, :monto, :metodo, 'pendiente')"),
                    {"oid": order_id, "monto": _total_est, "metodo": _cp_metodo_clean},
                )
            except Exception:
                pass
            # Trazabilidad: reserva de stock al crear pedido
            try:
                _conn2.execute(
                    text("INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia) VALUES (:sku, :tipo, :qty, :fecha, :ref)"),
                    {"sku": _sel_sku, "tipo": "pedido", "qty": -_cp_qty,
                     "fecha": datetime.now().strftime("%Y-%m-%d"), "ref": f"order_{order_id}"},
                )
                _conn2.commit()
            except Exception:
                pass  # stock_movements no bloquea el flujo principal
            _conn2.commit()
        # Verificar material disponible para el pedido recién creado
        _mat_check = _verificar_mat_cp(order_id)
        st.session_state.pop("cp_sel_sku", None)
        st.success(f"✅ Pedido #{order_id} enviado a Fer — {_cp_qty}x {_sel_prod['name']} · ${_total_est:,.0f}")
        if not _mat_check["ok"]:
            st.warning(
                f"⚠️ Alerta de material: falta {_mat_check.get('faltante_gr',0):.0f} g de "
                f"{_mat_check.get('material','?')} para fabricar este pedido. "
                f"(Necesario: {_mat_check.get('requerido_gr',0):.0f} g · Disponible: {_mat_check.get('disponible_gr',0):.0f} g)"
            )
        if _cp_urgente:
            st.warning("🔴 Marcado como urgente — Fer lo verá al tope de su cola.")
        st.balloons()

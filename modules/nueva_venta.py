"""modules/nueva_venta.py — Wizard rapido de venta para admin (<=30 s)."""
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, get_linea

_BG      = "#EBE6DC"
_SURFACE = "#FAF8F3"
_INK     = "#16181F"
_INK2    = "#3A3E4A"
_MUTED   = "#74798A"
_LINE    = "#DCD5C7"
_EP      = "#FF4B4B"
_OK      = "#2F9E54"


def render():
    st.markdown(
        "<div class='main-header'><h1>🛒 Nueva Venta</h1>"
        "<p>Registra una venta en menos de 30 segundos</p></div>",
        unsafe_allow_html=True,
    )

    step = st.session_state.get("nv_step", 0)

    _steps = ["Producto", "Detalle", "Confirmar"]
    _cols  = st.columns(3)
    for i, (col, label) in enumerate(zip(_cols, _steps)):
        with col:
            _c = _EP if i == step else (_OK if i < step else _LINE)
            st.markdown(
                f"<div style='text-align:center;padding:8px;background:{_SURFACE};"
                f"border-radius:8px;border:2px solid {_c};margin-bottom:4px;'>"
                f"<div style='font-size:0.58rem;font-weight:700;letter-spacing:.1em;"
                f"text-transform:uppercase;color:{_c};'>{i+1}. {label}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if step == 0:
        _step_producto()
    elif step == 1:
        _step_detalle()
    elif step == 2:
        _step_confirmar()


def _step_producto():
    with engine.connect() as conn:
        _df_l = pd.read_sql(text("SELECT DISTINCT client_id FROM products WHERE activo=1"), conn)

    _lids = [l for l in _df_l["client_id"].tolist() if l in LINEAS]
    if not _lids:
        st.warning("No hay productos activos.")
        return

    _lid_actual = st.session_state.get("nv_linea", _lids[0])
    if _lid_actual not in _lids:
        _lid_actual = _lids[0]

    _opts = {LINEAS[l]["nombre"]: l for l in _lids}
    _nombre_actual = next((n for n, lid in _opts.items() if lid == _lid_actual), list(_opts)[0])
    _sel_nombre = st.selectbox(
        "Línea",
        list(_opts.keys()),
        index=list(_opts.keys()).index(_nombre_actual),
        key="nv_linea_sel",
    )
    _sel_lid = _opts[_sel_nombre]
    if _sel_lid != st.session_state.get("nv_linea"):
        st.session_state["nv_linea"] = _sel_lid
        st.session_state.pop("nv_sku", None)
        st.rerun()

    _lcfg = get_linea(_sel_lid)

    with engine.connect() as conn:
        _prods = pd.read_sql(
            text("SELECT sku, name, price, weight_gr, stock FROM products WHERE client_id=:lid AND activo=1 ORDER BY name"),
            conn, params={"lid": _sel_lid},
        )

    if _prods.empty:
        st.info("Esta línea no tiene productos activos.")
        return

    st.markdown(
        f"<div style='font-size:0.6rem;font-weight:700;letter-spacing:.12em;"
        f"text-transform:uppercase;color:{_lcfg['color']};margin:16px 0 10px;'>SELECCIONAR PRODUCTO</div>",
        unsafe_allow_html=True,
    )

    _sel_sku = st.session_state.get("nv_sku")
    _cols    = st.columns(4)
    for i, (_, row) in enumerate(_prods.iterrows()):
        with _cols[i % 4]:
            _is_sel = (_sel_sku == row["sku"])
            _border = f"2px solid {_lcfg['color']}" if _is_sel else f"1px solid {_LINE}"
            _bg     = f"{_lcfg['color']}18" if _is_sel else _SURFACE
            st.markdown(
                f"<div style='background:{_bg};border:{_border};border-radius:12px;"
                f"padding:12px;margin-bottom:8px;'>"
                f"<div style='font-size:0.55rem;color:{_lcfg['color']};font-weight:700;letter-spacing:1px;'>{row['sku']}</div>"
                f"<div style='font-size:0.85rem;font-weight:700;color:{_INK};margin-top:2px;'>{row['name']}</div>"
                f"<div style='font-size:1rem;font-weight:800;color:{_lcfg['color']};margin-top:4px;'>${float(row['price']):,.0f}</div>"
                f"<div style='font-size:0.65rem;color:{_MUTED};'>Stock: {int(row['stock'] or 0)} uds</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            _lbl = "✓ Elegido" if _is_sel else "Elegir"
            _typ = "primary" if _is_sel else "secondary"
            if st.button(_lbl, key=f"nv_sel_{row['sku']}", use_container_width=True, type=_typ):
                st.session_state["nv_sku"]    = row["sku"]
                st.session_state["nv_precio"] = float(row["price"])
                st.rerun()

    if _sel_sku and not _prods[_prods["sku"] == _sel_sku].empty:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        _prod_row = _prods[_prods["sku"] == _sel_sku].iloc[0]
        _nv_qty   = st.number_input("Cantidad", min_value=1, max_value=100,
                                     value=st.session_state.get("nv_qty", 1), key="nv_qty_inp")
        st.session_state["nv_qty"] = int(_nv_qty)

        _total = float(_prod_row["price"]) * _nv_qty
        st.markdown(
            f"<div style='background:{_SURFACE};border-radius:10px;padding:14px;border:1px solid {_LINE};"
            f"border-left:3px solid {_lcfg['color']};margin-top:8px;'>"
            f"<b style='color:{_INK};'>{int(_nv_qty)}× {_prod_row['name']}</b>"
            f" — <b style='color:{_lcfg['color']};font-size:1.1rem;'>${_total:,.0f}</b></div>",
            unsafe_allow_html=True,
        )

        if st.button("Continuar →", type="primary", use_container_width=True, key="nv_next0"):
            st.session_state["nv_step"] = 1
            st.rerun()
    else:
        st.info("Seleccioná un producto para continuar.")


def _step_detalle():
    _sel_lid  = st.session_state.get("nv_linea")
    _sel_sku  = st.session_state.get("nv_sku")
    _sel_qty  = st.session_state.get("nv_qty", 1)
    _precio_b = st.session_state.get("nv_precio", 0)

    if not _sel_sku:
        st.error("Falta seleccionar producto. Volvé al paso 1.")
        if st.button("← Volver"):
            st.session_state["nv_step"] = 0
            st.rerun()
        return

    with engine.connect() as conn:
        _prod_row = pd.read_sql(text("SELECT name FROM products WHERE sku=:sku"), conn, params={"sku": _sel_sku})
    _prod_name = _prod_row.iloc[0]["name"] if not _prod_row.empty else _sel_sku

    st.markdown(
        f"<div style='background:{_SURFACE};border-radius:10px;padding:12px 16px;"
        f"border:1px solid {_LINE};margin-bottom:16px;'>"
        f"<b style='color:{_INK};'>{_prod_name}</b> × {_sel_qty}</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        _nv_cliente = st.text_input(
            "Cliente final",
            value=st.session_state.get("nv_cliente", ""),
            placeholder="Ej: María González",
            key="nv_cliente_inp",
        )
        st.session_state["nv_cliente"] = _nv_cliente
    with c2:
        _canales  = ["Presencial", "WhatsApp", "Instagram", "TikTok", "Email", "Otro"]
        _canal_i  = st.session_state.get("nv_canal_idx", 0)
        _nv_canal = st.selectbox("Canal", _canales, index=min(_canal_i, len(_canales)-1), key="nv_canal_inp")
        st.session_state["nv_canal_idx"] = _canales.index(_nv_canal)

    _nv_precio = st.number_input(
        "Precio unitario ($)",
        min_value=0, value=int(_precio_b), step=100,
        help="Podés ajustar si hay descuento",
        key="nv_precio_inp",
    )
    st.session_state["nv_precio"] = float(_nv_precio)

    _nv_notas = st.text_area(
        "Notas (opcional)",
        value=st.session_state.get("nv_notas", ""),
        placeholder="Color, medidas, packaging...",
        height=80,
        key="nv_notas_inp",
    )
    st.session_state["nv_notas"] = _nv_notas

    _total = float(_nv_precio) * _sel_qty
    st.markdown(
        f"<div style='background:{_SURFACE};border-radius:10px;padding:14px;border:1px solid {_LINE};"
        f"border-left:3px solid {_OK};margin-top:8px;'>"
        f"<b style='color:{_INK};'>Total: <span style='color:{_OK};font-size:1.2rem;'>${_total:,.0f}</span></b></div>",
        unsafe_allow_html=True,
    )

    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("← Volver", use_container_width=True, key="nv_back1"):
            st.session_state["nv_step"] = 0
            st.rerun()
    with cb2:
        if st.button("Confirmar →", type="primary", use_container_width=True, key="nv_next1"):
            st.session_state["nv_step"] = 2
            st.rerun()


def _step_confirmar():
    _sel_lid   = st.session_state.get("nv_linea")
    _sel_sku   = st.session_state.get("nv_sku")
    _sel_qty   = st.session_state.get("nv_qty", 1)
    _precio    = st.session_state.get("nv_precio", 0)
    _cliente   = st.session_state.get("nv_cliente", "")
    _canal_i   = st.session_state.get("nv_canal_idx", 0)
    _notas_usr = st.session_state.get("nv_notas", "")
    _canales   = ["Presencial", "WhatsApp", "Instagram", "TikTok", "Email", "Otro"]
    _canal_str = _canales[min(_canal_i, len(_canales)-1)]
    _total     = _precio * _sel_qty
    _lcfg      = get_linea(_sel_lid) if _sel_lid else {}

    with engine.connect() as conn:
        _prod = pd.read_sql(text("SELECT name FROM products WHERE sku=:sku"), conn, params={"sku": _sel_sku})
    _prod_name = _prod.iloc[0]["name"] if not _prod.empty else _sel_sku

    _c = _lcfg.get("color", _EP)
    st.markdown(
        f"<div style='background:{_SURFACE};border-radius:14px;padding:24px;border:2px solid {_c};'>"
        f"<div style='font-size:0.6rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;"
        f"color:{_c};margin-bottom:12px;'>CONFIRMAR VENTA</div>"
        f"<div style='font-size:1rem;font-weight:700;color:{_INK};'>{_sel_qty}× {_prod_name}</div>"
        f"<div style='font-size:0.8rem;color:{_MUTED};margin-top:4px;'>"
        f"{_lcfg.get('emoji','')} {_lcfg.get('nombre','')}</div>"
        + (f"<div style='font-size:0.8rem;color:{_INK};margin-top:6px;'>Cliente: {_cliente}</div>" if _cliente else "")
        + f"<div style='font-size:0.8rem;color:{_MUTED};margin-top:4px;'>Canal: {_canal_str}</div>"
        + (f"<div style='font-size:0.8rem;color:{_MUTED};margin-top:4px;'>{_notas_usr}</div>" if _notas_usr else "")
        + f"<div style='font-size:1.4rem;font-weight:800;color:{_OK};margin-top:12px;'>${_total:,.0f}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _cb1, _cb2 = st.columns(2)
    with _cb1:
        if st.button("← Editar", use_container_width=True, key="nv_back2"):
            st.session_state["nv_step"] = 1
            st.rerun()
    with _cb2:
        if st.button("✅ Registrar Venta", type="primary", use_container_width=True, key="nv_submit"):
            _notas_parts = []
            if _cliente:   _notas_parts.append(f"Cliente: {_cliente}")
            if _notas_usr.strip(): _notas_parts.append(_notas_usr.strip())
            _notas_parts.append(f"Canal: {_canal_str}")
            _notas_str = " | ".join(_notas_parts)

            try:
                with engine.begin() as conn:
                    _res = conn.execute(
                        text("""INSERT INTO orders (client_id, status, date, notas, canal_origen)
                                VALUES (:cid, 'Pendiente', :fecha, :notas, :canal)
                                RETURNING id"""),
                        {"cid": _sel_lid, "fecha": datetime.now().isoformat(),
                         "notas": _notas_str, "canal": _canal_str},
                    )
                    _oid = _res.scalar()
                    conn.execute(
                        text("INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario) VALUES (:oid, :sku, :qty, :precio)"),
                        {"oid": _oid, "sku": _sel_sku, "qty": _sel_qty, "precio": _precio},
                    )
                    try:
                        conn.execute(
                            text("INSERT INTO pagos (order_id, monto, metodo, estado) VALUES (:oid, :monto, 'transferencia', 'pendiente')"),
                            {"oid": _oid, "monto": _total},
                        )
                    except Exception:
                        pass
                    try:
                        conn.execute(
                            text("""INSERT INTO stock_movements (product_sku, tipo, cantidad, fecha, referencia)
                                    VALUES (:sku, 'pedido', :qty_neg, CURRENT_DATE, :ref)"""),
                            {"sku": _sel_sku, "qty_neg": -_sel_qty, "ref": f"order_{_oid}"},
                        )
                    except Exception:
                        pass

                st.success(
                    f"✅ Venta registrada — Pedido #{_oid}: "
                    f"{_sel_qty}× {_prod_name} · ${_total:,.0f}"
                )
                for k in ["nv_step","nv_linea","nv_sku","nv_qty","nv_precio",
                          "nv_cliente","nv_canal_idx","nv_notas"]:
                    st.session_state.pop(k, None)
                st.balloons()

            except Exception as e:
                st.error(f"Error al registrar: {e}")

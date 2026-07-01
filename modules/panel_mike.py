"""modules/panel_mike.py — Panel de inteligencia ecosistema (Mike)."""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS


@st.cache_data(ttl=300)
def _estado_ecosistema() -> dict:
    try:
        dem = pd.read_sql(
            text("""
                SELECT COUNT(*) AS n FROM orders
                WHERE status IN ('Pendiente','En Proceso')
                  AND date <= date('now','-2 days')
            """), engine
        ).iloc[0]["n"]
    except Exception:
        dem = 0
    try:
        lineas_activas = pd.read_sql(
            text("""
                SELECT DISTINCT client_id FROM orders
                WHERE date >= date('now','-7 days')
            """), engine
        )["client_id"].tolist()
        total_lineas = len([l for l in LINEAS if l not in ("admin", "fer_produccion")])
        inactivas = total_lineas - len(lineas_activas)
    except Exception:
        inactivas = 0
    try:
        mat_bajos = pd.read_sql(
            text("""
                SELECT COUNT(*) AS n FROM materials
                WHERE activo = 1 AND stock_gr <= stock_minimo_gr
            """), engine
        ).iloc[0]["n"]
    except Exception:
        mat_bajos = 0
    return {"demorados": int(dem), "lineas_inactivas": max(0, int(inactivas)), "mat_bajo_minimo": int(mat_bajos)}


@st.cache_data(ttl=300)
def _top_productos() -> pd.DataFrame:
    try:
        return pd.read_sql(
            text("""
                SELECT p.name AS producto, p.client_id AS linea_id,
                       SUM(oi.cantidad) AS unidades
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                JOIN products p ON p.sku = oi.product_sku
                WHERE o.date >= date('now','-30 days')
                  AND o.status != 'Cancelado'
                GROUP BY oi.product_sku
                ORDER BY unidades DESC
                LIMIT 5
            """), engine
        )
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _senales_mercado() -> pd.DataFrame:
    try:
        return pd.read_sql(
            text("""
                SELECT cliente_id, tipo, descripcion, fecha
                FROM senales_mercado
                WHERE fecha >= date('now','-7 days')
                ORDER BY fecha DESC
                LIMIT 30
            """), engine
        )
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _tendencia_precios() -> pd.DataFrame:
    try:
        return pd.read_sql(
            text("""
                SELECT ph.product_sku, p.name AS producto,
                       ph.precio_anterior, ph.precio_nuevo,
                       ph.fecha, ph.motivo
                FROM price_history ph
                JOIN products p ON p.sku = ph.product_sku
                ORDER BY ph.id DESC
                LIMIT 20
            """), engine
        )
    except Exception:
        return pd.DataFrame()


def render():
    from utils.mike import get_alertas_dashboard

    # ── Sección A — Estado del ecosistema ──────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin-bottom:4px;'>A · ESTADO DEL ECOSISTEMA</div>",
        unsafe_allow_html=True,
    )
    with st.expander("ℹ️ Qué analizar acá"):
        st.markdown("""
**Pedidos demorados** — Órdenes que llevan más de 48 h sin cambiar de estado (Pendiente → En Proceso → Listo).
Si este número sube, revisá si Fer tiene sobrecarga o si hay stock faltante que lo frena.
Un valor de 0 es el ideal; más de 2 simultáneos indica cuello de botella.

**Líneas inactivas** — Socios que no hicieron ningún pedido en los últimos 7 días.
Si una línea normalmente activa aparece acá, puede ser señal de una conversación pendiente o un problema no reportado.

**Materiales bajo mínimo** — Filamentos cuyo stock cayó por debajo del umbral configurado.
Cada uno en rojo es una fabricación que Fer no puede completar. Acción inmediata: hacer el pedido al proveedor.
        """)
    _estado = _estado_ecosistema()
    _a1, _a2, _a3 = st.columns(3)
    for _col, _val, _label, _sub, _warn in [
        (_a1, _estado["demorados"],       "Pedidos demorados",    "+48 h sin avanzar",     _estado["demorados"] > 0),
        (_a2, _estado["lineas_inactivas"], "Líneas inactivas",     "sin pedidos esta semana", _estado["lineas_inactivas"] > 0),
        (_a3, _estado["mat_bajo_minimo"],  "Materiales bajo mínimo", "requieren reposición", _estado["mat_bajo_minimo"] > 0),
    ]:
        _c = "#EF4444" if _warn else "#3FB950"
        with _col:
            st.markdown(
                f"<div style='background:#161B22;border-radius:14px;padding:20px 16px;"
                f"border:1px solid #21262D;border-top:3px solid {_c};text-align:center;margin-bottom:8px;'>"
                f"<div style='font-size:2.2rem;font-weight:800;color:{_c};line-height:1;'>{_val}</div>"
                f"<div style='font-size:0.75rem;font-weight:600;color:#C9D1D9;margin-top:8px;'>{_label}</div>"
                f"<div style='font-size:0.64rem;color:#6B7280;margin-top:4px;'>{_sub}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Sección B — Alertas activas ────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin:24px 0 12px;'>B · ALERTAS ACTIVAS</div>",
        unsafe_allow_html=True,
    )
    _alertas = get_alertas_dashboard()
    _cm = {"critico": "#EF4444", "atencion": "#F59E0B", "info": "#58A6FF"}
    _bm = {"critico": "#2D1117", "atencion": "#2D2007", "info": "#0D1B2E"}
    _dm = {"critico": "#451B1B", "atencion": "#3D2B0A", "info": "#1B2D4A"}
    if not _alertas:
        st.markdown(
            "<div style='background:#0D2818;border-radius:12px;padding:14px 20px;border:1px solid #238636;'>"
            "<span style='color:#3FB950;font-weight:700;'>✅ Sin alertas activas</span>"
            "<span style='color:#8B949E;margin-left:12px;font-size:0.8rem;'>El ecosistema está en orden.</span></div>",
            unsafe_allow_html=True,
        )
    else:
        for _a in _alertas:
            _c  = _cm.get(_a["nivel"], "#8B949E")
            _bg = _bm.get(_a["nivel"], "#161B22")
            _bd = _dm.get(_a["nivel"], "#21262D")
            st.markdown(
                f"<div style='background:{_bg};border-radius:12px;padding:14px 18px;"
                f"border:1px solid {_bd};border-left:4px solid {_c};margin-bottom:8px;'>"
                f"<div style='font-size:0.88rem;font-weight:700;color:{_c};'>{_a['titulo']}</div>"
                f"<div style='font-size:0.75rem;color:#8B949E;margin-top:4px;'>{_a['detalle']}</div>"
                f"<div style='font-size:0.7rem;color:#6B7280;margin-top:3px;'>→ {_a['accion']}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Sección C — Top 5 productos ────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin:24px 0 4px;'>C · TOP 5 PRODUCTOS (últimos 30 días · unidades)</div>",
        unsafe_allow_html=True,
    )
    with st.expander("ℹ️ Qué analizar acá"):
        st.markdown("""
**Qué muestra** — Los 5 productos más pedidos en los últimos 30 días, ordenados por unidades.
No incluye precios para mantener privacidad de márgenes.

**Cómo usarlo:**
- La barra de progreso es proporcional al producto #1 — si el segundo está casi igual, la demanda está distribuida (saludable).
- Si el top 1 aplasta al resto con el triple, es un producto estrella: conviene asegurarse de que nunca falte su material.
- Un producto que estaba en top 3 y desapareció puede indicar que el socio lo dejó de ofrecer o que hay un problema de stock.
- Usá este ranking para priorizar qué fabricaciones Fer debe tener listas ante un pico de demanda.
        """)

    _top = _top_productos()
    if _top.empty:
        st.caption("Sin ventas registradas en los últimos 30 días.")
    else:
        _max_u = int(_top["unidades"].max()) or 1
        for _, _r in _top.iterrows():
            _linea_nom = LINEAS.get(_r["linea_id"], {}).get("nombre", _r["linea_id"])
            _linea_color = LINEAS.get(_r["linea_id"], {}).get("color", "#8B949E")
            _pct = min(100, int(_r["unidades"]) / _max_u * 100)
            st.markdown(
                f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;"
                f"margin-bottom:6px;border:1px solid #21262D;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>"
                f"<span style='font-size:0.82rem;font-weight:700;color:#E6EDF3;'>{_r['producto']}</span>"
                f"<span style='font-size:0.75rem;font-weight:700;color:{_linea_color};'>{int(_r['unidades'])} u</span></div>"
                f"<div style='font-size:0.65rem;color:#6B7280;margin-bottom:4px;'>{_linea_nom}</div>"
                f"<div style='background:#21262D;border-radius:4px;height:5px;'>"
                f"<div style='background:{_linea_color};height:5px;border-radius:4px;width:{_pct:.0f}%;'></div></div></div>",
                unsafe_allow_html=True,
            )

    # ── Sección D — Señales de mercado ─────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin:24px 0 4px;'>D · SEÑALES DE MERCADO (últimos 7 días)</div>",
        unsafe_allow_html=True,
    )
    with st.expander("ℹ️ Qué analizar acá"):
        st.markdown("""
Las señales son observaciones registradas manualmente o por el agente sobre el entorno externo.
Cada una tiene un tipo que indica qué clase de información es:

| Tipo | Qué significa | Acción típica |
|------|---------------|---------------|
| 🟢 **demanda** | Interés o pedido fuera de catálogo, spike en consultas | Evaluar si conviene agregar el producto |
| 🟡 **competencia** | Cambio de precios o nuevo jugador en el mercado | Revisar si los precios del taller siguen siendo competitivos |
| 🔵 **tendencia** | Tendencia de diseño o material que se empieza a ver | Anticipar qué SKUs podrían demandar los socios |
| 🔴 **riesgo** | Faltante de insumo, problema de proveedor, queja | Actuar antes de que escale |

**Cómo usarlo:** Filtrá por tipo "riesgo" primero — esos son los que necesitan acción. Luego revisá "demanda" para detectar oportunidades de agregar productos al catálogo.
        """)

    _senales = _senales_mercado()
    if _senales.empty:
        st.caption("Sin señales registradas esta semana.")
    else:
        _tipos = ["Todos"] + sorted(_senales["tipo"].dropna().unique().tolist())
        _filtro = st.selectbox("Filtrar por tipo", _tipos, key="mike_filtro_senal")
        _df_s = _senales if _filtro == "Todos" else _senales[_senales["tipo"] == _filtro]
        _tipo_colors = {"demanda": "#22C55E", "competencia": "#F59E0B", "tendencia": "#58A6FF", "riesgo": "#EF4444"}
        for _, _s in _df_s.iterrows():
            _tc = _tipo_colors.get(str(_s.get("tipo", "")).lower(), "#8B949E")
            _linea_nom = LINEAS.get(str(_s.get("cliente_id", "")), {}).get("nombre", str(_s.get("cliente_id", "—")))
            st.markdown(
                f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;"
                f"margin-bottom:6px;border:1px solid #21262D;border-left:3px solid {_tc};'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span style='font-size:0.7rem;font-weight:700;color:{_tc};text-transform:uppercase;'>{_s.get('tipo','')}</span>"
                f"<span style='font-size:0.65rem;color:#6B7280;'>{str(_s.get('fecha',''))[:10]}</span></div>"
                f"<div style='font-size:0.82rem;color:#C9D1D9;margin-top:4px;'>{_s.get('descripcion','')}</div>"
                f"<div style='font-size:0.65rem;color:#6B7280;margin-top:3px;'>{_linea_nom}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Sección E.5 — Stock movements recientes ───────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin:24px 0 4px;'>E.5 · MOVIMIENTOS DE STOCK (últimos 20)</div>",
        unsafe_allow_html=True,
    )
    try:
        _mov = pd.read_sql(
            text("""
                SELECT sm.fecha, sm.product_sku, p.name AS producto,
                       sm.tipo, sm.cantidad, sm.referencia
                FROM stock_movements sm
                LEFT JOIN products p ON p.sku = sm.product_sku
                ORDER BY sm.id DESC LIMIT 20
            """), engine
        )
        if _mov.empty:
            st.caption("Sin movimientos de stock registrados todavía.")
        else:
            _tipo_c = {"produccion": "#3FB950", "pedido": "#F59E0B", "ajuste_manual": "#58A6FF"}
            for _, _m in _mov.iterrows():
                _tc = _tipo_c.get(str(_m.get("tipo", "")), "#8B949E")
                _qty_disp = f"+{_m['cantidad']}" if int(_m.get('cantidad', 0)) > 0 else str(int(_m.get('cantidad', 0)))
                st.markdown(
                    f"<div style='background:#161B22;border-radius:10px;padding:10px 14px;"
                    f"margin-bottom:5px;border:1px solid #21262D;border-left:3px solid {_tc};'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='font-size:0.8rem;font-weight:700;color:#E6EDF3;'>{_m.get('producto') or _m['product_sku']}</span>"
                    f"<span style='font-size:0.88rem;font-weight:700;color:{_tc};'>{_qty_disp}</span></div>"
                    f"<div style='font-size:0.65rem;color:#6B7280;margin-top:3px;'>"
                    f"{str(_m.get('fecha',''))[:10]} · {_m.get('tipo','')} · ref: {_m.get('referencia','')}</div></div>",
                    unsafe_allow_html=True,
                )
    except Exception as _e:
        st.caption(f"Sin datos: {_e}")

    # ── Sección E — Tendencia de precios ───────────────────────
    st.markdown(
        "<div style='font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;"
        "color:#58A6FF;margin:24px 0 4px;'>E · HISTORIAL DE PRECIOS</div>",
        unsafe_allow_html=True,
    )
    with st.expander("ℹ️ Qué analizar acá"):
        st.markdown("""
**Qué muestra** — Cada vez que Alejandra modifica el precio de un producto, queda registrado acá con el valor anterior, el nuevo, la fecha y el motivo.

**Para qué sirve:**
- **Detectar tendencia inflacionaria:** si hay muchos aumentos en el mismo período, puede indicar que el costo de materiales subió y hay que revisar los márgenes del resto del catálogo.
- **Auditoría de decisiones:** antes de hablar con un socio sobre precios, podés ver el historial completo de ese producto y justificar con datos.
- **Consistencia entre líneas:** si una línea tiene precios muy distintos a otra para el mismo tipo de producto, puede ser una oportunidad de revisión.
- **El motivo del cambio** (columna visible en el registro) es clave — "ajuste costo filamento" vs "promo temporal" tiene implicancias distintas.
        """)

    _precios = _tendencia_precios()
    if _precios.empty:
        st.markdown(
            "<div style='background:#161B22;border-radius:12px;padding:16px 20px;border:1px solid #21262D;'>"
            "<span style='color:#8B949E;font-size:0.82rem;'>Sin cambios de precios registrados.</span></div>",
            unsafe_allow_html=True,
        )
    else:
        for _, _ph in _precios.iterrows():
            _delta = float(_ph["precio_nuevo"] or 0) - float(_ph["precio_anterior"] or 0)
            _dc = "#22C55E" if _delta >= 0 else "#EF4444"
            _darrow = "▲" if _delta >= 0 else "▼"
            st.markdown(
                f"<div style='background:#161B22;border-radius:10px;padding:12px 16px;"
                f"margin-bottom:6px;border:1px solid #21262D;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<div><span style='font-size:0.82rem;font-weight:700;color:#E6EDF3;'>{_ph['producto']}</span>"
                f"<span style='font-size:0.65rem;color:#6B7280;margin-left:8px;'>{str(_ph.get('fecha',''))[:10]}</span></div>"
                f"<span style='font-size:0.88rem;font-weight:700;color:{_dc};'>{_darrow} ${abs(_delta):,.0f}</span></div>"
                f"<div style='font-size:0.72rem;color:#8B949E;margin-top:4px;'>"
                f"${float(_ph['precio_anterior'] or 0):,.0f} → ${float(_ph['precio_nuevo'] or 0):,.0f}"
                f"{(' · ' + str(_ph['motivo'])) if _ph.get('motivo') else ''}</div></div>",
                unsafe_allow_html=True,
            )

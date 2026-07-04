"""modules/publicar.py — Publicar en RRSS + sincronización catálogo web."""
import streamlit as st
from utils.lineas import LINEAS, PAGINAS_SOCIOS, _BASE_PAGES

# ── Config por línea: handle, hashtags, tono ──────────────────────────────────
_RRSS = {
    "admin": {
        "ig": "@magnitud19.studio", "tt": "@magnitud19",
        "hx_ig": "#magnitud19 #arquitectura #impresion3d #buenosaires #diseño3d #B2B #elpasaje3d",
        "hx_tt": "#magnitud19 #impresion3d #diseño #arquitectura",
        "cta": "Consultanos por DM o WhatsApp para proyectos B2B",
    },
    "fer_produccion": {
        "ig": "@melomano.3d", "tt": "@melomano3d",
        "hx_ig": "#melomano #musica #impresion3d #accesoriosmusica #guitarrista #buenosaires #elpasaje3d",
        "hx_tt": "#musica #impresion3d #guitarra #viral",
        "cta": "Para pedidos o consultas, escribinos",
    },
    "oasis_animal": {
        "ig": "@oasisanimal.3d", "tt": "@oasisanimal3d",
        "hx_ig": "#oasisanimal #mascotas #perros #gatos #impresion3d #accesoriosmascotas #buenosaires #elpasaje3d",
        "hx_tt": "#mascota #perro #gato #impresion3d #viral #fyp",
        "cta": "Pedidos por DM o WhatsApp. Envíos a todo el país",
    },
    "oasis_del_estero": {
        "ig": "@oasisestero.3d", "tt": "@oasisestero3d",
        "hx_ig": "#oasisdelestero #naturaleza #impresion3d #ecodesign #sustentable #buenosaires #elpasaje3d",
        "hx_tt": "#naturaleza #impresion3d #sustentable #viral",
        "cta": "Consultanos por DM o WhatsApp",
    },
    "olivia_coquette": {
        "ig": "@coquette.3d", "tt": "@coquette3d",
        "hx_ig": "#coquette #aesthetic #impresion3d #accesorios #moda3d #girlyboss #buenosaires #elpasaje3d",
        "hx_tt": "#coquette #aesthetic #viral #fyp #accesorios #trending",
        "cta": "DM o WhatsApp para pedir el tuyo ✨",
    },
    "francisco_sport": {
        "ig": "@fzone.sport", "tt": "@fzone3d",
        "hx_ig": "#fzone #sport #impresion3d #gaming #accesoriosdeportivos #buenosaires #elpasaje3d",
        "hx_tt": "#sport #gaming #impresion3d #viral #fyp",
        "cta": "Escribinos para pedir el tuyo",
    },
    "constantino_tech": {
        "ig": "@coretech.3d", "tt": "@coretech3d",
        "hx_ig": "#coretech #tecnologia #impresion3d #maker #electronica #buenosaires #elpasaje3d",
        "hx_tt": "#tech #impresion3d #maker #viral #fyp",
        "cta": "Consultas técnicas por DM o WhatsApp",
    },
    "pharma_delux": {
        "ig": "@pharmadelux.3d", "tt": "@pharmadelux3d",
        "hx_ig": "#pharmadelux #salud #impresion3d #equipamiento #buenosaires #elpasaje3d",
        "hx_tt": "#salud #impresion3d #innovacion #viral",
        "cta": "Consultas por DM o WhatsApp",
    },
    "aviation": {
        "ig": "@aerotech.3d", "tt": "@aerotech3d",
        "hx_ig": "#aerotech #aviacion #impresion3d #drones #modelismo #buenosaires #elpasaje3d",
        "hx_tt": "#drone #aviacion #impresion3d #viral",
        "cta": "Pedidos y consultas por DM o WhatsApp",
    },
}
_RRSS_DEFAULT = {
    "ig": "@elpasaje3dstudio", "tt": "@elpasaje3d",
    "hx_ig": "#impresion3d #buenosaires #elpasaje3d #3dprint",
    "hx_tt": "#impresion3d #3dprint #viral #fyp",
    "cta": "Escribinos por DM o WhatsApp",
}


def _cfg(uid: str) -> dict:
    return _RRSS.get(uid, _RRSS_DEFAULT)


def _caption_instagram(nombre, precio, stock, descripcion, cfg, emoji) -> str:
    desc_bloque = f"\n{descripcion[:120]}{'...' if len(descripcion) > 120 else ''}\n" if descripcion.strip() else ""
    stock_txt = f"{stock} disponibles" if stock > 0 else "¡Últimas unidades!"
    return (
        f"{emoji} {nombre}\n"
        f"{desc_bloque}\n"
        f"💰 ${precio:,.0f}\n"
        f"📦 {stock_txt} · Envíos a todo el país\n\n"
        f"{cfg['cta']}\n\n"
        f"{cfg['ig']}\n\n"
        f"{cfg['hx_ig']}"
    )


def _caption_tiktok(nombre, precio, stock, cfg, emoji) -> str:
    stock_txt = f"{stock} disponibles" if stock > 0 else "¡Quedan pocos!"
    return (
        f"{emoji} {nombre} de impresión 3D 🔥\n\n"
        f"✅ ${precio:,.0f}\n"
        f"✅ {stock_txt}\n"
        f"✅ Envíos a todo el país\n\n"
        f"Escribinos por mensaje 👇\n"
        f"{cfg['ig']}\n\n"
        f"{cfg['hx_tt']}"
    )


def _caption_story(nombre, precio, cfg, emoji) -> str:
    return (
        f"{emoji} {nombre}\n"
        f"${precio:,.0f} · Envíos incluidos\n"
        f"Deslizá para pedir 👆\n"
        f"{cfg['ig']}"
    )


def render(uid: str, lineas_activas: list, prod, hdr_color: str, hdr_nombre: str, hdr_emoji: str):
    """Tab principal de publicación RRSS + sync catálogo web."""
    cfg = _cfg(uid)

    st.markdown(
        f"<div style='font-size:0.62rem;font-weight:700;letter-spacing:3px;color:{hdr_color};"
        f"text-transform:uppercase;margin-bottom:16px;'>📲 PUBLICAR EN REDES SOCIALES</div>",
        unsafe_allow_html=True,
    )

    if prod.empty:
        st.info("Primero cargá productos en tu línea para poder publicarlos.")
        return

    # ── Selector de producto ──────────────────────────────────────────────────
    prod_activos = prod[prod.get("activo", 1) == 1].copy() if "activo" in prod.columns else prod.copy()
    prod_activos["_label"] = prod_activos.apply(
        lambda r: f"{r['name']} — ${float(r.get('price', 0) or 0):,.0f}", axis=1
    )

    _sel_lbl = st.selectbox(
        "Elegí el producto a publicar",
        options=prod_activos["_label"].tolist(),
        key=f"pub_sel_{uid}",
        label_visibility="visible",
    )

    _row = prod_activos[prod_activos["_label"] == _sel_lbl].iloc[0]
    _nombre   = str(_row["name"])
    _precio   = float(_row.get("precio_reventa", 0) or _row.get("price", 0) or 0)
    if _precio == 0:
        _precio = float(_row.get("price", 0) or 0)
    _stock    = int(_row.get("stock", 0) or 0)
    _desc     = str(_row.get("description", "") or "").strip()
    _sku      = str(_row.get("sku", ""))
    _emoji    = LINEAS.get(_row.get("client_id", uid), {}).get("emoji", hdr_emoji)
    _linea_id = str(_row.get("client_id", uid))

    # ── Preview + captions ───────────────────────────────────────────────────
    _col_prev, _col_cap = st.columns([1, 2])

    with _col_prev:
        _img_url = str(_row.get("imagen_url", "") or "").strip()
        if _img_url.startswith("http"):
            st.image(_img_url, use_container_width=True)
        else:
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{hdr_color}33,{hdr_color}11);"
                f"border-radius:16px;padding:40px 20px;text-align:center;"
                f"border:2px dashed {hdr_color}55;margin-bottom:8px;'>"
                f"<div style='font-size:2.5rem;'>{_emoji}</div>"
                f"<div style='font-size:0.75rem;font-weight:700;color:{hdr_color};margin-top:8px;'>"
                f"Sin foto todavía</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='text-align:center;padding:8px;'>"
            f"<div style='font-size:1rem;font-weight:800;'>{_nombre}</div>"
            f"<div style='font-size:1.3rem;font-weight:900;color:{hdr_color};'>${_precio:,.0f}</div>"
            f"<div style='font-size:0.7rem;color:#74798A;'>Stock: {_stock} u · SKU: {_sku}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Link WA directo ───────────────────────────────────────────────
        from urllib.parse import quote
        _wa_num = ""
        try:
            from utils.db import engine as _eng
            from sqlalchemy import text as _text
            with _eng.connect() as _wc:
                _wc_row = _wc.execute(
                    _text("SELECT whatsapp_numero FROM lineas_config WHERE client_id=:cid"),
                    {"cid": _linea_id},
                ).fetchone()
            if _wc_row and _wc_row[0]:
                _wa_num = str(_wc_row[0]).strip().replace("+", "").replace(" ", "")
        except Exception:
            pass

        if _wa_num:
            _wa_msg = f"Hola! Quiero pedir {_nombre} (SKU: {_sku}) — ${_precio:,.0f}"
            _wa_url = f"https://wa.me/{_wa_num}?text={quote(_wa_msg)}"
            st.link_button("💬 Link WhatsApp directo", url=_wa_url, use_container_width=True)
        else:
            _wa_msg = f"Hola! Me interesa {_nombre} (SKU: {_sku}) — ${_precio:,.0f}"
            _wa_url = f"https://wa.me/?text={quote(_wa_msg)}"
            st.link_button("💬 Link WhatsApp (sin número)", url=_wa_url, use_container_width=True)

        # ── Página web pública ────────────────────────────────────────────
        _slug = PAGINAS_SOCIOS.get(_linea_id)
        if _slug:
            st.link_button("🌐 Ver página web", url=f"{_BASE_PAGES}/{_slug}.html", use_container_width=True)

    with _col_cap:
        _ig_cap  = _caption_instagram(_nombre, _precio, _stock, _desc, cfg, _emoji)
        _tt_cap  = _caption_tiktok(_nombre, _precio, _stock, cfg, _emoji)
        _st_cap  = _caption_story(_nombre, _precio, cfg, _emoji)

        _tab_ig, _tab_tt, _tab_story = st.tabs(["📸 Instagram", "🎵 TikTok", "📱 Story"])

        with _tab_ig:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:1px;"
                "color:#E1306C;text-transform:uppercase;margin-bottom:6px;'>"
                "Caption listo para copiar</div>",
                unsafe_allow_html=True,
            )
            st.code(_ig_cap, language=None)
            st.caption(f"Handle: {cfg['ig']} · {len(_ig_cap)} chars")

        with _tab_tt:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:1px;"
                "color:#00F2EA;text-transform:uppercase;margin-bottom:6px;'>"
                "Caption para TikTok / Reels</div>",
                unsafe_allow_html=True,
            )
            st.code(_tt_cap, language=None)
            st.caption(f"Handle: {cfg['tt']} · Formato corto, más viralizador")

        with _tab_story:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;letter-spacing:1px;"
                "color:#F59E0B;text-transform:uppercase;margin-bottom:6px;'>"
                "Texto para story / sticker</div>",
                unsafe_allow_html=True,
            )
            st.code(_st_cap, language=None)
            st.caption("Texto corto ideal para sticker de swipe-up o story de feed")

    # ── Tip del día ──────────────────────────────────────────────────────────
    import datetime
    _tips = [
        "Los mejores horarios para postear en Instagram son martes y miércoles entre 11h–13h y 19h–21h (hora Argentina).",
        "En TikTok, los videos entre 15 y 30 segundos con música trending tienen 2× más views.",
        "Las stories con stickers de pregunta o encuesta tienen 3× más interacción que las estáticas.",
        "El primer comentario de tu publicación importa: responder rápido aumenta el alcance orgánico.",
        "En Reels, mostrar el proceso de fabricación genera más saves y shares que solo el producto final.",
        "Usá el link de WhatsApp directo en la bio de Instagram — convierte mejor que cualquier otro CTA.",
        "Subir 3 stories seguidas en el mismo día aumenta la visibilidad frente al algoritmo de Instagram.",
        "Los hashtags de nicho (menos de 500k posts) tienen mejor alcance que los genéricos.",
    ]
    _tip = _tips[datetime.date.today().toordinal() % len(_tips)]
    st.markdown(
        f"<div style='background:#EBE6DC;border-radius:12px;padding:12px 16px;"
        f"border-left:3px solid {hdr_color};margin-top:16px;'>"
        f"<div style='font-size:0.6rem;font-weight:700;color:{hdr_color};"
        f"text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>💡 Tip del día</div>"
        f"<div style='font-size:0.78rem;color:#3A3E4A;'>{_tip}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Sync catálogo web ─────────────────────────────────────────────────────
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.62rem;font-weight:700;letter-spacing:3px;color:#74798A;"
        "text-transform:uppercase;margin-bottom:10px;'>🌐 CATÁLOGO WEB</div>",
        unsafe_allow_html=True,
    )

    _slugs_disponibles = [(lid, PAGINAS_SOCIOS.get(lid)) for lid in lineas_activas if PAGINAS_SOCIOS.get(lid)]
    if not _slugs_disponibles:
        st.caption("Tu línea no tiene página web configurada todavía.")
        return

    _sa, _sb = st.columns([2, 1])
    with _sa:
        st.markdown(
            "<div style='font-size:0.78rem;color:#3A3E4A;'>"
            "Actualizá el catálogo web con tus precios y productos actuales. "
            "Después de exportar, el catálogo queda listo en la carpeta <code>exports/</code>.</div>",
            unsafe_allow_html=True,
        )
    with _sb:
        if st.button("🔄 Exportar catálogo web ahora", use_container_width=True, type="primary"):
            try:
                from utils.exports import exportar_catalogo_json
                _exported = []
                for _lid, _slg in _slugs_disponibles:
                    _, _path = exportar_catalogo_json(_lid)
                    _exported.append(f"✅ {_slg}-catalog.json")
                st.success("\n".join(_exported))
            except Exception as _e:
                st.error(f"Error al exportar: {_e}")

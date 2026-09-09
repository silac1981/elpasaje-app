"""
setup_redes.py — Agrega Open Graph + bloque de redes sociales a todos los catálogos.
Handles sugeridos (cambiar cuando se activen las cuentas reales).
"""
import re
import sys
from pathlib import Path

if "--confirmar" not in sys.argv:
    print("Script de setup. Ejecutar con --confirmar para aplicar.")
    sys.exit(0)

BASE_URL = "https://silac1981.github.io/elpasaje-app"
WA       = "5491165497234"

# ── Datos por página ────────────────────────────────────────────────────────
PAGES = {
    "index.html": {
        "title":   "El Pasaje 3D Studio · Taller de impresión 3D en Buenos Aires",
        "desc":    "Ecosistema de líneas de diseño impresas en 3D. Buenos Aires, Argentina. Manufactura aditiva familiar.",
        "image":   f"{BASE_URL}/static/img/elpasaje_og.jpg",
        "accent":  "#C9A84C",
        "ig":      "elpasaje3dstudio",
        "tiktok":  "elpasaje3d",
        "linkeod": None,
    },
    "sport.html": {
        "title":   "F-Zone · Cajitas Porta-Figuritas Mundial 2026 · El Pasaje",
        "desc":    "Cajitas 3D impresas en Buenos Aires. AFA · FIFA 26 · Argentina. Stock limitado. Por Francisco.",
        "image":   f"{BASE_URL}/static/productos/sport/cajita_afa_negro.jpg",
        "accent":  "#00F3FF",
        "ig":      "fzone.sport",
        "tiktok":  "fzone3d",
        "linkedin": None,
    },
    "coquette.html": {
        "title":   "Coquette · Accesorios y Moda 3D · El Pasaje",
        "desc":    "Moños, llaveros, monederos y accesorios de moda impresos en 3D. Por Olivia.",
        "image":   f"{BASE_URL}/static/img/coquette_og.jpg",
        "accent":  "#F9A8D4",
        "ig":      "coquette.3d",
        "tiktok":  "coquette3d",
        "linkedin": None,
    },
    "core-tech.html": {
        "title":   "Core Tech · Ingeniería y Piezas Técnicas 3D · El Pasaje",
        "desc":    "Piezas técnicas e industriales impresas en 3D. Por Constantino.",
        "image":   f"{BASE_URL}/static/img/coretech_og.jpg",
        "accent":  "#64748B",
        "ig":      "coretech.3d",
        "tiktok":  "coretech3d",
        "linkedin": None,
    },
    "magnitud19.html": {
        "title":   "Magnitud 19 · Studio Premium 3D · El Pasaje",
        "desc":    "Organización de escritorio y accesorios premium impresos en 3D. Por Alejandra.",
        "image":   f"{BASE_URL}/static/img/magnitud19_og.jpg",
        "accent":  "#B87333",
        "ig":      "magnitud19.studio",
        "tiktok":  None,
        "linkedin": None,
    },
    "aero-tech.html": {
        "title":   "Aero Tech · Accesorios Aeronáuticos 3D · El Pasaje",
        "desc":    "Accesorios para tripulantes y personal de aviación. Por Nando · Aerolíneas Argentinas.",
        "image":   f"{BASE_URL}/static/img/aerotech_og.jpg",
        "accent":  "#4455ff",
        "ig":      "aerotech.3d",
        "tiktok":  None,
        "linkedin": "aero-tech-3d",
    },
    "oasis-animal.html": {
        "title":   "Oasis Animal · Accesorios para Mascotas 3D · El Pasaje",
        "desc":    "Accesorios para mascotas impresos en 3D. El 10% va al refugio solidario.",
        "image":   f"{BASE_URL}/static/img/oasisanimal_og.jpg",
        "accent":  "#F472B6",
        "ig":      "oasisanimal.3d",
        "tiktok":  "oasisanimal3d",
        "linkedin": None,
    },
    "oasis-estero.html": {
        "title":   "Oasis del Estero · Plantas y Jardín 3D · El Pasaje",
        "desc":    "Macetas, kits de hidroponía y accesorios de jardín impresos en 3D.",
        "image":   f"{BASE_URL}/static/img/oasisestero_og.jpg",
        "accent":  "#34D399",
        "ig":      "oasisestero.3d",
        "tiktok":  None,
        "linkedin": None,
    },
    "pharma-delux.html": {
        "title":   "Pharma DeLux · Organizadores Farmacéuticos 3D · El Pasaje",
        "desc":    "Organizadores y accesorios para el sector farmacéutico impresos en 3D.",
        "image":   f"{BASE_URL}/static/img/pharmadelux_og.jpg",
        "accent":  "#FBBF24",
        "ig":      "pharmadelux.3d",
        "tiktok":  None,
        "linkedin": "pharma-delux-3d",
    },
    "melomano.html": {
        "title":   "Melómano · Accesorios Musicales 3D · El Pasaje",
        "desc":    "Accesorios para músicos y melómanos impresos en 3D. Por Fer.",
        "image":   f"{BASE_URL}/static/img/melomano_og.jpg",
        "accent":  "#9C6B3C",
        "ig":      "melomano.3d",
        "tiktok":  "melomano3d",
        "linkedin": None,
    },
    "luminis.html": {
        "title":   "Luminis · Iluminación y Diseño 3D · El Pasaje",
        "desc":    "Lámparas y accesorios de iluminación impresos en 3D. Buenos Aires.",
        "image":   f"{BASE_URL}/static/img/luminis_og.jpg",
        "accent":  "#F59E0B",
        "ig":      "luminis.3d",
        "tiktok":  None,
        "linkedin": None,
    },
    "vuelo-certero.html": {
        "title":   "Vuelo Certero · Equipamiento de Precisión 3D · El Pasaje",
        "desc":    "Accesorios para tiro y equipamiento de precisión impresos en 3D.",
        "image":   f"{BASE_URL}/static/img/vuelocertero_og.jpg",
        "accent":  "#6B7280",
        "ig":      "vuelocertero.3d",
        "tiktok":  None,
        "linkedin": None,
    },
}

# ── SVG icons ───────────────────────────────────────────────────────────────
SVG_IG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>'
SVG_TK = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.78 1.52V6.76a4.85 4.85 0 01-1.01-.07z"/></svg>'
SVG_LI = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
SVG_WA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'

# ── OG block ────────────────────────────────────────────────────────────────
def og_block(slug, d):
    url = f"{BASE_URL}/{slug}"
    return f"""
<!-- Open Graph / WhatsApp / redes sociales -->
<meta property="og:type"         content="website">
<meta property="og:url"          content="{url}">
<meta property="og:title"        content="{d['title']}">
<meta property="og:description"  content="{d['desc']}">
<meta property="og:image"        content="{d['image']}">
<meta property="og:image:width"  content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale"       content="es_AR">
<meta name="twitter:card"        content="summary_large_image">
<meta name="description"         content="{d['desc']}">"""

# ── Social footer block ──────────────────────────────────────────────────────
def social_block(d):
    accent = d["accent"]
    links = []

    if d.get("ig"):
        links.append(
            f'<a href="https://instagram.com/{d["ig"]}" target="_blank" rel="noopener" title="Instagram @{d["ig"]}" '
            f'style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;'
            f'border:1px solid rgba(255,255,255,0.12);color:rgba(255,255,255,0.45);text-decoration:none;transition:all .3s" '
            f'onmouseover="this.style.borderColor=\'{accent}\';this.style.color=\'{accent}\'" '
            f'onmouseout="this.style.borderColor=\'rgba(255,255,255,0.12)\';this.style.color=\'rgba(255,255,255,0.45)\'">'
            f'<span style="width:16px;height:16px;display:flex">{SVG_IG}</span></a>'
        )

    if d.get("tiktok"):
        links.append(
            f'<a href="https://tiktok.com/@{d["tiktok"]}" target="_blank" rel="noopener" title="TikTok @{d["tiktok"]}" '
            f'style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;'
            f'border:1px solid rgba(255,255,255,0.12);color:rgba(255,255,255,0.45);text-decoration:none;transition:all .3s" '
            f'onmouseover="this.style.borderColor=\'{accent}\';this.style.color=\'{accent}\'" '
            f'onmouseout="this.style.borderColor=\'rgba(255,255,255,0.12)\';this.style.color=\'rgba(255,255,255,0.45)\'">'
            f'<span style="width:16px;height:16px;display:flex">{SVG_TK}</span></a>'
        )

    if d.get("linkedin"):
        links.append(
            f'<a href="https://linkedin.com/company/{d["linkedin"]}" target="_blank" rel="noopener" title="LinkedIn" '
            f'style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;'
            f'border:1px solid rgba(255,255,255,0.12);color:rgba(255,255,255,0.45);text-decoration:none;transition:all .3s" '
            f'onmouseover="this.style.borderColor=\'{accent}\';this.style.color=\'{accent}\'" '
            f'onmouseout="this.style.borderColor=\'rgba(255,255,255,0.12)\';this.style.color=\'rgba(255,255,255,0.45)\'">'
            f'<span style="width:16px;height:16px;display:flex">{SVG_LI}</span></a>'
        )

    links.append(
        f'<a href="https://wa.me/{WA}" target="_blank" rel="noopener" title="WhatsApp" '
        f'style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;'
        f'border:1px solid rgba(37,211,102,0.25);color:rgba(37,211,102,0.5);text-decoration:none;transition:all .3s" '
        f'onmouseover="this.style.borderColor=\'#25D366\';this.style.color=\'#25D366\'" '
        f'onmouseout="this.style.borderColor=\'rgba(37,211,102,0.25)\';this.style.color=\'rgba(37,211,102,0.5)\'">'
        f'<span style="width:16px;height:16px;display:flex">{SVG_WA}</span></a>'
    )

    icons_html = "\n    ".join(links)
    return f"""
<!-- Redes sociales — generado por setup_redes.py -->
<div style="display:flex;justify-content:center;align-items:center;gap:10px;padding-top:14px;margin-top:12px;border-top:1px solid rgba(255,255,255,0.05)">
  <span style="font-size:.5rem;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.2);font-family:sans-serif;margin-right:6px">Seguinos</span>
  {icons_html}
</div>"""

# ── Procesador ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
MARKER = "<!-- Redes sociales — generado por setup_redes.py -->"

updated = []
skipped = []
errors  = []

for slug, data in PAGES.items():
    path = ROOT / slug
    if not path.exists():
        errors.append(f"NO EXISTE: {slug}")
        continue

    html = path.read_text(encoding="utf-8")

    # 1. Open Graph — solo agregar si no existe ya
    if 'property="og:title"' in html:
        og_added = False
    else:
        og = og_block(slug, data)
        # Insertar después del primer </title>
        html = html.replace("</title>", f"</title>{og}", 1)
        og_added = True

    # 2. Redes sociales en footer — solo si no está ya
    if MARKER in html:
        social_added = False
    else:
        block = social_block(data)
        # Insertar antes del primer </footer>
        if "</footer>" in html:
            html = html.replace("</footer>", f"{block}\n</footer>", 1)
            social_added = True
        else:
            social_added = False
            errors.append(f"Sin </footer>: {slug}")

    if og_added or social_added:
        path.write_text(html, encoding="utf-8")
        updated.append(f"{'OG+social' if og_added and social_added else 'OG' if og_added else 'social'}: {slug}")
    else:
        skipped.append(slug)

# ── Reporte ──────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  setup_redes.py — {len(PAGES)} páginas procesadas")
print(f"{'='*55}")
if updated:
    print(f"\n✅ Actualizadas ({len(updated)}):")
    for u in updated: print(f"   {u}")
if skipped:
    print(f"\n⏭  Sin cambios ({len(skipped)}):")
    for s in skipped: print(f"   {s}")
if errors:
    print(f"\n❌ Errores ({len(errors)}):")
    for e in errors: print(f"   {e}")
print()

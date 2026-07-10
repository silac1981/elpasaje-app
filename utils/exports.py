"""utils/exports.py — Genera JSON de catálogo web por línea (Capa 1 + Capa 2)."""
import os
import json
import base64
import urllib.request
import urllib.error
import pandas as pd
from sqlalchemy import text
from utils.db import engine
from utils.lineas import LINEAS, PAGINAS_SOCIOS

_GH_OWNER = "silac1981"
_GH_REPO  = "elpasaje-app"

_BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXPORTS_DIR = os.path.join(_BASE_DIR, "exports")

# linea_id → slug de la página web
_SLUG_MAP = {lid: slug for lid, slug in PAGINAS_SOCIOS.items() if slug}


def exportar_catalogo_json(linea_id: str) -> tuple:
    """Genera y guarda exports/{slug}-catalog.json para la línea dada.

    Retorna (catalog_dict, ruta_absoluta).
    Solo incluye productos Capa 2 con visibilidad='publico'.
    """
    slug = _SLUG_MAP.get(linea_id)
    if not slug:
        raise ValueError(f"La línea '{linea_id}' no tiene página web configurada.")

    os.makedirs(_EXPORTS_DIR, exist_ok=True)
    cfg = LINEAS.get(linea_id, {"nombre": linea_id, "color": "#6B7280", "emoji": "📦"})

    with engine.connect() as conn:
        # Capa 1 — productos 3D activos
        df_3d = pd.read_sql(
            text("""
                SELECT sku, name, price,
                       weight_gr AS peso_gr, stock, categoria,
                       COALESCE(description, '') AS description
                FROM products
                WHERE client_id = :cid
                  AND tipo_producto = 'propio_3d'
                  AND activo = 1
                ORDER BY name
            """),
            conn, params={"cid": linea_id},
        )

        # Capa 2 — productos de línea / compartidos / kits (solo públicos)
        df_c2 = pd.read_sql(
            text("""
                SELECT sku, name, price, stock, tipo_producto, categoria,
                       COALESCE(description, '') AS description
                FROM products
                WHERE client_id = :cid
                  AND tipo_producto != 'propio_3d'
                  AND visibilidad = 'publico'
                  AND activo = 1
                ORDER BY tipo_producto, name
            """),
            conn, params={"cid": linea_id},
        )

        # Componentes de todos los kits de la línea (join directo, sin f-string)
        df_kc = pd.read_sql(
            text("""
                SELECT kc.kit_sku, kc.component_sku, kc.cantidad,
                       p.name  AS comp_name,
                       p.price AS comp_price
                FROM kit_components kc
                JOIN  products kit ON kit.sku = kc.kit_sku
                LEFT JOIN products p   ON p.sku   = kc.component_sku
                WHERE kit.client_id     = :cid
                  AND kit.tipo_producto = 'kit_mixto'
                ORDER BY kc.kit_sku, kc.orden
            """),
            conn, params={"cid": linea_id},
        )

    def _clean(row, cols):
        out = {}
        for c in cols:
            v = row.get(c)
            out[c] = None if (v is not None and pd.isna(v)) else v
        return out

    productos_3d = [
        _clean(r, ["sku", "name", "price", "peso_gr", "stock", "categoria", "description"])
        for _, r in df_3d.iterrows()
    ]

    productos_linea = [
        _clean(r, ["sku", "name", "price", "stock", "tipo_producto", "categoria", "description"])
        for _, r in df_c2[df_c2["tipo_producto"] != "kit_mixto"].iterrows()
    ]

    kits = []
    for _, kr in df_c2[df_c2["tipo_producto"] == "kit_mixto"].iterrows():
        comps_df = df_kc[df_kc["kit_sku"] == kr["sku"]] if not df_kc.empty else pd.DataFrame()
        comps = [
            {
                "sku":      c["component_sku"],
                "nombre":   c.get("comp_name") or "",
                "cantidad": int(c.get("cantidad") or 1),
                "precio":   float(c.get("comp_price") or 0),
            }
            for _, c in comps_df.iterrows()
        ]
        kits.append({
            "sku":         kr["sku"],
            "nombre":      kr["name"],
            "precio":      float(kr["price"]),
            "stock":       int(kr.get("stock") or 0),
            "descripcion": kr.get("description") or "",
            "componentes": comps,
        })

    catalog = {
        "linea":          linea_id,
        "slug":           slug,
        "nombre":         cfg["nombre"],
        "color":          cfg["color"],
        "emoji":          cfg["emoji"],
        "generado":       pd.Timestamp.now().isoformat(timespec="seconds"),
        "productos_3d":   productos_3d,
        "productos_linea": productos_linea,
        "kits":           kits,
    }

    out_path = os.path.join(_EXPORTS_DIR, f"{slug}-catalog.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    return catalog, out_path


def push_exports_to_github(slug_catalog_pairs: list) -> tuple:
    """Commit catalog JSONs to GitHub via Contents API.

    Compares data excluding the 'generado' timestamp; skips files with no real changes.
    Requires GITHUB_TOKEN env var (fine-grained, Contents: read+write on this repo).

    Returns (pushed, skipped, errors) — lists of slugs or error strings.
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return [], [], ["GITHUB_TOKEN no configurado en Streamlit Secrets"]

    api_base = f"https://api.github.com/repos/{_GH_OWNER}/{_GH_REPO}/contents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    pushed, skipped, errors = [], [], []

    for slug, catalog in slug_catalog_pairs:
        path = f"exports/{slug}-catalog.json"
        url  = f"{api_base}/{path}"

        # Canonical representation for diffing (sin 'generado' para evitar falsos positivos)
        def _canonical(d):
            return json.dumps({k: v for k, v in d.items() if k != "generado"},
                              ensure_ascii=False, sort_keys=True)

        new_canonical = _canonical(catalog)
        full_json     = json.dumps(catalog, ensure_ascii=False, indent=2)
        new_b64       = base64.b64encode(full_json.encode("utf-8")).decode("ascii")

        # GET current file from repo
        sha = None
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                current = json.loads(resp.read())
            sha = current["sha"]
            current_bytes   = base64.b64decode(current["content"].replace("\n", ""))
            current_data    = json.loads(current_bytes.decode("utf-8"))
            current_canonical = _canonical(current_data)
            if current_canonical == new_canonical:
                skipped.append(slug)
                continue
        except urllib.error.HTTPError as e:
            if e.code != 404:
                errors.append(f"{slug}: GET HTTP {e.code}")
                continue
            # 404 → archivo nuevo, sha queda None

        # PUT (create or update)
        body = {
            "message": f"chore(exports): regenerar {slug}-catalog.json [bot]",
            "content": new_b64,
        }
        if sha:
            body["sha"] = sha

        try:
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"),
                headers=headers, method="PUT",
            )
            with urllib.request.urlopen(req):
                pass
            pushed.append(slug)
        except urllib.error.HTTPError as e:
            errors.append(f"{slug}: PUT HTTP {e.code} — {e.read().decode()[:200]}")

    return pushed, skipped, errors

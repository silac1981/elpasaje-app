"""
slicer_parser.py — El Pasaje 3D Studio
Extrae datos de impresión de archivos de slicer para pre-llenar el formulario de fabricación.

Soporta:
  .gcode  → Bambu Studio (export), PrusaSlicer, Cura
  .3mf    → Bambu Studio (proyecto con slice_info.config embebido o gcode dentro)

Retorna dict con claves: gramos, tiempo_min, material_tipo, color
"""

import re
import io
import zipfile
import xml.etree.ElementTree as ET


def parsear_archivo_slicer(uploaded_file) -> dict:
    nombre = uploaded_file.name.lower()
    data   = uploaded_file.read()
    if nombre.endswith(".3mf"):
        return _parse_3mf(data)
    return _parse_gcode(data.decode("utf-8", errors="ignore"))


# ─────────────────────────────────────────────────────────────
# GCODE — Bambu Studio export / PrusaSlicer / Cura
# ─────────────────────────────────────────────────────────────

def _parse_gcode(text: str) -> dict:
    result = {}

    # Gramos ── varios formatos de comentario
    for pat in [
        r"; total filament used \[g\] = ([\d.]+)",   # Bambu Studio
        r"; filament used \[g\] = ([\d.]+)",          # PrusaSlicer
        r";Filament used: ([\d.]+)g",                 # Cura (con gramos)
        r"; filament_weight = ([\d.]+)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["gramos"] = round(float(m.group(1)), 1)
            break

    # Tiempo ── "2h 14m 22s" (Bambu/Prusa) o ";TIME:8064" en segundos (Cura)
    m = re.search(r"; estimated printing time.*?= (.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if m:
        t  = m.group(1).strip()
        h  = int(re.search(r"(\d+)h", t).group(1)) if re.search(r"(\d+)h", t) else 0
        mi = int(re.search(r"(\d+)m(?!s)", t).group(1)) if re.search(r"(\d+)m(?!s)", t) else 0
        result["tiempo_min"] = h * 60 + mi
    else:
        m = re.search(r"^;TIME:(\d+)", text, re.MULTILINE)
        if m:
            result["tiempo_min"] = max(1, round(int(m.group(1)) / 60))

    # Material
    for pat in [
        r"; filament_type = (.+?)(?:;|$)",    # Bambu / PrusaSlicer
        r";Filament type = (.+?)(?:;|$)",      # Cura
        r"; filament type = (.+?)(?:;|$)",
    ]:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            result["material_tipo"] = m.group(1).strip()
            break

    # Color hex (#RRGGBB)
    m = re.search(r"; filament_colour = (#[0-9A-Fa-f]{6})", text, re.IGNORECASE)
    if m:
        result["color"] = m.group(1)

    return result


# ─────────────────────────────────────────────────────────────
# 3MF — ZIP con slice_info.config de Bambu o gcode embebido
# ─────────────────────────────────────────────────────────────

def _parse_3mf(data: bytes) -> dict:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()

            # 1. slice_info.config de Bambu Studio (fuente más precisa)
            cfg_candidates = [n for n in names if "slice_info" in n.lower()]
            if cfg_candidates:
                r = _parse_bambu_slice_info(
                    z.read(cfg_candidates[0]).decode("utf-8", errors="ignore")
                )
                if r.get("gramos"):
                    return r

            # 2. Gcode embebido (Bambu guarda plate_1.gcode dentro del ZIP)
            gcode_candidates = sorted(
                [n for n in names if n.lower().endswith(".gcode")],
                key=lambda n: "plate_1" in n.lower(),  # preferir plate_1
                reverse=True
            )
            if gcode_candidates:
                text = z.read(gcode_candidates[0]).decode("utf-8", errors="ignore")
                return _parse_gcode(text)

    except Exception:
        pass
    return {}


def _parse_bambu_slice_info(xml_text: str) -> dict:
    """
    Bambu slice_info.config (XML):
      <plate>
        <metadata key="weight" value="48.32"/>
        <metadata key="prediction" value="8156"/>   ← segundos
        <filament type="PLA" color="#FFFFFF" used_g="48.32"/>
      </plate>
    """
    result = {}
    try:
        root = ET.fromstring(xml_text)
        for plate in root.findall(".//plate"):
            for meta in plate.findall("metadata"):
                k, v = meta.get("key", ""), meta.get("value", "")
                if k == "weight" and v:
                    result["gramos"] = round(float(v), 1)
                elif k == "prediction" and v:
                    result["tiempo_min"] = max(1, round(int(v) / 60))
            fil = plate.find("filament")
            if fil is not None:
                if fil.get("type"):
                    result["material_tipo"] = fil.get("type")
                if fil.get("color"):
                    result["color"] = fil.get("color")
                if not result.get("gramos") and fil.get("used_g"):
                    result["gramos"] = round(float(fil.get("used_g")), 1)
            if result.get("gramos"):
                break  # primera placa con datos es suficiente
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────────────────────
# Helper: buscar material en la lista del DB
# ─────────────────────────────────────────────────────────────

def match_material_idx(material_tipo: str, nombres: list) -> int:
    """
    Dado el tipo de material del slicer ("PLA", "PETG", etc.)
    devuelve el índice en `nombres` que mejor coincide.
    """
    if not material_tipo or not nombres:
        return 0
    tipo = material_tipo.upper().strip()
    # Coincidencia exacta o substring
    for i, n in enumerate(nombres):
        if tipo in n.upper() or n.upper().startswith(tipo):
            return i
    return 0

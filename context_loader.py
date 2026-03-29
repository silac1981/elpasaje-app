# -*- coding: utf-8 -*-
"""
context_loader.py — Cargador Unificado de Fuentes de Datos
Alejandra Gomez Aguilera | SIA + El Pasaje

QUÉ HACE:
  Lee automáticamente TODAS las fuentes disponibles:
  1. Excel/CSV exportados de SAP (ZR154, errores, scoring)
  2. Documentos Word/PDF con procedimientos y manuales
  3. Google Drive (carpeta sincronizada localmente)
  4. Archivos de texto con notas y contexto manual

  El agente llama a get_contexto_completo() en cada consulta
  y recibe un texto estructurado con todo lo disponible.

CÓMO AGREGAR UNA FUENTE NUEVA:
  1. Agregás la ruta en FUENTES abajo
  2. La próxima vez que corra el agente, la lee automáticamente
  No necesitás tocar nada más.

FILOSOFÍA:
  El loader no falla si una fuente no existe — la omite.
  Así podés agregar fuentes futuras sin romper el sistema actual.
"""

import os
import json
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN DE FUENTES
# Agregá rutas acá para conectar nuevas fuentes
# ══════════════════════════════════════════════════════

BASE_SIA = Path(r"C:\Users\ar028883\Documents\SIA_Project")
BASE_EP  = Path(r"C:\Users\ar028883\Documents\elpasaje-app-clean")

# Google Drive — ruta local sincronizada
# (OneDrive en tu caso, o Google Drive cuando lo instales)
BASE_DRIVE = Path(r"C:\Users\ar028883\OneDrive\Documentos")

FUENTES = {

    # ── EXCEL/CSV DE SAP ──────────────────────────────
    "errores_sia": {
        "ruta": BASE_SIA / "reportes/analisis/ERRORES_DETECTADOS.xlsx",
        "tipo": "excel",
        "descripcion": "Errores detectados en última exportación ZR154",
        "max_filas": 20,  # cuántas filas mostrar al agente
    },
    "scoring_proveedores": {
        "ruta": BASE_SIA / "reportes/scoring/RANKING_PROVEEDORES.xlsx",
        "tipo": "excel",
        "descripcion": "Ranking y scoring de proveedores",
        "max_filas": 10,
    },
    "alertas_proveedores": {
        "ruta": BASE_SIA / "reportes/alertas/PROVEEDORES_EN_DETERIORO.xlsx",
        "tipo": "excel",
        "descripcion": "Proveedores con tendencia creciente de errores",
        "max_filas": 5,
    },
    "proyeccion_mensual": {
        "ruta": BASE_SIA / "reportes/alertas/PROYECCION_CIERRE_MENSUAL.xlsx",
        "tipo": "excel",
        "descripcion": "Proyección de cierre del período logístico",
        "max_filas": 3,
    },

    # ── DOCUMENTOS WORD/PDF ───────────────────────────
    # Para agregar un manual nuevo: copiás el archivo a la
    # carpeta docs/ y agregás una entrada acá
    "notas_manuales": {
        "ruta": BASE_SIA / "docs/notas_contexto.txt",
        "tipo": "texto",
        "descripcion": "Notas y contexto manual del analista",
    },
    "procedimientos": {
        "ruta": BASE_SIA / "docs/procedimientos_nuevos.txt",
        "tipo": "texto",
        "descripcion": "Procedimientos operativos nuevos",
    },

    # ── GOOGLE DRIVE / ONEDRIVE ───────────────────────
    # Archivos que subís a OneDrive y el agente lee automáticamente
    "drive_sia_notas": {
        "ruta": BASE_DRIVE / "SIA/notas_agente.txt",
        "tipo": "texto",
        "descripcion": "Notas sobre SIA desde OneDrive",
    },
    "drive_ep_notas": {
        "ruta": BASE_DRIVE / "ElPasaje/notas_agente.txt",
        "tipo": "texto",
        "descripcion": "Notas sobre El Pasaje desde OneDrive",
    },

    # ── EL PASAJE ─────────────────────────────────────
    "ep_odvs": {
        "ruta": BASE_EP / "ep_pasaje.db",
        "tipo": "sqlite_ep",
        "descripcion": "Estado actual ODVs El Pasaje",
    },
    "ep_notas": {
        "ruta": BASE_EP / "docs/notas_contexto.txt",
        "tipo": "texto",
        "descripcion": "Notas y contexto El Pasaje",
    },
    "ep_drive_notas": {
        "ruta": BASE_DRIVE / "ElPasaje/notas_agente.txt",
        "tipo": "texto",
        "descripcion": "Notas El Pasaje desde OneDrive",
    },

    # ── LOG MAESTRO ───────────────────────────────────
    "log_stats": {
        "ruta": BASE_EP / "log_maestro.db",
        "tipo": "sqlite_stats",
        "descripcion": "Estadísticas del log maestro unificado",
    },
}

# ══════════════════════════════════════════════════════
# FUNCIONES DE LECTURA POR TIPO
# ══════════════════════════════════════════════════════

def _leer_excel(ruta: Path, descripcion: str, max_filas: int = 10) -> str:
    """Lee un Excel y devuelve un resumen estructurado."""
    try:
        import pandas as pd
        df = pd.read_excel(ruta)
        if df.empty:
            return f"{descripcion}: vacío\n"

        lines = [f"{descripcion}: {len(df)} filas\n"]

        # Mostrar columnas disponibles
        lines.append(f"  Columnas: {', '.join(df.columns[:10].tolist())}")

        # Mostrar primeras filas como texto
        for _, row in df.head(max_filas).iterrows():
            fila = " | ".join([f"{k}: {v}" for k, v in row.items()
                               if k in df.columns[:8] and str(v) not in ('nan','None','')])
            if fila:
                lines.append(f"  → {fila[:150]}")

        return "\n".join(lines) + "\n"
    except Exception as e:
        return f"{descripcion}: error al leer ({e})\n"


def _leer_texto(ruta: Path, descripcion: str) -> str:
    """Lee un archivo de texto plano."""
    try:
        contenido = ruta.read_text(encoding='utf-8').strip()
        if not contenido:
            return ""
        # Limitar a 2000 caracteres para no sobrecargar el contexto
        if len(contenido) > 2000:
            contenido = contenido[:2000] + "\n[...texto truncado...]"
        return f"{descripcion}:\n{contenido}\n"
    except Exception:
        return ""


def _leer_pdf(ruta: Path, descripcion: str) -> str:
    """Lee un PDF y extrae el texto."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(ruta))
        texto = ""
        for page in reader.pages[:3]:  # máximo 3 páginas
            texto += page.extract_text() or ""
        if not texto.strip():
            return f"{descripcion}: PDF sin texto extraíble\n"
        if len(texto) > 2000:
            texto = texto[:2000] + "\n[...truncado...]"
        return f"{descripcion}:\n{texto}\n"
    except ImportError:
        return f"{descripcion}: instalar pypdf para leer PDFs (pip install pypdf)\n"
    except Exception as e:
        return f"{descripcion}: error al leer PDF ({e})\n"


def _leer_docx(ruta: Path, descripcion: str) -> str:
    """Lee un Word y extrae el texto."""
    try:
        import docx
        doc = docx.Document(str(ruta))
        texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if not texto:
            return ""
        if len(texto) > 2000:
            texto = texto[:2000] + "\n[...truncado...]"
        return f"{descripcion}:\n{texto}\n"
    except ImportError:
        return f"{descripcion}: instalar python-docx para leer Word (pip install python-docx)\n"
    except Exception as e:
        return f"{descripcion}: error al leer Word ({e})\n"


def _leer_sqlite_ep(ruta: Path, descripcion: str) -> str:
    """Lee estado actual de El Pasaje desde ep_pasaje.db."""
    try:
        import sqlite3
        conn = sqlite3.connect(str(ruta))
        conn.row_factory = sqlite3.Row

        totales = conn.execute("""
            SELECT COUNT(*) as total,
            SUM(CASE WHEN estado NOT IN ('Entregado','Cancelado') THEN total_odv ELSE 0 END) as pipeline,
            SUM(CASE WHEN estado='Producción' THEN 1 ELSE 0 END) as en_prod,
            SUM(CASE WHEN estado='Cotización' THEN 1 ELSE 0 END) as cotizaciones
            FROM odv_cabecera
        """).fetchone()

        odvs = conn.execute("""
            SELECT o.id_odv, c.nombre, o.estado, o.total_odv, o.fecha_entrega
            FROM odv_cabecera o JOIN clientes c ON o.cliente_id=c.id
            WHERE o.estado NOT IN ('Entregado','Cancelado')
            ORDER BY o.fecha_entrega ASC LIMIT 8
        """).fetchall()

        conn.close()

        lines = [f"{descripcion}:"]
        lines.append(f"  Total ODV: {totales['total']} | En producción: {totales['en_prod']} | "
                     f"Cotizaciones: {totales['cotizaciones']} | Pipeline: ${totales['pipeline']:,.0f}")
        if odvs:
            lines.append("  Activas:")
            for o in odvs:
                lines.append(f"    {o['id_odv']} | {o['nombre']} | {o['estado']} | "
                             f"${o['total_odv']:,.0f} | entrega: {o['fecha_entrega']}")
        return "\n".join(lines) + "\n"
    except Exception as e:
        return f"{descripcion}: error ({e})\n"


def _leer_sqlite_stats(ruta: Path, descripcion: str) -> str:
    """Lee estadísticas del log maestro."""
    try:
        import sqlite3
        conn = sqlite3.connect(str(ruta))
        total = conn.execute("SELECT COUNT(*) FROM log_eventos").fetchone()[0]
        con_res = conn.execute(
            "SELECT COUNT(*) FROM log_eventos WHERE resultado IS NOT NULL"
        ).fetchone()[0]
        por_sistema = conn.execute(
            "SELECT sistema, COUNT(*) FROM log_eventos GROUP BY sistema"
        ).fetchall()
        conn.close()

        pct = round(con_res/total*100, 1) if total > 0 else 0
        lines = [f"{descripcion}:"]
        lines.append(f"  Total eventos: {total:,} | Con resultado: {con_res:,} ({pct}%)")
        lines.append(f"  Por sistema: {dict(por_sistema)}")
        lines.append(f"  Listo para ML: {total >= 500 and pct >= 30}")
        return "\n".join(lines) + "\n"
    except Exception as e:
        return f"{descripcion}: error ({e})\n"


# ══════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL — lo que llama el agente
# ══════════════════════════════════════════════════════

def get_contexto_completo(sistema: str = "SIA") -> str:
    """
    Lee todas las fuentes disponibles y devuelve el contexto
    estructurado para el agente.

    PRINCIPIO:
    Solo devuelve lo que existe. Si una fuente no está,
    la omite silenciosamente sin error.

    Args:
        sistema: "SIA" | "ElPasaje" | "ambos"
    """
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = [f"\n═══ CONTEXTO UNIFICADO — {hoy} ═══\n"]

    fuentes_leidas = 0
    fuentes_omitidas = 0

    for nombre, config in FUENTES.items():
        ruta = Path(config["ruta"])
        desc = config["descripcion"]
        tipo = config["tipo"]

        if not ruta.exists():
            fuentes_omitidas += 1
            continue

        fuentes_leidas += 1

        if tipo == "excel":
            texto = _leer_excel(ruta, desc, config.get("max_filas", 10))
        elif tipo == "texto":
            texto = _leer_texto(ruta, desc)
        elif tipo == "pdf":
            texto = _leer_pdf(ruta, desc)
        elif tipo == "docx":
            texto = _leer_docx(ruta, desc)
        elif tipo == "sqlite_ep":
            texto = _leer_sqlite_ep(ruta, desc)
        elif tipo == "sqlite_stats":
            texto = _leer_sqlite_stats(ruta, desc)
        else:
            texto = ""

        if texto.strip():
            lineas.append(texto)

    lineas.append(f"\n[Fuentes cargadas: {fuentes_leidas} | Omitidas (no existen): {fuentes_omitidas}]\n")
    return "\n".join(lineas)


def crear_carpetas_necesarias():
    """
    Crea las carpetas que el loader necesita para funcionar.
    Corré esto una sola vez después de instalar.
    """
    carpetas = [
        BASE_SIA / "docs",
        BASE_EP  / "docs",
        BASE_DRIVE / "SIA",
        BASE_DRIVE / "ElPasaje",
    ]
    for c in carpetas:
        c.mkdir(parents=True, exist_ok=True)
        print(f"✅ {c}")

    # Crear archivos de notas vacíos como plantilla
    plantillas = [
        BASE_SIA / "docs/notas_contexto.txt",
        BASE_SIA / "docs/procedimientos_nuevos.txt",
        BASE_EP  / "docs/notas_contexto.txt",
        BASE_DRIVE / "SIA/notas_agente.txt",
        BASE_DRIVE / "ElPasaje/notas_agente.txt",
    ]
    for p in plantillas:
        if not p.exists():
            p.write_text(
                f"# Notas para el Agente IA\n"
                f"# Creado: {datetime.now().strftime('%d/%m/%Y')}\n"
                f"# Agregá acá cualquier contexto nuevo que quieras que el agente sepa.\n\n",
                encoding='utf-8'
            )
            print(f"📝 Plantilla creada: {p.name}")


# ══════════════════════════════════════════════════════
# INTEGRACIÓN CON agent_core.py
# ══════════════════════════════════════════════════════
# 
# En context_sia.py o context_elpasaje.py, reemplazás
# la función get_data_context() por esta llamada:
#
#   from context_loader import get_contexto_completo
#
#   def get_data_context():
#       return get_contexto_completo(sistema="SIA")
#
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🔧 Inicializando carpetas...\n")
    crear_carpetas_necesarias()

    print("\n📊 Probando carga de contexto...\n")
    ctx = get_contexto_completo()
    print(ctx)

    print("\n💡 CÓMO AGREGAR NUEVAS FUENTES:")
    print("  1. Copiás el archivo a una carpeta")
    print("  2. Agregás una entrada en FUENTES en context_loader.py")
    print("  3. El agente lo lee automáticamente")
    print("\n  Para PDFs de NotebookLM:")
    print("  → Exportá el resumen como .txt")
    print(f"  → Guardalo en: {BASE_SIA / 'docs/'}")
    print("  → El agente lo incorpora en la próxima consulta")

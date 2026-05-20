"""migration_v5b.py — Crea y semilla lineas_config desde el diccionario LINEAS.

La tabla pasa a ser la fuente de verdad mutable para configuración de cada línea
(número de WhatsApp, responsable, estado activo, etc.).
El diccionario LINEAS en utils/lineas.py queda como fallback de UI / valores por defecto.

Idempotente: se puede correr N veces sin error ni duplicados.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")

# Datos de seed: client_id → (responsable, activa, fin_solidario)
# Colores y emojis se toman del diccionario LINEAS de utils/lineas.py
_SEED_EXTRA = {
    "admin":            ("Alejandra Gomez Aguilera", 1, None),
    "oasis_animal":     ("Agustina",                 1, None),
    "oasis_del_estero": ("Fede",                     1, None),
    "pharma_delux":     ("Lucas",                    1, None),
    "aviation":         ("Nando",                    1, None),
    "olivia_coquette":  ("Olivia",                   1, None),
    "francisco_sport":  ("Francisco",                1, None),
    "constantino_tech": ("Constantino",              1, None),
    "vkhome_cliente":   ("Agustina",                 1, None),
    "agustina":         ("Agustina",                 1, None),
    "fer_produccion":   ("Fernando",                 1, None),
}

# Espejo de LINEAS para no importar Streamlit desde la migración
_LINEAS_SEED = {
    "admin":            {"nombre": "Administracion",          "color": "#1E3A8A", "emoji": "🏛️"},
    "oasis_animal":     {"nombre": "Oasis Animal",            "color": "#F472B6", "emoji": "🐾"},
    "oasis_del_estero": {"nombre": "Oasis del Estero",        "color": "#34D399", "emoji": "🌱"},
    "pharma_delux":     {"nombre": "Pharma DeLux",            "color": "#FBBF24", "emoji": "💊"},
    "aviation":         {"nombre": "Aviation Pro",            "color": "#0F3460", "emoji": "✈️"},
    "olivia_coquette":  {"nombre": "Coquette",                "color": "#F9A8D4", "emoji": "🎀"},
    "francisco_sport":  {"nombre": "Sport (Francisco)",       "color": "#F97316", "emoji": "⚽"},
    "constantino_tech": {"nombre": "Core Tech (Constantino)", "color": "#64748B", "emoji": "⚙️"},
    "vkhome_cliente":   {"nombre": "VK-Home",                 "color": "#A78BFA", "emoji": "🏡"},
    "agustina":         {"nombre": "Agustina",                "color": "#6366F1", "emoji": "✨"},
    "fer_produccion":   {"nombre": "Produccion",              "color": "#3FB950", "emoji": "🖨️"},
}


def run():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1. Crear tabla lineas_config si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lineas_config (
            client_id       TEXT PRIMARY KEY,
            nombre_display  TEXT NOT NULL,
            color_primario  TEXT DEFAULT '#6B7280',
            color_acento    TEXT DEFAULT '#6B7280',
            emoji_icono     TEXT DEFAULT '📦',
            responsable     TEXT,
            fin_solidario   TEXT,
            activa          INTEGER DEFAULT 1,
            whatsapp_numero TEXT
        )
    """)
    print("[OK] tabla lineas_config (IF NOT EXISTS)")

    # 2. Seed desde _LINEAS_SEED + _SEED_EXTRA (INSERT OR IGNORE → idempotente)
    insertados = 0
    for cid, cfg in _LINEAS_SEED.items():
        extra = _SEED_EXTRA.get(cid, (None, 1, None))
        responsable, activa, fin_solidario = extra
        try:
            cur.execute("""
                INSERT OR IGNORE INTO lineas_config
                    (client_id, nombre_display, color_primario, color_acento,
                     emoji_icono, responsable, fin_solidario, activa, whatsapp_numero)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """, (cid, cfg["nombre"], cfg["color"], cfg["color"],
                  cfg["emoji"], responsable, fin_solidario, activa))
            if cur.rowcount > 0:
                insertados += 1
        except sqlite3.Error as e:
            print(f"[WARN] {cid}: {e}")

    if insertados:
        print(f"[OK] {insertados} línea(s) insertada(s) en lineas_config")
    else:
        print("[SKIP] lineas_config ya tiene datos — ninguna fila nueva")

    # 3. Asegurar columna whatsapp_numero (por si la tabla existía sin ella)
    try:
        cur.execute("ALTER TABLE lineas_config ADD COLUMN whatsapp_numero TEXT")
        print("[OK] lineas_config.whatsapp_numero agregada")
    except sqlite3.OperationalError:
        print("[SKIP] lineas_config.whatsapp_numero ya existe")

    # 4. Índice
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lineas_config_cid ON lineas_config(client_id)")
    print("[OK] indice idx_lineas_config_cid")

    con.commit()
    con.close()

    # Mostrar estado final
    con2 = sqlite3.connect(DB_PATH)
    rows = con2.execute(
        "SELECT client_id, nombre_display, responsable, activa, whatsapp_numero "
        "FROM lineas_config ORDER BY client_id"
    ).fetchall()
    con2.close()
    print("\n--- lineas_config ---")
    print(f"{'client_id':<22} {'nombre':<28} {'responsable':<22} activa  wa_numero")
    print("-" * 90)
    for r in rows:
        wa = r[4] or "(sin configurar)"
        print(f"{r[0]:<22} {r[1]:<28} {(r[2] or ''):<22} {'Si' if r[3] else 'No'}     {wa}")
    print(f"\nTotal: {len(rows)} líneas\n")
    print("[OK] migration_v5b completada")


if __name__ == "__main__":
    run()

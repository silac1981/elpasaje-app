"""migration_v6.py — Repositorio de archivos de produccion.

Crea la tabla archivos_produccion para que Fernando pueda guardar
archivos .gcode / .3mf / .stl vinculados a un SKU u orden.
Los archivos se guardan como BLOB en la misma SQLite.
Idempotente: se puede correr N veces sin error ni duplicados.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def run():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS archivos_produccion (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sku         TEXT,
            order_id    INTEGER,
            filename    TEXT NOT NULL,
            tipo        TEXT DEFAULT 'otro',
            contenido   BLOB,
            size_kb     REAL DEFAULT 0,
            notas       TEXT,
            fecha       TEXT DEFAULT CURRENT_DATE,
            subido_por  TEXT DEFAULT 'fer_produccion'
        )
    """)
    print("[OK] tabla archivos_produccion (IF NOT EXISTS)")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_arch_sku      ON archivos_produccion(sku)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_arch_order_id ON archivos_produccion(order_id)")
    print("[OK] indices idx_arch_sku, idx_arch_order_id")

    con.commit()

    rows = con.execute(
        "SELECT COUNT(*) FROM archivos_produccion"
    ).fetchone()[0]
    con.close()

    print(f"[OK] archivos_produccion existente: {rows} archivo(s)")
    print("[OK] migration_v6 completada")


if __name__ == "__main__":
    run()

"""migration_v11.py — Agrega columna precio_socio a products (idempotente).
Sincroniza con precio_reventa para filas existentes.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def run():
    from utils.db import dialect as _dialect
    if _dialect == "postgresql":
        return
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cols = {r[1] for r in cur.execute("PRAGMA table_info(products)").fetchall()}
    if "precio_socio" not in cols:
        cur.execute("ALTER TABLE products ADD COLUMN precio_socio REAL DEFAULT 0")
        cur.execute("""
            UPDATE products
            SET precio_socio = precio_reventa
            WHERE precio_reventa IS NOT NULL AND precio_reventa > 0
        """)
        conn.commit()
        print("migration_v11 OK — columna precio_socio agregada y sincronizada")
    else:
        print("migration_v11 OK — precio_socio ya existe, sin cambios")

    conn.close()


if __name__ == "__main__":
    run()

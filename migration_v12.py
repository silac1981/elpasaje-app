"""migration_v12.py — Rol Fer → admin + timestamps ciclo de vida en orders (idempotente)."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def run():
    from utils.db import dialect as _dialect
    if _dialect == "postgresql":
        return
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # 1. Fer pasa a admin (decisión CEO)
    cur.execute("UPDATE tenants SET tipo='admin' WHERE id='fer_produccion' AND tipo='produccion'")
    if cur.rowcount:
        print("migration_v12: fer_produccion -> tipo=admin")

    # 2. Timestamps de ciclo de vida en orders
    existing = {r[1] for r in cur.execute("PRAGMA table_info(orders)").fetchall()}
    nuevas = {
        "started_at":          "TEXT",
        "completed_at":        "TEXT",
        "delivered_at":        "TEXT",
        "motivo_cancelacion":  "TEXT",
        "monto_venta":         "REAL DEFAULT 0",
    }
    for col, tipo in nuevas.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE orders ADD COLUMN {col} {tipo}")
            print(f"migration_v12: orders.{col} agregado")

    conn.commit()
    conn.close()
    print("migration_v12 OK")


if __name__ == "__main__":
    run()

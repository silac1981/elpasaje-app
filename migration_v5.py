"""migration_v5.py — Fase 4: tabla pagos + pago_id en orders + whatsapp_numero."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def run():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1. Tabla pagos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id         INTEGER NOT NULL REFERENCES orders(id),
            monto            REAL NOT NULL,
            metodo           TEXT NOT NULL DEFAULT 'transferencia',
            estado           TEXT NOT NULL DEFAULT 'pendiente',
            mp_preference_id TEXT,
            fecha            TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            notas            TEXT
        )
    """)
    print("[OK] tabla pagos (IF NOT EXISTS)")

    # 2. Columna pago_id en orders
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN pago_id INTEGER REFERENCES pagos(id)")
        print("[OK] orders.pago_id agregada")
    except sqlite3.OperationalError:
        print("[SKIP] orders.pago_id ya existe")

    # 3. Indices en pagos
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pagos_order ON pagos(order_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pagos_estado ON pagos(estado)")
    print("[OK] indices pagos")

    # 4. Columna whatsapp_numero en lineas_config
    try:
        cur.execute("ALTER TABLE lineas_config ADD COLUMN whatsapp_numero TEXT")
        print("[OK] lineas_config.whatsapp_numero agregada")
    except sqlite3.OperationalError:
        print("[SKIP] lineas_config.whatsapp_numero ya existe")

    con.commit()
    con.close()
    print("[OK] migration_v5 completada")


if __name__ == "__main__":
    run()

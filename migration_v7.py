"""migration_v7.py — precio_reventa + corrección precios OE + índice. Idempotente."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def run():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # 1. Agregar precio_reventa (idempotente)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN precio_reventa REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # columna ya existe

    # 2. Índice de apoyo para queries del socio
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_reventa
        ON products(client_id, precio_reventa)
    """)

    # 3. Resetear precio_reventa a 0: cada socia configura el suyo desde el panel
    cur.execute("UPDATE products SET precio_reventa = 0 WHERE tipo_producto = 'propio_3d'")

    # 4. Precios EP correctos (lo que las socias le pagan a EP)
    fixes = [
        ("OE-BOV-S", 3000),
        ("OE-BOV-M", 6000),
        ("OE-BOV-L", 9000),
        ("OE-BRR-M", 8000),
        ("OA-LPG-U", 1000),
    ]
    for sku, precio in fixes:
        cur.execute("UPDATE products SET price=? WHERE sku=?", (precio, sku))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run()
    print("migration_v7 OK")

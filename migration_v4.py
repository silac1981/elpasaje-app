"""migration_v4.py — El Pasaje 3D Studio · Mayo 2026
Agrega soporte para modelo de dos capas y revenue sharing.
Correr UNA vez contra elpasaje_v2.db. Idempotente: re-corrida es segura.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")


def migrate():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    ok  = "[OK]"
    skip = "[SKIP]"
    err  = "[FALTA]"

    # 1. Campo tipo_producto en products
    try:
        cur.execute("ALTER TABLE products ADD COLUMN tipo_producto TEXT DEFAULT 'propio_3d'")
        print(f"{ok} tipo_producto agregado a products")
    except Exception:
        print(f"{skip} tipo_producto ya existe")

    # 2. Campo visibilidad en products
    try:
        cur.execute("ALTER TABLE products ADD COLUMN visibilidad TEXT DEFAULT 'publico'")
        print(f"{ok} visibilidad agregado a products")
    except Exception:
        print(f"{skip} visibilidad ya existe")

    # 3. Campo proveedor_ref en products (para Tipo C: referencia a compra conjunta)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN proveedor_ref TEXT")
        print(f"{ok} proveedor_ref agregado a products")
    except Exception:
        print(f"{skip} proveedor_ref ya existe")

    # 4. Tabla revenue_rules (Tipo C — productos compartidos)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS revenue_rules (
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          product_sku  TEXT NOT NULL,
          linea_a      TEXT NOT NULL,
          linea_b      TEXT NOT NULL,
          split_a      REAL DEFAULT 0.5,
          split_b      REAL DEFAULT 0.5,
          notas        TEXT,
          activo       INTEGER DEFAULT 1,
          created_at   TEXT DEFAULT (datetime('now'))
        )
    """)
    print(f"{ok} revenue_rules creada (o ya existia)")

    # 5. Tabla kit_components (Tipo D — kits mixtos)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kit_components (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          kit_sku       TEXT NOT NULL,
          component_sku TEXT NOT NULL,
          cantidad      INTEGER DEFAULT 1,
          orden         INTEGER DEFAULT 0
        )
    """)
    print(f"{ok} kit_components creada (o ya existia)")

    # 6. Indices de performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_client   ON orders(client_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_client ON products(client_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_tipo   ON products(tipo_producto)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_senales_client  ON senales_mercado(cliente_id)")
    print(f"{ok} Indices creados (o ya existian)")

    con.commit()

    # Verificacion final
    print("\n-- Verificacion de schema -----------------------------------------")

    cur.execute("PRAGMA table_info(products)")
    cols_products = {row[1] for row in cur.fetchall()}
    for campo in ("tipo_producto", "visibilidad", "proveedor_ref"):
        estado = ok if campo in cols_products else err
        print(f"  products.{campo}: {estado}")

    for tabla in ("revenue_rules", "kit_components"):
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
        existe = cur.fetchone()
        print(f"  tabla {tabla}: {ok if existe else err}")

    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='index'
        AND name IN ('idx_orders_client','idx_products_client','idx_products_tipo','idx_senales_client')
        ORDER BY name
    """)
    indices = [r[0] for r in cur.fetchall()]
    for idx in ("idx_orders_client","idx_products_client","idx_products_tipo","idx_senales_client"):
        print(f"  indice {idx}: {ok if idx in indices else err}")

    cur.execute("SELECT COUNT(*) FROM products WHERE tipo_producto IS NULL")
    nulos = cur.fetchone()[0]
    if nulos:
        print(f"\n[BACKFILL] {nulos} products con tipo_producto NULL -> rellenando con 'propio_3d'...")
        cur.execute("UPDATE products SET tipo_producto='propio_3d' WHERE tipo_producto IS NULL")
        con.commit()
        print(f"{ok} Backfill tipo_producto completado")

    cur.execute("SELECT COUNT(*) FROM products WHERE visibilidad IS NULL")
    nulos_v = cur.fetchone()[0]
    if nulos_v:
        print(f"[BACKFILL] {nulos_v} products con visibilidad NULL -> rellenando con 'publico'...")
        cur.execute("UPDATE products SET visibilidad='publico' WHERE visibilidad IS NULL")
        con.commit()
        print(f"{ok} Backfill visibilidad completado")

    print("\n[OK] Migration v4 completada\n")
    con.close()


if __name__ == "__main__":
    migrate()

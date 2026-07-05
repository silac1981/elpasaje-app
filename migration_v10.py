"""migration_v10.py — Catálogo F-Zone (Francisco Sport) · Cajitas Porta-Figuritas Mundial 2026
Prefijo FSP-. Idempotente (INSERT OR IGNORE).
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")

# (sku, name, client_id, price, weight_gr, stock, categoria, description, tipo_producto)
PRODUCTOS_FSP = [
    # weight_gr=1470 -> costo filamento+luz+maquina = $3.800 (precio interno El Pasaje a Francisco)
    ("FSP-001", "Cajita Porta-Figuritas AFA",
     "francisco_sport", 10000, 1470, 5,
     "Coleccionables",
     "Caja 3D impresa con el escudo AFA y tres estrellas en relieve. Cierre a presión, separador interior para repetidas y faltantes. Edición Mundial 2026.",
     "propio_3d"),

    ("FSP-002", "Cajita Porta-Figuritas FIFA 26",
     "francisco_sport", 10000, 1470, 5,
     "Coleccionables",
     "Diseño exclusivo FIFA 26 con la Copa del Mundo en alto relieve sobre fondo oscuro. Cierre a presión, separador interior. Edición limitada.",
     "propio_3d"),

    ("FSP-003", "Cajita Porta-Figuritas Argentina FIFA",
     "francisco_sport", 10000, 1470, 5,
     "Coleccionables",
     "Franjas celeste y blanco con la Copa del Mundo en relieve dorado. Cierre a presión, separador interior para repetidas. El regalo ideal para hinchas.",
     "propio_3d"),
]

FOTOS_FSP = {
    "FSP-001": "assets/sport/cajita_afa.jpg",
    "FSP-002": "assets/sport/cajita_fifa26.jpg",
    "FSP-003": "assets/sport/cajita_argentina.jpg",
}


def run():
    from utils.db import dialect as _dialect
    if _dialect == "postgresql":
        return
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    inserted = 0
    for sku, name, cid, price, weight_gr, stock, categoria, description, tipo in PRODUCTOS_FSP:
        cur.execute("""
            INSERT OR IGNORE INTO products
              (sku, name, client_id, price, weight_gr, stock,
               categoria, description, tipo_producto, activo, visibilidad, color)
            VALUES (?,?,?,?,?,?,?,?,?,1,'publico','#F97316')
        """, (sku, name, cid, price, weight_gr, stock, categoria, description, tipo))
        if cur.rowcount:
            inserted += 1

    for sku, foto in FOTOS_FSP.items():
        cur.execute(
            "UPDATE products SET imagen_url=? WHERE sku=? AND (imagen_url IS NULL OR imagen_url='')",
            (foto, sku)
        )

    conn.commit()
    conn.close()
    print(f"migration_v10 OK — {inserted} productos FSP insertados")


if __name__ == "__main__":
    run()

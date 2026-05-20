import sqlite3, os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")
conn = sqlite3.connect(DB)
cur  = conn.cursor()

HOY = datetime.now().strftime("%Y-%m-%d")

productos = [
    ("FSP-001", "francisco_sport", "pla_blanco", "Cajita Porta-Figuritas AFA",
     "Caja 3D impresa para guardar figuritas del Mundial 2026. Diseño escudo AFA con 3 estrellas en relieve. Cierre a presión, interior separador para repetidas y faltantes. Edición limitada — ideal regalo o colección.",
     "Coleccionables", "Blanco / Dorado", 10000, 35, 75, 5, "assets/sport/cajita_afa.jpg", HOY, 1),

    ("FSP-002", "francisco_sport", "pla_negro", "Cajita Porta-Figuritas FIFA 26",
     "Caja 3D impresa para guardar figuritas del Mundial 2026. Diseño exclusivo FIFA 26 con la Copa del Mundo en alto relieve sobre fondo oscuro. Cierre a presión, interior separador para repetidas y faltantes. Edición limitada.",
     "Coleccionables", "Negro / Dorado", 10000, 35, 75, 5, "assets/sport/cajita_fifa26.jpg", HOY, 1),

    ("FSP-003", "francisco_sport", "pla_blanco", "Cajita Porta-Figuritas Argentina FIFA",
     "Caja 3D impresa para figuritas del Mundial 2026. Diseño bandera argentina con la Copa del Mundo. Franjas celeste y blanco con copa en relieve dorado. Cierre a presión, separador interior. El regalo ideal para hinchas.",
     "Coleccionables", "Celeste / Blanco", 10000, 35, 75, 5, "assets/sport/cajita_argentina.jpg", HOY, 1),
]

cur.execute("SELECT sku FROM products WHERE client_id='francisco_sport'")
existing = [r[0] for r in cur.fetchall()]
print("Productos existentes Sport:", existing)

inserted = 0
for p in productos:
    if p[0] not in existing:
        cur.execute("""INSERT INTO products
            (sku, client_id, material_id, name, description, categoria, color,
             price, weight_gr, tiempo_impresion_min, stock, imagen_url, fecha_alta, activo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", p)
        print(f"  + {p[0]} — {p[3]}")
        inserted += 1
    else:
        print(f"  ~ {p[0]} ya existe, omitido")

conn.commit()
conn.close()
print(f"Listo: {inserted} productos insertados.")

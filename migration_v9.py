"""migration_v9.py — Catálogo Oasis del Estero · Macetas + Jardinería + Kits · Mayo 2026
Prefijo ODE- (no OE-) para evitar el UPDATE que mueve OE-* a vkhome_cliente en init_schema.
Idempotente (INSERT OR IGNORE).
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")

# (sku, name, client_id, price, weight_gr, stock, categoria, description, tipo_producto)
PRODUCTOS_ODE = [

    # ── MACETAS ──────────────────────────────────────────────────────────────
    ("ODE-MAC-S",    "Maceta Orgánica Textura S",
     "oasis_del_estero", 4500,  435, 2,
     "Macetas",
     "Textura topográfica en relieve · filamento stone/mármol · ideal suculentas y cactus",
     "linea_propio"),

    ("ODE-MAC-M",    "Maceta Orgánica Textura M",
     "oasis_del_estero", 7500,  726, 2,
     "Macetas",
     "Textura topográfica en relieve · filamento stone/mármol · plantas medianas",
     "linea_propio"),

    ("ODE-MAC-BC-M", "Maceta Bicolor Diagonal M",
     "oasis_del_estero", 9500,  919, 1,
     "Macetas",
     "CFS bicolor gris/negro · franjas diagonales · diseño exclusivo K2 Plus",
     "linea_propio"),

    # ── SOPORTES ELEVADORES ───────────────────────────────────────────────────
    ("ODE-SEL-S",    "Soporte Elevador para Maceta S",
     "oasis_del_estero", 3200,  310, 0,
     "Macetas",
     "Base con 3 patas bola · eleva maceta 8cm · evita charcos · interior/exterior",
     "linea_propio"),

    ("ODE-SEL-M",    "Soporte Elevador para Maceta M",
     "oasis_del_estero", 4800,  465, 1,
     "Macetas",
     "Base con 3 patas bola · versión negra · combina con maceta bicolor",
     "linea_propio"),

    # ── JARDINERÍA — MARCADORES ───────────────────────────────────────────────
    ("ODE-MRP-3",    "Set 3 Marcadores de Plantas",
     "oasis_del_estero", 1800,   50, 0,
     "Jardinería",
     "Etiquetas identificadoras · palito + cartel · personalizables con nombre de planta",
     "linea_propio"),

    ("ODE-MRP-5",    "Set 5 Marcadores Personalizados",
     "oasis_del_estero", 2800,   80, 0,
     "Jardinería",
     "Con nombre de planta grabado + fecha de siembra · ideal regalo jardinero",
     "linea_propio"),

    ("ODE-MRP-10",   "Set 10 Marcadores Personalizados",
     "oasis_del_estero", 4500,  140, 0,
     "Jardinería",
     "Pack completo para colección de plantas · nombre + cuidados · por pedido",
     "linea_propio"),

    # ── TUTORES / SOPORTES PARA PLANTAS ──────────────────────────────────────
    ("ODE-TUT-S",    "Tutor Espiral S (plantas 20–40cm)",
     "oasis_del_estero",  800,   30, 0,
     "Jardinería",
     "Soporte helicoidal · PETG resistente · plantas trepadoras y aromáticas pequeñas",
     "linea_propio"),

    ("ODE-TUT-M",    "Tutor Espiral M (plantas 40–70cm)",
     "oasis_del_estero", 1200,   50, 0,
     "Jardinería",
     "Soporte helicoidal · PETG resistente · tomates cherry, albahaca, trepadoras medianas",
     "linea_propio"),

    ("ODE-TUT-3PK",  "Pack 3 Tutores Espiral (surtido S+M+L)",
     "oasis_del_estero", 3200,  150, 0,
     "Jardinería",
     "Pack mixto ideal para jardín en balcón · 3 tamaños · color a elección",
     "linea_propio"),

    # ── ACCESORIOS ────────────────────────────────────────────────────────────
    ("ODE-CAR-U",    "Cartelito Identificador de Maceta",
     "oasis_del_estero",  600,   15, 0,
     "Jardinería",
     "Plaquita con nombre del propietario + especie · personalizable · por unidad",
     "linea_propio"),

    ("ODE-SEM-U",    "Organizador de Semillas (6 compartimentos)",
     "oasis_del_estero", 3500,  115, 0,
     "Jardinería",
     "Caja modular 6 divisiones con tapa y etiqueta · para almacenar semillas",
     "linea_propio"),

    # ── KITS REGALO ───────────────────────────────────────────────────────────
    ("ODE-KIT-JAR",  "Kit Jardinero Urbano",
     "oasis_del_estero", 12000,   0, 0,
     "Kits",
     "Maceta Orgánica S + Set 5 Marcadores + Tutor M · caja kraft · regalo completo",
     "kit_mixto"),

    ("ODE-KIT-SUC",  "Kit Suculentas",
     "oasis_del_estero", 18000,   0, 0,
     "Kits",
     "2x Maceta Orgánica S + Bandeja Oval S + Set 3 Marcadores · listo para regalar",
     "kit_mixto"),
]

FOTOS_ODE = {
    "ODE-MAC-S":    "OE-macetas-blancas-bandeja-negra-frente.jpg",
    "ODE-MAC-M":    "OE-macetas-blancas-bandeja-negra-lateral.jpg",
    "ODE-MAC-BC-M": "OE-maceta-bicolor-bandeja-blanca.jpg",
    "ODE-SEL-M":    "OE-maceta-bicolor-soporte-negro-frente.jpg",
    "ODE-KIT-SUC":  "OE-macetas-bandeja-conjunto.jpg",
    "ODE-KIT-JAR":  "OE-macetas-bandeja-conjunto.jpg",
}


def run():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Limpiar productos con prefijo OE-MAC/OE-SEL/OE-MRP/OE-TUT/OE-KIT-JAR/OE-KIT-SUC
    # que pudieron haberse insertado en la versión anterior con prefijo OE-
    viejos = [
        "OE-MAC-S","OE-MAC-M","OE-MAC-BC-M","OE-SEL-S","OE-SEL-M",
        "OE-MRP-3","OE-MRP-5","OE-MRP-10","OE-TUT-S","OE-TUT-M","OE-TUT-3PK",
        "OE-CAR-U","OE-SEM-U","OE-KIT-JAR","OE-KIT-SUC",
    ]
    placeholders = ",".join("?" * len(viejos))
    cur.execute(f"DELETE FROM products WHERE sku IN ({placeholders})", viejos)

    inserted = 0
    for sku, name, cid, price, weight_gr, stock, categoria, description, tipo in PRODUCTOS_ODE:
        cur.execute("""
            INSERT OR IGNORE INTO products
              (sku, name, client_id, price, weight_gr, stock,
               categoria, description, tipo_producto, activo, visibilidad, color)
            VALUES (?,?,?,?,?,?,?,?,?,1,'publico','#2D6A4F')
        """, (sku, name, cid, price, weight_gr, stock, categoria, description, tipo))
        if cur.rowcount:
            inserted += 1

    for sku, foto in FOTOS_ODE.items():
        cur.execute(
            "UPDATE products SET imagen_url=? WHERE sku=? AND (imagen_url IS NULL OR imagen_url='')",
            (foto, sku)
        )

    conn.commit()
    conn.close()
    print(f"migration_v9 OK — {inserted} productos ODE insertados/actualizados")


if __name__ == "__main__":
    run()

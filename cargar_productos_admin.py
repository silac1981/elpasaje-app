"""
cargar_productos_admin.py
=========================
Carga el catálogo base de productos de admin (Fer).
Estos son los productos que todos los socios pueden pedir.

Ejecutar desde la carpeta del proyecto:
    python cargar_productos_admin.py
"""

import os
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")
engine  = create_engine(f"sqlite:///{DB_PATH}")

PRODUCTOS_ADMIN = [
    # sku           material_id      name                          desc                                              cat        color      price   weight  tiempo  stock
    ("ADM-001", "pla_blanco",   "Base Rectangular S",         "Base impresa estándar 10x8cm. Uso general.",      "General", "Blanco",  1800,   40,     20,     20),
    ("ADM-002", "pla_blanco",   "Base Rectangular M",         "Base impresa estándar 15x12cm. Uso general.",     "General", "Blanco",  2400,   65,     32,     15),
    ("ADM-003", "pla_negro",    "Base Rectangular L",         "Base impresa estándar 20x15cm. Uso general.",     "General", "Negro",   3200,   95,     48,     10),
    ("ADM-004", "pla_blanco",   "Soporte Cilíndrico S",       "Soporte redondo 8cm diámetro. Múltiple uso.",     "General", "Blanco",  1600,   35,     18,     20),
    ("ADM-005", "pla_negro",    "Soporte Cilíndrico M",       "Soporte redondo 12cm diámetro. Múltiple uso.",    "General", "Negro",   2200,   60,     30,     15),
    ("ADM-006", "pla_blanco",   "Caja con Tapa S",            "Caja 8x6x4cm con tapa a presión.",                "General", "Blanco",  2800,   55,     28,     10),
    ("ADM-007", "pla_blanco",   "Caja con Tapa M",            "Caja 12x9x5cm con tapa a presión.",               "General", "Blanco",  3800,   85,     42,     8),
    ("ADM-008", "pla_negro",    "Panel Personalizado S",      "Panel plano 10x10cm. Texto o logo en relieve.",   "General", "Negro",   3500,   70,     35,     10),
    ("ADM-009", "pla_negro",    "Panel Personalizado M",      "Panel plano 15x15cm. Texto o logo en relieve.",   "General", "Negro",   5000,   110,    55,     8),
    ("ADM-010", "petg_gris",    "Soporte con Gancho",         "Soporte con gancho doble para colgar objetos.",   "General", "Gris",    2600,   50,     25,     12),
    ("ADM-011", "pla_blanco",   "Porta Nombre de Escritorio", "Porta nombre 12x4cm. Personalizable con legajo.", "Oficina", "Blanco",  2200,   45,     22,     15),
    ("ADM-012", "pla_negro",    "Clip Organizador Cables",    "Clip organizador de cables para escritorio.",     "Oficina", "Negro",   1400,   20,     10,     25),
    ("ADM-013", "petg_naranja", "Tope de Seguridad",          "Tope naranja para puertas y cajones.",            "General", "Naranja", 1200,   25,     12,     20),
    ("ADM-014", "pla_blanco",   "Separador Modular",          "Separador de cajón o bandeja 20x5cm.",            "General", "Blanco",  1600,   30,     15,     20),
    ("ADM-015", "petg_gris",    "Pieza a Pedido (custom)",    "Pieza personalizada. Coordinar specs con Fer.",   "General", "A definir",8000,  150,    75,     3),
]

with engine.connect() as conn:
    print("📦 Cargando catálogo base de Fer (admin)...\n")

    for sku, mat, name, desc, cat, color, price, weight, tiempo, stock in PRODUCTOS_ADMIN:
        conn.execute(text("""
            INSERT INTO products
                (sku, client_id, material_id, name, description, categoria, color,
                 price, weight_gr, tiempo_impresion_min, stock)
            VALUES
                (:sku, 'admin', :mat, :name, :desc, :cat, :color,
                 :price, :weight, :tiempo, :stock)
            ON CONFLICT(sku) DO UPDATE SET
                name                 = excluded.name,
                description          = excluded.description,
                categoria            = excluded.categoria,
                color                = excluded.color,
                price                = excluded.price,
                weight_gr            = excluded.weight_gr,
                tiempo_impresion_min = excluded.tiempo_impresion_min,
                stock                = excluded.stock
        """), {
            "sku": sku, "mat": mat, "name": name, "desc": desc,
            "cat": cat, "color": color, "price": price,
            "weight": weight, "tiempo": tiempo, "stock": stock
        })
        print(f"   ✅ {sku} — {name}")

    conn.commit()

print(f"\n🚀 {len(PRODUCTOS_ADMIN)} productos admin cargados.")
print("   El selector de Cargar Pedido ya tiene opciones.")
print("   Próximo paso: git add + commit + push de la DB.")

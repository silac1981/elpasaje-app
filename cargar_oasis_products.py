"""
cargar_oasis_products.py
========================
Carga el catálogo completo de Oasis Animal en el EPCC
+ Apartado B2B VK-Home en el canal de Agustina
Ejecutar desde: magnitud19-backend-share
"""
import sqlite3
from datetime import datetime

DB = r"C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share\elpasaje_v2.db"
conn = sqlite3.connect(DB)
HOY = datetime.now().strftime("%Y-%m-%d")

print()
print("╔══════════════════════════════════════════════╗")
print("║  Cargando catálogo Oasis Animal + VK-Home    ║")
print("╚══════════════════════════════════════════════╝")
print()

# ── PRODUCTOS OASIS ANIMAL ──
productos_oasis = [
    # (sku, client_id, material_id, name, description, categoria, color, price, weight_gr, tiempo_min, stock)
    (
        "OAS-LLA-001", "oasis_animal", "pla_negro",
        "Llavero Perrito Globo",
        "Llavero artístico forma de perrito globo. Estilo pop-art. Disponible en múltiples colores. Ideal para regalo y souvenir. Ya fabricado y con stock.",
        "Accesorios", "Multicolor",
        1000, 18, 25, 30  # 30 unidades ya fabricadas
    ),
    (
        "OAS-EST-001", "oasis_animal", "pla_negro",
        "Estación Evolutiva — Módulo Inicial",
        "Soporte comedero ergonómico para cachorros y gatos. Altura baja. Cuida postura y digestión desde los primeros meses. Se fabrica por pedido.",
        "Estación Evolutiva", "Negro",
        8000, 180, 240, 0
    ),
    (
        "OAS-EST-002", "oasis_animal", "pla_negro",
        "Estación Evolutiva — Módulo Alto",
        "Soporte comedero ergonómico para perros medianos y grandes. Altura elevada. El mismo soporte que crece con el animal. Por pedido.",
        "Estación Evolutiva", "Negro",
        10000, 280, 360, 0
    ),
    (
        "OAS-COM-001", "oasis_animal", "pla_negro",
        "Soporte Comedero con Cuenco — Patita",
        "Soporte comedero negro con cuenco cerámico diseño patita. Estético y funcional. Mayorista socios $9.000 — Precio público $18.000. Por pedido.",
        "Comederos", "Negro/Blanco",
        9000, 320, 180, 0
    ),
    (
        "OAS-COM-002", "oasis_animal", "pla_negro",
        "Soporte Comedero con Cuenco — Huesito",
        "Soporte comedero negro con cuenco cerámico diseño huesito. Relieve en bajorrelieve. Mayorista socios $9.000 — Precio público $18.000. Por pedido.",
        "Comederos", "Negro/Blanco",
        9000, 320, 180, 0
    ),
    (
        "OAS-TAG-001", "oasis_animal", "pla_negro",
        "Guardián Tag",
        "Chapa con QR de emergencia en material fosforescente. Para caminatas nocturnas. Seguridad premium que brilla cuando importa. $800 al público.",
        "Identificación", "Negro fosforescente",
        800, 15, 20, 0
    ),
    (
        "OAS-LIT-001", "oasis_animal", "pla_blanco",
        "Memory Litophany",
        "Litofanía 3D personalizada con foto de tu mascota. Al encender una vela, revela la imagen. El producto más emotivo del catálogo. 16hs de impresión. Por pedido.",
        "Memoria", "Blanco",
        35000, 120, 960, 0
    ),
    (
        "OAS-TRV-001", "oasis_animal", "pla_negro",
        "Travel Kit Ergonómico",
        "Set de comederos de encastre rápido para viajes. Compacto, estético, resistente. Para quienes viajan con sus mascotas. A cotizar según tamaño.",
        "Viaje", "Negro",
        12000, 200, 280, 0
    ),
    (
        "OAS-JOY-001", "oasis_animal", "pla_rosa",
        "Pet Jewelry Coquette",
        "Dije 3D con la inicial de tu mascota. En alianza con Olivia (Coquette). Para collar o pulsera. Vínculo emocional hecho objeto. A cotizar.",
        "Joyería", "Rosa/Personalizado",
        4500, 8, 45, 0
    ),
]

# ── PRODUCTOS VK-HOME EN CANAL AGUSTINA (B2B) ──
productos_vkhome_en_oasis = [
    (
        "OAS-B2B-VKH-001", "oasis_animal", "pla_negro",
        "Bandeja Decorativa Orgánica — VK-Home",
        "Bandeja redonda con patas esféricas orgánicas. Diseño minimalista premium. En alianza B2B con VK-Home. Ideal para home decor y regalos corporativos.",
        "B2B VK-Home", "Negro/Colores",
        15000, 350, 300, 0
    ),
    (
        "OAS-B2B-VKH-002", "oasis_animal", "pla_negro",
        "Soporte Aromático — VK-Home",
        "Base decorativa para difusor y spray de ambiente. Estilo nórdico. En alianza B2B con VK-Home. El mismo producto que usa Oasis en sus ambientes.",
        "B2B VK-Home", "Negro",
        12000, 280, 240, 0
    ),
]

print("► Cargando productos Oasis Animal...")
cargados = 0
existentes = 0
for p in productos_oasis + productos_vkhome_en_oasis:
    existe = conn.execute("SELECT sku FROM products WHERE sku=?", (p[0],)).fetchone()
    if existe:
        existentes += 1
        print(f"  ⏭️  {p[3]} (ya existe)")
        continue
    conn.execute("""
        INSERT INTO products
        (sku, client_id, material_id, name, description, categoria,
         color, price, weight_gr, tiempo_impresion_min, stock, fecha_alta, activo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)
    """, (*p, HOY))
    cargados += 1
    print(f"  ✅ {p[3]} — ${p[7]:,}")

# ── PRIMER ORDEN HISTÓRICA (los 2 comederos de hace 1 año) ──
print()
print("► Registrando venta histórica VK-Home (2 comederos ~$9.000 total)...")
existe_order = conn.execute(
    "SELECT id FROM orders WHERE notas LIKE '%historica%vkhome%'"
).fetchone()

if not existe_order:
    conn.execute("""
        INSERT INTO orders (client_id, status, date, notas, color_pedido)
        VALUES ('vkhome_cliente', 'Listo', '2025-01-01',
                'Venta historica vkhome — 2 comederos ceramica aprox $9000 total. Fecha exacta desconocida. Registrada para trazabilidad.',
                '#F472B6')
    """)
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("""
        INSERT INTO order_items (order_id, product_sku, cantidad, precio_unitario)
        VALUES (?, 'OAS-COM-001', 2, 4500)
    """, (order_id,))
    print(f"  ✅ Venta histórica registrada (Order #{order_id})")
else:
    print("  ⏭️  Venta histórica ya registrada")

# ── SEÑAL DE MERCADO ──
print()
print("► Registrando señales de mercado...")
senales = [
    (HOY, "vkhome_cliente", "Oasis Animal",
     "Llavero Perrito Globo",
     "Le encantó",
     "B2B / Reventa",
     "Los vende a $5.000 (nosotros a $1.000). Pedido 30 unidades ya entregado.",
     "Alejandra", "WhatsApp"),
    (HOY, "vkhome_cliente", "Oasis Animal",
     "Soporte Comedero",
     "Le encantó",
     "B2B / Reventa",
     "Compraron 2 hace ~1 año a $9.000. Primera venta registrada del ecosistema.",
     "Alejandra", "Presencial"),
]
for s in senales:
    conn.execute("""
        INSERT INTO senales_mercado
        (fecha, cliente_id, linea, producto, reaccion, segmento_detectado,
         oportunidad, fuente, canal, procesado_por_ia)
        VALUES (?,?,?,?,?,?,?,?,?,0)
    """, s)
print(f"  ✅ {len(senales)} señales registradas")

conn.commit()

# ── RESUMEN ──
print()
print("═" * 50)
total_oasis = conn.execute(
    "SELECT COUNT(*), SUM(price*stock) FROM products WHERE client_id='oasis_animal'"
).fetchone()
print(f"Productos Oasis Animal: {total_oasis[0]} SKUs")
print(f"Valor stock actual:     ${total_oasis[1] or 0:,.0f}")
print()
print("Catálogo completo:")
prods = conn.execute(
    "SELECT name, price, stock, categoria FROM products WHERE client_id='oasis_animal' ORDER BY categoria"
).fetchall()
for p in prods:
    stock_txt = f"Stock: {p[2]}" if p[2] > 0 else "Por pedido"
    print(f"  • [{p[3]}] {p[0]} — ${p[1]:,} — {stock_txt}")

print()
print("✅ Catálogo Oasis Animal cargado.")
print("   Próximo paso:")
print("   git add elpasaje_v2.db")
print('   git commit -m "feat: catalogo Oasis Animal + B2B VK-Home"')
print("   git push")

conn.close()

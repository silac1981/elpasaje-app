import sqlite3
db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Aseguramos que la tabla de productos tenga la columna de peso (Mejora #59)
try:
    cursor.execute("ALTER TABLE products ADD COLUMN weight_gr REAL")
except:
    pass # Si ya existe, no hace nada

# 2. Actualizamos pesos reales para el cálculo de Fer (Mejora #81)
# Organizador Kaizen: 450g | Cubo Infinito: 120g | Llaveros: 15g
datos_peso = [
    (450.0, "REC-ORG"),
    (120.0, "REC-CUB"),
    (15.0, "COQ-TEX-01"),
    (15.0, "SOL-REC-HUE")
]

for peso, sku in datos_peso:
    cursor.execute("UPDATE products SET weight_gr = ? WHERE sku = ?", (peso, sku))

# 3. Creamos la tabla de Órdenes si no existe (El puente que Claude va a usar)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        product_name TEXT,
        quantity INTEGER,
        material TEXT,
        status TEXT DEFAULT 'Pendiente',
        date TEXT
    )
""")

conn.commit()
conn.close()
print("✅ Cimientos Reforzados: Pesos actualizados y Tabla de Órdenes creada.")

import sqlite3
db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Creamos la tabla de Ventas Realizadas (Mejora #105)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT,
        product_name TEXT,
        price REAL,
        client_id TEXT,
        date TEXT
    )
""")

conn.commit()
conn.close()
print("✅ Caja Registradora Activada: El sistema ahora puede procesar ventas instantáneas.")

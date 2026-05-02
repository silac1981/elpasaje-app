import sqlite3
db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Definición robusta de tablas (Cimientos de Alta Magnitud) [cite: 2, 51]
tablas = {
    "tenants": "id TEXT PRIMARY KEY, name TEXT, slug TEXT, email TEXT, password TEXT",
    "products": "sku TEXT PRIMARY KEY, name TEXT, price REAL, stock INTEGER, client_id TEXT, weight_gr REAL",
    "materials": "id TEXT PRIMARY KEY, name TEXT, stock_gr REAL, cost_kg REAL",
    "orders": "id TEXT PRIMARY KEY, client_id TEXT, product_name TEXT, status TEXT, date TEXT"
}

# Reinicio controlado: Borramos y recreamos para limpiar el 'datatype mismatch' 
for tabla, esquema in tablas.items():
    cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
    cursor.execute(f"CREATE TABLE {tabla} ({esquema})")

# Carga de Socios Oficiales (Mejora #23, #49) [cite: 45, 49]
socios = [
    ("admin", "Administración (Ale/Fer)", "admin", "admin@elpasaje.com", "admin123"),
    ("agus", "Oasis Animal (Agustina)", "agus", "oasis_animal@elpasaje.com", "agus123"),
    ("fede", "Oasis del Estero (Fede)", "fede", "oasis_del_estero@elpasaje.com", "fede123"),
    ("lucas", "Pharma DeLux (Lucas)", "lucas", "pharma_delux@elpasaje.com", "lucas123"),
    ("nando", "Aviation (Nando)", "nando", "aviation@elpasaje.com", "nando123")
]
cursor.executemany("INSERT INTO tenants VALUES (?,?,?,?,?)", socios)

# Carga de Materiales de Fer (Mejora #5, #55, #83) 
materiales = [
    ("m1", "PLUMARMOL", 5000.0, 2500.0), 
    ("m2", "PLANEGRO MATE", 3500.0, 2200.0)
]
cursor.executemany("INSERT INTO materials VALUES (?,?,?,?)", materiales)

conn.commit()
conn.close()
print("✅ Bloque de Cimientos REPARADO. Materiales y Socios sincronizados.")

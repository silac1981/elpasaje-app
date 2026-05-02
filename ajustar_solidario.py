import sqlite3
db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Ajustamos a Agus como Negocio y creamos el Refugio/Solidario aparte
familias_actualizadas = [
    ("oasis_animal", "Oasis Animal (Negocio)", "#FFB6C1", "🐾", "REGLA_X3"),
    ("solidario_general", "Fondo Solidario El Pasaje", "#FFFFFF", "❤️", "DONACION_DIRECTA"),
    ("refugio_oasis", "Refugio Oasis (Donaciones)", "#E0FFFF", "🏠", "DONACION_DIRECTA")
]

cursor.executemany("INSERT OR REPLACE INTO tenants_config VALUES (?,?,?,?,?)", familias_actualizadas)

# 2. Creamos la tabla de DONACIONES (Mejora #120)
# Para rastrear de dónde viene la plata (Llaveros, QR en showroom, aporte directo)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origen TEXT,
        monto REAL,
        destino TEXT,
        fecha TEXT
    )
""")

conn.commit()
conn.close()
print("✅ Identidades Separadas: Negocio de Agus y Líneas Solidarias listas.")

import sqlite3

db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Aseguramos columnas necesarias
try:
    cursor.execute("ALTER TABLE tenants ADD COLUMN email TEXT")
except: pass
try:
    cursor.execute("ALTER TABLE tenants ADD COLUMN password TEXT")
except: pass

# 2. Lista de Socios con SLUGS (lo que pide la DB)
# Estructura: (id, name, slug, email, password)
socios = [
    ("admin", "Alejandra (Admin)", "admin", "admin@elpasaje.com", "123"),
    ("nely", "Mujeres Virtuosas (Nely)", "nely", "Mujeres_Virtuosas@elpasaje.com", "nely123"),
    ("agus", "Oasis Animal (Agus)", "agus", "Oasis_Animal@elpasaje.com", "agus123"),
    ("fede", "Oasis del Estero (Fede)", "fede", "Oasis_del_Estero@elpasaje.com", "fede123"),
    ("nando", "Aviation (Nando)", "nando", "Aviation@elpasaje.com", "123"),
    ("lucas", "Pharma DeLux (Lucas)", "lucas", "Pharma_DeLux@elpasaje.com", "lucas123")
]

# 3. Limpiamos e insertamos con todos los campos obligatorios
cursor.execute("DELETE FROM tenants")
for uid, nombre, slug, email, clave in socios:
    cursor.execute("""
        INSERT INTO tenants (id, name, slug, email, password) 
        VALUES (?, ?, ?, ?, ?)
    """, (uid, nombre, slug, email, clave))

conn.commit()
conn.close()
print("✅ ¡LOGRADO! Base de datos sincronizada con Slugs y nuevos accesos.")

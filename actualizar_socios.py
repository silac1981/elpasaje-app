import sqlite3

db_path = "elpasaje_v2.db"

socios = [
    ("admin", "admin", "123"),
    ("Mujeres Virtuosas (Nely)", "Mujeres_Virtuosas@elpasaje.com", "nely123"),
    ("Oasis Animal (Agus)", "Oasis_Animal@elpasaje.com", "agus123"),
    ("Oasis del Estero (Fede)", "Oasis_del_Estero@elpasaje.com", "fede123"),
    ("Aviation (Nando)", "Aviation@elpasaje.com", "123"),
    ("Pharma DeLux (Lucas)", "Pharma_DeLux@elpasaje.com", "lucas123")
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Limpiamos y recargamos socios para evitar duplicados
cursor.execute("DELETE FROM tenants")
for nombre, email, clave in socios:
    # Usamos el email como ID para simplificar el login
    cursor.execute("INSERT INTO tenants (id, name, email, password) VALUES (?, ?, ?, ?)", 
                  (email.split('@')[0], nombre, email, clave))

conn.commit()
conn.close()
print("✅ Socios actualizados: Nando y Lucas incorporados.")

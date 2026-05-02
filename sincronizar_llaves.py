import sqlite3
db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Lista Maestra Corregida (Estandarización de Código y Formatos)
# Estructura: (ID, Nombre, Email, Password)
credenciales = [
    ("admin", "Administración (Ale/Fer)", "admin@elpasaje.com", "admin123"),
    ("oasis_animal", "Oasis Animal (Agustina)", "oasis_animal@elpasaje.com", "agus123"),
    ("oasis_del_estero", "Oasis del Estero (Fede)", "oasis_del_estero@elpasaje.com", "fede123"),
    ("pharma_delux", "Pharma DeLux (Lucas)", "pharma_delux@elpasaje.com", "lucas123"),
    ("aviation", "Aviation (Nando)", "aviation@elpasaje.com", "nando123")
]

cursor.execute("DELETE FROM tenants")
for uid, nombre, email, contra in credenciales:
    cursor.execute("INSERT INTO tenants (id, name, slug, email, password) VALUES (?, ?, ?, ?, ?)", 
                  (uid, nombre, uid, email, contra))

conn.commit()
conn.close()
print("✅ Credenciales Sincronizadas: Ya podés entrar con los correos oficiales.")

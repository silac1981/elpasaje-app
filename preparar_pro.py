import sqlite3
db = "elpasaje_v2.db"
conn = sqlite3.connect(db)
cursor = conn.cursor()
socios = [
    ("admin", "Alejandra (Admin)", "admin", "admin@elpasaje.com", "123"),
    ("nando", "Aviation (Nando)", "nando", "Aviation@elpasaje.com", "123"),
    ("lucas", "Pharma DeLux (Lucas)", "lucas", "Pharma_DeLux@elpasaje.com", "lucas123"),
    ("nely", "Mujeres Virtuosas (Nely)", "nely", "Mujeres_Virtuosas@elpasaje.com", "nely123"),
    ("agus", "Oasis Animal (Agus)", "agus", "Oasis_Animal@elpasaje.com", "agus123")
]
cursor.execute("DELETE FROM tenants")
cursor.executemany("INSERT INTO tenants (id, name, slug, email, password) VALUES (?, ?, ?, ?, ?)", socios)
conn.commit()
conn.close()
print("✅ Base de datos lista para la versión Pro.")

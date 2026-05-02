import sqlite3
DB = r"C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share\elpasaje_v2.db"
conn = sqlite3.connect(DB)
cols = conn.execute("PRAGMA table_info(tenants)").fetchall()
print("Columnas de tenants:")
for c in cols:
    print(f"  {c[1]} ({c[2]})")
conn.close()

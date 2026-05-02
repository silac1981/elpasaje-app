import sqlite3

conn = sqlite3.connect('elpasaje_v2.db')
cursor = conn.cursor()

try:
    # Eliminamos la tabla de socios para que el sistema la recree limpia
    cursor.execute('DROP TABLE IF EXISTS tenants')
    # También borramos los productos para evitar conflictos de integridad
    cursor.execute('DROP TABLE IF EXISTS products')
    print("✅ Tablas antiguas limpiadas para el nuevo esquema.")
except Exception as e:
    print(f"❌ Error al limpiar: {e}")

conn.commit()
conn.close()
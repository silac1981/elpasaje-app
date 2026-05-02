import sqlite3
import os

db_origen = "elpasaje_database.db"
db_destino = "elpasaje_v2.db"

def rescate_final():
    if not os.path.exists(db_origen):
        print(f"❌ Error: No encuentro el archivo {db_origen} en esta carpeta.")
        print(f"Archivos en carpeta actual: {os.listdir('.')}")
        return

    size = os.path.getsize(db_origen)
    print(f"📦 Tamaño del archivo detectado: {size} bytes")

    try:
        conn_v = sqlite3.connect(db_origen)
        cursor = conn_v.cursor()
        
        # Intentamos un volcado directo de lo que vimos en el binario
        print("⏳ Extrayendo Organizador Kaizen y Cubo Infinito...")
        cursor.execute("SELECT name, price_x3, weight_gr FROM products")
        filas = cursor.fetchall()
        
        conn_n = sqlite3.connect(db_destino)
        cursor_n = conn_n.cursor()
        
        for fila in filas:
            nombre, precio, peso = fila
            sku = f"REC-{nombre[:3].upper()}"
            cursor_n.execute("""
                INSERT INTO products (id, client_id, sku, name, price, cost, stock, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"old_{nombre}", "admin", sku, nombre, precio, peso, 10, 1))
        
        conn_n.commit()
        conn_v.close()
        conn_n.close()
        print("✅ ¡LOGRADO! Los datos históricos han vuelto a la Magnitud.")
        
    except Exception as e:
        print(f"❌ Error al leer las tablas: {e}")

rescate_final()

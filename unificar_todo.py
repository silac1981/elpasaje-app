import sqlite3
import pandas as pd

db_viejisima = "elpasaje_database.db"
db_actual = "elpasaje_v2.db"

def rescatar_todo():
    try:
        conn_v = sqlite3.connect(db_viejisima)
        cursor = conn_v.cursor()
        
        # Le preguntamos a la DB qué tablas tiene realmente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [t[0] for t in cursor.fetchall()]
        print(f"🔍 Tablas encontradas en la DB vieja: {tablas}")

        # Buscamos la tabla de productos (sin importar mayúsculas/minúsculas)
        tabla_objetivo = next((t for t in tablas if t.lower() == 'products'), None)

        if tabla_objetivo:
            df = pd.read_sql(f"SELECT * FROM {tabla_objetivo}", conn_v)
            conn_v.close()
            
            # Mapeo manual basado en tus archivos 
            df_ready = pd.DataFrame()
            df_ready['name'] = df['name']
            # Usamos price_x3 si existe (según tu esquema anterior )
            df_ready['price'] = df['price_x3'] if 'price_x3' in df.columns else 0.0
            df_ready['cost'] = df['weight_gr'] if 'weight_gr' in df.columns else 0.0
            df_ready['sku'] = "HIST-" + df.index.astype(str)
            df_ready['client_id'] = "admin"
            df_ready['stock'] = 10
            df_ready['id'] = "recup_" + df.index.astype(str)

            # Insertar en la nueva [cite: 197]
            conn_n = sqlite3.connect(db_actual)
            df_ready.to_sql("products", conn_n, if_exists="append", index=False)
            conn_n.close()
            print("✅ ¡LOGRADO! Datos históricos recuperados.")
        else:
            print(f"❌ No se encontró nada parecido a 'products'. Tablas disponibles: {tablas}")
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    rescatar_todo()

import sqlite3

db_path = "elpasaje_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Asignamos productos a los nuevos socios para que el gráfico no esté vacío
# (Socio Nuevo, SKU del producto rescatado)
actualizaciones = [
    ("Aviation.com", "REC-ORG"),   # Organizador Kaizen para Nando
    ("Pharma_DeLux.com", "REC-CUB"), # Cubo Infinito para Lucas
    ("project_hub", "HUB-EXT-01")    # Prototipo para el Hub
]

for cli, sku in actualizaciones:
    cursor.execute("UPDATE products SET client_id = ? WHERE sku = ?", (cli, sku))

conn.commit()
conn.close()
print("✅ Líneas sincronizadas: Nando, Lucas y el Hub ya tienen sus datos vinculados.")

import sqlite3
from datetime import datetime

DB = r"C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share\elpasaje_v2.db"
conn = sqlite3.connect(DB)
hoy = datetime.now().strftime("%Y-%m-%d")

print("Cargando primeros clientes reales...")

clientes = [
    {
        "id": "oasis_animal_agustina",
        "name": "Agustina — Oasis Animal",
        "email": "agustina@elpasaje.com",
        "password": "pendiente",
        "telefono": "",
        "tipo": "socio",
        "sector": "Bienestar animal / RSE",
        "fecha_alta": hoy,
        "activo": 1,
        "segmento": "B2B",
        "lead_source": "Familia directa",
        "potencial": "Alto",
        "canal_preferido": "WhatsApp",
        "ciudad": "Buenos Aires",
        "rubro": "Bienestar animal",
        "notas_agente": "Cunada de Alejandra. Directora Oasis Animal. Canal solidario del ecosistema. Lanzamiento conjunto con Fede.",
        "es_cliente_real": 0,
        "fecha_primer_contacto": hoy,
        "linea_interes": "Oasis Animal",
    },
    {
        "id": "vkhome_cliente",
        "name": "VK-Home — Agustina",
        "email": "vkhome@cliente.com",
        "password": "pendiente",
        "telefono": "",
        "tipo": "cliente_externo",
        "sector": "Hogar / Decoracion",
        "fecha_alta": hoy,
        "activo": 1,
        "segmento": "B2B",
        "lead_source": "Red de contactos directa",
        "potencial": "Alto",
        "canal_preferido": "WhatsApp",
        "ciudad": "Buenos Aires",
        "rubro": "Hogar y decoracion",
        "notas_agente": "Primera cliente externa real. Pedido EP-2026-001 ya cargado. Alta frecuencia potencial.",
        "es_cliente_real": 1,
        "fecha_primer_contacto": hoy,
        "linea_interes": "Magnitud 19 / Oasis del Estero",
    },
]

for c in clientes:
    existe = conn.execute("SELECT id FROM tenants WHERE id = ?", (c["id"],)).fetchone()
    if existe:
        print(f"  ⏭️  {c['name']} ya existe")
        continue
    conn.execute("""
        INSERT INTO tenants
        (id, name, email, password, telefono, tipo, sector, fecha_alta, activo,
         segmento, lead_source, potencial, canal_preferido, ciudad, rubro,
         notas_agente, es_cliente_real, fecha_primer_contacto, linea_interes)
        VALUES
        (:id,:name,:email,:password,:telefono,:tipo,:sector,:fecha_alta,:activo,
         :segmento,:lead_source,:potencial,:canal_preferido,:ciudad,:rubro,
         :notas_agente,:es_cliente_real,:fecha_primer_contacto,:linea_interes)
    """, c)
    print(f"  ✅ {c['name']} cargado")

# Tabla maquinas
conn.execute("""
    CREATE TABLE IF NOT EXISTS maquinas (
        id TEXT PRIMARY KEY,
        modelo TEXT,
        marca TEXT,
        fecha_compra TEXT,
        horas_uso_total REAL DEFAULT 0,
        costo_compra REAL,
        vida_util_horas REAL DEFAULT 10000,
        costo_hora_amortizacion REAL,
        estado TEXT DEFAULT 'activa',
        observaciones TEXT
    )
""")
existe_maq = conn.execute("SELECT id FROM maquinas WHERE id='creality_k2_plus_01'").fetchone()
if not existe_maq:
    conn.execute("""
        INSERT INTO maquinas VALUES
        ('creality_k2_plus_01','K2 Plus','Creality','2025-01-01',
         0,850000,10000,85.0,'activa',
         'Impresora principal. FDM multi-material. A cargo de Fer.')
    """)
    print("  ✅ Creality K2 Plus cargada")
else:
    print("  ⏭️  Creality K2 Plus ya existe")

# Campos en orders
for sql, desc in [
    ("ALTER TABLE orders ADD COLUMN maquina_id TEXT DEFAULT 'creality_k2_plus_01'","maquina_id en orders"),
    ("ALTER TABLE orders ADD COLUMN horas_impresion REAL","horas_impresion en orders"),
    ("ALTER TABLE orders ADD COLUMN gramos_consumidos REAL","gramos_consumidos en orders"),
    ("ALTER TABLE orders ADD COLUMN costo_real REAL","costo_real en orders"),
    ("ALTER TABLE orders ADD COLUMN fallo_impresion INTEGER DEFAULT 0","fallo_impresion en orders"),
    ("ALTER TABLE orders ADD COLUMN motivo_fallo TEXT","motivo_fallo en orders"),
]:
    try:
        conn.execute(sql)
        print(f"  ✅ {desc}")
    except sqlite3.OperationalError:
        print(f"  ⏭️  {desc} ya existe")

# Tabla senales_mercado
conn.execute("""
    CREATE TABLE IF NOT EXISTS senales_mercado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        cliente_id TEXT,
        linea TEXT,
        producto TEXT,
        reaccion TEXT,
        segmento_detectado TEXT,
        oportunidad TEXT,
        fuente TEXT,
        canal TEXT,
        procesado_por_ia INTEGER DEFAULT 0,
        notas TEXT
    )
""")
print("  ✅ Tabla senales_mercado OK")

# Tabla overhead
conn.execute("""
    CREATE TABLE IF NOT EXISTS overhead (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT,
        monto_mensual REAL,
        unidad TEXT DEFAULT 'pesos',
        categoria TEXT,
        activo INTEGER DEFAULT 1,
        fecha_alta TEXT
    )
""")
for concepto, monto, cat in [
    ('Electricidad estimada', 15000, 'Servicios'),
    ('Amortizacion Creality K2 Plus', 8500, 'Maquinaria'),
    ('Internet y nube', 5000, 'Infraestructura'),
    ('Insumos varios', 3000, 'Produccion'),
]:
    existe = conn.execute("SELECT id FROM overhead WHERE concepto=?", (concepto,)).fetchone()
    if not existe:
        conn.execute("INSERT INTO overhead (concepto,monto_mensual,categoria,fecha_alta) VALUES (?,?,?,?)",
                     (concepto, monto, cat, hoy))
        print(f"  ✅ Overhead: {concepto} ${monto:,.0f}/mes")

conn.commit()

# Resumen
print()
print("═" * 48)
print("RESUMEN FINAL:")
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for t in tablas:
    n = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"  {t[0]:<28} {n:>4} registros")

total_oh = conn.execute("SELECT SUM(monto_mensual) FROM overhead WHERE activo=1").fetchone()[0]
print(f"\nOverhead mensual total: ${total_oh:,.0f}")
print("\n✅ Todo listo. Hacé git add + commit + push para subir los cambios.")
conn.close()

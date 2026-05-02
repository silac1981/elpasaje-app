import sqlite3
import os
from datetime import datetime

# ── CONFIGURACION ──
DB_PATH = r"C:\Users\ar028883\Documents\La_Piedad_Tech_Design\magnitud19-backend-share\elpasaje_v2.db"

def ejecutar(conn, sql, desc=""):
    try:
        conn.execute(sql)
        if desc:
            print(f"  ✅ {desc}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e) or "already exists" in str(e):
            if desc:
                print(f"  ⏭️  {desc} (ya existe)")
        else:
            print(f"  ❌ {desc}: {e}")

print()
print("╔══════════════════════════════════════════════╗")
print("║  EPCC — Actualizacion Paso 1                 ║")
print("║  Segmentacion de clientes + Maquinas         ║")
print("╚══════════════════════════════════════════════╝")
print()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# ══════════════════════════════════════
# 1. AGREGAR CAMPOS A TENANTS
# ══════════════════════════════════════
print("► PASO 1: Campos de segmentacion en tenants")

campos_tenants = [
    ("ALTER TABLE tenants ADD COLUMN segmento TEXT DEFAULT 'B2C'",
     "Campo segmento (B2B / B2C / Corporativo / Institucional)"),
    ("ALTER TABLE tenants ADD COLUMN lead_source TEXT",
     "Campo lead_source (como llego el cliente)"),
    ("ALTER TABLE tenants ADD COLUMN potencial TEXT DEFAULT 'Medio'",
     "Campo potencial (Alto / Medio / Bajo)"),
    ("ALTER TABLE tenants ADD COLUMN canal_preferido TEXT",
     "Campo canal_preferido (WhatsApp / Instagram / Presencial)"),
    ("ALTER TABLE tenants ADD COLUMN ciudad TEXT DEFAULT 'Buenos Aires'",
     "Campo ciudad"),
    ("ALTER TABLE tenants ADD COLUMN rubro TEXT",
     "Campo rubro (sector del cliente)"),
    ("ALTER TABLE tenants ADD COLUMN notas_agente TEXT",
     "Campo notas_agente (observaciones del agente IA)"),
    ("ALTER TABLE tenants ADD COLUMN es_cliente_real INTEGER DEFAULT 0",
     "Flag es_cliente_real (1=compro, 0=contacto)"),
    ("ALTER TABLE tenants ADD COLUMN fecha_primer_contacto TEXT",
     "Campo fecha_primer_contacto"),
    ("ALTER TABLE tenants ADD COLUMN linea_interes TEXT",
     "Campo linea_interes (que linea le interesa)"),
]

for sql, desc in campos_tenants:
    ejecutar(conn, sql, desc)

# ══════════════════════════════════════
# 2. CARGAR PRIMEROS CLIENTES REALES
# ══════════════════════════════════════
print()
print("► PASO 2: Cargar primeros clientes reales")

hoy = datetime.now().strftime("%Y-%m-%d")

# Verificar si ya existen
existe_agustina = conn.execute(
    "SELECT id FROM tenants WHERE id = 'oasis_animal_agustina'"
).fetchone()

existe_vkhome = conn.execute(
    "SELECT id FROM tenants WHERE id = 'vkhome_cliente'"
).fetchone()

if not existe_agustina:
    conn.execute("""
        INSERT INTO tenants
        (id, name, email, password, role, segmento, lead_source,
         potencial, canal_preferido, ciudad, rubro, notas_agente,
         es_cliente_real, fecha_primer_contacto, linea_interes)
        VALUES
        ('oasis_animal_agustina',
         'Agustina — Oasis Animal',
         'agustina@elpasaje.com',
         'pendiente',
         'socio',
         'B2B',
         'Familia directa',
         'Alto',
         'WhatsApp',
         'Buenos Aires',
         'Bienestar animal / RSE',
         'Cuñada de Alejandra. Directora Oasis Animal. Lanzamiento conjunto con Fede (Oasis del Estero). Canal solidario del ecosistema.',
         0,
         ?, ?)
    """, (hoy, 'Oasis Animal'))
    print("  ✅ Agustina / Oasis Animal cargada")
else:
    print("  ⏭️  Agustina ya existe")

if not existe_vkhome:
    conn.execute("""
        INSERT INTO tenants
        (id, name, email, password, role, segmento, lead_source,
         potencial, canal_preferido, ciudad, rubro, notas_agente,
         es_cliente_real, fecha_primer_contacto, linea_interes)
        VALUES
        ('vkhome_cliente',
         'VK-Home — Agustina',
         'vkhome@cliente.com',
         'pendiente',
         'cliente_externo',
         'B2B',
         'Red de contactos directa',
         'Alto',
         'WhatsApp',
         'Buenos Aires',
         'Hogar / Decoracion',
         'Primera cliente externa real. Pedido EP-2026-001 ya cargado. Canal hogar/decoracion. Alta frecuencia potencial.',
         1,
         ?, ?)
    """, (hoy, 'Magnitud 19 / Oasis del Estero'))
    print("  ✅ VK-Home cargada como primer cliente externo real")
else:
    print("  ⏭️  VK-Home ya existe")

# ══════════════════════════════════════
# 3. CREAR TABLA MAQUINAS
# ══════════════════════════════════════
print()
print("► PASO 3: Tabla maquinas")

ejecutar(conn, """
    CREATE TABLE IF NOT EXISTS maquinas (
        id TEXT PRIMARY KEY,
        modelo TEXT NOT NULL,
        marca TEXT,
        fecha_compra TEXT,
        horas_uso_total REAL DEFAULT 0,
        costo_compra REAL,
        vida_util_horas REAL DEFAULT 10000,
        costo_hora_amortizacion REAL,
        estado TEXT DEFAULT 'activa',
        observaciones TEXT,
        fecha_ultimo_mantenimiento TEXT
    )
""", "Tabla maquinas creada")

# Cargar la Creality K2 Plus
existe_maq = conn.execute(
    "SELECT id FROM maquinas WHERE id = 'creality_k2_plus_01'"
).fetchone()

if not existe_maq:
    conn.execute("""
        INSERT INTO maquinas
        (id, modelo, marca, fecha_compra, horas_uso_total,
         costo_compra, vida_util_horas, costo_hora_amortizacion,
         estado, observaciones)
        VALUES
        ('creality_k2_plus_01',
         'K2 Plus',
         'Creality',
         '2025-01-01',
         0,
         850000,
         10000,
         85.0,
         'activa',
         'Impresora principal del estudio. FDM multi-material. A cargo de Fernando (Fer).')
    """)
    print("  ✅ Creality K2 Plus cargada")
else:
    print("  ⏭️  Creality K2 Plus ya existe")

# ══════════════════════════════════════
# 4. AGREGAR CAMPOS DE PRODUCCION A ORDERS
# ══════════════════════════════════════
print()
print("► PASO 4: Campos de produccion en orders")

campos_orders = [
    ("ALTER TABLE orders ADD COLUMN maquina_id TEXT DEFAULT 'creality_k2_plus_01'",
     "Campo maquina_id"),
    ("ALTER TABLE orders ADD COLUMN horas_impresion REAL",
     "Campo horas_impresion"),
    ("ALTER TABLE orders ADD COLUMN gramos_consumidos REAL",
     "Campo gramos_consumidos"),
    ("ALTER TABLE orders ADD COLUMN costo_real REAL",
     "Campo costo_real (calculado)"),
    ("ALTER TABLE orders ADD COLUMN fallo_impresion INTEGER DEFAULT 0",
     "Flag fallo_impresion (para ML)"),
    ("ALTER TABLE orders ADD COLUMN motivo_fallo TEXT",
     "Campo motivo_fallo (texto libre para IA)"),
]

for sql, desc in campos_orders:
    ejecutar(conn, sql, desc)

# ══════════════════════════════════════
# 5. CREAR TABLA SENALES_MERCADO
# ══════════════════════════════════════
print()
print("► PASO 5: Tabla senales_mercado")

ejecutar(conn, """
    CREATE TABLE IF NOT EXISTS senales_mercado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
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
""", "Tabla senales_mercado creada")

# ══════════════════════════════════════
# 6. CREAR TABLA OVERHEAD
# ══════════════════════════════════════
print()
print("► PASO 6: Tabla overhead (costos indirectos)")

ejecutar(conn, """
    CREATE TABLE IF NOT EXISTS overhead (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        monto_mensual REAL,
        unidad TEXT DEFAULT 'pesos',
        categoria TEXT,
        activo INTEGER DEFAULT 1,
        fecha_alta TEXT,
        notas TEXT
    )
""", "Tabla overhead creada")

# Cargar costos base conocidos
costos_base = [
    ('Electricidad estimada', 15000, 'pesos', 'Servicios'),
    ('Amortizacion Creality K2 Plus', 8500, 'pesos', 'Maquinaria'),
    ('Internet y nube', 5000, 'pesos', 'Infraestructura'),
    ('Insumos varios (cinta, solvente, etc)', 3000, 'pesos', 'Produccion'),
]

for concepto, monto, unidad, categoria in costos_base:
    existe = conn.execute(
        "SELECT id FROM overhead WHERE concepto = ?", (concepto,)
    ).fetchone()
    if not existe:
        conn.execute("""
            INSERT INTO overhead (concepto, monto_mensual, unidad, categoria, fecha_alta)
            VALUES (?, ?, ?, ?, ?)
        """, (concepto, monto, unidad, categoria, hoy))
        print(f"  ✅ Overhead: {concepto} — ${monto:,.0f}/mes")

conn.commit()

# ══════════════════════════════════════
# RESUMEN FINAL
# ══════════════════════════════════════
print()
print("═" * 50)
print("RESUMEN DEL SISTEMA ACTUALIZADO:")
print("═" * 50)

tablas = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print(f"\nTablas en la DB ({len(tablas)} total):")
for t in tablas:
    count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"  • {t[0]:<25} {count:>5} registros")

print()
print("Clientes reales cargados:")
clientes = conn.execute("""
    SELECT name, segmento, lead_source, potencial, linea_interes
    FROM tenants
    WHERE role IN ('cliente_externo', 'socio')
    AND es_cliente_real IS NOT NULL
    ORDER BY fecha_primer_contacto DESC
""").fetchall()

for c in clientes:
    print(f"  • {c[0]}")
    print(f"    Segmento: {c[1]} | Fuente: {c[2]} | Potencial: {c[3]}")
    print(f"    Linea: {c[4]}")

print()
print("Maquinas registradas:")
maquinas = conn.execute("SELECT modelo, marca, estado FROM maquinas").fetchall()
for m in maquinas:
    print(f"  • {m[1]} {m[0]} — {m[2]}")

print()
overhead_total = conn.execute(
    "SELECT SUM(monto_mensual) FROM overhead WHERE activo = 1"
).fetchone()[0]
print(f"Overhead mensual total: ${overhead_total:,.0f}")

conn.close()
print()
print("✅ PASO 1 COMPLETADO")
print("   Proximos pasos:")
print("   • Hacer git add + commit + push del elpasaje_v2.db")
print("   • Cargar mas clientes a medida que llegan")
print("   • Cuando tengas 20+ clientes: activar modulo de segmentacion IA")

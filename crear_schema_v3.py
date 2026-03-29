"""
crear_schema_v3.py
==================
Crea el esquema completo de elpasaje_v2.db desde cero.
ADVERTENCIA: borra y recrea todas las tablas. Solo usar cuando no hay datos reales.

Ejecutar desde la carpeta del proyecto:
    python crear_schema_v3.py
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")
engine  = create_engine(f"sqlite:///{DB_PATH}")

HOY = datetime.now().strftime("%Y-%m-%d")

TABLAS = [
    # ─────────────────────────────────────────────
    #  NÚCLEO DEL ECOSISTEMA
    # ─────────────────────────────────────────────
    ("tenants", """
        CREATE TABLE tenants (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            telefono    TEXT,
            tipo        TEXT DEFAULT 'familia',   -- 'familia' | 'b2b' | 'admin'
            sector      TEXT,                     -- área dentro de la empresa
            fecha_alta  TEXT DEFAULT CURRENT_DATE,
            activo      INTEGER DEFAULT 1
        )
    """),

    ("materials", """
        CREATE TABLE materials (
            material_id     TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            tipo            TEXT,                 -- 'PLA' | 'PETG' | 'TPU'
            color           TEXT,
            proveedor       TEXT,
            stock_gr        REAL DEFAULT 0,
            cost_kg         REAL DEFAULT 0,
            stock_minimo_gr INTEGER DEFAULT 200,
            fecha_compra    TEXT,
            precio_compra   REAL,                 -- precio real pagado (para trazabilidad)
            activo          INTEGER DEFAULT 1
        )
    """),

    ("products", """
        CREATE TABLE products (
            sku                  TEXT PRIMARY KEY,
            client_id            TEXT NOT NULL REFERENCES tenants(id),
            material_id          TEXT REFERENCES materials(material_id),
            name                 TEXT NOT NULL,
            description          TEXT,
            categoria            TEXT,            -- 'Taller' | 'Oficina' | 'Tech' | 'General'
            color                TEXT,
            price                REAL DEFAULT 0,
            weight_gr            REAL DEFAULT 0,
            tiempo_impresion_min INTEGER DEFAULT 0,
            stock                INTEGER DEFAULT 0,
            imagen_url           TEXT,
            fecha_alta           TEXT DEFAULT CURRENT_DATE,
            activo               INTEGER DEFAULT 1
        )
    """),

    ("orders", """
        CREATE TABLE orders (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id         TEXT NOT NULL REFERENCES tenants(id),
            status            TEXT DEFAULT 'Pendiente',  -- 'Pendiente'|'En Proceso'|'Listo'|'Cancelado'
            date              TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega_est TEXT,
            notas             TEXT,
            color_pedido      TEXT
        )
    """),

    ("order_items", """
        CREATE TABLE order_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES orders(id),
            product_sku     TEXT NOT NULL REFERENCES products(sku),
            cantidad        INTEGER DEFAULT 1,
            precio_unitario REAL DEFAULT 0        -- precio al momento del pedido
        )
    """),

    # ─────────────────────────────────────────────
    #  TRAZABILIDAD TEMPORAL (para análisis y predicción)
    # ─────────────────────────────────────────────
    ("price_history", """
        CREATE TABLE price_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku     TEXT NOT NULL REFERENCES products(sku),
            precio_anterior REAL,
            precio_nuevo    REAL,
            fecha           TEXT DEFAULT CURRENT_DATE,
            motivo          TEXT                  -- 'ajuste inflacion' | 'rediseno' | etc
        )
    """),

    ("stock_movements", """
        CREATE TABLE stock_movements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT NOT NULL REFERENCES products(sku),
            tipo        TEXT NOT NULL,            -- 'entrada'|'venta'|'ajuste'|'merma'
            cantidad    INTEGER NOT NULL,
            fecha       TEXT DEFAULT CURRENT_TIMESTAMP,
            referencia  TEXT                      -- nro de pedido u observación
        )
    """),

    ("production_log", """
        CREATE TABLE production_log (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id          INTEGER REFERENCES orders(id),
            product_sku       TEXT NOT NULL REFERENCES products(sku),
            material_id       TEXT REFERENCES materials(material_id),
            gramos_usados     REAL,
            tiempo_real_min   INTEGER,
            fecha_inicio      TEXT,
            fecha_fin         TEXT,
            resultado         TEXT DEFAULT 'ok'   -- 'ok'|'fallo'|'reimpresion'
        )
    """),

    # ─────────────────────────────────────────────
    #  CONTEXTO DE VENTAS (para modelos predictivos)
    # ─────────────────────────────────────────────
    ("sales_context", """
        CREATE TABLE sales_context (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES orders(id),
            canal           TEXT,                 -- 'presencial'|'whatsapp'|'instagram'
            sector_empresa  TEXT,                 -- 'hangar_a'|'oficina_economica'|etc
            fue_con_muestra INTEGER DEFAULT 0,    -- 1=sí llevó muestra física
            referido_por    TEXT,                 -- client_id del referente o null
            primera_compra  INTEGER DEFAULT 0     -- 1=primera compra del cliente
        )
    """),

    # ─────────────────────────────────────────────
    #  FONDOS SOLIDARIOS
    # ─────────────────────────────────────────────
    ("donations", """
        CREATE TABLE donations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fondo       TEXT NOT NULL,
            monto       REAL NOT NULL,
            tipo        TEXT,                     -- 'urna'|'qr'|'redondeo'|'producto'
            descripcion TEXT,
            fecha       TEXT DEFAULT CURRENT_DATE
        )
    """),
]

# ─────────────────────────────────────────────────
#  DATOS INICIALES
# ─────────────────────────────────────────────────
TENANTS_INICIALES = [
    ("admin",            "Alejandra",                         "admin@elpasaje.com",       "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  None,          "admin",   "Direccion Economica", HOY, 1),
    ("olivia_coquette",  "Olivia",                            "coquette@elpasaje.com",    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "familia", None,                  HOY, 1),
    ("francisco_sport",  "Francisco",                         "fsport@elpasaje.com",      "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "familia", None,                  HOY, 1),
    ("constantino_tech", "Constantino",                       "coretech@elpasaje.com",    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "familia", None,                  HOY, 1),
    ("aviation",         "Fernando Gomez Aguilera (Nando)",   "aviation@elpasaje.com",    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "b2b",     "Mantenimiento",       HOY, 1),
    ("oasis_animal",     "Oasis Animal",                      "oasisanimal@elpasaje.com", "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "b2b",     None,                  HOY, 1),
    ("oasis_del_estero", "Oasis del Estero",                  "oasisestero@elpasaje.com", "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "b2b",     None,                  HOY, 1),
    ("pharma_delux",     "Pharma DeLux",                      "pharma@elpasaje.com",      "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",    None,          "b2b",     None,                  HOY, 1),
]

MATERIALS_INICIALES = [
    # material_id         name                    tipo    color              proveedor   stock_gr  cost_kg  stock_min  fecha_compra  precio_compra
    ("petg_gris",        "PETG Gris Mecánico",   "PETG", "Gris Mecánico",   None,       800,      2350,    200,       HOY,          2350),
    ("petg_naranja",     "PETG Naranja Seguridad","PETG", "Naranja Seguridad",None,      600,      2400,    200,       HOY,          2400),
    ("pla_seda_azul",    "PLA Seda Azul Aerolínea","PLA", "Azul Aerolínea",  None,       500,      2600,    200,       HOY,          2600),
    ("pla_seda_gris",    "PLA Seda Gris Acero",  "PLA",  "Gris Acero",      None,       400,      2550,    200,       HOY,          2550),
    ("pla_rosa",         "PLA Rosa Coquette",    "PLA",  "Rosa",            None,       700,      2400,    200,       HOY,          2400),
    ("pla_blanco",       "PLA Blanco",           "PLA",  "Blanco",          None,       1000,     2200,    300,       HOY,          2200),
    ("pla_negro",        "PLA Negro",            "PLA",  "Negro",           None,       1000,     2200,    300,       HOY,          2200),
]

PRODUCTS_AVIATION = [
    # sku         client  material         name                         desc                                                          cat       color              price   weight  tiempo  stock
    ("AVP-001", "aviation", "petg_gris",    "Rampa-Safe",               "Soporte celular/radio con base pesada. Legajo en relieve.",   "Taller", "Gris Mecánico",   4500,   85,     45,     5),
    ("AVP-002", "aviation", "petg_gris",    "Mate-Carro",               "Accesorio para carro personal. Sostiene mate y termo.",        "Taller", "Gris Mecánico",   3800,   70,     35,     5),
    ("AVP-003", "aviation", "petg_naranja", "Clip Seguridad EPP",       "Clip naranja alta visibilidad para EPP personal.",             "Taller", "Naranja Seguridad",2200,  35,     18,     8),
    ("AVP-004", "aviation", "petg_gris",    "Porta-Credencial Pro",     "Funda rígida 3D con legajo. Protege tarjeta magnética.",       "Taller", "Gris Mecánico",   2800,   45,     22,     8),
    ("AVP-005", "aviation", "petg_gris",    "Organizador Banco Personal","Bandeja modular: llaves, documentos y mate.",                 "Taller", "Gris Mecánico",   5500,   120,    60,     3),
    ("AVP-006", "aviation", "pla_seda_azul","Dock Checklist",           "Soporte post-its y lapicera. Forma de pista de aterrizaje.",   "Oficina","Azul Aerolínea",  4200,   75,     38,     5),
    ("AVP-007", "aviation", "pla_seda_azul","Organizador Fuselaje",     "Clips forma remaches aeronáuticos para cables escritorio.",    "Oficina","Azul Aerolínea",  3500,   60,     30,     6),
    ("AVP-008", "aviation", "pla_seda_gris","Torre de Control",         "Soporte auriculares inspirado en torres EZE/AEP.",             "Oficina","Gris Acero",      5800,   110,    55,     3),
    ("AVP-009", "aviation", "pla_seda_azul","Placa Analista Senior",    "Placa escritorio con nombre y legajo. Estética cabina.",       "Oficina","Azul Aerolínea",  4800,   90,     45,     4),
    ("AVP-010", "aviation", "pla_seda_gris","Portabotella Aero",        "Soporte botella/termo con base antideslizante.",               "Oficina","Gris Acero",      3200,   55,     28,     6),
    ("AVP-011", "aviation", "pla_seda_gris","Soporte Monitor Desk",     "Elevador de monitor con bandeja inferior.",                    "Tech",   "Gris Acero",      7500,   180,    90,     3),
    ("AVP-012", "aviation", "petg_gris",    "Portacelular 360",         "Porta celular articulado 360° base pesada antideslizante.",    "Tech",   "Gris Mecánico",   3800,   65,     33,     6),
    ("AVP-013", "aviation", "pla_seda_gris","Hub Organizador USB",      "Soporte para hub USB y cables de carga.",                      "Tech",   "Gris Acero",      4500,   95,     48,     4),
]

# ─────────────────────────────────────────────────
#  EJECUCIÓN
# ─────────────────────────────────────────────────
with engine.connect() as conn:

    print("🗑️  Eliminando tablas anteriores...")
    # Orden inverso para respetar foreign keys
    for tabla, _ in reversed(TABLAS):
        conn.execute(text(f"DROP TABLE IF EXISTS {tabla}"))
    print("   OK\n")

    print("🏗️  Creando esquema v3...")
    for tabla, ddl in TABLAS:
        conn.execute(text(ddl))
        print(f"   ✅ {tabla}")
    print()

    print("👥 Insertando tenants...")
    for row in TENANTS_INICIALES:
        conn.execute(text("""
            INSERT INTO tenants (id, name, email, password, telefono, tipo, sector, fecha_alta, activo)
            VALUES (:id, :name, :email, :pwd, :tel, :tipo, :sector, :fecha, :activo)
        """), dict(zip(["id","name","email","pwd","tel","tipo","sector","fecha","activo"], row)))
        print(f"   ✅ {row[0]} — {row[1]}")
    print()

    print("🧵 Insertando materiales...")
    for row in MATERIALS_INICIALES:
        conn.execute(text("""
            INSERT INTO materials
            (material_id, name, tipo, color, proveedor, stock_gr, cost_kg, stock_minimo_gr, fecha_compra, precio_compra)
            VALUES (:mid, :name, :tipo, :color, :prov, :stock, :cost, :min, :fcompra, :pcompra)
        """), dict(zip(["mid","name","tipo","color","prov","stock","cost","min","fcompra","pcompra"], row)))
        print(f"   ✅ {row[0]} — {row[1]}")
    print()

    print("✈️  Insertando productos Aviation Pro...")
    for row in PRODUCTS_AVIATION:
        conn.execute(text("""
            INSERT INTO products
            (sku, client_id, material_id, name, description, categoria, color,
             price, weight_gr, tiempo_impresion_min, stock)
            VALUES (:sku,:cid,:mid,:name,:desc,:cat,:color,:price,:weight,:tiempo,:stock)
        """), dict(zip(["sku","cid","mid","name","desc","cat","color","price","weight","tiempo","stock"], row)))
        print(f"   ✅ {row[0]} — {row[3]}")
    print()

    conn.commit()

print("=" * 50)
print("🚀 Esquema v3 creado exitosamente")
print(f"   Base de datos: {DB_PATH}")
print(f"   Tablas: {len(TABLAS)}")
print(f"   Tenants: {len(TENANTS_INICIALES)}")
print(f"   Materiales: {len(MATERIALS_INICIALES)}")
print(f"   Productos Aviation Pro: {len(PRODUCTS_AVIATION)}")
print()
print("   Credenciales:")
print("   admin@elpasaje.com    / admin123")
print("   aviation@elpasaje.com / 123")
print("   (resto de socios: email@elpasaje.com / 123)")
print("=" * 50)

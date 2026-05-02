"""
crear_schema_v3.py
==================
DOS MODOS DE USO:

  IMPORTADO POR main.py (Streamlit Cloud / producción):
      from crear_schema_v3 import init_schema
      init_schema()   # crea tablas solo si no existen — no borra datos

  SCRIPT MANUAL (instalación desde cero, solo en local):
      python crear_schema_v3.py
      → DROP + CREATE + seed completo. BORRA datos existentes.
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DIR, "elpasaje_v2.db")
HOY     = datetime.now().strftime("%Y-%m-%d")

# ─────────────────────────────────────────────────────────
#  DDL — todas las tablas con IF NOT EXISTS
#  (funciona tanto para init_schema como para crear_schema)
# ─────────────────────────────────────────────────────────

TABLAS = [
    ("tenants", """
        CREATE TABLE IF NOT EXISTS tenants (
            id                    TEXT PRIMARY KEY,
            name                  TEXT NOT NULL,
            email                 TEXT UNIQUE NOT NULL,
            password              TEXT NOT NULL,
            telefono              TEXT,
            tipo                  TEXT DEFAULT 'familia',
            sector                TEXT,
            fecha_alta            TEXT DEFAULT CURRENT_DATE,
            activo                INTEGER DEFAULT 1,
            segmento              TEXT,
            lead_source           TEXT,
            potencial             TEXT,
            canal_preferido       TEXT,
            ciudad                TEXT DEFAULT 'Buenos Aires',
            rubro                 TEXT,
            notas_agente          TEXT,
            es_cliente_real       INTEGER DEFAULT 0,
            fecha_primer_contacto TEXT,
            linea_interes         TEXT
        )
    """),

    ("tenant_lineas", """
        CREATE TABLE IF NOT EXISTS tenant_lineas (
            tenant_id  TEXT NOT NULL REFERENCES tenants(id),
            linea_id   TEXT NOT NULL REFERENCES tenants(id),
            PRIMARY KEY (tenant_id, linea_id)
        )
    """),

    ("materials", """
        CREATE TABLE IF NOT EXISTS materials (
            material_id     TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            tipo            TEXT,
            color           TEXT,
            proveedor       TEXT,
            stock_gr        REAL DEFAULT 0,
            cost_kg         REAL DEFAULT 0,
            stock_minimo_gr INTEGER DEFAULT 200,
            fecha_compra    TEXT,
            precio_compra   REAL,
            activo          INTEGER DEFAULT 1
        )
    """),

    ("products", """
        CREATE TABLE IF NOT EXISTS products (
            sku                  TEXT PRIMARY KEY,
            client_id            TEXT NOT NULL REFERENCES tenants(id),
            material_id          TEXT REFERENCES materials(material_id),
            name                 TEXT NOT NULL,
            description          TEXT,
            categoria            TEXT,
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
        CREATE TABLE IF NOT EXISTS orders (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id                 TEXT NOT NULL REFERENCES tenants(id),
            status                    TEXT DEFAULT 'Pendiente',
            date                      TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega_est         TEXT,
            notas                     TEXT,
            color_pedido              TEXT,
            maquina_id                TEXT DEFAULT 'creality_k2_plus_01',
            horas_impresion           REAL,
            gramos_consumidos         REAL,
            costo_real                REAL,
            fallo_impresion           INTEGER DEFAULT 0,
            motivo_fallo              TEXT,
            referencia_archivo        TEXT,
            fecha_entrega_solicitada  TEXT
        )
    """),

    ("order_items", """
        CREATE TABLE IF NOT EXISTS order_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES orders(id),
            product_sku     TEXT NOT NULL REFERENCES products(sku),
            cantidad        INTEGER DEFAULT 1,
            precio_unitario REAL DEFAULT 0
        )
    """),

    ("price_history", """
        CREATE TABLE IF NOT EXISTS price_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku     TEXT NOT NULL REFERENCES products(sku),
            precio_anterior REAL,
            precio_nuevo    REAL,
            fecha           TEXT DEFAULT CURRENT_DATE,
            motivo          TEXT
        )
    """),

    ("stock_movements", """
        CREATE TABLE IF NOT EXISTS stock_movements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT NOT NULL REFERENCES products(sku),
            tipo        TEXT NOT NULL,
            cantidad    INTEGER NOT NULL,
            fecha       TEXT DEFAULT CURRENT_TIMESTAMP,
            referencia  TEXT
        )
    """),

    ("production_log", """
        CREATE TABLE IF NOT EXISTS production_log (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id          INTEGER REFERENCES orders(id),
            product_sku       TEXT NOT NULL REFERENCES products(sku),
            material_id       TEXT REFERENCES materials(material_id),
            gramos_usados     REAL,
            tiempo_real_min   INTEGER,
            fecha_inicio      TEXT,
            fecha_fin         TEXT,
            resultado         TEXT DEFAULT 'ok'
        )
    """),

    ("sales_context", """
        CREATE TABLE IF NOT EXISTS sales_context (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES orders(id),
            canal           TEXT,
            sector_empresa  TEXT,
            fue_con_muestra INTEGER DEFAULT 0,
            referido_por    TEXT,
            primera_compra  INTEGER DEFAULT 0
        )
    """),

    ("donations", """
        CREATE TABLE IF NOT EXISTS donations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fondo       TEXT NOT NULL,
            monto       REAL NOT NULL,
            tipo        TEXT,
            descripcion TEXT,
            fecha       TEXT DEFAULT CURRENT_DATE
        )
    """),

    ("log_agente", """
        CREATE TABLE IF NOT EXISTS log_agente (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto        TEXT DEFAULT 'ElPasaje',
            tipo            TEXT NOT NULL,
            senal           TEXT NOT NULL,
            dato_observado  TEXT,
            accion_sugerida TEXT,
            etiquetas       TEXT,
            confianza       REAL DEFAULT 0.7,
            origen          TEXT DEFAULT 'agente',
            fecha           TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """),

    ("senales_mercado", """
        CREATE TABLE IF NOT EXISTS senales_mercado (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha            TEXT DEFAULT CURRENT_DATE,
            cliente_id       TEXT,
            linea            TEXT,
            producto         TEXT,
            reaccion         TEXT,
            oportunidad      TEXT,
            fuente           TEXT,
            canal            TEXT,
            notas            TEXT,
            procesado_por_ia INTEGER DEFAULT 0
        )
    """),
]

# ─────────────────────────────────────────────────────────
#  DATOS INICIALES
# ─────────────────────────────────────────────────────────

TENANTS_INICIALES = [
    ("admin",            "Alejandra",                          "admin@elpasaje.com",        "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9", None, "admin",         "Direccion Economica",              HOY, 1, None,  None,        None,   None,           "Buenos Aires",        None,                       None, 1, HOY, "Todas"),
    ("olivia_coquette",  "Olivia",                             "coquette@elpasaje.com",     "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "familia",       None,                               HOY, 1, "B2C", "Familia",   "Alto", "Presencial",   "Buenos Aires",        "Estética",                 None, 1, HOY, "Coquette"),
    ("francisco_sport",  "Francisco",                          "fsport@elpasaje.com",       "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "familia",       None,                               HOY, 1, "B2C", "Familia",   "Alto", "Presencial",   "Buenos Aires",        "Deportes",                 None, 1, HOY, "Francisco Sport"),
    ("constantino_tech", "Constantino",                        "coretech@elpasaje.com",     "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "familia",       None,                               HOY, 1, "B2C", "Familia",   "Alto", "Presencial",   "Buenos Aires",        "Tecnología",               None, 1, HOY, "Core Tech"),
    ("aviation",         "Fernando Gomez Aguilera (Nando)",    "aviation@elpasaje.com",     "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "b2b",           "Mantenimiento AA",                 HOY, 1, "B2B", "Red Nando", "Alto", "WhatsApp",     "Buenos Aires",        "Aeronáutico",              None, 1, HOY, "Aviation Pro"),
    ("oasis_animal",     "Oasis Animal",                       "oasisanimal@elpasaje.com",  "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "b2b",           None,                               HOY, 1, "B2B", "Red Nando", "Alto", "WhatsApp",     "Buenos Aires",        "Veterinario",              None, 1, HOY, "Oasis Animal"),
    ("oasis_del_estero", "Oasis del Estero",                   "oasisestero@elpasaje.com",  "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "b2b",           None,                               HOY, 1, "B2B", "Red Nando", "Medio","WhatsApp",     "Santiago del Estero", None,                       None, 1, HOY, "Oasis del Estero"),
    ("pharma_delux",     "Pharma DeLux",                       "pharma@elpasaje.com",       "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "b2b",           None,                               HOY, 1, "B2B", "Directo",   "Alto", "Email",        "Buenos Aires",        "Farmacéutico",             None, 1, HOY, "Pharma DeLux"),
    ("fer_produccion",   "Fernando (Fer)",                     "fer@elpasaje.com",          "a29461d9796a45974014a214c0ece938a5f9dcd8799f26b26c34d3e8adf31c69",  None, "produccion",    "Fabricacion y Materiales",         HOY, 1, None,  None,        None,   "Presencial",   "Buenos Aires",        None,                       None, 1, HOY, None),
    ("agustina",         "Agustina",                           "agustina@elpasaje.com",     "1baedd25059490937a8f7a52dbaf5a7c168bc49f5bac0d7bc48bd6b58a84a421",  None, "socio_multi",   None,                               HOY, 1, "B2B", "Directo",   "Alto", "WhatsApp",     "Buenos Aires",        "Decoracion / Veterinaria", None, 1, HOY, "Oasis Animal + VK-Home"),
    ("vkhome_cliente",   "VK-Home / Agustina",                 "vkhome@cliente.com",        "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  None, "cliente_externo",None,                             HOY, 1, "B2B", "Directo",   "Alto", "Presencial",   "Buenos Aires",        "Decoracion",               None, 1, HOY, "VK-Home"),
]

TENANT_LINEAS_INICIALES = [
    ("agustina", "oasis_animal"),
    ("agustina", "vkhome_cliente"),
]

MATERIALS_INICIALES = [
    ("petg_gris",     "PETG Gris Mecánico",     "PETG", "Gris Mecánico",    None, 800,  2350, 200, HOY, 2350),
    ("petg_naranja",  "PETG Naranja Seguridad",  "PETG", "Naranja Seguridad",None, 600,  2400, 200, HOY, 2400),
    ("pla_seda_azul", "PLA Seda Azul Aerolínea", "PLA",  "Azul Aerolínea",   None, 500,  2600, 200, HOY, 2600),
    ("pla_seda_gris", "PLA Seda Gris Acero",     "PLA",  "Gris Acero",       None, 400,  2550, 200, HOY, 2550),
    ("pla_rosa",      "PLA Rosa Coquette",        "PLA",  "Rosa",             None, 700,  2400, 200, HOY, 2400),
    ("pla_blanco",    "PLA Blanco",               "PLA",  "Blanco",           None, 1000, 2200, 300, HOY, 2200),
    ("pla_negro",     "PLA Negro",                "PLA",  "Negro",            None, 1000, 2200, 300, HOY, 2200),
]

PRODUCTS_AVIATION = [
    ("AVP-001", "aviation", "petg_gris",    "Rampa-Safe",                "Soporte celular/radio con base pesada. Legajo en relieve.",    "Taller", "Gris Mecánico",    4500, 85,  45, 5),
    ("AVP-002", "aviation", "petg_gris",    "Mate-Carro",                "Accesorio para carro personal. Sostiene mate y termo.",         "Taller", "Gris Mecánico",    3800, 70,  35, 5),
    ("AVP-003", "aviation", "petg_naranja", "Clip Seguridad EPP",        "Clip naranja alta visibilidad para EPP personal.",              "Taller", "Naranja Seguridad", 2200, 35,  18, 8),
    ("AVP-004", "aviation", "petg_gris",    "Porta-Credencial Pro",      "Funda rígida 3D con legajo. Protege tarjeta magnética.",        "Taller", "Gris Mecánico",    2800, 45,  22, 8),
    ("AVP-005", "aviation", "petg_gris",    "Organizador Banco Personal", "Bandeja modular: llaves, documentos y mate.",                  "Taller", "Gris Mecánico",    5500, 120, 60, 3),
    ("AVP-006", "aviation", "pla_seda_azul","Dock Checklist",            "Soporte post-its y lapicera. Forma de pista de aterrizaje.",    "Oficina","Azul Aerolínea",   4200, 75,  38, 5),
    ("AVP-007", "aviation", "pla_seda_azul","Organizador Fuselaje",      "Clips forma remaches aeronáuticos para cables escritorio.",     "Oficina","Azul Aerolínea",   3500, 60,  30, 6),
    ("AVP-008", "aviation", "pla_seda_gris","Torre de Control",          "Soporte auriculares inspirado en torres EZE/AEP.",              "Oficina","Gris Acero",       5800, 110, 55, 3),
    ("AVP-009", "aviation", "pla_seda_azul","Placa Analista Senior",     "Placa escritorio con nombre y legajo. Estética cabina.",        "Oficina","Azul Aerolínea",   4800, 90,  45, 4),
    ("AVP-010", "aviation", "pla_seda_gris","Portabotella Aero",         "Soporte botella/termo con base antideslizante.",                "Oficina","Gris Acero",       3200, 55,  28, 6),
    ("AVP-011", "aviation", "pla_seda_gris","Soporte Monitor Desk",      "Elevador de monitor con bandeja inferior.",                     "Tech",   "Gris Acero",       7500, 180, 90, 3),
    ("AVP-012", "aviation", "petg_gris",    "Portacelular 360",          "Porta celular articulado 360° base pesada antideslizante.",     "Tech",   "Gris Mecánico",    3800, 65,  33, 6),
    ("AVP-013", "aviation", "pla_seda_gris","Hub Organizador USB",       "Soporte para hub USB y cables de carga.",                       "Tech",   "Gris Acero",       4500, 95,  48, 4),
]

# (sku, client_id, material_id, name, description, categoria, color, price, weight_gr, tiempo_min, stock)
PRODUCTS_SOCIOS = [
    # ── COQUETTE (olivia_coquette) ──────────────────────────
    ("COQ-MON-001","olivia_coquette","pla_rosa",   "Mono Textil Silk",         "Mono artesanal impresion 3D acabado seda",                  "accesorios","#F9A8D4",1500, 22,  35, 5),
    ("COQ-MON-002","olivia_coquette","pla_rosa",   "Monedero Silk Coquette",   "Monedero 3D cierre magnetico acabado silk",                 "accesorios","#F9A8D4",2800, 60,  90, 3),
    ("COQ-LLA-001","olivia_coquette","pla_rosa",   "Llavero Peonia",           "Llavero floral detalle fino",                               "accesorios","#F9A8D4",1200, 15,  25, 8),
    ("COQ-ARG-001","olivia_coquette","pla_rosa",   "Argolla Coquette",         "Aro decorativo 3D personalizable",                         "joyeria",   "#F9A8D4",1800, 20,  30, 4),
    ("COQ-PRE-001","olivia_coquette","pla_rosa",   "Prendedor Floral",         "Prendedor 3D estilo romantico",                            "accesorios","#F9A8D4",1400, 18,  28, 6),
    ("COQ-CAJ-001","olivia_coquette","pla_rosa",   "Cajita Corazon",           "Cajita regalo 3D acabado mate",                            "regaleria", "#F9A8D4",2200, 45,  65, 3),
    ("COQ-XVA-001","olivia_coquette","pla_rosa",   "Kit Quinceanyera",         "Set 3 piezas personalizado XV anios",                      "especiales","#F9A8D4",4500, 120, 180,2),
    # ── SPORT (francisco_sport) ─────────────────────────────
    ("FZ-CAP-001", "francisco_sport","pla_negro",  "Cap-Hanger Pro",           "Soporte aerodinamico para gorras no deforma la visera",     "deportivo", "#F97316",1800, 45,  60, 4),
    ("FZ-PFX-001", "francisco_sport","pla_negro",  "Parche Flexible",          "Aplique 3D para mochila/campera personalizable",            "identidad", "#F97316",900,  25,  35, 10),
    ("FZ-GMR-001", "francisco_sport","pla_negro",  "Aplique Gamer",            "Soporte auriculares sello El Pasaje escritorio gamer",      "gamer",     "#F97316",1200, 30,  45, 6),
    ("FZ-TRO-001", "francisco_sport","pla_negro",  "Trofeo Mini",              "Trofeo impreso personalizable nombre y deporte",            "trofeos",   "#F97316",2200, 65,  90, 3),
    ("FZ-NUM-001", "francisco_sport","pla_negro",  "Numero de Camiseta",       "Numero 3D rigido para camiseta o mochila",                  "identidad", "#F97316",600,  12,  18, 20),
    ("FZ-ORC-001", "francisco_sport","pla_negro",  "Organizador Cancha",       "Soporte pizarron tactico mini para escritorio",             "entrenamiento","#F97316",3900,95, 130,2),
    # ── CORE TECH (constantino_tech) ────────────────────────
    ("CT-SIM-001", "constantino_tech","petg_gris", "Soporte Instrumento Medicion","Base calibres micrometros laboratorio escuela",          "educativo", "#64748B",2400, 70,  95, 4),
    ("CT-GAB-001", "constantino_tech","petg_gris", "Gabinete Microelectronica","Carcasa Arduino/ESP32/RaspberryPi",                         "electronica","#64748B",3800, 100, 140,3),
    ("CT-ORG-001", "constantino_tech","petg_gris", "Organizador Anti-Estatico","Bandeja componentes electronicos anti-ESD",                 "electronica","#64748B",4200, 110, 155,2),
    ("CT-KAI-001", "constantino_tech","petg_gris", "Organizador Kaizen",       "Sistema modular 5S estacion de trabajo",                   "productividad","#64748B",5500,150,210,2),
    ("CT-CUB-001", "constantino_tech","petg_gris", "Cubo Infinito Magnetico",  "Cubo articulado 8 segmentos imanes integrados",             "juguete",   "#64748B",3800, 90,  125,3),
    ("CT-RPI-001", "constantino_tech","petg_gris", "Case Raspberry Pi 5",      "Carcasa ventilada RPi5 soporte activo",                     "electronica","#64748B",4500, 120, 165,2),
    # ── PHARMA DELUX (pharma_delux) ─────────────────────────
    ("PD-ORG-001", "pharma_delux",   "pla_blanco", "Organizador Consultorio",  "Soporte instrumental medico escritorio consultorio",        "medico",    "#FBBF24",5200, 140, 195,2),
    ("PD-ORL-001", "pharma_delux",   "pla_blanco", "Organizador con Logo Lab", "Organizador con logo laboratorio farmaceutico",             "medico",    "#FBBF24",6000, 155, 215,2),
    ("PD-PAS-001", "pharma_delux",   "pla_blanco", "Porta-Pastillas Semanal",  "Pastillero 7 compartimentos etiquetado",                   "salud",     "#FBBF24",1800, 50,  70, 8),
    ("PD-MUE-001", "pharma_delux",   "pla_blanco", "Muestrero Medico",         "Soporte tarjetas muestras medicas escritorio",              "medico",    "#FBBF24",2800, 75,  105,4),
    ("PD-SER-001", "pharma_delux",   "pla_blanco", "Soporte Seringa",          "Porta-jeringas organizador tecnico",                       "medico",    "#FBBF24",3800, 100, 140,3),
    ("PD-GIF-001", "pharma_delux",   "pla_blanco", "Gift Set Laboratorio",     "Kit 3 piezas personalizado para laboratorio",               "gift",      "#FBBF24",4500, 125, 175,2),
    # ── OASIS DEL ESTERO (oasis_del_estero) ─────────────────
    ("OE-MAC-001", "oasis_del_estero","pla_blanco","Maceta Modular",           "Maceta geometrica minimalista drenaje integrado apilable",  "hogar",     "#34D399",1200, 55,  75, 6),
    ("OE-MAC-002", "oasis_del_estero","pla_blanco","Maceta Colgante",          "Sistema sujecion integrado balcon/ventana",                 "hogar",     "#34D399",1500, 65,  90, 5),
    ("OE-ID-001",  "oasis_del_estero","pla_blanco","Identificador Planta",     "Tag nombre planta personalizable resistente al agua",       "jardin",    "#34D399",400,  10,  15, 25),
    ("OE-REG-001", "oasis_del_estero","pla_blanco","Regadera Decorativa Mini", "Regadera impresa 3D ornamental",                           "jardin",    "#34D399",800,  35,  50, 8),
    ("OE-SOP-001", "oasis_del_estero","pla_blanco","Soporte Macetas Pared",    "Rack impreso 3 macetas en linea para pared",                "hogar",     "#34D399",2200, 90,  125,3),
    ("OE-FAU-001", "oasis_del_estero","pla_blanco","Figura Fauna Local",       "Animal chaquenio impreso decorativo coleccionable",         "arte",      "#34D399",2800, 80,  115,4),
    # ── OASIS ANIMAL (oasis_animal) — ya existe, OR IGNORE protege
    ("OAS-COM-001","oasis_animal",   "pla_blanco", "Soporte Comedero con Cuenco","Soporte impreso patita para comedero",                   "mascotas",  "#F472B6",4500, 95,  60, 5),
    # ── VKHOME (vkhome_cliente) ──────────────────────────────
    ("VKH-ORG-001","vkhome_cliente", "pla_blanco", "Organizador Escritorio VK","Set modular escritorio hogar-oficina 3 piezas",             "hogar",     "#A78BFA",3500, 95,  135,3),
    ("VKH-POT-001","vkhome_cliente", "pla_blanco", "Porta-Cables VK",          "Organizador cables escritorio adhesivo",                    "hogar",     "#A78BFA",1200, 30,  45, 8),
    ("VKH-COC-001","vkhome_cliente", "pla_blanco", "Soporte Cocina VK",        "Soporte utensilios cocina imantado",                       "cocina",    "#A78BFA",2800, 75,  105,4),
    ("VKH-DEC-001","vkhome_cliente", "pla_blanco", "Marco Foto 3D",            "Marco fotografico geometrico personalizable",               "deco",      "#A78BFA",2200, 60,  85, 4),
]

_TENANT_COLS = ("id","name","email","pwd","tel","tipo","sector","fecha","activo",
                "segmento","lead_source","potencial","canal_preferido","ciudad","rubro",
                "notas_agente","es_cliente_real","fecha_primer_contacto","linea_interes")

# ─────────────────────────────────────────────────────────
#  init_schema() — SEGURO para Streamlit Cloud
#  Crea tablas IF NOT EXISTS, inserta seed con OR IGNORE.
#  No borra nada. Cero efectos secundarios si ya existe todo.
# ─────────────────────────────────────────────────────────

def init_schema():
    """Inicializa el schema en producción. Seguro para llamar en cada arranque."""
    _engine = create_engine(f"sqlite:///{DB_PATH}")
    with _engine.connect() as conn:
        for _, ddl in TABLAS:
            conn.execute(text(ddl))

        for row in TENANTS_INICIALES:
            conn.execute(text("""
                INSERT OR IGNORE INTO tenants
                (id,name,email,password,telefono,tipo,sector,fecha_alta,activo,
                 segmento,lead_source,potencial,canal_preferido,ciudad,rubro,
                 notas_agente,es_cliente_real,fecha_primer_contacto,linea_interes)
                VALUES
                (:id,:name,:email,:pwd,:tel,:tipo,:sector,:fecha,:activo,
                 :segmento,:lead_source,:potencial,:canal_preferido,:ciudad,:rubro,
                 :notas_agente,:es_cliente_real,:fecha_primer_contacto,:linea_interes)
            """), dict(zip(_TENANT_COLS, row)))

        for tid, lid in TENANT_LINEAS_INICIALES:
            conn.execute(
                text("INSERT OR IGNORE INTO tenant_lineas (tenant_id, linea_id) VALUES (:tid, :lid)"),
                {"tid": tid, "lid": lid}
            )

        for row in MATERIALS_INICIALES:
            conn.execute(text("""
                INSERT OR IGNORE INTO materials
                (material_id,name,tipo,color,proveedor,stock_gr,cost_kg,stock_minimo_gr,fecha_compra,precio_compra)
                VALUES (:mid,:name,:tipo,:color,:prov,:stock,:cost,:min,:fcompra,:pcompra)
            """), dict(zip(["mid","name","tipo","color","prov","stock","cost","min","fcompra","pcompra"], row)))

        for row in PRODUCTS_AVIATION:
            conn.execute(text("""
                INSERT OR IGNORE INTO products
                (sku,client_id,material_id,name,description,categoria,color,
                 price,weight_gr,tiempo_impresion_min,stock)
                VALUES (:sku,:cid,:mid,:name,:desc,:cat,:color,:price,:weight,:tiempo,:stock)
            """), dict(zip(["sku","cid","mid","name","desc","cat","color","price","weight","tiempo","stock"], row)))

        for row in PRODUCTS_SOCIOS:
            conn.execute(text("""
                INSERT OR IGNORE INTO products
                (sku,client_id,material_id,name,description,categoria,color,
                 price,weight_gr,tiempo_impresion_min,stock)
                VALUES (:sku,:cid,:mid,:name,:desc,:cat,:color,:price,:weight,:tiempo,:stock)
            """), dict(zip(["sku","cid","mid","name","desc","cat","color","price","weight","tiempo","stock"], row)))

        # ── Migraciones para installs existentes ──────────────
        _migrations = [
            "ALTER TABLE orders ADD COLUMN maquina_id TEXT DEFAULT 'creality_k2_plus_01'",
            "ALTER TABLE orders ADD COLUMN horas_impresion REAL",
            "ALTER TABLE orders ADD COLUMN gramos_consumidos REAL",
            "ALTER TABLE orders ADD COLUMN costo_real REAL",
            "ALTER TABLE orders ADD COLUMN fallo_impresion INTEGER DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN motivo_fallo TEXT",
            "ALTER TABLE orders ADD COLUMN referencia_archivo TEXT",
            "ALTER TABLE orders ADD COLUMN fecha_entrega_solicitada TEXT",
            "ALTER TABLE senales_mercado ADD COLUMN segmento_detectado TEXT",
            "ALTER TABLE senales_mercado ADD COLUMN oportunidad TEXT",
        ]
        for _m in _migrations:
            try:
                conn.execute(text(_m))
            except Exception:
                pass  # columna ya existe

        # ── Actualizar password de vkhome si tiene valor legacy ──
        conn.execute(text(
            "UPDATE tenants SET password=:h WHERE id='vkhome_cliente' AND password='pendiente'"
        ), {"h": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"})

        conn.commit()

# ─────────────────────────────────────────────────────────
#  crear_schema() — DESTRUCTIVO, solo para instalación local
#  Borra todo y recrea desde cero.
# ─────────────────────────────────────────────────────────

def crear_schema():
    """Borra y recrea el schema completo. SOLO usar en local para instalación fresca."""
    _engine = create_engine(f"sqlite:///{DB_PATH}")
    with _engine.connect() as conn:
        print("🗑️  Eliminando tablas anteriores...")
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
                INSERT INTO tenants
                (id,name,email,password,telefono,tipo,sector,fecha_alta,activo,
                 segmento,lead_source,potencial,canal_preferido,ciudad,rubro,
                 notas_agente,es_cliente_real,fecha_primer_contacto,linea_interes)
                VALUES
                (:id,:name,:email,:pwd,:tel,:tipo,:sector,:fecha,:activo,
                 :segmento,:lead_source,:potencial,:canal_preferido,:ciudad,:rubro,
                 :notas_agente,:es_cliente_real,:fecha_primer_contacto,:linea_interes)
            """), dict(zip(_TENANT_COLS, row)))
            print(f"   ✅ {row[0]} — {row[1]}")
        print()

        print("🔗 Insertando vínculos multi-línea...")
        for tid, lid in TENANT_LINEAS_INICIALES:
            conn.execute(text("INSERT INTO tenant_lineas (tenant_id, linea_id) VALUES (:tid, :lid)"),
                         {"tid": tid, "lid": lid})
            print(f"   ✅ {tid} → {lid}")
        print()

        print("🧵 Insertando materiales...")
        for row in MATERIALS_INICIALES:
            conn.execute(text("""
                INSERT INTO materials
                (material_id,name,tipo,color,proveedor,stock_gr,cost_kg,stock_minimo_gr,fecha_compra,precio_compra)
                VALUES (:mid,:name,:tipo,:color,:prov,:stock,:cost,:min,:fcompra,:pcompra)
            """), dict(zip(["mid","name","tipo","color","prov","stock","cost","min","fcompra","pcompra"], row)))
            print(f"   ✅ {row[0]} — {row[1]}")
        print()

        print("✈️  Insertando productos Aviation Pro...")
        for row in PRODUCTS_AVIATION:
            conn.execute(text("""
                INSERT INTO products
                (sku,client_id,material_id,name,description,categoria,color,
                 price,weight_gr,tiempo_impresion_min,stock)
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


if __name__ == "__main__":
    crear_schema()

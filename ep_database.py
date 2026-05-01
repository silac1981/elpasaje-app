"""
╔══════════════════════════════════════════════════════════╗
║         EL PASAJE 3D STUDIO — BASE DE DATOS             ║
║         ep_database.py                                   ║
║         Motor: SQLite — escalable, sin servidor          ║
╚══════════════════════════════════════════════════════════╝

TABLAS:
  - clientes        → quién compra
  - productos       → qué se vende
  - odv_cabecera    → la orden completa
  - odv_detalle     → líneas de producto por orden
  - odv_insumos     → costo real de fabricación
  - log_agente      → patrones y senales detectadas
  - precios         → historial de precios por producto
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════

DB_PATH = Path(os.environ.get("EP_DB_PATH", 
    r"C:\Trabajo\ElPasaje\ep_pasaje.db"))

def get_conn():
    """Conexión a la base. Crea el archivo si no existe."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # devuelve dicts, no tuplas
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ══════════════════════════════════════════════════════
# CREACIÓN DE TABLAS
# ══════════════════════════════════════════════════════

def crear_tablas():
    """Crea todas las tablas si no existen. Seguro de correr múltiples veces."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    -- CLIENTES
    CREATE TABLE IF NOT EXISTS clientes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo          TEXT UNIQUE NOT NULL,        -- CLI-001
        nombre          TEXT NOT NULL,               -- VK-Home
        tipo            TEXT NOT NULL,               -- B2B / B2C / Corporativo / Feria
        canal_entrada   TEXT,                        -- Referido / Instagram / Feria
        vinculo         TEXT,                        -- "Agustina trabaja en VK-Home"
        potencial       TEXT DEFAULT 'Medio',        -- Alto / Medio / Bajo
        frecuencia      TEXT DEFAULT 'Unico',        -- Recurrente / Unico
        email           TEXT,
        telefono        TEXT,
        notas           TEXT,                        -- texto libre para el agente
        fecha_alta      TEXT DEFAULT (datetime('now')),
        activo          INTEGER DEFAULT 1
    );

    -- PRODUCTOS
    CREATE TABLE IF NOT EXISTS productos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo          TEXT UNIQUE NOT NULL,        -- PRD-001
        nombre          TEXT NOT NULL,               -- Bandeja chica 10x5cm
        marca_ep        TEXT NOT NULL,               -- El Pasaje Industrial / Magnitud 19 / etc
        categoria       TEXT NOT NULL,               -- Deco B2B / Pets-Tech / Corporativo / Deporte
        usuario_final   TEXT,                        -- Ejecutivo / Mascota / Hogar
        material        TEXT DEFAULT 'PLA',
        peso_gramos     REAL,                        -- del Slicer
        hs_maquina      REAL,                        -- horas de impresión
        costo_material  REAL,                        -- $ en insumos
        precio_mayorista REAL,                       -- precio B2B
        precio_minorista REAL,                       -- precio final consumidor
        personalizable  INTEGER DEFAULT 0,           -- 0=No / 1=Sí
        categoria_margen TEXT DEFAULT 'Medium',      -- High / Medium / Low
        contexto_uso    TEXT,                        -- "resuelve problema" / "estetica"
        notas           TEXT,
        fecha_alta      TEXT DEFAULT (datetime('now')),
        activo          INTEGER DEFAULT 1
    );

    -- ODV CABECERA
    CREATE TABLE IF NOT EXISTS odv_cabecera (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        id_odv          TEXT UNIQUE NOT NULL,        -- EP-2026-001
        cliente_id      INTEGER NOT NULL,
        canal_venta     TEXT,                        -- Feria / WhatsApp / B2B / Instagram
        fecha_pedido    TEXT NOT NULL,
        fecha_entrega   TEXT,
        estado          TEXT DEFAULT 'Cotización',   -- Cotización/Confirmado/Producción/Entregado/Cancelado
        categoria_margen TEXT DEFAULT 'Medium',
        responsable     TEXT,                        -- Fernando / Alejandra / Constantino
        notas           TEXT,                        -- TEXTO LIBRE — alimento del agente
        total_odv       REAL DEFAULT 0,
        fecha_creacion  TEXT DEFAULT (datetime('now')),
        fecha_mod       TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    );

    -- ODV DETALLE (líneas de producto)
    CREATE TABLE IF NOT EXISTS odv_detalle (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        id_odv          TEXT NOT NULL,
        nro_linea       INTEGER NOT NULL,
        producto_id     INTEGER NOT NULL,
        cantidad        REAL NOT NULL,
        precio_unitario REAL NOT NULL,
        descuento_pct   REAL DEFAULT 0,
        precio_final    REAL,                        -- calculado: precio_unitario * (1 - descuento)
        subtotal        REAL,                        -- calculado: cantidad * precio_final
        estado_linea    TEXT DEFAULT 'Pendiente',
        notas           TEXT,
        FOREIGN KEY (id_odv) REFERENCES odv_cabecera(id_odv),
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );

    -- ODV INSUMOS (manifiesto técnico - nivel 3)
    CREATE TABLE IF NOT EXISTS odv_insumos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        id_odv          TEXT NOT NULL,
        nro_linea       INTEGER NOT NULL,
        producto_id     INTEGER NOT NULL,
        material        TEXT,
        gramos_reales   REAL,                        -- del Slicer
        hs_maquina      REAL,
        costo_material  REAL,
        tarifa_kwh      REAL DEFAULT 150,            -- actualizar según boleta
        consumo_kw      REAL DEFAULT 0.15,           -- consumo impresora
        costo_energia   REAL,                        -- calculado
        costo_total     REAL,                        -- material + energía
        precio_venta    REAL,
        margen_pesos    REAL,
        margen_pct      REAL,
        responsable     TEXT,                        -- quién fabricó
        fecha_inicio    TEXT,
        fecha_fin       TEXT,
        FOREIGN KEY (id_odv) REFERENCES odv_cabecera(id_odv)
    );

    -- LOG DEL AGENTE
    CREATE TABLE IF NOT EXISTS log_agente (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha           TEXT DEFAULT (datetime('now')),
        proyecto        TEXT NOT NULL,               -- ElPasaje / SIA
        tipo            TEXT NOT NULL,               -- Patron / Anomalia / Senal / Alerta
        senal           TEXT NOT NULL,               -- descripción
        dato_observado  TEXT,
        accion_sugerida TEXT,
        estado          TEXT DEFAULT 'Pendiente',    -- Pendiente / Revisado / Implementado
        etiquetas       TEXT,                        -- "corporativo|b2b|ergonomico"
        confianza       REAL DEFAULT 0.7,            -- 0 a 1 — qué tan seguro está el agente
        origen          TEXT DEFAULT 'agente'        -- agente / manual
    );

    -- HISTORIAL DE PRECIOS
    CREATE TABLE IF NOT EXISTS precios_historial (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id     INTEGER NOT NULL,
        precio_mayorista REAL,
        precio_minorista REAL,
        costo_material  REAL,
        fecha           TEXT DEFAULT (datetime('now')),
        motivo          TEXT,                        -- "actualización insumos" / "cambio estrategia"
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"✅ Base de datos creada/verificada en: {DB_PATH}")

# ══════════════════════════════════════════════════════
# FUNCIONES DE CARGA
# ══════════════════════════════════════════════════════

def cargar_datos_iniciales():
    """Carga los primeros datos reales de El Pasaje."""
    conn = get_conn()
    cur = conn.cursor()

    # Cliente — VK-Home / Agustina
    cur.execute("""
        INSERT OR IGNORE INTO clientes 
        (codigo, nombre, tipo, canal_entrada, vinculo, potencial, frecuencia, notas)
        VALUES (?,?,?,?,?,?,?,?)
    """, ("CLI-001", "VK-Home (Agustina)", "B2B", "Referido",
          "Agustina trabaja en VK-Home — negocio de decoración de la hermana",
          "Alto", "Recurrente",
          "Primera cliente B2B real. Logró colocar bandejas y apoya-cosas. Canal deco/expo."))

    # Cliente — Oasis Animal
    cur.execute("""
        INSERT OR IGNORE INTO clientes
        (codigo, nombre, tipo, canal_entrada, potencial, frecuencia, notas)
        VALUES (?,?,?,?,?,?,?)
    """, ("CLI-002", "Oasis Animal", "B2B", "Directo",
          "Alto", "Recurrente",
          "Pide portapatos adaptables, llaveros y portabolsitas para feria. Segmento Pets-Tech."))

    # Productos — Bandejas VK-Home
    productos = [
        ("PRD-001", "Bandeja chica 10x5cm",             "El Pasaje Industrial", "Deco B2B",    "Hogar/Deco", "PLA", 80,  3.0, 1500, 3000, 4500),
        ("PRD-002", "Bandeja mediana 20x7cm",            "El Pasaje Industrial", "Deco B2B",    "Hogar/Deco", "PLA", 150, 5.0, 3000, 6000, 9000),
        ("PRD-003", "Bandeja grande 30x10cm",            "El Pasaje Industrial", "Deco B2B",    "Hogar/Deco", "PLA", 280, 4.0, 5000, 10000,15000),
        ("PRD-004", "Bandeja patitas redondas Negro mate","El Pasaje Industrial", "Deco B2B",    "Hogar/Deco", "PLA", 230, 4.0, 4000, 8000, 12000),
        ("PRD-005", "Bandeja patitas redondas Mármol",   "El Pasaje Industrial", "Deco B2B",    "Hogar/Deco", "PLA", 230, 4.0, 4000, 8000, 12000),
        ("PRD-006", "Elevador de notebook",              "Magnitud 19",          "Corporativo", "Ejecutivo",  "PLA", 300, 5.0, 4500, 9000, 15000),
    ]

    for p in productos:
        cur.execute("""
            INSERT OR IGNORE INTO productos
            (codigo, nombre, marca_ep, categoria, usuario_final, material,
             peso_gramos, hs_maquina, costo_material, precio_mayorista, precio_minorista,
             categoria_margen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,'High')
        """, p)

    # ODV Cabecera — primer pedido real
    cur.execute("""
        INSERT OR IGNORE INTO odv_cabecera
        (id_odv, cliente_id, canal_venta, fecha_pedido, fecha_entrega,
         estado, categoria_margen, responsable, notas)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, ("EP-2026-001", 1, "B2B - Referido", "2026-03-28", "2026-03-30",
          "Producción", "High", "Fernando",
          "3 juegos de bandejas (chica/mediana/grande) + 4 bandejas con patitas redondas. Cliente expo próxima. Muy buena recepción del producto."))

    # ODV Detalle
    lineas = [
        ("EP-2026-001", 1, 1, 2,  3000, 0),   # 2 bandejas chicas
        ("EP-2026-001", 2, 2, 2,  6000, 0),   # 2 medianas
        ("EP-2026-001", 3, 3, 1,  10000, 0),  # 1 grande
        ("EP-2026-001", 4, 4, 3,  8000, 0),   # 3 negras mate
        ("EP-2026-001", 5, 5, 1,  8000, 0),   # 1 mármol
    ]
    for ln in lineas:
        id_odv, nro, prod_id, cant, precio, desc = ln
        precio_final = precio * (1 - desc)
        subtotal = cant * precio_final
        cur.execute("""
            INSERT OR IGNORE INTO odv_detalle
            (id_odv, nro_linea, producto_id, cantidad, precio_unitario,
             descuento_pct, precio_final, subtotal, estado_linea)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (id_odv, nro, prod_id, cant, precio, desc, precio_final, subtotal, "Producción"))

    # Actualizar total ODV
    cur.execute("""
        UPDATE odv_cabecera SET total_odv = (
            SELECT SUM(subtotal) FROM odv_detalle WHERE id_odv = 'EP-2026-001'
        ) WHERE id_odv = 'EP-2026-001'
    """)

    # ODV Insumos
    insumos = [
        ("EP-2026-001", 1, 1, "PLA", 80,  3.0, 1500, 150, 0.15),
        ("EP-2026-001", 2, 2, "PLA", 150, 5.0, 3000, 150, 0.15),
        ("EP-2026-001", 3, 3, "PLA", 280, 4.0, 5000, 150, 0.15),
        ("EP-2026-001", 4, 4, "PLA", 230, 4.0, 4000, 150, 0.15),
        ("EP-2026-001", 5, 5, "PLA", 230, 4.0, 4000, 150, 0.15),
    ]
    for ins in insumos:
        id_odv, nro, prod_id, mat, gr, hs, cmat, kwh, kw = ins
        cenergia = hs * kw * kwh
        ctotal = cmat + cenergia
        cur.execute("""
            INSERT OR IGNORE INTO odv_insumos
            (id_odv, nro_linea, producto_id, material, gramos_reales,
             hs_maquina, costo_material, tarifa_kwh, consumo_kw,
             costo_energia, costo_total)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (id_odv, nro, prod_id, mat, gr, hs, cmat, kwh, kw, cenergia, ctotal))

    # Primera entrada del log
    cur.execute("""
        INSERT OR IGNORE INTO log_agente
        (proyecto, tipo, senal, dato_observado, accion_sugerida, etiquetas, confianza, origen)
        VALUES (?,?,?,?,?,?,?,?)
    """, ("ElPasaje", "Senal de Mercado",
          "Muy buena recepción elevadores de notebook en entorno corporativo",
          "Gerente Aerolíneas + Pablo (profe) + companero — perfil ejecutivo",
          "Desarrollar línea corporativa elevadores — segmento diferenciado de feria",
          "corporativo|ergonomico|b2b_potencial|magnitud19",
          0.85, "manual"))

    conn.commit()
    conn.close()
    print("✅ Datos iniciales cargados")

# ══════════════════════════════════════════════════════
# FUNCIONES DE CONSULTA
# ══════════════════════════════════════════════════════

def get_resumen_dia():
    """Resumen del día para el agente."""
    conn = get_conn()
    cur = conn.cursor()

    odv = cur.execute("""
        SELECT COUNT(*) as total, SUM(total_odv) as facturado
        FROM odv_cabecera
        WHERE DATE(fecha_creacion) = DATE('now')
    """).fetchone()

    produccion = cur.execute("""
        SELECT COUNT(*) as en_produccion FROM odv_cabecera
        WHERE estado = 'Producción'
    """).fetchone()

    pendientes = cur.execute("""
        SELECT COUNT(*) as pendientes FROM odv_cabecera
        WHERE estado IN ('Cotización', 'Confirmado')
    """).fetchone()

    conn.close()
    return {
        "odv_hoy": odv["total"],
        "facturado_hoy": odv["facturado"] or 0,
        "en_produccion": produccion["en_produccion"],
        "pendientes_confirmar": pendientes["pendientes"],
    }

def get_productos_mas_vendidos(limit=5):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT p.nombre, p.marca_ep, p.categoria,
               SUM(d.cantidad) as unidades,
               SUM(d.subtotal) as revenue
        FROM odv_detalle d
        JOIN productos p ON d.producto_id = p.id
        GROUP BY p.id
        ORDER BY revenue DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def registrar_log(proyecto, tipo, senal, dato="", accion="", etiquetas="", confianza=0.7, origen="agente"):
    conn = get_conn()
    conn.execute("""
        INSERT INTO log_agente
        (proyecto, tipo, senal, dato_observado, accion_sugerida, etiquetas, confianza, origen)
        VALUES (?,?,?,?,?,?,?,?)
    """, (proyecto, tipo, senal, dato, accion, etiquetas, confianza, origen))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🏗️  Inicializando base de datos El Pasaje...")
    crear_tablas()
    cargar_datos_iniciales()
    
    print("\n📊 Verificando datos:")
    resumen = get_resumen_dia()
    for k, v in resumen.items():
        print(f"   {k}: {v}")
    
    print("\n🏆 Productos cargados:")
    for p in get_productos_mas_vendidos(10):
        print(f"   {p['nombre']} ({p['marca_ep']}) — {p['unidades']} u — ${p['revenue']:,.0f}")

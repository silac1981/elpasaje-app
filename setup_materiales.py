"""Carga inicial real de materiales desde catalogo MakerPanda."""
import sqlite3
import sys

if "--confirmar" not in sys.argv:
    print("Script de setup. Ejecutar con --confirmar para aplicar.")
    sys.exit(0)

conn = sqlite3.connect('elpasaje_v2.db')
c = conn.cursor()

PRECIO_PLA    = 24140
PRECIO_SILK   = 23910
PRECIO_PETG   = 19920
PRECIO_ASA    = 34999
PRECIO_MADERA = 23830

STOCK_PLA  = 25000
STOCK_SILK = 30000
STOCK_PETG = 25000
STOCK_ASA  = 30000

MIN_PLA  = 2000
MIN_SILK = 1000
MIN_PETG = 2000
MIN_ASA  = 1000

HOY  = '2026-05-28'
PROV = 'MakerPanda'

updates = [
    ('pla_negro',     'PLA Negro',     'PLA',  'Negro',   STOCK_PLA,  PRECIO_PLA,   MIN_PLA,  PRECIO_PLA),
    ('pla_blanco',    'PLA Blanco',    'PLA',  'Blanco',  STOCK_PLA,  PRECIO_PLA,   MIN_PLA,  PRECIO_PLA),
    ('pla_rosa',      'PLA Rosa',      'PLA',  'Rosa',    STOCK_PLA,  PRECIO_PLA,   MIN_PLA,  PRECIO_PLA),
    ('pla_seda_azul', 'PLA Silk Azul', 'SILK', 'Azul',    STOCK_SILK, PRECIO_SILK,  MIN_SILK, PRECIO_SILK),
    ('pla_seda_gris', 'PLA Silk Gris', 'SILK', 'Gris',    STOCK_SILK, PRECIO_SILK,  MIN_SILK, PRECIO_SILK),
    ('petg_gris',     'PETG Gris',     'PETG', 'Gris',    STOCK_PETG, PRECIO_PETG,  MIN_PETG, PRECIO_PETG),
    ('petg_naranja',  'PETG Naranja',  'PETG', 'Naranja', STOCK_PETG, PRECIO_PETG,  MIN_PETG, PRECIO_PETG),
]

for u in updates:
    c.execute(
        'UPDATE materials SET name=?, tipo=?, color=?, proveedor=?, stock_gr=?, '
        'cost_kg=?, stock_minimo_gr=?, precio_compra=?, activo=1 WHERE material_id=?',
        (u[1], u[2], u[3], PROV, u[4], u[5], u[6], u[7], u[0])
    )
print(f'Actualizados: {len(updates)} existentes')

nuevos = [
    # PLA
    ('pla_celeste',          'PLA Celeste',           'PLA',  'Celeste',         STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_azul_marino',      'PLA Azul Marino',       'PLA',  'Azul Marino',     STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_azul_hielo',       'PLA Azul Hielo',        'PLA',  'Azul Hielo',      STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_rojo',             'PLA Rojo',              'PLA',  'Rojo',            STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_rojo_borgona',     'PLA Rojo Borgona',      'PLA',  'Rojo Borgona',    STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_verde',            'PLA Verde',             'PLA',  'Verde',           STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_verde_turquesa',   'PLA Verde Turquesa',    'PLA',  'Verde Turquesa',  STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_naranja',          'PLA Naranja',           'PLA',  'Naranja',         STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_amarillo',         'PLA Amarillo',          'PLA',  'Amarillo',        STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_amarillo_solar',   'PLA Amarillo Solar',    'PLA',  'Amarillo Solar',  STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_gris',             'PLA Gris',              'PLA',  'Gris',            STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_gris_pizarra',     'PLA Gris Pizarra',      'PLA',  'Gris Pizarra',    STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_violeta',          'PLA Violeta',           'PLA',  'Violeta',         STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_lavanda',          'PLA Lavanda',           'PLA',  'Lavanda',         STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_menta',            'PLA Menta',             'PLA',  'Menta',           STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_beige',            'PLA Beige',             'PLA',  'Beige',           STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_marron',           'PLA Marron',            'PLA',  'Marron',          STOCK_PLA,  PRECIO_PLA,    MIN_PLA,  PRECIO_PLA),
    ('pla_madera',           'PLA Madera',            'PLA',  'Madera',          STOCK_PLA,  PRECIO_MADERA, MIN_PLA,  PRECIO_MADERA),
    # SILK
    ('pla_silk_dorado',        'PLA Silk Dorado',       'SILK', 'Dorado',          STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    ('pla_silk_cobre',         'PLA Silk Cobre',        'SILK', 'Cobre',           STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    ('pla_silk_negro_rojo',    'PLA Silk Negro/Rojo',   'SILK', 'Negro Rojo',      STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    ('pla_silk_negro_violeta', 'PLA Silk Negro/Violeta','SILK', 'Negro Violeta',   STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    ('pla_silk_azul_violeta',  'PLA Silk Azul/Violeta', 'SILK', 'Azul Violeta',    STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    ('pla_silk_azul_verde',    'PLA Silk Azul/Verde',   'SILK', 'Azul Verde',      STOCK_SILK, PRECIO_SILK,   MIN_SILK, PRECIO_SILK),
    # PETG
    ('petg_negro',       'PETG Negro',        'PETG', 'Negro',       STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_blanco',      'PETG Blanco',       'PETG', 'Blanco',      STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_azul',        'PETG Azul',         'PETG', 'Azul',        STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_rojo',        'PETG Rojo',         'PETG', 'Rojo',        STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_verde',       'PETG Verde',        'PETG', 'Verde',       STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_amarillo',    'PETG Amarillo',     'PETG', 'Amarillo',    STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_plateado',    'PETG Plateado',     'PETG', 'Plateado',    STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    ('petg_translucido', 'PETG Translucido',  'PETG', 'Translucido', STOCK_PETG, PRECIO_PETG,   MIN_PETG, PRECIO_PETG),
    # ASA
    ('asa_negro',  'ASA Negro',  'ASA', 'Negro',  STOCK_ASA, PRECIO_ASA, MIN_ASA, PRECIO_ASA),
    ('asa_blanco', 'ASA Blanco', 'ASA', 'Blanco', STOCK_ASA, PRECIO_ASA, MIN_ASA, PRECIO_ASA),
]

insertados = 0
for n in nuevos:
    c.execute(
        'INSERT OR IGNORE INTO materials '
        '(material_id, name, tipo, color, proveedor, stock_gr, cost_kg, '
        'stock_minimo_gr, fecha_compra, precio_compra, activo) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,1)',
        (n[0], n[1], n[2], n[3], PROV, n[4], n[5], n[6], HOY, n[7])
    )
    if c.rowcount > 0:
        insertados += 1

conn.commit()

c.execute('SELECT tipo, COUNT(*), SUM(stock_gr)/1000 FROM materials WHERE activo=1 GROUP BY tipo ORDER BY tipo')
print(f'\nInsertados: {insertados} nuevos\n')
print('Resumen por tipo:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]} colores  |  {int(r[2])} kg stock total')
c.execute('SELECT COUNT(*) FROM materials WHERE activo=1')
print(f'\nTotal materiales activos: {c.fetchone()[0]}')
conn.close()

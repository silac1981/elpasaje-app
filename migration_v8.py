"""migration_v8.py — Seed productos Magnitud 19 + Melómano. Idempotente."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")

MAGNITUD_19 = [
    # (sku, name, client_id, price, weight_gr, stock, categoria, description, tipo_producto)
    ("M19-FDE-S", "Fidget de escritorio — Botones",    "admin",  8500, 45,  0, "Fidgets",        "Botones táctiles de diferentes resistencias. Anclaje para el hiperfoco. Respaldo Aldana.",       "propio_3d"),
    ("M19-FDE-R", "Fidget de escritorio — Rueda",      "admin",  9500, 52,  0, "Fidgets",        "Rueda giratoria de precisión. Mecanismo silencioso para reuniones y trabajo profundo.",          "propio_3d"),
    ("M19-FDE-T", "Fidget de escritorio — Texturas",   "admin",  8000, 38,  0, "Fidgets",        "Placa de texturas multisensorial. Para regulación sensorial en escritorio.",                     "propio_3d"),
    ("M19-FCO-U", "Fidget corporal — Reuniones",       "admin",  6500, 28,  0, "Fidgets",        "Para sostener en la mano durante presentaciones. Discreto, premium, efectivo.",                  "propio_3d"),
    ("M19-KRS-U", "Kit Regulación Sensorial Niños",    "admin", 22000,  0,  0, "Kits",           "Set validado por Aldana para niños neurodivergentes. 3 piezas + guía de uso.",                  "propio_3d"),
    ("M19-PNE-U", "Porta-notebook ejecutivo",          "admin", 18000, 380, 0, "Oficina",        "Negro/oro. Acabado premium. Para laptop 13-15 pulgadas.",                                       "propio_3d"),
    ("M19-BAN-U", "Bandeja de objetos personales",     "admin", 12000, 220, 0, "Oficina",        "Ancla de escritorio. Diseño para llaves, reloj, airpods, tarjetas.",                            "propio_3d"),
    ("M19-ORD-U", "Organizador de escritorio modular", "admin", 15000, 290, 0, "Oficina",        "Sistema modular expandible. Negro con detalles oro.",                                            "propio_3d"),
    ("M19-STB-U", "Stand de tablet — consultorio",     "admin", 14000, 260, 0, "Oficina",        "Para consultorios de Aldana y escritorios ejecutivos. Ajustable.",                              "propio_3d"),
    ("VC-QPR-U",  "Quiver Pro — soporte arco + 12 flechas",   "admin", 42000, 380, 0, "Vuelo Certero", "Soporte vertical arco + tubo 12 flechas + bandeja accesorios.",        "propio_3d"),
    ("VC-FJG-U",  "Fletcher Jig 360°",                "admin", 15000, 120, 0, "Vuelo Certero", "Jig de emplumado ajustable shafts 4-10mm. PETG + imanes.",                                      "propio_3d"),
    ("VC-TBX-U",  "Tournament Box — ajedrez",         "admin", 55000,   0, 0, "Vuelo Certero", "Caja magnética con tablero + compartimentos. Multicolor CFS.",                                   "propio_3d"),
    ("VC-PPT-U",  "Porta-pelotas tenis (3u)",         "admin", 10000,  90, 0, "Vuelo Certero", "Soporte de pared o escritorio para 3 pelotas de tenis.",                                         "propio_3d"),
    ("VC-PRA-U",  "Porta-raqueta de pared premium",   "admin", 16000, 150, 0, "Vuelo Certero", "Diseño premium. Sin el genérico de Amazon.",                                                     "propio_3d"),
]

MELOMANO = [
    ("MEL-VSO-U", "Vinyl Sommelier — 27 divisores A-Z+#", "fer_produccion", 67000, 420, 0, "Organización",  "Divisores con letras doradas fabricados en CFS. Para estante Ikea Kallax. El set completo.",   "propio_3d"),
    ("MEL-HWS-U", "Heavyweight Stabilizer",               "fer_produccion", 30000, 335, 0, "Audio técnico", "Peso de plato 320-350g cargado con monedas de peso real. Iniciales grabadas. Mejora la reproducción.", "propio_3d"),
    ("MEL-ISQ-U", "Iso-Spike Quartet — 4 spikes",         "fer_produccion", 27000, 180, 0, "Audio técnico", "Desacoplantes para parlantes. Base PETG + punta TPU. Reducción de vibración real y medible.",   "propio_3d"),
    ("MEL-NPP-U", "Now Playing Premium",                   "fer_produccion", 23000, 160, 0, "Display",       "Expone el vinilo que está sonando. Base de corcho. Silueta tocadiscos o guitarra.",             "propio_3d"),
    ("MEL-ADH-U", "Audiophile Desk Hub",                   "fer_produccion", 42000, 480, 0, "Escritorio",    "Auriculares + porta-cartuchos + cables + bandeja stylus. Para el escritorio del melómano serio.", "propio_3d"),
    ("MEL-SAU-U", "Stand armónica y ukelele",              "fer_produccion", 15000, 140, 0, "Instrumento",   "Para el músico con instrumentos pequeños en el espacio de escucha.",                            "propio_3d"),
    ("MEL-PNB-U", "Porta-notebook Melómano",               "fer_produccion", 16000, 350, 0, "Escritorio",    "Negro/cobre. El escritorio del que trabaja escuchando vinilo.",                                  "propio_3d"),
]


def run():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    for sku, name, cid, price, weight_gr, stock, categoria, description, tipo in (MAGNITUD_19 + MELOMANO):
        cur.execute("""
            INSERT OR IGNORE INTO products
              (sku, name, client_id, price, weight_gr, stock,
               categoria, description, tipo_producto, activo, visibilidad)
            VALUES (?,?,?,?,?,?,?,?,?,1,'publico')
        """, (sku, name, cid, price, weight_gr, stock, categoria, description, tipo))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run()
    print("migration_v8 OK — productos M19 + Melómano insertados")
